#!/usr/bin/env python3
"""
Script to check if Working Professional demographic data is properly stored in ChromaDB
"""

import asyncio
from loguru import logger
from vector_store import get_chroma_manager

async def check_chromadb_demographics():
    """Check demographic data in ChromaDB specifically for Working Professionals"""
    try:
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # Search for all demographic data first
        logger.info("Searching for demographic data in ChromaDB...")
        all_demo_docs = await chroma_manager.search_student_data(
            query="demographic_type",
            k=30  # Get up to 30 documents
        )
        
        logger.info(f"Found {len(all_demo_docs)} total demographic documents in ChromaDB")
        
        # Filter results manually for Working Professional
        wp_docs = [doc for doc in all_demo_docs if doc.metadata.get('demographic_type') == 'Working Professional']
        logger.info(f"Found {len(wp_docs)} Working Professional documents")
        
        # Print details of each Working Professional document
        for i, doc in enumerate(wp_docs):
            logger.info(f"\n=== Working Professional Document {i+1} ===")
            logger.info(f"Content: {doc.page_content}")
            logger.info(f"Metadata: {doc.metadata}")
        
        # Also check if these students have survey data
        if wp_docs:
            student_ids = [doc.metadata.get('student_id') for doc in wp_docs]
            logger.info(f"\nChecking survey data for Working Professional students: {student_ids}")
            
            all_survey_docs = []
            for student_id in student_ids:
                # Get all survey docs and filter manually
                survey_docs = await chroma_manager.search_survey_data(
                    query="survey data",
                    k=10
                )
                # Filter manually
                student_survey_docs = [doc for doc in survey_docs if doc.metadata.get('student_id') == student_id]
                all_survey_docs.extend(student_survey_docs)
                logger.info(f"Student {student_id}: Found {len(student_survey_docs)} survey documents")
            
            logger.info(f"Total survey documents for Working Professional students: {len(all_survey_docs)}")
        
        # Check the segmentation analysis query specifically
        logger.info("\n=== Testing Segmentation Analysis Query ===")
        segmentation_demo_docs = await chroma_manager.search_student_data(
            query="demographic_type Working Professional Fresh Graduate Career Switcher",
            k=30
        )
        logger.info(f"Segmentation query found {len(segmentation_demo_docs)} demographic documents")
        
        # Count by demographic type
        demo_counts = {}
        for doc in segmentation_demo_docs:
            demo_type = doc.metadata.get('demographic_type')
            if demo_type:
                demo_counts[demo_type] = demo_counts.get(demo_type, 0) + 1
        
        logger.info("Demographic counts in segmentation query:")
        for demo_type, count in demo_counts.items():
            logger.info(f"  {demo_type}: {count}")
            
    except Exception as e:
        logger.error(f"Error checking ChromaDB demographics: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(check_chromadb_demographics())