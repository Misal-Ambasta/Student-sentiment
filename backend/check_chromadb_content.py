#!/usr/bin/env python3
"""
Script to check the actual content in ChromaDB
"""

import asyncio
from loguru import logger
from vector_store import get_chroma_manager

async def check_chromadb_content():
    """Check what's actually stored in ChromaDB"""
    try:
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # Get all documents from survey_data collection
        # We'll search with a very general query to get all documents
        all_docs = await chroma_manager.search_survey_data(
            query="student survey data",
            k=10  # Get more documents
        )
        
        logger.info(f"Found {len(all_docs)} total documents in ChromaDB")
        
        # Check the first few documents in detail
        for i, doc in enumerate(all_docs[:3]):
            logger.info(f"\n=== Document {i+1} ===")
            logger.info(f"Metadata: {doc.metadata}")
            logger.info(f"Full Content:\n{doc.page_content}")
            logger.info(f"Content Length: {len(doc.page_content)} characters")
            
            # Check for detailed scores
            content = doc.page_content
            has_detailed_scores = False
            
            if "Course A Detailed Scores:" in content:
                logger.info("✓ Has Course A detailed scores")
                has_detailed_scores = True
            if "Course B Detailed Scores:" in content:
                logger.info("✓ Has Course B detailed scores")
                has_detailed_scores = True
            if "CSBT Detailed Scores:" in content:
                logger.info("✓ Has CSBT detailed scores")
                has_detailed_scores = True
            if "Dost Support Scores:" in content:
                logger.info("✓ Has Dost Support scores")
                has_detailed_scores = True
            if "Product Support Scores:" in content:
                logger.info("✓ Has Product Support scores")
                has_detailed_scores = True
                
            if not has_detailed_scores:
                logger.warning("✗ No detailed scores found in this document")
                
        # Also check the collection info
        try:
            # Access the underlying ChromaDB collection to get count
            collection = chroma_manager.survey_data_db._collection
            count = collection.count()
            logger.info(f"\nTotal documents in survey_data collection: {count}")
        except Exception as e:
            logger.warning(f"Could not get collection count: {e}")
            
    except Exception as e:
        logger.error(f"Error checking ChromaDB content: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(check_chromadb_content())