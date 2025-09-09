#!/usr/bin/env python3
"""
Script to check what data exists for a specific student in the database
"""

from loguru import logger
from celery_tasks.data_processing import get_sync_db
from sqlalchemy import text

def check_student_data():
    """Check what data exists for specific students"""
    try:
        # Get database connection
        db = get_sync_db()
        
        # Check what students exist
        query = text("""
            SELECT DISTINCT student_id 
            FROM surveys 
            ORDER BY student_id
        """)
        
        result = db.execute(query)
        students = [row[0] for row in result.fetchall()]
        
        logger.info(f"Found {len(students)} unique students: {students[:10]}...")  # Show first 10
        
        # Check data for student fsd25_08007 specifically
        target_student = "fsd25_08007"
        logger.info(f"\n=== Checking data for {target_student} ===")
        
        query = text("""
            SELECT student_id, timestamp, nps_score, course_id, week_number,
                   aspect_1_score, aspect_2_score, aspect_3_score, comments,
                   course_a_scores, course_b_scores, csbt_scores,
                   dost_support_scores, product_support_scores
            FROM surveys
            WHERE student_id = :student_id
            ORDER BY timestamp
        """)
        
        result = db.execute(query, {"student_id": target_student})
        rows = result.fetchall()
        
        logger.info(f"Found {len(rows)} records for {target_student}")
        
        for i, row in enumerate(rows):
            logger.info(f"\nRecord {i+1}:")
            logger.info(f"  Student: {row[0]}")
            logger.info(f"  Timestamp: {row[1]}")
            logger.info(f"  NPS: {row[2]}")
            logger.info(f"  Course: {row[3]}")
            logger.info(f"  Week: {row[4]}")
            logger.info(f"  Aspect scores: {row[5]}, {row[6]}, {row[7]}")
            logger.info(f"  Comments: {row[8]}")
            logger.info(f"  Course A scores: {row[9]}")
            logger.info(f"  Course B scores: {row[10]}")
            logger.info(f"  CSBT scores: {row[11]}")
            logger.info(f"  Dost support: {row[12]}")
            logger.info(f"  Product support: {row[13]}")
            
            # Check if detailed scores are empty
            has_detailed = any([
                row[9] and row[9] != {},  # course_a_scores
                row[10] and row[10] != {},  # course_b_scores
                row[11] and row[11] != {},  # csbt_scores
                row[12] and row[12] != {},  # dost_support_scores
                row[13] and row[13] != {}   # product_support_scores
            ])
            
            if has_detailed:
                logger.info("  ✓ Has detailed scores")
            else:
                logger.warning("  ✗ No detailed scores")
        
        # Also check a few other students to see if they have detailed scores
        logger.info(f"\n=== Checking other students for detailed scores ===")
        for student in students[:3]:
            if student != target_student:
                query = text("""
                    SELECT student_id, course_a_scores, course_b_scores, csbt_scores
                    FROM surveys
                    WHERE student_id = :student_id
                    LIMIT 1
                """)
                
                result = db.execute(query, {"student_id": student})
                row = result.fetchone()
                
                if row:
                    has_detailed = any([
                        row[1] and row[1] != {},  # course_a_scores
                        row[2] and row[2] != {},  # course_b_scores
                        row[3] and row[3] != {}   # csbt_scores
                    ])
                    
                    logger.info(f"Student {student}: {'✓ Has detailed scores' if has_detailed else '✗ No detailed scores'}")
                    if has_detailed:
                        logger.info(f"  Course A: {row[1]}")
        
    except Exception as e:
        logger.error(f"Error checking student data: {e}")
        raise

if __name__ == "__main__":
    check_student_data()