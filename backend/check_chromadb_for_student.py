#!/usr/bin/env python3
"""
Script to check what's in ChromaDB for a specific student
"""

from loguru import logger
from vector_store import ChromaManager

async def check_chromadb_for_student():
    """Check what data is in ChromaDB for student fsd25_08007"""
    try:
        # Initialize ChromaManager
        chroma_manager = ChromaManager()
        
        target_student = "fsd25_08007"
        logger.info(f"Searching ChromaDB for {target_student}")
        
        # Search for this specific student
        results = await chroma_manager.search_survey_data(
            query=f"student {target_student}",
            k=10
        )
        
        logger.info(f"Found {len(results)} documents for {target_student}")
        
        for i, doc in enumerate(results):
            logger.info(f"\n=== Document {i+1} ===")
            logger.info(f"Metadata: {doc.metadata}")
            logger.info(f"Content preview: {doc.page_content[:200]}...")
            
            # Check if this document contains detailed scores
            content = doc.page_content
            has_course_a = "Course A Detailed Scores:" in content and "lecture_experience" in content
            has_course_b = "Course B Detailed Scores:" in content and "lecture_experience" in content
            has_csbt = "CSBT Detailed Scores:" in content and "curriculum_design" in content
            
            logger.info(f"Has Course A detailed: {has_course_a}")
            logger.info(f"Has Course B detailed: {has_course_b}")
            logger.info(f"Has CSBT detailed: {has_csbt}")
            
            if doc.metadata.get('student_id') == target_student:
                logger.info("✓ This document is for our target student")
                if not (has_course_a or has_course_b or has_csbt):
                    logger.warning("✗ But it lacks detailed scores!")
                    logger.info(f"Full content: {content}")
            else:
                logger.info(f"This document is for student: {doc.metadata.get('student_id')}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_chromadb_for_student())