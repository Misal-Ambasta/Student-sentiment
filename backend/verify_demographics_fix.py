#!/usr/bin/env python3
"""
Script to verify that demographic data cleanup was successful
and that segmentation analysis should now work properly.
"""

import asyncio
import sys
import os
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Demographics
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

async def verify_demographics():
    """Verify demographic data after cleanup"""
    logger.info("Verifying demographic data after cleanup...")
    
    async for session in get_db():
        # Get total count of demographic records
        total_count_query = select(func.count(Demographics.id))
        total_result = await session.execute(total_count_query)
        total_count = total_result.scalar()
        
        logger.info(f"Total demographic records: {total_count}")
        
        # Get count by demographic type
        type_count_query = (
            select(Demographics.demographic_type, func.count(Demographics.id))
            .group_by(Demographics.demographic_type)
        )
        type_results = await session.execute(type_count_query)
        
        logger.info("\nCounts by demographic type:")
        for demo_type, count in type_results:
            logger.info(f"  {demo_type}: {count} records")
        
        # Get sample of Working Professional records
        wp_query = (
            select(Demographics)
            .where(Demographics.demographic_type == "Working Professional")
            .options(selectinload(Demographics.student))
            .limit(3)
        )
        wp_results = await session.execute(wp_query)
        wp_records = wp_results.scalars().all()
        
        logger.info("\nSample Working Professional records:")
        for record in wp_records:
            logger.info(f"  Student ID: {record.student_id}")
        
        # Check for any duplicate student IDs
        duplicate_query = (
            select(Demographics.student_id, func.count(Demographics.id))
            .group_by(Demographics.student_id)
            .having(func.count(Demographics.id) > 1)
        )
        duplicate_results = await session.execute(duplicate_query)
        duplicates = duplicate_results.all()
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} students with duplicate demographic records:")
            for student_id, count in duplicates:
                logger.warning(f"  Student ID {student_id}: {count} records")
        else:
            logger.success("✓ No duplicate demographic records found")
        
        # Verify we have the expected distribution
        expected_total = 10  # Based on our cleanup script results
        if total_count == expected_total:
            logger.success(f"✓ Total count matches expected: {total_count}")
        else:
            logger.warning(f"⚠ Total count ({total_count}) doesn't match expected ({expected_total})")
        
        return total_count > 0 and len(duplicates) == 0

if __name__ == "__main__":
    success = asyncio.run(verify_demographics())
    if success:
        logger.success("\n✓ Demographic data verification completed successfully!")
        logger.info("The segmentation analysis should now work properly with this cleaned data.")
    else:
        logger.error("\n✗ Issues found with demographic data")
        sys.exit(1)