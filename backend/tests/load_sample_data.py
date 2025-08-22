#!/usr/bin/env python3
"""
Script to load sample data into the database and ChromaDB vector store.
This will populate the system with fsd25 course data for testing.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from celery_tasks.data_processing import process_survey_file, process_demographics_file, get_sync_db
from sqlalchemy import text, create_engine
from loguru import logger

# Create synchronous database engine
DATABASE_URL = os.getenv("NEON_DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/student_sense"))
# Remove sslmode parameter if present and add SSL support for Neon
if "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]
sync_engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

async def load_sample_data():
    """Load sample data files into the system"""
    try:
        # Paths to sample data files
        sample_dir = Path(__file__).parent.parent / "sample_data_10"
        survey_file = sample_dir / "nps_sample_10.csv"
        demographics_file = sample_dir / "demographics_sample_10.csv"
        
        logger.info("Starting sample data loading...")
        
        # Check if files exist
        if not survey_file.exists():
            logger.error(f"Survey file not found: {survey_file}")
            return False
            
        if not demographics_file.exists():
            logger.error(f"Demographics file not found: {demographics_file}")
            return False
        
        # Process survey data
        logger.info(f"Processing survey file: {survey_file}")
        process_survey_file("sample_survey", str(survey_file))
        
        # Process demographics data
        logger.info(f"Processing demographics file: {demographics_file}")
        process_demographics_file("sample_demographics", str(demographics_file))
        
        # Verify data was loaded
        from sqlalchemy.orm import sessionmaker
        SyncSessionLocal = sessionmaker(bind=sync_engine)
        db = SyncSessionLocal()
        
        try:
            # Check survey data
            survey_count = db.execute(
                text("SELECT COUNT(*) FROM surveys WHERE course_id = 'fsd25'")
            ).scalar()
            
            # Check student data
            student_count = db.execute(
                text("SELECT COUNT(*) FROM students WHERE student_id LIKE 'fsd25_%'")
            ).scalar()
            
            logger.info(f"Data loading completed successfully!")
            logger.info(f"Loaded {survey_count} survey records for course fsd25")
            logger.info(f"Loaded {student_count} student records for course fsd25")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(load_sample_data())
    if success:
        print("Sample data loaded successfully!")
        sys.exit(0)
    else:
        print("Failed to load sample data!")
        sys.exit(1)