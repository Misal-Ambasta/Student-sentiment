# RAG-Student-sense Backend

This is the backend for the RAG-Student-sense application, which provides enhanced RAG (Retrieval-Augmented Generation) capabilities for analyzing student survey data.

## Features

- FastAPI backend with async support
- PostgreSQL database for structured data storage
- ChromaDB for vector embeddings and semantic search
- Multiple LLM providers (Gemini, Groq, OpenAI) with fallback mechanism
- Celery for background task processing
- WebSockets for real-time updates
- Enhanced file processing with intelligent header mapping
- RAG-based chat interface for student data analysis

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis (for Celery)
- ChromaDB

### Installation

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate  # On Windows
# OR
source .venv/bin/activate  # On Unix/Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env` file:

```
# Database
POSTGRES_URL=postgresql+asyncpg://username:password@localhost:5432/student_sense

# Vector Store
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# LLM Providers
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

4. Initialize the database:

```bash
python init_db.py
```

## Running the Application

1. Start the FastAPI server:

```bash
python run.py
```

2. Start the Celery worker:

```bash
celery -A celery_worker worker --loglevel=info
```

## API Endpoints

### File Upload

- `POST /api/upload/file`: Upload a file for processing
- `GET /api/upload/status/{file_id}`: Check file processing status
- `GET /api/upload/files`: List all uploaded files
- `DELETE /api/upload/file/{file_id}`: Delete a file

### Chat

- `POST /api/chat/query`: Process a chat query
- `POST /api/chat/stream`: Stream a chat response
- `POST /api/chat/classify`: Classify a query
- `GET /api/chat/suggestions`: Get query suggestions
- `GET /api/chat/sessions`: List all chat sessions
- `GET /api/chat/session/{session_id}`: Get a specific chat session
- `DELETE /api/chat/session/{session_id}`: Delete a chat session

### WebSockets

- `WebSocket /api/ws`: Connect to WebSocket for real-time updates

## Architecture

- `main.py`: FastAPI application entry point
- `database.py`: SQLAlchemy models and database connection
- `vector_store.py`: ChromaDB integration for vector embeddings
- `llm_integration.py`: LLM providers integration with fallback mechanism
- `routers/`: API endpoints
  - `upload.py`: File upload endpoints
  - `chat.py`: Chat endpoints
  - `websocket.py`: WebSocket endpoints
- `celery_tasks/`: Background tasks
  - `data_processing.py`: File processing tasks

## License

MIT