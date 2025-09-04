#!/usr/bin/env python3
"""
Script to refresh ChromaDB with demographic data from the database
"""

import asyncio
from loguru import logger
from celery_tasks.data_processing import get_sync_db
from vector_store import get_chroma_manager
from sqlalchemy import text

async def refresh_demographics_in_chromadb():
    """Refresh ChromaDB with demographic data from database"""
    try:
        # Get database connection
        db = get_sync_db()
        
        # Get all demographic data
        query = text("""
            SELECT student_id, demographic_type, current_grade, attendance_rate
            FROM demographics
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        logger.info(f"Found {len(rows)} demographic records to refresh in ChromaDB")
        
        # Convert to list of dictionaries
        demographic_data = []
        for row in rows:
            demographic_data.append({
                'student_id': row[0],
                'demographic_type': row[1],
                'current_grade': row[2],
                'attendance_rate': row[3]
            })
        
        db.close()
        
        if not demographic_data:
            logger.info("No demographic data found to refresh")
            return
        
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # Clear existing demographic data
        logger.info("Clearing existing demographic data from ChromaDB...")
        try:
            # Delete all documents with document_type = demographics
            collection = chroma_manager.student_db._collection
            # Get all document IDs
            all_data = collection.get(where={"document_type": "demographics"})
            if all_data['ids']:
                logger.info(f"Deleting {len(all_data['ids'])} existing demographic documents")
                collection.delete(ids=all_data['ids'])
            else:
                logger.info("No existing demographic documents to delete")
        except Exception as e:
            logger.warning(f"Could not clear existing demographic data: {e}")
        
        # Add refreshed data to ChromaDB
        logger.info("Adding refreshed demographic data to ChromaDB...")
        doc_ids = await chroma_manager.add_student_data(demographic_data)
        
        logger.info(f"Successfully refreshed {len(doc_ids)} demographic documents in ChromaDB")
        
        # Verify the data
        logger.info("\nVerifying demographic data in ChromaDB...")
        demo_docs = await chroma_manager.search_student_data(
            query="demographic_type Working Professional Fresh Graduate Career Switcher",
            filter_metadata={"document_type": "demographics"},
            k=10
        )
        
        # Count by demographic type
        demo_counts = {}
        for doc in demo_docs:
            demo_type = doc.metadata.get('demographic_type')
            if demo_type:
                demo_counts[demo_type] = demo_counts.get(demo_type, 0) + 1
        
        logger.info("Demographic counts in ChromaDB:")
        for demo_type, count in demo_counts.items():
            logger.info(f"  {demo_type}: {count}")
        
    except Exception as e:
        logger.error(f"Error refreshing demographic data in ChromaDB: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting demographic data refresh in ChromaDB...")
    asyncio.run(refresh_demographics_in_chromadb())
    logger.info("Demographic data refresh completed!")