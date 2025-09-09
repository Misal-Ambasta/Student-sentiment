#!/usr/bin/env python3
"""
Script to check detailed scores for student fsd25_08007
"""

from loguru import logger
from celery_tasks.data_processing import get_sync_db
from sqlalchemy import text

def check_specific_student():
    """Check detailed scores for student fsd25_08007"""
    try:
        # Get database connection
        db = get_sync_db()
        
        target_student = "fsd25_08007"
        logger.info(f"Checking detailed scores for {target_student}")
        
        query = text("""
            SELECT course_a_scores, course_b_scores, csbt_scores,
                   dost_support_scores, product_support_scores
            FROM surveys
            WHERE student_id = :student_id
        """)
        
        result = db.execute(query, {"student_id": target_student})
        row = result.fetchone()
        
        if row:
            logger.info(f"Course A scores: {row[0]}")
            logger.info(f"Course B scores: {row[1]}")
            logger.info(f"CSBT scores: {row[2]}")
            logger.info(f"Dost support scores: {row[3]}")
            logger.info(f"Product support scores: {row[4]}")
            
            # Check if any detailed scores exist
            has_detailed = any([
                row[0] and row[0] != {},
                row[1] and row[1] != {},
                row[2] and row[2] != {},
                row[3] and row[3] != {},
                row[4] and row[4] != {}
            ])
            
            if has_detailed:
                logger.info("✓ Student has detailed scores in database")
            else:
                logger.warning("✗ Student has NO detailed scores in database")
        else:
            logger.error(f"No data found for {target_student}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    check_specific_student()