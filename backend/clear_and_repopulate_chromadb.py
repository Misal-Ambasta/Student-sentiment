#!/usr/bin/env python3
"""
Script to completely clear ChromaDB and repopulate with fresh data
"""

import asyncio
from loguru import logger
from vector_store import get_chroma_manager
from celery_tasks.data_processing import get_sync_db, add_survey_data_to_chroma
from sqlalchemy import text

async def clear_and_repopulate_chromadb():
    """Clear ChromaDB completely and repopulate with fresh data"""
    try:
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        logger.info("Clearing existing ChromaDB data...")
        
        # Clear the survey data collection
        try:
            # Access the underlying collection and delete all documents
            collection = chroma_manager.survey_data_db._collection
            # Get all document IDs
            all_data = collection.get()
            if all_data['ids']:
                logger.info(f"Deleting {len(all_data['ids'])} existing documents")
                collection.delete(ids=all_data['ids'])
            else:
                logger.info("No existing documents to delete")
        except Exception as e:
            logger.warning(f"Error clearing collection: {e}")
        
        logger.info("Fetching fresh data from database...")
        
        # Get database connection
        db = get_sync_db()
        
        # Get all survey data with detailed scores
        query = text("""
            SELECT student_id, timestamp, nps_score, course_id, week_number,
                   aspect_1_score, aspect_2_score, aspect_3_score, comments,
                   course_a_scores, course_b_scores, csbt_scores,
                   dost_support_scores, product_support_scores
            FROM surveys
            ORDER BY student_id, timestamp
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        logger.info(f"Found {len(rows)} survey records to process")
        
        # Convert to list of dictionaries
        survey_data = []
        for row in rows:
            # Handle JSONB data (already parsed as dictionaries)
            course_a_scores = row[9] if row[9] else {}
            course_b_scores = row[10] if row[10] else {}
            csbt_scores = row[11] if row[11] else {}
            dost_support_scores = row[12] if row[12] else {}
            product_support_scores = row[13] if row[13] else {}
            
            survey_data.append({
                'student_id': row[0],
                'timestamp': row[1],
                'nps_score': row[2],
                'course_id': row[3],
                'week_number': row[4],
                'aspect_1_score': row[5],
                'aspect_2_score': row[6],
                'aspect_3_score': row[7],
                'comments': row[8],
                'course_a_scores': course_a_scores,
                'course_b_scores': course_b_scores,
                'csbt_scores': csbt_scores,
                'dost_support_scores': dost_support_scores,
                'product_support_scores': product_support_scores
            })
        
        logger.info(f"Sample data for first record:")
        if survey_data:
            sample = survey_data[0]
            logger.info(f"Student: {sample['student_id']}")
            logger.info(f"Course A scores: {sample['course_a_scores']}")
            logger.info(f"Course B scores: {sample['course_b_scores']}")
            logger.info(f"CSBT scores: {sample['csbt_scores']}")
        
        # Add data to ChromaDB in batches
        batch_size = 5
        for i in range(0, len(survey_data), batch_size):
            batch = survey_data[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: records {i+1} to {min(i+batch_size, len(survey_data))}")
            
            # Use the existing function to add data
            add_survey_data_to_chroma(batch)
        
        logger.info(f"Successfully repopulated ChromaDB with {len(survey_data)} records")
        
        # Verify the data
        logger.info("\nVerifying repopulated data...")
        test_docs = await chroma_manager.search_survey_data(
            query="student survey data",
            k=3
        )
        
        for i, doc in enumerate(test_docs):
            logger.info(f"\nVerification Document {i+1}:")
            logger.info(f"Student: {doc.metadata.get('student_id')}")
            content = doc.page_content
            has_detailed = "Course A Detailed Scores:" in content
            logger.info(f"Has detailed scores: {has_detailed}")
            if has_detailed:
                logger.info("✓ Detailed scores are present")
            else:
                logger.warning("✗ No detailed scores found")
        
    except Exception as e:
        logger.error(f"Error in clear and repopulate: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(clear_and_repopulate_chromadb())