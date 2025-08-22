import os
from typing import AsyncGenerator, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, func, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool
from loguru import logger
from datetime import datetime

# Get database URL from environment variable
DATABASE_URL = os.getenv("NEON_DATABASE_URL", os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/student_sense"))

# Ensure the URL uses the asyncpg driver
if DATABASE_URL and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    logger.info(f"Using database URL with asyncpg driver: {DATABASE_URL}")

# Remove sslmode parameter from URL as asyncpg doesn't support it directly
if "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]
    logger.info(f"Removed SSL parameters from URL for asyncpg compatibility: {DATABASE_URL}")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
    connect_args={"ssl": True},  # Enable SSL for Neon.tech PostgreSQL
)

# Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create base class for models
Base = declarative_base()

# Define models
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    demographics = relationship("Demographics", back_populates="student")
    surveys = relationship("Survey", back_populates="student")

class Demographics(Base):
    __tablename__ = "demographics"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"), index=True)
    demographic_type = Column(String, index=True)
    current_grade = Column(String)
    attendance_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="demographics")

class Survey(Base):
    __tablename__ = "surveys"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"), index=True)
    timestamp = Column(DateTime, index=True)
    nps_score = Column(Integer)
    course_id = Column(String, index=True)
    week_number = Column(Integer)
    aspect_1_score = Column(Integer)
    aspect_2_score = Column(Integer)
    aspect_3_score = Column(Integer)
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="surveys")

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    status = Column(String, index=True)  # 'uploaded', 'processing', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    file_metadata = Column(Text, nullable=True)  # JSON string - renamed from metadata to avoid SQLAlchemy reserved name
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

# Database initialization function
async def init_db():
    try:
        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()