import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import managers and routers after environment variables are loaded
from database import init_db, get_db
from vector_store import get_chroma_manager
from llm_integration import get_llm_manager
from routers import upload, chat, websocket, database

# Configure logging
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    backtrace=True,
    diagnose=True,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Initialize ChromaDB
    logger.info("Initializing ChromaDB...")
    chroma_manager = get_chroma_manager()
    
    # Initialize LLM Manager
    logger.info("Initializing LLM Manager...")
    llm_manager = get_llm_manager()
    
    # Create upload directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")

# Create FastAPI app
app = FastAPI(
    title="RAG-Student-sense API",
    description="API for RAG-powered historical intelligence platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )

# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])
app.include_router(database.router, tags=["database"])

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "RAG-Student-sense API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)