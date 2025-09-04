#!/usr/bin/env python3
"""
Simple script to check if ChromaDB collections are empty
"""

import os
from loguru import logger

# Import the ChromaDB directory path
from vector_store import CHROMA_DIR, ChromaManager

def check_chromadb_collections():
    """
    Check if ChromaDB collections exist and if they have any documents
    """
    try:
        logger.info(f"Checking ChromaDB directory at {CHROMA_DIR}")
        
        if not os.path.exists(CHROMA_DIR):
            logger.info(f"ChromaDB directory not found at {CHROMA_DIR}")
            return "ChromaDB directory does not exist"
        
        # Create a ChromaManager instance
        chroma_manager = ChromaManager()
        
        # Check collection counts
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
        
        return f"ChromaDB collection counts - Survey: {survey_count}, Student: {student_count}, Chat History: {chat_history_count}"
    
    except Exception as e:
        logger.error(f"Error checking ChromaDB: {str(e)}")
        return f"Failed to check ChromaDB: {str(e)}"

# Run the function if executed directly
if __name__ == "__main__":
    result = check_chromadb_collections()
    print(result)