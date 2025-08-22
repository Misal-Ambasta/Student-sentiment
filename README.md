# RAG Student Sense

A comprehensive AI-powered student analytics platform that leverages Retrieval-Augmented Generation (RAG) to provide intelligent insights into student performance, engagement, and feedback analysis.

## 🚀 Features

### Core Functionality
- **Intelligent Chat Interface**: AI-powered conversational interface for querying student data
- **Automated Data Processing**: Upload and process student survey data and demographics
- **Multi-Modal Analysis**: Support for various analysis types including:
  - Individual student analysis
  - Weekly performance reports
  - Demographic segmentation analysis
  - Course aspect analysis
- **Real-time WebSocket Communication**: Live updates for file processing and analysis completion
- **Vector Database Integration**: ChromaDB for efficient similarity search and retrieval

### Analysis Types
- **Individual Analysis**: Detailed insights for specific students
- **Weekly Reports**: Temporal analysis of student performance trends
- **Segmentation Analysis**: Demographic-based student grouping and analysis
- **Aspect Analysis**: Course-specific feedback and rating analysis

### Data Management
- **Multi-format Support**: CSV, XLS, XLSX file uploads
- **Automated Data Mapping**: Intelligent header mapping using LLM
- **PostgreSQL Database**: Robust data storage with async operations
- **Background Processing**: Celery-based asynchronous task processing for file processing, data analysis, and embedding generation
- **Task Queue Management**: Redis as message broker for reliable task distribution and result storage

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Store**: ChromaDB for embeddings and similarity search
- **LLM Integration**: Multi-provider support (Google Gemini, Groq, OpenAI)
- **Background Tasks**: Celery with Redis for asynchronous file processing, data analysis, and embedding generation
- **Message Broker**: Redis for task queue management and caching
- **WebSocket**: Real-time communication

### Frontend (React + TypeScript)
- **Framework**: React 19 with TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Charts**: Chart.js and Recharts
- **Build Tool**: Vite
- **UI Components**: Custom components with Lucide React icons

## 🔄 Background Processing with Celery & Redis

### Why Celery and Redis?

The RAG Student Sense application uses **Celery** with **Redis** as the message broker to handle computationally intensive and time-consuming tasks asynchronously. This architecture ensures that the main FastAPI application remains responsive while processing large datasets and generating embeddings.

### When are Celery Tasks Used?

1. **File Upload Processing** (`/api/upload/both-files`, `/api/upload/file`):
   - Parse and validate uploaded CSV/Excel files
   - Transform data according to intelligent header mapping
   - Store processed data in PostgreSQL database
   - Generate embeddings for survey comments and student data
   - Add embeddings to ChromaDB vector store

2. **Data Analysis Tasks**:
   - Generate comprehensive student analysis reports
   - Process demographic segmentation analysis
   - Create weekly performance reports
   - Calculate NPS trends and risk assessments

3. **Embedding Generation**:
   - Convert text data (comments, feedback) into vector embeddings
   - Update ChromaDB collections with new embeddings
   - Maintain vector store consistency

### Redis Configuration

Redis serves multiple purposes in the application:
- **Message Broker**: Queues tasks for Celery workers
- **Result Backend**: Stores task results and status
- **Caching**: Improves performance for frequently accessed data
- **Session Storage**: Maintains task progress and status information

### Real-time Updates

Celery tasks integrate with WebSocket connections to provide real-time progress updates:
- File processing progress notifications
- Analysis completion alerts
- Error handling and status updates
- Background task monitoring

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 16 or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6 or higher (required for Celery task queue and caching)
- **API Keys**: Google AI, Groq, and/or OpenAI API keys

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd RAG-Student-sense
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv .venv

# On Windows
source .venv/Scripts/activate

# On macOS/Linux
source .venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure your `.env` file with the following variables:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
NEON_DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here

# ChromaDB Configuration
CHROMA_CLOUD_HOST=https://api.chromadb.com
CHROMA_TENANT=your_chroma_tenant_id
CHROMA_DATABASE=your_database_name
CHROMADB_API_KEY=your_chromadb_api_key

# RAG Collections
RAG_COLLECTION_HISTORICAL=historical_knowledge
RAG_COLLECTION_INTERVENTIONS=interventions_knowledge
RAG_COLLECTION_COMMENTS=weekly_comments_vectorized

# LLM API Keys
GROQ_API_KEY=your_groq_api_key_here
NOMIC_API_KEY=your_nomic_api_key_here

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0
```

#### Database Setup
```bash
# Initialize the database
python init_db.py

# Load sample data (optional)
python load_sample_data.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Redis Setup (for Celery)

Install and start Redis server:

**On Windows:**
- Download Redis from the official website or use WSL
- Start Redis server

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

## 🚀 Running the Application

### Development Mode

#### 1. Start Redis (if not already running)
```bash
redis-server
```

#### 2. Start Celery Worker (Backend)
```bash
cd backend
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # macOS/Linux
celery -A celery_worker worker --loglevel=info
```

#### 3. Start Backend Server
```bash
cd backend
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # macOS/Linux
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Start Frontend Development Server
```bash
cd frontend
npm run dev
```

### Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📊 Usage

### 1. Data Upload
1. Navigate to the Upload page
2. Upload your student survey data (CSV/Excel format)
3. Upload demographics data
4. Wait for processing completion

### 2. Chat Interface
1. Go to the Chat page
2. Ask questions about student data:
   - "Show me individual analysis for student ID 12345"
   - "Generate a weekly report for Course A"
   - "Analyze demographic segments for working professionals"
   - "What are the aspect scores for CSBT course?"

### 3. Dashboard
- View overall system status
- Monitor file processing progress
- Access quick analytics

## 🔧 API Endpoints

### Chat Endpoints
- `POST /api/chat/query` - Process chat queries with auto-classification
- `GET /api/chat/stream` - Stream chat responses
- `WebSocket /api/chat/ws` - Real-time chat communication

### Upload Endpoints
- `POST /api/upload/both-files` - Upload survey and demographics files
- `POST /api/upload/file` - Upload single file
- `GET /api/upload/status/{file_id}` - Check upload status

### Data Endpoints
- `GET /api/data/students` - Retrieve student data
- `GET /api/data/surveys` - Retrieve survey data
- `GET /api/data/demographics` - Retrieve demographics data

## 🧪 Testing

### Backend Tests
```bash
cd backend
source .venv/Scripts/activate
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📁 Project Structure

```
RAG-Student-sense/
├── backend/
│   ├── routers/           # FastAPI route handlers
│   ├── celery_tasks/      # Background task definitions
│   ├── tests/            # Backend tests
│   ├── uploads/          # File upload directory
│   ├── logs/             # Application logs
│   ├── chroma_db/        # ChromaDB storage
│   ├── main.py           # FastAPI application entry point
│   ├── database.py       # Database models and configuration
│   ├── llm_integration.py # LLM and RAG implementation
│   ├── vector_store.py   # ChromaDB integration
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── stores/       # Zustand state management
│   │   ├── lib/          # Utility functions and API
│   │   └── App.tsx       # Main React application
│   ├── public/           # Static assets
│   └── package.json      # Node.js dependencies
├── sample_data_10/       # Sample data files
└── README.md            # This file
```

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` files to version control
- **API Keys**: Store all API keys securely in environment variables
- **Database**: Use strong passwords and enable SSL connections
- **CORS**: Configure CORS settings appropriately for production
- **Input Validation**: All user inputs are validated using Pydantic models

## 🚀 Deployment

### Production Deployment

1. **Backend Deployment**:
   - Use a production WSGI server like Gunicorn
   - Configure environment variables
   - Set up PostgreSQL database
   - Configure Redis for Celery
   - Set up reverse proxy (Nginx)

2. **Frontend Deployment**:
   - Build the production bundle: `npm run build`
   - Serve static files with a web server
   - Configure API endpoints for production

### Docker Deployment (Optional)

Create Docker containers for both backend and frontend services with proper orchestration using Docker Compose.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📝 License

[Add your license information here]

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs` endpoint
- Review the logs in the `backend/logs/` directory

## 🔄 Version History

- **v1.0.0**: Initial release with core RAG functionality
- **v1.1.0**: Added multi-provider LLM support
- **v1.2.0**: Enhanced analysis types and WebSocket integration

---

**Built with ❤️ using FastAPI, React, and modern AI technologies**