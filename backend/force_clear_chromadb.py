#!/usr/bin/env python3
"""
Script to forcefully clear ChromaDB and repopulate with fresh data
"""

import asyncio
import os
import shutil
from loguru import logger
from vector_store import get_chroma_manager
from celery_tasks.data_processing import get_sync_db
from sqlalchemy import text

async def force_clear_and_repopulate():
    """Forcefully clear ChromaDB by deleting the database files and repopulating"""
    try:
        logger.info("Starting forceful clear and repopulate of ChromaDB...")
        
        # Delete the ChromaDB directory to completely clear it
        chroma_db_path = "./chroma_db"
        if os.path.exists(chroma_db_path):
            logger.info(f"Deleting ChromaDB directory: {chroma_db_path}")
            shutil.rmtree(chroma_db_path)
            logger.info("ChromaDB directory deleted")
        else:
            logger.info("ChromaDB directory doesn't exist")
        
        # Now create a fresh ChromaDB instance
        logger.info("Creating fresh ChromaDB instance...")
        chroma_manager = get_chroma_manager()
        
        # Get fresh data from database
        logger.info("Fetching fresh data from PostgreSQL...")
        db = get_sync_db()
        
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
        
        logger.info(f"Found {len(rows)} survey records to add")
        
        # Convert to list of dictionaries
        survey_data = []
        for row in rows:
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
                'course_a_scores': row[9] if row[9] else {},
                'course_b_scores': row[10] if row[10] else {},
                'csbt_scores': row[11] if row[11] else {},
                'dost_support_scores': row[12] if row[12] else {},
                'product_support_scores': row[13] if row[13] else {}
            })
        
        # Show sample data
        if survey_data:
            sample = survey_data[0]
            logger.info(f"Sample data - Student: {sample['student_id']}")
            logger.info(f"Course A scores: {sample['course_a_scores']}")
            logger.info(f"Course B scores: {sample['course_b_scores']}")
            logger.info(f"CSBT scores: {sample['csbt_scores']}")
        
        # Add all data to ChromaDB
        logger.info("Adding data to fresh ChromaDB...")
        doc_ids = await chroma_manager.add_survey_data(survey_data)
        
        logger.info(f"Successfully added {len(doc_ids)} documents to ChromaDB")
        
        # Verify with specific student
        logger.info("\nVerifying data for student fsd25_08007...")
        test_docs = await chroma_manager.search_survey_data(
            query="student fsd25_08007",
            filter_metadata={"student_id": "fsd25_08007"},
            k=5
        )
        
        logger.info(f"Found {len(test_docs)} documents for fsd25_08007")
        for i, doc in enumerate(test_docs):
            logger.info(f"\nDocument {i+1}:")
            logger.info(f"Student: {doc.metadata.get('student_id')}")
            content = doc.page_content
            has_detailed = "Course A Detailed Scores:" in content
            logger.info(f"Has detailed scores: {has_detailed}")
            if has_detailed:
                logger.info("✓ SUCCESS: Detailed scores are present")
            else:
                logger.warning("✗ PROBLEM: No detailed scores found")
                logger.info(f"Content: {content[:300]}...")
        
    except Exception as e:
        logger.error(f"Error in force clear and repopulate: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(force_clear_and_repopulate())