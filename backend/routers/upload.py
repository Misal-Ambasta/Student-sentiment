import os
import uuid
import shutil
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database import get_db, File as DBFile
from vector_store import get_chroma_manager
from llm_integration import get_llm_manager, LLMProvider
from celery_tasks.data_processing import process_file

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}

# Upload directory
UPLOAD_DIR = "uploads"

@router.post("/both-files")
async def upload_both_files(
    background_tasks: BackgroundTasks,
    nps_file: UploadFile = File(...),
    demographics_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload both NPS and demographics files in a single request"""
    results = []
    
    # Process NPS file
    nps_result = await process_upload_file(background_tasks, nps_file, "survey", db)
    results.append(nps_result)
    
    # Process demographics file
    demographics_result = await process_upload_file(background_tasks, demographics_file, "demographics", db)
    results.append(demographics_result)
    
    return results

async def process_upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    file_type: str,
    db: AsyncSession
):
    """Process a single file upload"""
    try:
        # Check file extension
        _, file_ext = os.path.splitext(file.filename)
        if file_ext.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {file_ext} not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Create unique file ID and path
        file_id = str(uuid.uuid4())
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create file record in database
        db_file = DBFile(
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path),
            status="uploaded",
            file_metadata=f'{{"file_type": "{file_type}"}}' # Store file_type in file_metadata
        )
        
        db.add(db_file)
        await db.commit()
        
        # Start background processing
        background_tasks.add_task(process_file, file_id, file_path, file_type)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "File uploaded successfully and queued for processing"
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{file_id}")
async def get_file_status(file_id: str, db: AsyncSession = Depends(get_db)):
    """Get file processing status"""
    try:
        # Query file status from database
        from sqlalchemy import text
        query = await db.execute(text("SELECT * FROM files WHERE file_id = :file_id"), {"file_id": file_id})
        file = query.fetchone()
        
        if not file:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Parse file_metadata if available
        header_mapping = None
        if file.file_metadata:
            import json
            try:
                metadata = json.loads(file.file_metadata)
                if 'header_mapping' in metadata:
                    header_mapping = metadata['header_mapping']
            except json.JSONDecodeError:
                logger.error(f"Error parsing file_metadata for file {file_id}")
        
        return {
            "file_id": file.file_id,
            "filename": file.filename,
            "status": file.status,
            "message": file.error_message if file.status == "failed" else None,
            "created_at": file.created_at,
            "updated_at": file.updated_at,
            "headerMapping": header_mapping
        }
    except Exception as e:
        logger.error(f"Error getting file status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def get_files(limit: int = 10, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Get list of uploaded files"""
    try:
        # Query files from database
        query = await db.execute(
            f"SELECT * FROM files ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
        )
        files = query.fetchall()
        
        # Count total files
        count_query = await db.execute("SELECT COUNT(*) FROM files")
        total = count_query.scalar()
        
        return {
            "files": [
                {
                    "file_id": file.file_id,
                    "filename": file.filename,
                    "status": file.status,
                    "created_at": file.created_at,
                    "updated_at": file.updated_at
                }
                for file in files
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview/{file_id}")
async def get_file_preview(file_id: str, db: AsyncSession = Depends(get_db)):
    """Get a preview of file contents"""
    try:
        # Query file from database
        query = await db.execute(f"SELECT * FROM files WHERE file_id = '{file_id}'")
        file = query.fetchone()
        
        if not file:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Check if file exists
        if not os.path.exists(file.file_path):
            raise HTTPException(status_code=404, detail=f"File not found on disk")
        
        # Read file preview based on file extension
        _, file_ext = os.path.splitext(file.file_path)
        
        if file_ext.lower() == ".csv":
            import pandas as pd
            df = pd.read_csv(file.file_path, nrows=10)  # Read only first 10 rows
            headers = df.columns.tolist()
            rows = df.head(5).to_dict('records')  # Convert first 5 rows to dict
            
        elif file_ext.lower() in [".xls", ".xlsx"]:
            import pandas as pd
            df = pd.read_excel(file.file_path, nrows=10)  # Read only first 10 rows
            headers = df.columns.tolist()
            rows = df.head(5).to_dict('records')  # Convert first 5 rows to dict
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_ext}")
        
        return {
            "headers": headers,
            "rows": rows
        }
        
    except Exception as e:
        logger.error(f"Error getting file preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/file/{file_id}")
async def delete_file(file_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a file"""
    try:
        # Query file from database
        query = await db.execute(f"SELECT * FROM files WHERE file_id = '{file_id}'")
        file = query.fetchone()
        
        if not file:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Delete file from disk
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Delete file from database
        await db.execute(f"DELETE FROM files WHERE file_id = '{file_id}'")
        await db.commit()
        
        return {"message": f"File {file_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))