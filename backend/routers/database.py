from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from database import get_db, Base, engine, Student, Demographics, Survey, File, ChatSession, ChatMessage
from typing import Dict, Any, List
from loguru import logger
import json
import os
import shutil
from vector_store import get_chroma_manager, CHROMA_DIR

router = APIRouter(prefix="/api/database", tags=["database"])

@router.delete("/tables")
async def delete_all_tables(db: AsyncSession = Depends(get_db)):
    """
    Delete all database tables.
    WARNING: This will permanently remove all table structures and data.
    """
    try:
        # Drop all tables using SQLAlchemy metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("All database tables have been deleted")
        return {"message": "All database tables have been successfully deleted"}
    
    except Exception as e:
        logger.error(f"Error deleting tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete tables: {str(e)}")

@router.delete("/data")
async def clear_all_data(db: AsyncSession = Depends(get_db)):
    """
    Delete all data from all tables while keeping table structures intact.
    """
    try:
        # List of all table models in dependency order (to handle foreign key constraints)
        tables_to_clear = [
            ChatMessage,  # Has foreign key to ChatSession
            ChatSession,
            Survey,       # Has foreign key to Student
            Demographics, # Has foreign key to Student
            File,
            Student,      # Referenced by other tables
        ]
        
        # Delete data from each table
        for table_model in tables_to_clear:
            result = await db.execute(text(f"DELETE FROM {table_model.__tablename__}"))
            logger.info(f"Deleted {result.rowcount} rows from {table_model.__tablename__}")
        
        await db.commit()
        
        logger.info("All data has been cleared from database tables")
        return {"message": "All data has been successfully cleared from database tables"}
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Error clearing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@router.delete("/reset")
async def reset_all_data(db: AsyncSession = Depends(get_db)):
    """
    Reset endpoint that deletes all data from PostgreSQL tables and ChromaDB.
    This is a complete reset of the application's data.
    """
    try:
        # Step 1: Clear all PostgreSQL tables
        tables_to_clear = [
            ChatMessage,  # Has foreign key to ChatSession
            ChatSession,
            Survey,       # Has foreign key to Student
            Demographics, # Has foreign key to Student
            File,
            Student,      # Referenced by other tables
        ]
        
        # Delete data from each table
        for table_model in tables_to_clear:
            result = await db.execute(text(f"DELETE FROM {table_model.__tablename__}"))
            logger.info(f"Reset: Deleted {result.rowcount} rows from {table_model.__tablename__}")
        
        await db.commit()
        
        # Step 2: Clear ChromaDB collections by directly accessing the collections
        try:
            # Import here to avoid circular imports
            from vector_store import get_chroma_manager, ChromaManager
            
            # Get the ChromaDB manager
            chroma_manager = get_chroma_manager()
            
            # Reset the ChromaDB manager instance to force recreation
            import vector_store
            vector_store._chroma_manager = None
            
            # Try to delete the ChromaDB directory if it exists
            try:
                if os.path.exists(CHROMA_DIR) and os.path.isdir(CHROMA_DIR):
                    shutil.rmtree(CHROMA_DIR)
                    logger.info(f"Reset: Removed ChromaDB directory at {CHROMA_DIR}")
                
                # Create a new ChromaDB manager to initialize fresh collections
                import vector_store
                vector_store._chroma_manager = None
                new_chroma_manager = ChromaManager()
                
                # Verify collections are empty
                survey_count = len(new_chroma_manager.survey_db._collection.get()['ids'])
                student_count = len(new_chroma_manager.student_db._collection.get()['ids'])
                chat_history_count = len(new_chroma_manager.chat_history_db._collection.get()['ids'])
                
                logger.info(f"Reset: ChromaDB collections recreated with counts - Survey: {survey_count}, Student: {student_count}, Chat History: {chat_history_count}")
                
                # Update the singleton instance
                vector_store._chroma_manager = new_chroma_manager
            except PermissionError as pe:
                logger.warning(f"Reset: Could not delete ChromaDB directory due to permission error: {str(pe)}")
                logger.warning("Reset: ChromaDB will be cleared on next server restart")
            except Exception as e:
                logger.warning(f"Reset: Issue with ChromaDB reset: {str(e)}")
                logger.warning("Reset: ChromaDB will be cleared on next server restart")
            
        except Exception as e:
            logger.error(f"Error resetting ChromaDB: {str(e)}")
            # Continue with the response even if ChromaDB reset fails
        
        logger.info("Complete reset of all data (PostgreSQL and ChromaDB) successful")
        return {"message": "All data has been successfully reset from PostgreSQL and ChromaDB"}
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during complete data reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset all data: {str(e)}")

@router.get("/data")
async def fetch_all_table_data(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Fetch row counts from all database tables.
    Returns a dictionary with table names as keys and their row counts as values.
    """
    try:
        result = {}
        
        # Define all table models
        table_models = {
            "students": Student,
            "demographics": Demographics,
            "surveys": Survey,
            "files": File,
            "chat_sessions": ChatSession,
            "chat_messages": ChatMessage,
        }
        
        # Get row count from each table
        for table_name, table_model in table_models.items():
            try:
                # Get count of records from the table
                query_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = query_result.scalar()
                result[table_name] = count
                    
            except Exception as table_error:
                logger.warning(f"Error fetching count from {table_name}: {str(table_error)}")
                result[table_name] = 0
        
        # Add summary information
        total_records = sum(count for count in result.values() if isinstance(count, int))
        result["_summary"] = {
            "total_tables": len(table_models),
            "total_records": total_records
        }
        
        logger.info(f"Fetched row counts from {len(table_models)} tables with {total_records} total records")
        return result
    
    except Exception as e:
        logger.error(f"Error fetching table data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch table data: {str(e)}")

@router.get("/tables/info")
async def get_table_info(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Get information about all database tables including structure and row counts.
    """
    try:
        result = {}
        
        # Get table information using SQLAlchemy inspector
        async with engine.connect() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            table_names = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
            
            for table_name in table_names:
                try:
                    # Get column information
                    columns = await conn.run_sync(lambda sync_conn: inspector.get_columns(table_name))
                    
                    # Get row count
                    count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.scalar()
                    
                    result[table_name] = {
                        "row_count": row_count,
                        "columns": [
                            {
                                "name": col["name"],
                                "type": str(col["type"]),
                                "nullable": col["nullable"],
                                "primary_key": col.get("primary_key", False)
                            }
                            for col in columns
                        ]
                    }
                    
                except Exception as table_error:
                    logger.warning(f"Error getting info for table {table_name}: {str(table_error)}")
                    result[table_name] = {"error": str(table_error)}
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting table info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get table info: {str(e)}")