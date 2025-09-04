#!/usr/bin/env python3
"""
Debug script to test individual analysis data retrieval
"""

import asyncio
from loguru import logger
from vector_store import get_chroma_manager

async def debug_individual_analysis():
    """Debug individual analysis data retrieval"""
    try:
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # First, let's see what students are available
        all_docs = await chroma_manager.search_survey_data(
            query="student survey data",
            k=5
        )
        
        logger.info(f"Found {len(all_docs)} documents")
        available_students = set()
        for doc in all_docs:
            student_id = doc.metadata.get('student_id')
            if student_id:
                available_students.add(student_id)
        
        logger.info(f"Available students: {list(available_students)}")
        
        # Test with an actual student from the data
        if available_students:
            test_student = list(available_students)[0]
            logger.info(f"\n=== Testing with student: {test_student} ===")
            
            # Test query for this specific student
            query = f"Analyze student {test_student} performance"
            
            # Search for relevant documents with student filter
            filter_metadata = {"student_id": test_student}
            
            survey_docs = await chroma_manager.search_survey_data(
                query=query,
                filter_metadata=filter_metadata,
                k=5
            )
            
            logger.info(f"Found {len(survey_docs)} documents for student {test_student}")
            
            # Print the content of each document
            for i, doc in enumerate(survey_docs):
                logger.info(f"\n=== Document {i+1} ===")
                logger.info(f"Content: {doc.page_content}")
                logger.info(f"Metadata: {doc.metadata}")
                
                # Check if detailed scores are present in the content
                content = doc.page_content
                if "Course A Detailed Scores:" in content:
                    logger.info("✓ Found Course A detailed scores")
                else:
                    logger.warning("✗ No Course A detailed scores found")
                    
                if "Course B Detailed Scores:" in content:
                    logger.info("✓ Found Course B detailed scores")
                else:
                    logger.warning("✗ No Course B detailed scores found")
                    
                if "CSBT Detailed Scores:" in content:
                    logger.info("✓ Found CSBT detailed scores")
                else:
                    logger.warning("✗ No CSBT detailed scores found")
        else:
            logger.warning("No students found in ChromaDB")
            
    except Exception as e:
        logger.error(f"Error in debug: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(debug_individual_analysis())