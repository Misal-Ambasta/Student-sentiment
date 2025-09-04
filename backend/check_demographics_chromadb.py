#!/usr/bin/env python3
import asyncio
import logging
from celery_tasks.data_processing import get_sync_db
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_demographics():
    """Check demographic data in database only"""
    
    logger.info("=== CHECKING DATABASE DEMOGRAPHICS ===")
    
    # Check database demographics
    db = get_sync_db()
    
    # Get all demographics from database
    query = text("""
        SELECT student_id, demographic_type 
        FROM demographics 
        ORDER BY demographic_type, student_id
    """)
    
    result = db.execute(query)
    db_demographics = result.fetchall()
    logger.info(f"Total demographics records in database: {len(db_demographics)}")
    
    # Count by demographic type
    demographic_counts = {}
    for student_id, demographic in db_demographics:
        demographic_counts[demographic] = demographic_counts.get(demographic, 0) + 1
    
    logger.info("Database demographic counts:")
    for demo, count in demographic_counts.items():
        logger.info(f"  {demo}: {count}")
    
    # Check specific Working Professional students
    query = text("""
        SELECT student_id 
        FROM demographics 
        WHERE demographic_type = 'Working Professional'
        ORDER BY student_id
    """)
    
    result = db.execute(query)
    working_prof_students = [row[0] for row in result.fetchall()]
    logger.info(f"Working Professional students in DB: {working_prof_students}")
    
    # Check if these students have survey data
    if working_prof_students:
        query = text("""
            SELECT DISTINCT student_id, COUNT(*) as survey_count
            FROM surveys 
            WHERE student_id = ANY(:student_ids)
            GROUP BY student_id
            ORDER BY student_id
        """)
        
        result = db.execute(query, {"student_ids": working_prof_students})
        survey_data = result.fetchall()
        
        logger.info("Survey data for Working Professional students:")
        for student_id, count in survey_data:
            logger.info(f"  {student_id}: {count} surveys")
    
    db.close()
    
    logger.info("\n=== DATABASE ANALYSIS COMPLETE ===")
    logger.info("Next step: Check ChromaDB separately if needed.")

if __name__ == "__main__":
    check_database_demographics()