#!/usr/bin/env python3
"""
Script to reprocess existing survey data to populate ChromaDB with detailed scores
"""

import asyncio
from loguru import logger
from celery_tasks.data_processing import get_sync_db, add_survey_data_to_chroma
from sqlalchemy import text

def reprocess_survey_data():
    """Reprocess existing survey data to populate ChromaDB with detailed scores"""
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
        
        logger.info(f"Found {len(rows)} survey records to reprocess")
        
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
        
        db.close()
        
        if not survey_data:
            logger.info("No survey data found to reprocess")
            return
        
        # Process data in smaller batches to avoid memory issues
        batch_size = 5
        for i in range(0, len(survey_data), batch_size):
            batch = survey_data[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(survey_data)-1)//batch_size + 1} ({len(batch)} records)")
            
            try:
                # Use the existing data processing function
                add_survey_data_to_chroma(batch)
                logger.info(f"Successfully processed batch {i//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                # Continue with next batch
                continue
        
        logger.success(f"Successfully reprocessed {len(survey_data)} survey records")
        
    except Exception as e:
        logger.error(f"Error reprocessing survey data: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting survey data reprocessing...")
    reprocess_survey_data()
    logger.info("Reprocessing completed!")