#!/usr/bin/env python3

import os
import sys
import logging
import json
import sqlite3
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Constants
CHROMA_DIR = "./chroma_db"

def check_chromadb_directory():
    """Check if ChromaDB directory exists and report its status"""
    try:
        if not os.path.exists(CHROMA_DIR):
            logger.info(f"ChromaDB directory does not exist at {CHROMA_DIR}")
            return False
        
        if not os.path.isdir(CHROMA_DIR):
            logger.info(f"{CHROMA_DIR} exists but is not a directory")
            return False
        
        # Check for key ChromaDB files
        sqlite_file = os.path.join(CHROMA_DIR, "chroma.sqlite3")
        if os.path.exists(sqlite_file):
            logger.info(f"ChromaDB SQLite file exists at {sqlite_file}")
        else:
            logger.info(f"ChromaDB SQLite file does not exist at {sqlite_file}")
            return True
        
        # List collections directory if it exists
        collections_dir = os.path.join(CHROMA_DIR, "collections")
        if os.path.exists(collections_dir) and os.path.isdir(collections_dir):
            collections = os.listdir(collections_dir)
            logger.info(f"Collections directory contains: {collections}")
        else:
            logger.info("Collections directory does not exist")
            
        return True
    except Exception as e:
        logger.error(f"Error checking ChromaDB directory: {str(e)}")
        return False
        
def check_sqlite_collections():
    """Check ChromaDB collections directly from SQLite database"""
    try:
        sqlite_file = os.path.join(CHROMA_DIR, "chroma.sqlite3")
        if not os.path.exists(sqlite_file):
            logger.info(f"ChromaDB SQLite file does not exist at {sqlite_file}")
            return False
            
        # Connect to SQLite database
        conn = sqlite3.connect(sqlite_file)
        cursor = conn.cursor()
        
        # Get collections
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collections'")
        if cursor.fetchone() is None:
            logger.info("No collections table found in ChromaDB")
            conn.close()
            return False
            
        cursor.execute("SELECT name, id FROM collections")
        collections = cursor.fetchall()
        
        if not collections:
            logger.info("No collections found in ChromaDB")
            conn.close()
            return True
            
        logger.info(f"Found {len(collections)} collections in ChromaDB:")
        
        # Check each collection for embeddings
        for name, collection_id in collections:
            # Get table structure to find the right column name
            cursor.execute(f"PRAGMA table_info(embeddings)")
            columns = cursor.fetchall()
            collection_id_column = None
            
            # Find the column that likely refers to collection_id
            for col in columns:
                if 'collection' in col[1].lower() and 'id' in col[1].lower():
                    collection_id_column = col[1]
                    break
            
            if collection_id_column:
                cursor.execute(f"SELECT COUNT(*) FROM embeddings WHERE {collection_id_column} = ?", (collection_id,))
                count = cursor.fetchone()[0]
                logger.info(f"Collection '{name}' (ID: {collection_id}) has {count} embeddings")
            else:
                # If we can't find the right column, just count all embeddings
                cursor.execute(f"SELECT COUNT(*) FROM embeddings")
                count = cursor.fetchone()[0]
                logger.info(f"Collection '{name}' (ID: {collection_id}) - Unable to filter by collection, total embeddings in DB: {count}")
            
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error checking ChromaDB collections: {str(e)}")
        return False

def main():
    logger.info("Starting ChromaDB directory check")
    
    # Check ChromaDB directory
    chroma_exists = check_chromadb_directory()
    
    if chroma_exists:
        logger.info("ChromaDB directory exists and was checked successfully")
        
        # Check collections in SQLite database
        logger.info("Checking ChromaDB collections in SQLite database")
        check_sqlite_collections()
    else:
        logger.info("ChromaDB directory check failed or directory does not exist")
    
    logger.info("ChromaDB check completed")

if __name__ == "__main__":
    main()