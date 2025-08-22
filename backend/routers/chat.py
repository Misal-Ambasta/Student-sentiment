import os
import uuid
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from pydantic import BaseModel

from database import get_db, ChatSession, ChatMessage
from vector_store import get_chroma_manager
from llm_integration import get_llm_manager, LLMProvider

router = APIRouter()

# Pydantic models for request validation
class ChatQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    response_format: Optional[str] = None
    auto_classify: Optional[bool] = True

@router.post("/query")
async def chat_query(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Process a chat query using RAG with automatic classification"""
    try:
        # Extract values from request
        query = request.query
        session_id = request.session_id
        student_id = request.student_id
        course_id = request.course_id
        response_format = request.response_format
        auto_classify = request.auto_classify
        
        # Auto-classify query if enabled and no response_format provided
        if auto_classify and not response_format:
            classification_result = await classify_query(query)
            response_format = classification_result["query_type"]
            
            # Extract parameters from classification if not already provided
            extracted_params = classification_result.get("parameters", {})
            if not course_id and "course_id" in extracted_params:
                course_id = extracted_params["course_id"]
            if not student_id and "student_id" in extracted_params:
                student_id = extracted_params["student_id"]
            
            logger.info(f"Auto-classified query as: {response_format}")
            if extracted_params:
                logger.info(f"Extracted parameters: {extracted_params}")
        
        # Create session if not provided or if session doesn't exist
        if not session_id:
            session_id = str(uuid.uuid4())
            
            # Create session in database
            session = ChatSession(
                session_id=session_id,
                title=query[:50] + "..." if len(query) > 50 else query
            )
            db.add(session)
            await db.commit()
        else:
            # Check if session exists, create if not
            from sqlalchemy import select
            result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
            existing_session = result.scalar_one_or_none()
            
            if not existing_session:
                # Create session in database
                session = ChatSession(
                    session_id=session_id,
                    title=query[:50] + "..." if len(query) > 50 else query
                )
                db.add(session)
                await db.commit()
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=query
        )
        db.add(user_message)
        await db.commit()
        
        # Process query
        response = await process_query(query, session_id, student_id, course_id, response_format)
        
        # Parse JSON response for structured analysis types
        parsed_response = response
        analysis_type = None
        if response_format in ["individual_analysis", "weekly_report", "segmentation_analysis", "aspect_analysis"]:
            try:
                import json
                parsed_response = json.loads(response)
                analysis_type = parsed_response.get("type")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response for {response_format}")
                parsed_response = response
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response
        )
        db.add(assistant_message)
        await db.commit()
        
        return {
            "session_id": session_id,
            "query": query,
            "response": parsed_response,
            "classification": response_format,
            "analysis_type": analysis_type
        }
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/stream")
async def websocket_endpoint(
    websocket: WebSocket,
    query: str,
    session_id: Optional[str] = None,
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    response_format: Optional[str] = None,
    auto_classify: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for streaming chat responses with automatic classification"""
    await websocket.accept()
    
    try:
        # Auto-classify query if enabled and no response_format provided
        if auto_classify and not response_format:
            classification_result = await classify_query(query)
            response_format = classification_result["query_type"]
            
            # Extract parameters from classification if not already provided
            extracted_params = classification_result.get("parameters", {})
            if not course_id and "course_id" in extracted_params:
                course_id = extracted_params["course_id"]
            if not student_id and "student_id" in extracted_params:
                student_id = extracted_params["student_id"]
            
            logger.info(f"Auto-classified query as: {response_format}")
            if extracted_params:
                logger.info(f"Extracted parameters: {extracted_params}")
            
            # Send classification result to frontend
            await websocket.send_text(json.dumps({
                "type": "classification",
                "classification": response_format,
                "confidence": classification_result.get("confidence", "high"),
                "parameters": extracted_params
            }))
        
        # Create session if not provided or if session doesn't exist
        if not session_id:
            session_id = str(uuid.uuid4())
            
            # Create session in database
            session = ChatSession(
                session_id=session_id,
                title=query[:50] + "..." if len(query) > 50 else query
            )
            db.add(session)
            await db.commit()
        else:
            # Check if session exists, create if not
            from sqlalchemy import select
            result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
            existing_session = result.scalar_one_or_none()
            
            if not existing_session:
                # Create session in database
                session = ChatSession(
                    session_id=session_id,
                    title=query[:50] + "..." if len(query) > 50 else query
                )
                db.add(session)
                await db.commit()
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=query
        )
        db.add(user_message)
        await db.commit()
        
        # Send session info to frontend
        await websocket.send_text(json.dumps({
            "type": "session_info",
            "session_id": session_id
        }))
        
        # Stream response
        logger.info(f"Starting to stream response for query: {query}")
        full_response = ""
        try:
            async for chunk in stream_response(query, session_id, student_id, course_id, response_format):
                logger.info(f"Received chunk from stream_response: {chunk[:100]}...")
                # The stream_response function yields the complete response at once
                # so we handle it as a complete response rather than streaming chunks
                full_response = chunk
                break  # Since stream_response yields the complete response, we only need the first yield
            logger.info(f"Completed streaming, full_response length: {len(full_response)}")
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            raise
        
        # Send response based on format type
        if response_format in ["individual_analysis", "weekly_report", "segmentation_analysis", "aspect_analysis"]:
            # For structured analysis types, parse and send the complete JSON response
            try:
                parsed_response = json.loads(full_response)
                await websocket.send_text(json.dumps({
                    "type": "structured_response",
                    "analysis_type": response_format,
                    "data": parsed_response
                }))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response for {response_format}")
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "content": full_response
                }))
        else:
            # For general questions and other types, send as regular response
            await websocket.send_text(json.dumps({
                "type": "response",
                "content": full_response
            }))
        
        # Send completion signal
        await websocket.send_text(json.dumps({
            "type": "complete",
            "session_id": session_id
        }))
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_message)
        await db.commit()
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            pass  # WebSocket might already be closed

def calculate_classification_confidence(query: str, classification: str) -> float:
    """Calculate confidence score for query classification based on keyword matching"""
    query_lower = query.lower()
    
    # Define keyword patterns for each classification type
    classification_keywords = {
        "individual_analysis": ["student", "analyze", "performance", "individual", "specific", "id", "name"],
        "weekly_report": ["weekly", "report", "batch", "overall", "comprehensive", "summary", "week"],
        "segmentation_analysis": ["compare", "demographic", "segment", "group", "vs", "versus", "professional", "graduate"],
        "aspect_analysis": ["course", "aspect", "sherpa", "support", "instructor", "feedback", "module"],
        "general_question": ["what", "how", "why", "explain", "general", "about"],
        "student_analysis": ["student", "satisfaction", "performance", "progress", "achievement"],
        "trend_analysis": ["trend", "pattern", "over time", "historical", "change", "evolution"],
        "recommendation": ["recommend", "suggest", "advice", "should", "best", "improve"]
    }
    
    # Get keywords for the classified type
    keywords = classification_keywords.get(classification, [])
    
    if not keywords:
        return 0.5  # Medium confidence for unknown classifications
    
    # Count keyword matches
    matches = sum(1 for keyword in keywords if keyword in query_lower)
    
    # Calculate confidence based on keyword density
    if matches == 0:
        return 0.4  # Low confidence if no keywords match
    elif matches == 1:
        return 0.6  # Medium confidence for single match
    elif matches == 2:
        return 0.8  # High confidence for multiple matches
    else:
        return 0.9  # Very high confidence for many matches

@router.get("/classify")
async def classify_query(query: str):
    """Classify a query to determine intent and extract parameters"""
    try:
        llm_manager = get_llm_manager()
        
        # Create classification prompt
        prompt = f"""
        Classify the following query and extract any parameters.
        
        Categories:
        - individual_analysis: Questions asking for analysis of a specific student
        - weekly_report: Questions asking for weekly reports or comprehensive batch analysis
        - segmentation_analysis: Questions asking for demographic-based group comparisons
        - aspect_analysis: Questions asking for detailed analysis of specific course aspects
        - general_question: General questions about education or the platform
        - student_analysis: Questions about specific student performance or satisfaction
        - trend_analysis: Questions about trends or patterns in student data
        - recommendation: Requests for recommendations or suggestions
        - other: Queries that don't fit into the above categories
        
        Query: {query}
        
        Return ONLY a JSON object in this exact format:
        {{
            "category": "category_name",
            "course_id": "extracted_course_id_or_null",
            "student_id": "extracted_student_id_or_null",
            "week_number": "extracted_week_number_or_null"
        }}
        
        Examples:
        - "Generate weekly report for course id: fsd25" -> {{"category": "weekly_report", "course_id": "fsd25", "student_id": null, "week_number": null}}
        - "Analyze student fsd25_001" -> {{"category": "individual_analysis", "course_id": null, "student_id": "fsd25_001", "week_number": null}}
        - "Hi" -> {{"category": "general_question", "course_id": null, "student_id": null, "week_number": null}}
        """
        
        # Get classification
        classification_response = await llm_manager.generate_response(
            prompt=prompt,
            preferred_provider=LLMProvider.GROQ  # Use Groq for classification (fast)
        )
        
        # Parse JSON response
        import json
        try:
            classification_data = json.loads(classification_response.strip())
            classification = classification_data.get("category", "other").lower()
            extracted_course_id = classification_data.get("course_id")
            extracted_student_id = classification_data.get("student_id")
            extracted_week_number = classification_data.get("week_number")
        except json.JSONDecodeError:
            # Fallback to old behavior if JSON parsing fails
            classification = classification_response.strip().lower()
            extracted_course_id = None
            extracted_student_id = None
            extracted_week_number = None
        
        # Validate classification
        valid_categories = [
            "individual_analysis",
            "weekly_report",
            "segmentation_analysis",
            "aspect_analysis",
            "general_question",
            "student_analysis",
            "trend_analysis",
            "recommendation",
            "other"
        ]
        
        # Calculate confidence based on keyword matching and classification certainty
        confidence = calculate_classification_confidence(query, classification)
        
        if classification not in valid_categories:
            classification = "other"
            confidence = 0.3  # Low confidence for fallback classification
        
        # Prepare parameters
        parameters = {}
        if extracted_course_id and extracted_course_id != "null":
            parameters["course_id"] = extracted_course_id
        if extracted_student_id and extracted_student_id != "null":
            parameters["student_id"] = extracted_student_id
        if extracted_week_number and extracted_week_number != "null":
            parameters["week_number"] = extracted_week_number
        
        return {
            "query_type": classification,
            "confidence": confidence,
            "suggested_format": "json" if classification in ["individual_analysis", "weekly_report", "segmentation_analysis", "aspect_analysis"] else "text",
            "parameters": parameters
        }
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_suggestions(context: Optional[str] = None):
    """Get query suggestions based on context"""
    try:
        llm_manager = get_llm_manager()
        
        # Create suggestions prompt
        prompt = f"""
        Generate 5 useful query suggestions for an educational analytics platform.
        The suggestions should be diverse and cover different aspects of student performance and satisfaction.
            
        {f"Context: {context}" if context else ""}
        
        Return the suggestions as a numbered list, one per line, without any additional text.
        """
        
        # Get suggestions
        suggestions_text = await llm_manager.generate_response(
            prompt=prompt,
            preferred_provider=LLMProvider.GROQ  # Use Groq for suggestions (fast)
        )
        
        # Parse suggestions
        suggestions = []
        for line in suggestions_text.strip().split("\n"):
            # Remove numbering and whitespace
            suggestion = line.strip()
            if suggestion:
                # Remove numbering (e.g., "1. ", "2) ", etc.)
                suggestion = suggestion.lstrip("0123456789.)").strip()
                suggestions.append(suggestion)
        
        # Limit to 5 suggestions
        suggestions = suggestions[:5]
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_sessions(limit: int = 10, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Get list of chat sessions"""
    try:
        # Query sessions from database
        query = await db.execute(
            f"SELECT * FROM chat_sessions ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
        )
        sessions = query.fetchall()
        
        # Count total sessions
        count_query = await db.execute("SELECT COUNT(*) FROM chat_sessions")
        total = count_query.scalar()
        
        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                }
                for session in sessions
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get chat session details"""
    try:
        # Query session from database
        session_query = await db.execute(
            f"SELECT * FROM chat_sessions WHERE session_id = '{session_id}'"
        )
        session = session_query.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session with ID {session_id} not found")
        
        # Query messages from database
        messages_query = await db.execute(
            f"SELECT * FROM chat_messages WHERE session_id = '{session_id}' ORDER BY created_at ASC"
        )
        messages = messages_query.fetchall()
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at
                }
                for message in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a chat session"""
    try:
        # Query session from database
        session_query = await db.execute(
            f"SELECT * FROM chat_sessions WHERE session_id = '{session_id}'"
        )
        session = session_query.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session with ID {session_id} not found")
        
        # Delete messages from database
        await db.execute(f"DELETE FROM chat_messages WHERE session_id = '{session_id}'")
        
        # Delete session from database
        await db.execute(f"DELETE FROM chat_sessions WHERE session_id = '{session_id}'")
        
        await db.commit()
        
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_query(
    query: str,
    session_id: str,
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    response_format: Optional[str] = None
) -> str:
    """Process a chat query using RAG"""
    try:
        # Get managers
        chroma_manager = get_chroma_manager()
        llm_manager = get_llm_manager()
        
        # Determine template type based on response format
        template_type = "general"
        if response_format == "student_analysis":
            template_type = "student_analysis"
        elif response_format == "summarization":
            template_type = "summarization"
        elif response_format == "individual_analysis":
            template_type = "individual_analysis"
        elif response_format == "weekly_report":
            template_type = "weekly_report"
        elif response_format == "segmentation_analysis":
            template_type = "segmentation_analysis"
        elif response_format == "aspect_analysis":
            template_type = "aspect_analysis"
        
        # Prepare filter metadata
        filter_metadata = {}
        if student_id:
            filter_metadata["student_id"] = student_id
        if course_id:
            filter_metadata["course_id"] = course_id
        
        # Search for relevant documents
        survey_docs = await chroma_manager.search_survey_data(
            query=query,
            filter_metadata=filter_metadata if filter_metadata else None,
            k=5
        )
        
        student_docs = []
        if student_id:
            student_docs = await chroma_manager.search_student_data(
                query=query,
                filter_metadata={"student_id": student_id},
                k=3
            )
        elif response_format == "segmentation_analysis":
            # For segmentation analysis, get both demographic data and survey responses
            demographic_docs = await chroma_manager.search_student_data(
                query="demographic_type Working Professional Fresh Graduate Career Switcher",
                filter_metadata={"document_type": "demographics"},
                k=20  # Get more documents for comprehensive analysis
            )
            
            # Also get survey responses for course rating calculations
            survey_response_docs = await chroma_manager.search_survey_data(
                query="Course A Course B CSBT experience rating score aspect",
                filter_metadata={"document_type": "survey"},
                k=30  # Get survey responses for course calculations
            )
            
            student_docs = demographic_docs + survey_response_docs
        
        # Combine documents
        documents = survey_docs + student_docs
        
        if not documents:
            # No relevant documents found, use general response
            prompt = f"""
            You are an AI assistant for an educational platform. Answer the following question:
            
            {query}
            
            If you don't know the answer, just say that you don't have enough information.
            """
            
            return await llm_manager.generate_response(prompt=prompt)
        
        # Generate RAG response
        response = await llm_manager.rag_chat_response(
            question=query,
            documents=documents,
            template_type=template_type
        )
        
        return response
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise

async def stream_response(
    query: str,
    session_id: str,
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    response_format: Optional[str] = None
):
    """Stream a chat response using RAG"""
    try:
        # Get managers
        chroma_manager = get_chroma_manager()
        llm_manager = get_llm_manager()
        
        # Determine template type based on response format
        template_type = "general"
        if response_format == "student_analysis":
            template_type = "student_analysis"
        elif response_format == "summarization":
            template_type = "summarization"
        elif response_format == "individual_analysis":
            template_type = "individual_analysis"
        elif response_format == "weekly_report":
            template_type = "weekly_report"
        elif response_format == "segmentation_analysis":
            template_type = "segmentation_analysis"
        elif response_format == "aspect_analysis":
            template_type = "aspect_analysis"
        
        # Prepare filter metadata
        filter_metadata = {}
        if student_id:
            filter_metadata["student_id"] = student_id
        if course_id:
            filter_metadata["course_id"] = course_id
        
        # Search for relevant documents
        survey_docs = await chroma_manager.search_survey_data(
            query=query,
            filter_metadata=filter_metadata if filter_metadata else None,
            k=5
        )
        
        student_docs = []
        if student_id:
            student_docs = await chroma_manager.search_student_data(
                query=query,
                filter_metadata={"student_id": student_id},
                k=3
            )
        
        # Combine documents
        documents = survey_docs + student_docs
        
        if not documents:
            # No relevant documents found, use general response
            prompt = f"""
            You are an AI assistant for an educational platform. Answer the following question:
            
            {query}
            
            If you don't know the answer, just say that you don't have enough information.
            """
            
            # Generate response (not streaming for simple case)
            response = await llm_manager.generate_response(
                prompt=prompt
            )
            yield response
        else:
            # Generate RAG response (not streaming for now)
            response = await llm_manager.rag_chat_response(
                question=query,
                documents=documents,
                template_type=template_type
            )
            yield response
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        yield f"Error: {str(e)}"