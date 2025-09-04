#!/usr/bin/env python3
"""
Script to clean up duplicate demographic records in the database
"""

from celery_tasks.data_processing import get_sync_db
from sqlalchemy import text
from loguru import logger

def cleanup_duplicate_demographics():
    """Remove duplicate demographic records, keeping only the most recent for each student"""
    try:
        db = get_sync_db()
        
        logger.info("Starting cleanup of duplicate demographic records...")
        
        # First, let's see what we have
        count_query = text("SELECT COUNT(*) FROM demographics")
        total_count = db.execute(count_query).scalar()
        logger.info(f"Total demographic records before cleanup: {total_count}")
        
        # Count duplicates
        duplicate_query = text("""
            SELECT student_id, COUNT(*) as count
            FROM demographics
            GROUP BY student_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = db.execute(duplicate_query).fetchall()
        logger.info(f"Found {len(duplicates)} students with duplicate records:")
        
        for student_id, count in duplicates:
            logger.info(f"  {student_id}: {count} records")
        
        # Delete duplicates, keeping only the most recent record for each student
        cleanup_query = text("""
            DELETE FROM demographics 
            WHERE id NOT IN (
                SELECT DISTINCT ON (student_id) id
                FROM demographics
                ORDER BY student_id, created_at DESC
            )
        """)
        
        result = db.execute(cleanup_query)
        deleted_count = result.rowcount
        
        db.commit()
        
        # Check final count
        final_count = db.execute(count_query).scalar()
        logger.info(f"Deleted {deleted_count} duplicate records")
        logger.info(f"Total demographic records after cleanup: {final_count}")
        
        # Verify no duplicates remain
        remaining_duplicates = db.execute(duplicate_query).fetchall()
        if remaining_duplicates:
            logger.warning(f"Still have {len(remaining_duplicates)} students with duplicates!")
        else:
            logger.info("✓ All duplicates successfully removed")
        
        # Show final demographic counts
        final_counts_query = text("""
            SELECT demographic_type, COUNT(*) as count
            FROM demographics
            GROUP BY demographic_type
            ORDER BY demographic_type
        """)
        
        final_counts = db.execute(final_counts_query).fetchall()
        logger.info("Final demographic counts:")
        for demo_type, count in final_counts:
            logger.info(f"  {demo_type}: {count}")
        
        db.close()
        logger.info("Cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    cleanup_duplicate_demographics()