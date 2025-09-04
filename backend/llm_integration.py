import os
import enum
import json
from typing import Dict, List, Any, Optional, Union, Callable
from loguru import logger
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from confidence_calculator import get_confidence_calculator

class LLMProvider(enum.Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"

class MultiLLMManager:
    def __init__(self):
        # Initialize API keys from environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Initialize LLM models
        self.llm_models = {}
        self._init_llm_models()
        
        # Initialize RAG templates
        self.rag_templates = {}
        self._init_rag_templates()
        
        logger.info("LLM Manager initialized successfully")
    
    def _init_llm_models(self):
        """Initialize LLM models"""
        try:
            # Initialize Gemini model
            if self.google_api_key:
                self.llm_models[LLMProvider.GEMINI] = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.google_api_key,
                    temperature=0.7,
                    max_output_tokens=2048
                )
                logger.info("Gemini model initialized")
            else:
                logger.warning("Google API key not found, Gemini model not initialized")
            
            # Initialize Groq model
            if self.groq_api_key:
                self.llm_models[LLMProvider.GROQ] = ChatGroq(
                    model="openai/gpt-oss-120b",
                    api_key=self.groq_api_key,
                    temperature=0.4,
                    top_p=0.95,
                    max_tokens=2048,
                    streaming=True
                )
                logger.info("Groq model initialized")
            else:
                logger.warning("Groq API key not found, Groq model not initialized")
            
            # Initialize OpenAI model
            if self.openai_api_key:
                self.llm_models[LLMProvider.OPENAI] = ChatOpenAI(
                    model="gpt-4o",
                    api_key=self.openai_api_key,
                    temperature=0.7,
                    top_p=0.95,
                    max_tokens=2048,
                    streaming=True
                )
                logger.info("OpenAI model initialized")
            else:
                logger.warning("OpenAI API key not found, OpenAI model not initialized")
        except Exception as e:
            logger.error(f"Error initializing LLM models: {e}")
            raise
    
    def _init_rag_templates(self):
        """Initialize RAG templates"""
        try:
            # Student analysis template
            student_analysis_template = """
            You are an expert educational analyst tasked with providing insights about student performance and satisfaction.
            
            Use the following context information to provide a detailed analysis about the student:
            
            {context}
            
            Based on the above context, please provide a comprehensive analysis addressing the following aspects:
            1. Overall satisfaction level and trends over time
            2. Key strengths and areas of improvement in the student's experience
            3. Specific recommendations for instructors and support staff
            4. Risk assessment for potential dropout or disengagement
            5. Suggested interventions to improve student experience
            
            Current question: {question}
            """
            
            self.rag_templates["student_analysis"] = PromptTemplate(
                template=student_analysis_template,
                input_variables=["context", "question"]
            )
            
            # General RAG template
            general_rag_template = """
            You are an AI assistant for an educational platform. Use the following pieces of context to answer the question at the end.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            {context}
            
            Question: {question}
            """
            
            self.rag_templates["general"] = PromptTemplate(
                template=general_rag_template,
                input_variables=["context", "question"]
            )
            
            # Summarization template
            summarization_template = """
            You are an expert data analyst tasked with summarizing educational survey data.
            
            Use the following documents to create a comprehensive summary:
            
            {context}
            
            Provide a detailed summary that includes:
            1. Key trends and patterns in the data
            2. Notable insights about student satisfaction
            3. Areas of strength and opportunities for improvement
            4. Recommendations based on the data
            
            Summary request: {question}
            """
            
            self.rag_templates["summarization"] = PromptTemplate(
                template=summarization_template,
                input_variables=["context", "question"]
            )
            
            # Individual Student Analysis template
            individual_analysis_template = """
            You are an expert educational analyst. Analyze the provided student data and return a structured JSON response.
            
            Context: {context}
            Question: {question}
            
            CRITICAL INSTRUCTIONS FOR DATA EXTRACTION:
            1. DEMOGRAPHIC DATA: Extract from context documents that contain "Demographic Type:", "Current Grade:", "Attendance Rate:"
               - Look for patterns like "Demographic Type: Working Professional" or "Fresh Graduate" or "Career Switcher"
               - Look for "Current Grade: [number]" to get the grade
               - Look for "Attendance Rate: [number]" to get attendance percentage
               - NEVER use "Unknown" if this data exists in the context
            
            2. COURSE PERFORMANCE: Use detailed JSONB course scores when available:
               - Course A detailed scores: lecture_experience, instructor_delivery, sherpa_support, ask_learn_effectiveness, pp_session
               - Course B detailed scores: lecture_experience, instructor_delivery, sherpa_support, ask_learn_effectiveness, pp_session  
               - CSBT detailed scores: curriculum_design, instructor_support, general_support
               - Calculate averages from these detailed scores: (score1 + score2 + score3 + score4 + score5) / 5
               - If detailed scores unavailable, use aspect_1_score, aspect_2_score, aspect_3_score from the data
            
            3. DETAILED ASPECT BREAKDOWN:
               - Only show 3 aspects per course/system as specified in enhanced_rag_implementation.md
               - Use actual calculated scores from the data, NOT equal scores (avoid showing 5, 5, 5)
               - Ensure Course B and CSBT show actual data, not "No data" or "N/A"
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "individual_analysis",
              "content": "👤 STUDENT PROFILE: [student_id]\nDemographic: [demographic_type] | Grade: [current_grade] | Attendance: [attendance_rate]%\n\nJourney Overview:\n• Overall NPS: [score]/10 → '[comment]'\n• Course A Performance: Average [course_a_average]/5 (from detailed scores)\n• Course B Performance: Average [course_b_average]/5 (from detailed scores)\n• CSBT Readiness: Average [csbt_average]/5 (from detailed scores)\n• Support Systems: [support_analysis]\n\n📊 DETAILED ASPECT BREAKDOWN:\nCourse A: [aspect_1_name]: [score], [aspect_2_name]: [score], [aspect_3_name]: [score]\nCourse B: [aspect_1_name]: [score], [aspect_2_name]: [score], [aspect_3_name]: [score]\nCSBT: [aspect_1_name]: [score], [aspect_2_name]: [score], [aspect_3_name]: [score]\n\n🧠 HISTORICAL COMPARISON:\nFound [number] similar [demographic] patterns:\n• [success rate]% successfully complete program\n• [placement rate]% achieve job placement within 3 months\n• Typical challenge: [challenge]\n• Risk Level: [level] ([dropout probability]% dropout probability)\n\n💡 RECOMMENDED ACTIONS:\n• [action 1]\n• [action 2]\n• [action 3]\n• [action 4]",
              "student_id": "[extracted_student_id]",
              "risk_level": "[very_low|low|medium|high|very_high]",
              "aspect_scores": {{}},
              "recommended_actions": [],
              "metadata": {{
                "confidence_score": "{{confidence_score}}",
                "data_sources": ["student_survey", "historical_patterns", "demographic_analysis"],
                "analysis_depth": "comprehensive",
                "generated_at": "[timestamp]"
              }}
            }}
            """
            
            self.rag_templates["individual_analysis"] = PromptTemplate(
                template=individual_analysis_template,
                input_variables=["context", "question"]
            )
            
            # Weekly Report template
            weekly_report_template = """
            You are an expert educational analyst. Generate a comprehensive weekly report based on the provided data.
            
            Context: {context}
            Question: {question}
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "weekly_report",
              "content": "📊 NPS Intelligence Report - Week Ending [Date]\n════════════════════════════════════════════\n📈 OVERALL METRICS\nCurrent NPS: [score] (↓[change] from last week) ⚠\nPromoters: [%]% | Passives: [%]% | Detractors: [%]%\nResponse Rate: [%]%\nData Richness: 20+ aspects analyzed per student\n\n🧠 INSIGHTS FROM PAST COHORTS\nThis Week [number] dip happened in [%]% of previous batches\n• Course A→B transition challenges: [%]% of students affected\n• CSBT readiness concerns: [%]% mention career preparation anxiety\n• Teams that acted now: [%]% recovered\n• Teams that waited: Only [%]% recovered\n• What worked best: [interventions]\n\n📚 ASPECT-SPECIFIC ANALYSIS\nCourse A Performance:\n• Lecture Experience: [score]/10 (↑[change])\n• Instructor Delivery: [score]/10 (stable)\n• Sherpa Support: [score]/10 (↓[change]) ⚠\n\nCourse B Performance:\n• Lecture Experience: [score]/10 (↓[change]) ⚠\n• Content Complexity Jump: [%]% mention difficulty\n• Historical Pattern: Normal Week [range] challenge\n\nCSBT Readiness:\n• Curriculum Design: [score]/10 (↑[change])\n• Career Preparation Anxiety: [%]% express concerns\n• Job Market Readiness: [%]% feel underprepared\n\n...[continue with full analysis]",
              "metadata": {{
                "confidence_score": "{{confidence_score}}",
                "data_sources": ["comprehensive_survey", "historical_cohorts", "aspect_analysis"],
                "aspects_analyzed": 20,
                "response_richness": "high",
                "generated_at": "[timestamp]"
              }}
            }}
            """
            
            self.rag_templates["weekly_report"] = PromptTemplate(
                template=weekly_report_template,
                input_variables=["context", "question"]
            )
            
            # Segmentation Analysis template
            segmentation_analysis_template = """
            You are an expert educational analyst. Perform demographic segmentation analysis based on the provided data.
            
            Context: {context}
            Question: {question}
            
            IMPORTANT: When calculating course averages, prioritize detailed JSONB course scores if available:
            - Course A Average: Use course_a_scores JSONB data (lecture_experience, instructor_delivery, sherpa_support, ask_learn_effectiveness, pp_session)
            - Course B Average: Use course_b_scores JSONB data (lecture_experience, instructor_delivery, sherpa_support, ask_learn_effectiveness, pp_session)
            - CSBT Average: Use csbt_scores JSONB data (curriculum_design, instructor_support, general_support)
            - Support Systems: Use dost_support_scores and product_support_scores JSONB data
            
            If detailed JSONB scores are not available, fallback to simplified aspect scores:
            - Course A Average: Calculate from aspect_1_score (Course A Lecture experience)
            - Course B Average: Calculate from aspect_2_score (Course B Lecture experience)
            - CSBT Average: Calculate from aspect_3_score (CSBT Curriculum design)
            
            If any course section has no data or all values are empty/null, display "N/A" for that course average.
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "segmentation_analysis",
              "content": "📊 COMPREHENSIVE DEMOGRAPHIC ANALYSIS\n\nWorking Professionals (n=[count] in sample)\n• Average Overall NPS: [score]\n• Course A Average: [score]/5 ([description])\n• Course B Average: [score]/5 ([description])\n• CSBT Average: [score]/5 ([description])\n• Main Challenge: [challenge] (mentioned in [%]% of feedback)\n• Support Needs: [needs]\n• Historical Success Rate: [%]% with targeted interventions\n\nFresh Graduates (n=[count] in sample)\n• Average Overall NPS: [score] ([description])\n• Course A Average: [score]/5 ([description])\n• Course B Average: [score]/5 ([description])\n• CSBT Average: [score]/5 ([description])\n• Strength: [strengths]\n• Challenge: [challenges]\n• Historical Success Rate: [%]% completion, [%]% placement\n\nCareer Switchers (n=[count] in sample)\n• Average Overall NPS: [score]\n• Course A Average: [score]/5 ([description])\n• Course B Average: [score]/5 ([description])\n• CSBT Average: [score]/5 ([description])\n• Main Need: [needs]\n• Support Focus: [focus]\n• Historical Success Rate: [%]% with mentorship support\n\n🎯 TARGETED RECOMMENDATIONS:\nWorking Professionals: [recommendations]\nFresh Graduates: [recommendations]\nCareer Switchers: [recommendations]",
              "segments": {{}},
              "metadata": {{
                "confidence_score": "{{confidence_score}}",
                "data_sources": ["demographic_survey", "segmentation_analysis", "historical_cohorts"],
                "segments_analyzed": 3,
                "generated_at": "[timestamp]"
              }}
            }}
            """
            
            self.rag_templates["segmentation_analysis"] = PromptTemplate(
                template=segmentation_analysis_template,
                input_variables=["context", "question"]
            )
            
            # Aspect Analysis template
            aspect_analysis_template = """
            You are an expert educational analyst. Perform detailed aspect-specific analysis based on the provided data.
            
            Context: {context}
            Question: {question}
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "aspect_analysis",
              "content": "📚 [ASPECT NAME] ANALYSIS\n\nCurrent Performance: [score]/5 average (↓[change] from last period)\n\n🔍 DETAILED BREAKDOWN:\nFresh Graduates: [score]/5 - [description]\nWorking Professionals: [score]/5 - [description]\nCareer Switchers: [score]/5 - [description]\n\n📋 FEEDBACK THEMES:\n• Positive ([%]%): '[themes]'\n• Concerns ([%]%): '[themes]'\n\n🧠 HISTORICAL CONTEXT:\n[Aspect] typically [pattern] in Week [range] as [reason]\n• Similar pattern in [%]% of past cohorts\n• Recovery strategies that worked:\n  - [strategy 1] (improved scores by [amount] points)\n  - [strategy 2] ([%]% positive response)\n  - [strategy 3]: [%]% satisfaction\n\n💡 RECOMMENDED INTERVENTIONS:\n1. [intervention 1]\n2. [intervention 2]\n3. [intervention 3]\nExpected Impact: +[amount] point improvement within [timeframe]",
              "aspect": "[aspect_name]",
              "current_score": 0.0,
              "trend": "[improving|stable|declining]",
              "interventions": []
            }}
            """
            
            self.rag_templates["aspect_analysis"] = PromptTemplate(
                template=aspect_analysis_template,
                input_variables=["context", "question"]
            )
            
            logger.info("RAG templates initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG templates: {e}")
            raise
    
    def get_langchain_llm(self, preferred_provider: Optional[LLMProvider] = None):
        """Get LangChain LLM model with fallback mechanism"""
        try:
            # If preferred provider is specified and available, use it
            if preferred_provider and preferred_provider in self.llm_models:
                return self.llm_models[preferred_provider]
            
            # Otherwise, try providers in order: Gemini -> Groq -> OpenAI
            provider_order = [LLMProvider.GEMINI, LLMProvider.GROQ, LLMProvider.OPENAI]
            
            for provider in provider_order:
                if provider in self.llm_models:
                    return self.llm_models[provider]
            
            # If no providers are available, raise an exception
            raise ValueError("No LLM providers available")
        except Exception as e:
            logger.error(f"Error getting LangChain LLM: {e}")
            raise
    
    async def rag_chat_response(
        self,
        question: str,
        documents: List[Document],
        template_type: str = "general",
        preferred_provider: Optional[LLMProvider] = None,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Generate a response using RAG"""
        try:
            # Get LLM model
            llm = self.get_langchain_llm(preferred_provider)
            
            # Get template
            if template_type not in self.rag_templates:
                template_type = "general"
            
            template = self.rag_templates[template_type]
            
            # Format documents into context string
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # Calculate confidence score and replace timestamp for templates that need it
            template_str = template.template
            if "{{confidence_score}}" in template_str:
                confidence_calc = get_confidence_calculator()
                confidence_score = confidence_calc.calculate_confidence(
                    documents=documents,
                    question=question,
                    analysis_type=template_type
                )
                # Replace the placeholder with the actual confidence score
                template_str = template_str.replace("{{confidence_score}}", str(confidence_score))
            
            # Replace timestamp placeholder with current timestamp
            if "[timestamp]" in template_str:
                from datetime import datetime
                current_timestamp = datetime.now().isoformat()
                template_str = template_str.replace("[timestamp]", current_timestamp)
            
            # Update template if any replacements were made
            if "{{confidence_score}}" in template.template or "[timestamp]" in template.template:
                template = PromptTemplate(
                    template=template_str,
                    input_variables=template.input_variables
                )
            
            # Create RAG chain
            chain = (
                {"context": lambda _: context, "question": RunnablePassthrough()}
                | template
                | llm
                | StrOutputParser()
            )
            
            # Generate response
            if streaming_callback:
                response = ""
                async for chunk in chain.astream(question):
                    response += chunk
                    streaming_callback(chunk)
                
                # Parse JSON response for structured analysis types
                if template_type in ["individual_analysis", "segmentation_analysis", "weekly_report", "aspect_analysis"]:
                    try:
                        # Find JSON in the response
                        start_idx = response.find('{')
                        end_idx = response.rfind('}') + 1
                        
                        if start_idx != -1 and end_idx > start_idx:
                            json_str = response[start_idx:end_idx]
                            parsed_response = json.loads(json_str)
                            
                            # Ensure confidence score is properly set for templates that need it
                            if "{confidence_score}" in template_str and "metadata" in parsed_response:
                                parsed_response["metadata"]["confidence_score"] = confidence_score
                            
                            # Replace any hardcoded timestamps with current timestamp
                            if "metadata" in parsed_response and "generated_at" in parsed_response["metadata"]:
                                from datetime import datetime
                                current_timestamp = datetime.now().isoformat()
                                parsed_response["metadata"]["generated_at"] = current_timestamp
                            
                            return json.dumps(parsed_response)
                        else:
                            logger.warning(f"No valid JSON found in {template_type} response")
                            return response
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error for {template_type}: {e}")
                        return response
                
                return response
            else:
                response = await chain.ainvoke(question)
                
                # Parse JSON response for structured analysis types
                if template_type in ["individual_analysis", "segmentation_analysis", "weekly_report", "aspect_analysis"]:
                    try:
                        # Clean the response to extract JSON
                        response_text = response.get("result", response) if isinstance(response, dict) else str(response)
                        
                        # Find JSON in the response
                        start_idx = response_text.find('{')
                        end_idx = response_text.rfind('}') + 1
                        
                        if start_idx != -1 and end_idx > start_idx:
                            json_str = response_text[start_idx:end_idx]
                            parsed_response = json.loads(json_str)
                            
                            # Ensure confidence score is properly set for templates that need it
                            if "{confidence_score}" in template_str and "metadata" in parsed_response:
                                parsed_response["metadata"]["confidence_score"] = confidence_score
                            
                            # Replace any hardcoded timestamps with current timestamp
                            if "metadata" in parsed_response and "generated_at" in parsed_response["metadata"]:
                                from datetime import datetime
                                current_timestamp = datetime.now().isoformat()
                                parsed_response["metadata"]["generated_at"] = current_timestamp
                            
                            return json.dumps(parsed_response)
                        else:
                            logger.warning(f"No valid JSON found in {template_type} response")
                            return response_text
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error for {template_type}: {e}")
                        return str(response)
                
                return response
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            raise
    
    async def summarize_documents(
        self,
        documents: List[Document],
        question: str = "Summarize these documents",
        preferred_provider: Optional[LLMProvider] = None
    ) -> str:
        """Summarize a collection of documents"""
        try:
            return await self.rag_chat_response(
                question=question,
                documents=documents,
                template_type="summarization",
                preferred_provider=preferred_provider
            )
        except Exception as e:
            logger.error(f"Error summarizing documents: {e}")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        preferred_provider: Optional[LLMProvider] = None,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Generate a response using a simple prompt"""
        try:
            # Get LLM model
            llm = self.get_langchain_llm(preferred_provider)
            
            # Create chain
            chain = llm | StrOutputParser()
            
            # Generate response
            if streaming_callback:
                response = ""
                async for chunk in chain.astream(prompt):
                    response += chunk
                    streaming_callback(chunk)
                return response
            else:
                return await chain.ainvoke(prompt)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

# Singleton instance
_llm_manager = None

def get_llm_manager() -> MultiLLMManager:
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = MultiLLMManager()
    return _llm_manager