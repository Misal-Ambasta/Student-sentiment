#!/usr/bin/env python3
"""
Script to forcefully clear ChromaDB collections without repopulating
"""

import asyncio
import os
import shutil
from loguru import logger
from vector_store import get_chroma_manager

async def force_clear_chromadb():
    """Forcefully clear ChromaDB by deleting the database files without repopulating"""
    try:
        logger.info("Starting forceful clear of ChromaDB...")
        
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
        
        # Verify collections are empty
        # Get collection counts
        try:
            survey_count = len(chroma_manager.survey_db._collection.get()['ids'])
            logger.info(f"Survey collection count: {survey_count}")
        except Exception as e:
            logger.error(f"Error checking survey collection: {str(e)}")
            survey_count = "Error"
            
        try:
            student_count = len(chroma_manager.student_db._collection.get()['ids'])
            logger.info(f"Student collection count: {student_count}")
        except Exception as e:
            logger.error(f"Error checking student collection: {str(e)}")
            student_count = "Error"
            
        try:
            chat_history_count = len(chroma_manager.chat_history_db._collection.get()['ids'])
            logger.info(f"Chat history collection count: {chat_history_count}")
        except Exception as e:
            logger.error(f"Error checking chat history collection: {str(e)}")
            chat_history_count = "Error"
        
        logger.info(f"ChromaDB collections recreated with counts - Survey: {survey_count}, Student: {student_count}, Chat History: {chat_history_count}")
        
        return True, f"ChromaDB successfully cleared. Collection counts - Survey: {survey_count}, Student: {student_count}, Chat History: {chat_history_count}"
    
    except Exception as e:
        logger.error(f"Error clearing ChromaDB: {str(e)}")
        return False, f"Failed to clear ChromaDB: {str(e)}"

# Run the function if executed directly
if __name__ == "__main__":
    success, message = asyncio.run(force_clear_chromadb())
    print(message)