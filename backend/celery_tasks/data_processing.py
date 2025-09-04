import os
import pandas as pd
import json
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

def safe_int_convert(value):
    """Safely convert value to integer, return 0 if conversion fails"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0

# Import managers
from database import get_db, engine, Base
from vector_store import get_chroma_manager
from llm_integration import get_llm_manager, LLMProvider
from routers.websocket import broadcast_file_update
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine as sync_create_engine, text

# Celery app
from celery import Celery

# Create Celery app
celery_app = Celery(
    "data_processing",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Create synchronous database engine for Celery tasks
DATABASE_URL = os.getenv("NEON_DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/student_sense"))
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
if "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

sync_engine = sync_create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
SyncSessionLocal = sessionmaker(bind=sync_engine)

def get_sync_db():
    """Get synchronous database session for Celery tasks"""
    db = SyncSessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise

@celery_app.task
def process_file(file_id: str, file_path: str, file_type: str):
    """Process uploaded file"""
    try:
        logger.info(f"Processing file {file_id} of type {file_type}")
        
        # Update file status to processing
        update_file_status(file_id, "processing")
        
        # Broadcast update
        broadcast_file_update(file_id, "processing", "File processing started")
        
        # Process file based on type
        if file_type == "survey":
            process_survey_file(file_id, file_path)
        elif file_type == "demographics":
            process_demographics_file(file_id, file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Update file status to completed
        update_file_status(file_id, "completed")
        
        # Broadcast update
        broadcast_file_update(file_id, "completed", "File processing completed successfully")
        
        logger.info(f"File {file_id} processed successfully")
        return {"status": "success", "file_id": file_id}
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {e}")
        
        # Update file status to failed
        update_file_status(file_id, "failed", str(e))
        
        # Broadcast update
        broadcast_file_update(file_id, "failed", f"File processing failed: {str(e)}")
        
        return {"status": "error", "file_id": file_id, "error": str(e)}

def update_file_status(file_id: str, status: str, error_message: Optional[str] = None):
    """Update file status in database"""
    try:
        # Get database session
        db = get_sync_db()
        
        # Update file status
        if error_message:
            query = text(
                "UPDATE files SET status = :status, error_message = :error_message, "
                "updated_at = :updated_at WHERE file_id = :file_id"
            )
            db.execute(query, {
                "status": status,
                "error_message": error_message,
                "updated_at": datetime.utcnow(),
                "file_id": file_id
            })
        else:
            query = text(
                "UPDATE files SET status = :status, "
                "updated_at = :updated_at WHERE file_id = :file_id"
            )
            db.execute(query, {
                "status": status,
                "updated_at": datetime.utcnow(),
                "file_id": file_id
            })
        
        db.commit()
        db.close()
        logger.info(f"Updated file {file_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating file status: {e}")
        raise

def update_file_metadata(file_id: str, metadata_update: Dict[str, Any]):
    """Update file metadata in database"""
    try:
        # Get database session
        db = get_sync_db()
        
        # Get current file_metadata
        query = text("SELECT file_metadata FROM files WHERE file_id = :file_id")
        result = db.execute(query, {"file_id": file_id}).fetchone()
        
        if not result:
            logger.error(f"File {file_id} not found")
            db.close()
            return
        
        # Parse current file_metadata
        current_metadata = {}
        if result.file_metadata:
            try:
                current_metadata = json.loads(result.file_metadata)
            except json.JSONDecodeError:
                logger.warning(f"Invalid file_metadata format for file {file_id}")
        
        # Update file_metadata
        current_metadata.update(metadata_update)
        
        # Save updated file_metadata
        metadata_json = json.dumps(current_metadata)
        update_query = text(
            "UPDATE files SET file_metadata = :metadata, "
            "updated_at = :updated_at WHERE file_id = :file_id"
        )
        db.execute(update_query, {
            "metadata": metadata_json,
            "updated_at": datetime.utcnow(),
            "file_id": file_id
        })
        
        db.commit()
        db.close()
        logger.info(f"Updated metadata for file {file_id}")
    except Exception as e:
        logger.error(f"Error updating file metadata: {e}")
        raise

def process_survey_file(file_id: str, file_path: str):
    """Process survey file"""
    try:
        # Read file
        df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
        
        # Check if file has expected format
        is_real_format = len(df.columns) >= 20  # Real format has 24 columns
        
        # Map headers using intelligent mapping
        header_mapping = None
        if is_real_format:
            # Use Groq to map headers
            header_mapping = map_headers_with_llm(df)
            
            # Transform data using mapping
            transformed_data = transform_survey_data(df, header_mapping)
        else:
            # Assume file already has expected format
            transformed_data = transform_simple_survey_data(df)
            # Create a simple mapping for display
            header_mapping = {
                "student_id": df.columns[0],
                "timestamp": df.columns[1] if len(df.columns) > 1 else "DERIVED",
                "nps_score": df.columns[2] if len(df.columns) > 2 else "DERIVED",
                "comments": df.columns[-1] if len(df.columns) > 3 else "DERIVED"
            }
        
        # Save transformed data to database
        save_survey_data(transformed_data)
        
        # Add data to ChromaDB
        add_survey_data_to_chroma(transformed_data)
        
        # Store header mapping in file metadata
        if header_mapping:
            update_file_metadata(file_id, {"header_mapping": header_mapping})
        
        logger.info(f"Survey file {file_id} processed successfully")
    except Exception as e:
        logger.error(f"Error processing survey file: {e}")
        raise

def process_demographics_file(file_id: str, file_path: str):
    """Process demographics file"""
    try:
        # Read file
        df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
        
        # Transform data
        transformed_data = transform_demographics_data(df)
        
        # Create a mapping for display
        header_mapping = {
            "student_id": df.columns[0],
            "name": df.columns[1] if len(df.columns) > 1 else "DERIVED",
            "email": df.columns[2] if len(df.columns) > 2 else "DERIVED",
            "program": df.columns[3] if len(df.columns) > 3 else "DERIVED",
            "year": df.columns[4] if len(df.columns) > 4 else "DERIVED",
            "gender": df.columns[5] if len(df.columns) > 5 else "DERIVED"
        }
        
        # Save transformed data to database
        save_demographics_data(transformed_data)
        
        # Add data to ChromaDB
        add_demographics_data_to_chroma(transformed_data)
        
        # Store header mapping in file metadata
        update_file_metadata(file_id, {"header_mapping": header_mapping})
        
        logger.info(f"Demographics file {file_id} processed successfully")
    except Exception as e:
        logger.error(f"Error processing demographics file: {e}")
        raise

def map_headers_with_llm(df: pd.DataFrame) -> Dict[str, str]:
    """Map headers using LLM"""
    try:
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Create prompt with first 3 rows of data
        sample_data = df.head(3).to_string(index=False)
        
        prompt = f"""
        You are an expert data analyst tasked with mapping CSV headers to a standardized schema.
        
        The CSV file has the following columns and sample data:
        
        {sample_data}
        
        Map these columns to the following required schema:
        - student_id: Student identifier
        - timestamp: When the survey was taken
        - nps_score: Net Promoter Score (0-10)
        - course_id: Course identifier
        - week_number: Week number in the course
        - aspect_1_score: First aspect score
        - aspect_2_score: Second aspect score
        - aspect_3_score: Third aspect score
        - comments: Student comments or feedback
        
        For the mapping:
        1. The "student_id" should map to the "Student code" column
        2. The "timestamp" should map to the "Timestamp" column
        3. The "nps_score" should map to the main NPS question response
        4. The "course_id" should be extracted from the student_id (value before underscore)
        5. The "week_number" should be calculated from the timestamp or default to 1
        6. For aspect scores, select the 3 most representative scores from available ratings
        7. The "comments" should combine improvement feedback and additional feedback
        
        Return the mapping as a JSON object with the required schema fields as keys and the original column names as values.
        For derived fields like course_id, use "DERIVED" as the value.
        """
        
        # Generate mapping using asyncio event loop handling
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new thread to run the async function
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        llm_manager.generate_response(
                            prompt=prompt,
                            preferred_provider=LLMProvider.GROQ
                        )
                    )
                    mapping_text = future.result()
            else:
                # If no loop is running, use asyncio.run
                mapping_text = asyncio.run(llm_manager.generate_response(
                    prompt=prompt,
                    preferred_provider=LLMProvider.GROQ
                ))
        except RuntimeError:
            # Fallback: create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                mapping_text = loop.run_until_complete(llm_manager.generate_response(
                    prompt=prompt,
                    preferred_provider=LLMProvider.GROQ
                ))
            finally:
                loop.close()
        
        # Parse mapping
        mapping = json.loads(mapping_text)
        
        logger.info(f"Generated header mapping: {mapping}")
        return mapping
    except Exception as e:
        logger.error(f"Error mapping headers: {e}")
        # Fallback to default mapping
        return {
            "student_id": "Student code",
            "timestamp": "Timestamp",
            "nps_score": df.columns[2],  # Assume third column is NPS score
            "course_id": "DERIVED",
            "week_number": "DERIVED",
            "aspect_1_score": df.columns[4] if len(df.columns) > 4 else "DERIVED",
            "aspect_2_score": df.columns[9] if len(df.columns) > 9 else "DERIVED",
            "aspect_3_score": df.columns[14] if len(df.columns) > 14 else "DERIVED",
            "comments": df.columns[3] if len(df.columns) > 3 else "DERIVED"
        }

def transform_survey_data(df: pd.DataFrame, header_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Transform survey data using header mapping"""
    transformed_data = []
    
    for _, row in df.iterrows():
        item = {}
        
        # Map fields using header mapping
        for target_field, source_field in header_mapping.items():
            if source_field == "DERIVED":
                # Handle derived fields
                if target_field == "course_id" and "student_id" in item:
                    # Extract course_id from student_id
                    student_id = item["student_id"]
                    item[target_field] = student_id.split("_")[0] if "_" in student_id else "unknown"
                elif target_field == "week_number":
                    # Default to week 1
                    item[target_field] = 1
                else:
                    # Default value
                    item[target_field] = "unknown" if target_field in ["student_id", "course_id"] else 0
            else:
                # Map direct fields
                if source_field in row:
                    item[target_field] = row[source_field]
                else:
                    # Field not found
                    item[target_field] = "unknown" if target_field in ["student_id", "course_id"] else 0
        
        # Extract detailed course scores from 24-column format
        if len(df.columns) >= 24:
            # Course A scores (columns 5-9): Lecture, Instructor, Sherpa, Ask&Learn, PP
            course_a_scores = {
                "lecture_experience": safe_int_convert(row.iloc[4]) if len(row) > 4 else 0,
                "instructor_delivery": safe_int_convert(row.iloc[5]) if len(row) > 5 else 0,
                "sherpa_support": safe_int_convert(row.iloc[6]) if len(row) > 6 else 0,
                "ask_learn_effectiveness": safe_int_convert(row.iloc[7]) if len(row) > 7 else 0,
                "pp_session": safe_int_convert(row.iloc[8]) if len(row) > 8 else 0
            }
            
            # Course B scores (columns 10-14): Same aspects for Course B
            course_b_scores = {
                "lecture_experience": safe_int_convert(row.iloc[9]) if len(row) > 9 else 0,
                "instructor_delivery": safe_int_convert(row.iloc[10]) if len(row) > 10 else 0,
                "sherpa_support": safe_int_convert(row.iloc[11]) if len(row) > 11 else 0,
                "ask_learn_effectiveness": safe_int_convert(row.iloc[12]) if len(row) > 12 else 0,
                "pp_session": safe_int_convert(row.iloc[13]) if len(row) > 13 else 0
            }
            
            # CSBT scores (columns 15-17): Curriculum, Instructor, Support
            csbt_scores = {
                "curriculum_design": safe_int_convert(row.iloc[14]) if len(row) > 14 else 0,
                "instructor_support": safe_int_convert(row.iloc[15]) if len(row) > 15 else 0,
                "general_support": safe_int_convert(row.iloc[16]) if len(row) > 16 else 0
            }
            
            # Dost support (column 18)
            dost_support_scores = {
                "dost_support": safe_int_convert(row.iloc[17]) if len(row) > 17 else 0
            }
            
            # Product support scores (columns 19-23): LMS, Assess, Ticketing, PSC, PAI
            product_support_scores = {
                "lms_platform": safe_int_convert(row.iloc[18]) if len(row) > 18 else 0,
                "assess_platform": safe_int_convert(row.iloc[19]) if len(row) > 19 else 0,
                "ticketing_system": safe_int_convert(row.iloc[20]) if len(row) > 20 else 0,
                "psc_sessions": safe_int_convert(row.iloc[21]) if len(row) > 21 else 0,
                "pai_evaluation": safe_int_convert(row.iloc[22]) if len(row) > 22 else 0
            }
            
            # Add JSONB data to item
            item["course_a_scores"] = course_a_scores
            item["course_b_scores"] = course_b_scores
            item["csbt_scores"] = csbt_scores
            item["dost_support_scores"] = dost_support_scores
            item["product_support_scores"] = product_support_scores
        
        # Handle comments field specially
        if "comments" not in item or not item["comments"]:
            # Try to combine improvement feedback and additional feedback
            improvement_feedback = row.get(df.columns[3], "")
            additional_feedback = row.get(df.columns[23], "") if len(df.columns) > 23 else ""
            
            comments = ""
            if improvement_feedback:
                comments += f"Improvement needed: {improvement_feedback}"
            if additional_feedback:
                if comments:
                    comments += "\n\n"
                comments += f"Additional feedback: {additional_feedback}"
            
            if not comments:
                comments = "No additional feedback provided"
            
            item["comments"] = comments
        
        # Convert timestamp to datetime
        if "timestamp" in item and item["timestamp"]:
            try:
                item["timestamp"] = pd.to_datetime(item["timestamp"])
            except:
                item["timestamp"] = datetime.utcnow()
        else:
            item["timestamp"] = datetime.utcnow()
        
        transformed_data.append(item)
    
    return transformed_data

def transform_simple_survey_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Transform survey data that already has expected format"""
    transformed_data = []
    
    for _, row in df.iterrows():
        item = {
            "student_id": row.get("student_id", "unknown"),
            "timestamp": pd.to_datetime(row.get("timestamp", datetime.utcnow())),
            "nps_score": int(row.get("nps_score", 0)),
            "course_id": row.get("course_id", "unknown"),
            "week_number": int(row.get("week_number", 1)),
            "aspect_1_score": int(row.get("aspect_1_score", 0)),
            "aspect_2_score": int(row.get("aspect_2_score", 0)),
            "aspect_3_score": int(row.get("aspect_3_score", 0)),
            "comments": row.get("comments", "No additional feedback provided")
        }
        
        transformed_data.append(item)
    
    return transformed_data

def transform_demographics_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Transform demographics data"""
    transformed_data = []
    
    for _, row in df.iterrows():
        item = {
            "student_id": row.get("student_id", "unknown"),
            "demographic_type": row.get("demographic_type", "unknown"),
            "current_grade": row.get("current_grade", "unknown"),
            "attendance_rate": float(row.get("attendance_rate", 0))
        }
        
        transformed_data.append(item)
    
    return transformed_data

def save_survey_data(data: List[Dict[str, Any]]):
    """Save survey data to database"""
    try:
        # Get database session
        db = get_sync_db()
        
        for item in data:
            # Check if student exists
            student_query = text("SELECT * FROM students WHERE student_id = :student_id")
            student = db.execute(student_query, {"student_id": item['student_id']}).fetchone()
            
            # Create student if not exists
            if not student:
                insert_student = text(
                    "INSERT INTO students (student_id, created_at, updated_at) "
                    "VALUES (:student_id, :created_at, :updated_at)"
                )
                db.execute(insert_student, {
                    "student_id": item['student_id'],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            
            # Insert survey
            insert_survey = text(
                "INSERT INTO surveys "
                "(student_id, timestamp, nps_score, course_id, week_number, "
                "aspect_1_score, aspect_2_score, aspect_3_score, comments, "
                "course_a_scores, course_b_scores, csbt_scores, dost_support_scores, product_support_scores, "
                "created_at, updated_at) "
                "VALUES "
                "(:student_id, :timestamp, :nps_score, :course_id, :week_number, "
                ":aspect_1_score, :aspect_2_score, :aspect_3_score, :comments, "
                ":course_a_scores, :course_b_scores, :csbt_scores, :dost_support_scores, :product_support_scores, "
                ":created_at, :updated_at)"
            )
            db.execute(insert_survey, {
                "student_id": item['student_id'],
                "timestamp": item['timestamp'],
                "nps_score": item['nps_score'],
                "course_id": item['course_id'],
                "week_number": item['week_number'],
                "aspect_1_score": item['aspect_1_score'],
                "aspect_2_score": item['aspect_2_score'],
                "aspect_3_score": item['aspect_3_score'],
                "comments": item['comments'],
                "course_a_scores": json.dumps(item.get('course_a_scores', {})),
                "course_b_scores": json.dumps(item.get('course_b_scores', {})),
                "csbt_scores": json.dumps(item.get('csbt_scores', {})),
                "dost_support_scores": json.dumps(item.get('dost_support_scores', {})),
                "product_support_scores": json.dumps(item.get('product_support_scores', {})),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        
        db.commit()
        db.close()
        logger.info(f"Saved {len(data)} survey records to database")
    except Exception as e:
        logger.error(f"Error saving survey data: {e}")
        raise

def save_demographics_data(data: List[Dict[str, Any]]):
    """Save demographics data to database with upsert logic"""
    try:
        # Get database session
        db = get_sync_db()
        
        for item in data:
            # Check if student exists
            student_query = text("SELECT * FROM students WHERE student_id = :student_id")
            student = db.execute(student_query, {"student_id": item['student_id']}).fetchone()
            
            # Create student if not exists
            if not student:
                insert_student = text(
                    "INSERT INTO students (student_id, created_at, updated_at) "
                    "VALUES (:student_id, :created_at, :updated_at)"
                )
                db.execute(insert_student, {
                    "student_id": item['student_id'],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            
            # Check if demographics already exists for this student
            demographics_query = text("SELECT id FROM demographics WHERE student_id = :student_id")
            existing_demo = db.execute(demographics_query, {"student_id": item['student_id']}).fetchone()
            
            if existing_demo:
                # Update existing demographics
                update_demographics = text(
                    "UPDATE demographics SET "
                    "demographic_type = :demographic_type, "
                    "current_grade = :current_grade, "
                    "attendance_rate = :attendance_rate, "
                    "updated_at = :updated_at "
                    "WHERE student_id = :student_id"
                )
                db.execute(update_demographics, {
                    "student_id": item['student_id'],
                    "demographic_type": item['demographic_type'],
                    "current_grade": item['current_grade'],
                    "attendance_rate": item['attendance_rate'],
                    "updated_at": datetime.utcnow()
                })
            else:
                # Insert new demographics
                insert_demographics = text(
                    "INSERT INTO demographics "
                    "(student_id, demographic_type, current_grade, attendance_rate, created_at, updated_at) "
                    "VALUES "
                    "(:student_id, :demographic_type, :current_grade, :attendance_rate, :created_at, :updated_at)"
                )
                db.execute(insert_demographics, {
                    "student_id": item['student_id'],
                    "demographic_type": item['demographic_type'],
                    "current_grade": item['current_grade'],
                    "attendance_rate": item['attendance_rate'],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
        
        db.commit()
        db.close()
        logger.info(f"Saved {len(data)} demographics records to database (with upsert logic)")
    except Exception as e:
        logger.error(f"Error saving demographics data: {e}")
        raise

def add_survey_data_to_chroma(data: List[Dict[str, Any]]):
    """Add survey data to ChromaDB"""
    try:
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # Add data to ChromaDB (handle async call)
        import asyncio
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, chroma_manager.add_survey_data(data))
                future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            asyncio.run(chroma_manager.add_survey_data(data))
        
        logger.info(f"Added {len(data)} survey records to ChromaDB")
    except Exception as e:
        logger.error(f"Error adding survey data to ChromaDB: {e}")
        raise

def add_demographics_data_to_chroma(data: List[Dict[str, Any]]):
    """Add demographics data to ChromaDB"""
    try:
        # Get ChromaDB manager
        chroma_manager = get_chroma_manager()
        
        # Add data to ChromaDB (handle async call)
        import asyncio
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, chroma_manager.add_student_data(data))
                future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            asyncio.run(chroma_manager.add_student_data(data))
        
        logger.info(f"Added {len(data)} demographics records to ChromaDB")
    except Exception as e:
        logger.error(f"Error adding demographics data to ChromaDB: {e}")
        raise

@celery_app.task
def perform_comprehensive_analysis(student_id: str):
    """Perform comprehensive analysis for a student"""
    try:
        logger.info(f"Performing comprehensive analysis for student {student_id}")
        
        # Get database session
        db = get_sync_db()
        
        # Get student data
        student_query = text("SELECT * FROM students WHERE student_id = :student_id")
        student = db.execute(student_query, {"student_id": student_id}).fetchone()
        
        if not student:
            db.close()
            raise ValueError(f"Student with ID {student_id} not found")
        
        # Get demographics data
        demographics_query = text("SELECT * FROM demographics WHERE student_id = :student_id")
        demographics = db.execute(demographics_query, {"student_id": student_id}).fetchall()
        
        # Get survey data
        survey_query = text("SELECT * FROM surveys WHERE student_id = :student_id ORDER BY timestamp DESC")
        surveys = db.execute(survey_query, {"student_id": student_id}).fetchall()
        
        db.close()
        
        # Prepare data for analysis
        demographic_data = [
            {
                "demographic_type": d.demographic_type,
                "current_grade": d.current_grade,
                "attendance_rate": d.attendance_rate
            }
            for d in demographics
        ]
        
        survey_data = [
            {
                "timestamp": s.timestamp,
                "nps_score": s.nps_score,
                "course_id": s.course_id,
                "week_number": s.week_number,
                "aspect_1_score": s.aspect_1_score,
                "aspect_2_score": s.aspect_2_score,
                "aspect_3_score": s.aspect_3_score,
                "comments": s.comments
            }
            for s in surveys
        ]
        
        # Calculate aspect scores
        aspect_scores = calculate_aspect_scores(survey_data)
        
        # Perform sentiment analysis
        sentiment_analysis = perform_sentiment_analysis(survey_data)
        
        # Generate insights
        insights = generate_insights(
            student_id,
            demographic_data,
            aspect_scores,
            sentiment_analysis
        )
        
        logger.info(f"Comprehensive analysis for student {student_id} completed successfully")
        
        return insights
    except Exception as e:
        logger.error(f"Error performing comprehensive analysis: {e}")
        raise

def calculate_aspect_scores(survey_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aspect scores from survey data"""
    try:
        # Initialize scores
        aspect_1_total = 0
        aspect_2_total = 0
        aspect_3_total = 0
        count = 0
        
        # Calculate average scores
        for survey in survey_data:
            aspect_1_total += survey["aspect_1_score"]
            aspect_2_total += survey["aspect_2_score"]
            aspect_3_total += survey["aspect_3_score"]
            count += 1
        
        # Calculate averages
        aspect_1_avg = aspect_1_total / count if count > 0 else 0
        aspect_2_avg = aspect_2_total / count if count > 0 else 0
        aspect_3_avg = aspect_3_total / count if count > 0 else 0
        
        # Calculate overall score
        overall_avg = (aspect_1_avg + aspect_2_avg + aspect_3_avg) / 3
        
        return {
            "aspect_1_avg": aspect_1_avg,
            "aspect_2_avg": aspect_2_avg,
            "aspect_3_avg": aspect_3_avg,
            "overall_avg": overall_avg
        }
    except Exception as e:
        logger.error(f"Error calculating aspect scores: {e}")
        raise

def perform_sentiment_analysis(survey_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform sentiment analysis on survey comments"""
    try:
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Combine comments
        comments = "\n\n".join([survey["comments"] for survey in survey_data if survey["comments"]])
        
        if not comments:
            return {
                "sentiment": "neutral",
                "positive_aspects": [],
                "negative_aspects": [],
                "keywords": []
            }
        
        # Create prompt
        prompt = f"""
        Perform sentiment analysis on the following student feedback comments:
        
        {comments}
        
        Provide the analysis as a JSON object with the following structure:
        {{
            "sentiment": "positive", "negative", or "neutral",
            "positive_aspects": [list of positive aspects mentioned],
            "negative_aspects": [list of negative aspects mentioned],
            "keywords": [list of important keywords]
        }}
        
        Return ONLY the JSON object, nothing else.
        """
        
        # Generate analysis
        analysis_text = llm_manager.generate_response(
            prompt=prompt,
            preferred_provider=LLMProvider.GEMINI
        )
        
        # Parse analysis
        analysis = json.loads(analysis_text)
        
        return analysis
    except Exception as e:
        logger.error(f"Error performing sentiment analysis: {e}")
        # Return default analysis
        return {
            "sentiment": "neutral",
            "positive_aspects": [],
            "negative_aspects": [],
            "keywords": []
        }

def generate_insights(
    student_id: str,
    demographic_data: List[Dict[str, Any]],
    aspect_scores: Dict[str, Any],
    sentiment_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate insights from analysis data"""
    try:
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Create prompt
        prompt = f"""
        Generate insights and recommendations for a student based on the following data:
        
        Student ID: {student_id}
        
        Demographic Data:
        {json.dumps(demographic_data, indent=2)}
        
        Aspect Scores:
        {json.dumps(aspect_scores, indent=2)}
        
        Sentiment Analysis:
        {json.dumps(sentiment_analysis, indent=2)}
        
        Provide the insights as a JSON object with the following structure:
        {{
            "summary": "Brief summary of the student's situation",
            "strengths": [list of student's strengths],
            "areas_for_improvement": [list of areas where the student can improve],
            "recommendations": [list of specific recommendations],
            "risk_assessment": {{"level": "high", "medium", or "low", "factors": [risk factors]}},
            "action_items": [list of specific actions to take]
        }}
        
        Return ONLY the JSON object, nothing else.
        """
        
        # Generate insights
        insights_text = llm_manager.generate_response(
            prompt=prompt,
            preferred_provider=LLMProvider.GEMINI
        )
        
        # Parse insights
        insights = json.loads(insights_text)
        
        return insights
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        # Return default insights
        return {
            "summary": f"Unable to generate insights for student {student_id}",
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": [],
            "risk_assessment": {"level": "medium", "factors": ["Insufficient data"]},
            "action_items": ["Collect more data for this student"]
        }