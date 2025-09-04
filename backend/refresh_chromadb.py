#!/usr/bin/env python3
"""
Script to refresh ChromaDB with detailed survey data including JSONB course scores
"""

import asyncio
import json
from loguru import logger
from celery_tasks.data_processing import get_sync_db
from vector_store import get_chroma_manager
from sqlalchemy import text

async def refresh_survey_data_in_chromadb():
    """Refresh ChromaDB with detailed survey data from database"""
    try:
        # Get database connection
        db = get_sync_db()
        
        # Get all survey data with detailed scores
        query = text("""
            SELECT student_id, timestamp, nps_score, course_id, week_number,
                   aspect_1_score, aspect_2_score, aspect_3_score, comments,
                   course_a_scores, course_b_scores, csbt_scores,
                   dost_support_scores, product_support_scores
            FROM surveys
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        logger.info(f"Found {len(rows)} survey records to refresh in ChromaDB")
        
        # Convert to list of dictionaries
        survey_data = []
        for row in rows:
            # Handle JSONB data (already parsed as dictionaries)
            course_a_scores = row[9] if row[9] else {}
            course_b_scores = row[10] if row[10] else {}
            csbt_scores = row[11] if row[11] else {}
            dost_support_scores = row[12] if row[12] else {}
            product_support_scores = row[13] if row[13] else {}
            
            # If they're strings, parse them
            if isinstance(course_a_scores, str):
                course_a_scores = json.loads(course_a_scores)
            if isinstance(course_b_scores, str):
                course_b_scores = json.loads(course_b_scores)
            if isinstance(csbt_scores, str):
                csbt_scores = json.loads(csbt_scores)
            if isinstance(dost_support_scores, str):
                dost_support_scores = json.loads(dost_support_scores)
            if isinstance(product_support_scores, str):
                product_support_scores = json.loads(product_support_scores)
            
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
        
        db.close()
        
        if not survey_data:
            logger.info("No survey data found to refresh")
            return
        
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # Clear existing survey data
        logger.info("Clearing existing survey data from ChromaDB...")
        try:
            # Delete the collection and recreate it
            chroma_manager.survey_db.delete_collection()
            chroma_manager.survey_db = chroma_manager._init_collection("survey_data")
            logger.info("Cleared existing survey data")
        except Exception as e:
            logger.warning(f"Could not clear existing data: {e}")
        
        # Add refreshed data to ChromaDB
        logger.info("Adding refreshed survey data to ChromaDB...")
        doc_ids = await chroma_manager.add_survey_data(survey_data)
        
        logger.info(f"Successfully refreshed {len(doc_ids)} survey documents in ChromaDB")
        
    except Exception as e:
        logger.error(f"Error refreshing ChromaDB: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting ChromaDB refresh...")
    asyncio.run(refresh_survey_data_in_chromadb())
    logger.info("ChromaDB refresh completed!")