import os
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get ChromaDB URL from environment variable
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

# Define collection names
COLLECTION_SURVEY_DATA = "survey_data"
COLLECTION_STUDENT_DATA = "student_data"
COLLECTION_CHAT_HISTORY = "chat_history"

# Embedding model configuration
EMBEDDING_DIMENSION = 768

class MultiModelEmbeddings(Embeddings):
    """Custom embedding class with fallback models"""
    
    def __init__(self):
        self.primary_model = None
        self.fallback_model_1 = None
        self.fallback_model_2 = None
        self.current_model = None
        self._initialize_models()
        logger.info(f"Using embedding model: {self.current_model}")
    
    def _initialize_models(self):
        """Initialize embedding models with fallback strategy"""
        # Initialize primary model (Gemini - 768 dimensions)
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            self.primary_model = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                output_dimensionality=768
            )
            logger.info("Initialized Gemini embeddings as primary model")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini embeddings: {e}")
            self.primary_model = None
            
        # Initialize first fallback: Nomic embeddings
        nomic_api_key = os.getenv('NOMIC_API_KEY')
        if nomic_api_key:
            try:
                from langchain_nomic import NomicEmbeddings
                self.fallback_model_1 = NomicEmbeddings(
                    model="nomic-embed-text-v1.5",
                    nomic_api_key=nomic_api_key,
                    dimensionality=768
                )
                logger.info("Initialized Nomic embeddings as first fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize Nomic embeddings: {e}")
                self.fallback_model_1 = None
        else:
            logger.warning("NOMIC_API_KEY not found, skipping Nomic embeddings")
            self.fallback_model_1 = None
            
        # Initialize second fallback: HuggingFace model (768 dimensions)
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.fallback_model_2 = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info("Initialized HuggingFace embeddings as second fallback")
        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFace embeddings: {e}")
            self.fallback_model_2 = None
            
        # Determine current model
        if self.primary_model:
            self.current_model = "models/gemini-embedding-001"
        elif self.fallback_model_1:
            self.current_model = "nomic-embed-text-v1.5"
        elif self.fallback_model_2:
            self.current_model = "all-mpnet-base-v2"
        else:
            raise ValueError("No embedding models could be initialized")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents using the available model with runtime fallback"""
        # Try primary model first (Gemini with 768 dimensions)
        if self.primary_model:
            try:
                # For Gemini, use output_dimensionality parameter
                if hasattr(self.primary_model, 'model') and 'gemini' in str(self.primary_model.model):
                    return self.primary_model.embed_documents(texts, output_dimensionality=768)
                else:
                    return self.primary_model.embed_documents(texts)
            except Exception as e:
                logger.warning(f"Primary embedding model failed: {e}. Trying fallback models...")
                
        # Try first fallback
        if self.fallback_model_1:
            try:
                return self.fallback_model_1.embed_documents(texts)
            except Exception as e:
                logger.warning(f"First fallback embedding model failed: {e}. Trying second fallback...")
                
        # Try second fallback
        if self.fallback_model_2:
            try:
                return self.fallback_model_2.embed_documents(texts)
            except Exception as e:
                logger.error(f"Second fallback embedding model failed: {e}")
                
        raise ValueError("All embedding models failed")
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query using the available model with runtime fallback"""
        # Try primary model first (Gemini with 768 dimensions)
        if self.primary_model:
            try:
                # For Gemini, use output_dimensionality parameter
                if hasattr(self.primary_model, 'model') and 'gemini' in str(self.primary_model.model):
                    return self.primary_model.embed_query(text, output_dimensionality=768)
                else:
                    return self.primary_model.embed_query(text)
            except Exception as e:
                logger.warning(f"Primary embedding model failed: {e}. Trying fallback models...")
                
        # Try first fallback
        if self.fallback_model_1:
            try:
                return self.fallback_model_1.embed_query(text)
            except Exception as e:
                logger.warning(f"First fallback embedding model failed: {e}. Trying second fallback...")
                
        # Try second fallback
        if self.fallback_model_2:
            try:
                return self.fallback_model_2.embed_query(text)
            except Exception as e:
                logger.error(f"Second fallback embedding model failed: {e}")
                
        raise ValueError("All embedding models failed")

class ChromaManager:
    def __init__(self):
        self.embeddings = MultiModelEmbeddings()
        
        # Initialize collections
        self.survey_db = self._init_collection(COLLECTION_SURVEY_DATA)
        self.student_db = self._init_collection(COLLECTION_STUDENT_DATA)
        self.chat_history_db = self._init_collection(COLLECTION_CHAT_HISTORY)
        
        logger.info("ChromaDB initialized successfully")
    
    def _init_collection(self, collection_name: str) -> Chroma:
        """Initialize a ChromaDB collection"""
        try:
            return Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_DIR
            )
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection {collection_name}: {e}")
            raise
    
    async def add_survey_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Add survey data to ChromaDB"""
        try:
            documents = []
            ids = []
            
            for item in data:
                # Create document content
                content = f"Student ID: {item.get('student_id', 'Unknown')}\n"
                content += f"NPS Score: {item.get('nps_score', 'Unknown')}\n"
                content += f"Course ID: {item.get('course_id', 'Unknown')}\n"
                content += f"Week Number: {item.get('week_number', 'Unknown')}\n"
                content += f"Aspect 1 Score: {item.get('aspect_1_score', 'Unknown')}\n"
                content += f"Aspect 2 Score: {item.get('aspect_2_score', 'Unknown')}\n"
                content += f"Aspect 3 Score: {item.get('aspect_3_score', 'Unknown')}\n"
                content += f"Comments: {item.get('comments', '')}\n"
                
                # Add detailed JSONB course scores if available
                course_a_scores = item.get('course_a_scores', {})
                if course_a_scores and isinstance(course_a_scores, dict):
                    content += f"\nCourse A Detailed Scores:\n"
                    for aspect, score in course_a_scores.items():
                        content += f"  {aspect}: {score}\n"
                
                course_b_scores = item.get('course_b_scores', {})
                if course_b_scores and isinstance(course_b_scores, dict):
                    content += f"\nCourse B Detailed Scores:\n"
                    for aspect, score in course_b_scores.items():
                        content += f"  {aspect}: {score}\n"
                
                csbt_scores = item.get('csbt_scores', {})
                if csbt_scores and isinstance(csbt_scores, dict):
                    content += f"\nCSBT Detailed Scores:\n"
                    for aspect, score in csbt_scores.items():
                        content += f"  {aspect}: {score}\n"
                
                dost_support_scores = item.get('dost_support_scores', {})
                if dost_support_scores and isinstance(dost_support_scores, dict):
                    content += f"\nDost Support Scores:\n"
                    for aspect, score in dost_support_scores.items():
                        content += f"  {aspect}: {score}\n"
                
                product_support_scores = item.get('product_support_scores', {})
                if product_support_scores and isinstance(product_support_scores, dict):
                    content += f"\nProduct Support Scores:\n"
                    for aspect, score in product_support_scores.items():
                        content += f"  {aspect}: {score}\n"
                
                # Create metadata
                metadata = {
                    "student_id": item.get("student_id", ""),
                    "timestamp": str(item.get("timestamp", "")),
                    "nps_score": item.get("nps_score", 0),
                    "course_id": item.get("course_id", ""),
                    "week_number": item.get("week_number", 0),
                    "document_type": "survey"
                }
                
                # Create document
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
                
                # Generate ID
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
            
            # Add documents to ChromaDB
            self.survey_db.add_documents(documents=documents, ids=ids)
            logger.info(f"Added {len(documents)} survey documents to ChromaDB")
            
            return ids
        except Exception as e:
            logger.error(f"Error adding survey data to ChromaDB: {e}")
            raise
    
    async def add_student_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Add student demographic data to ChromaDB"""
        try:
            documents = []
            ids = []
            
            for item in data:
                # Create document content
                content = f"Student ID: {item.get('student_id', 'Unknown')}\n"
                content += f"Demographic Type: {item.get('demographic_type', 'Unknown')}\n"
                content += f"Current Grade: {item.get('current_grade', 'Unknown')}\n"
                content += f"Attendance Rate: {item.get('attendance_rate', 'Unknown')}\n"
                
                # Create metadata
                metadata = {
                    "student_id": item.get("student_id", ""),
                    "demographic_type": item.get("demographic_type", ""),
                    "current_grade": item.get("current_grade", ""),
                    "attendance_rate": item.get("attendance_rate", 0),
                    "document_type": "demographics"
                }
                
                # Create document
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
                
                # Generate ID
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
            
            # Add documents to ChromaDB
            self.student_db.add_documents(documents=documents, ids=ids)
            logger.info(f"Added {len(documents)} student documents to ChromaDB")
            
            return ids
        except Exception as e:
            logger.error(f"Error adding student data to ChromaDB: {e}")
            raise
    
    async def add_chat_history(self, session_id: str, messages: List[Dict[str, Any]]) -> str:
        """Add chat history to ChromaDB"""
        try:
            # Create document content
            content = f"Session ID: {session_id}\n\n"
            
            for msg in messages:
                role = msg.get("role", "unknown")
                content += f"{role.capitalize()}: {msg.get('content', '')}\n\n"
            
            # Create metadata
            metadata = {
                "session_id": session_id,
                "message_count": len(messages),
                "document_type": "chat_history"
            }
            
            # Create document
            doc = Document(page_content=content, metadata=metadata)
            
            # Generate ID
            doc_id = str(uuid.uuid4())
            
            # Add document to ChromaDB
            self.chat_history_db.add_documents(documents=[doc], ids=[doc_id])
            logger.info(f"Added chat history for session {session_id} to ChromaDB")
            
            return doc_id
        except Exception as e:
            logger.error(f"Error adding chat history to ChromaDB: {e}")
            raise
    
    async def search_survey_data(self, query: str, filter_metadata: Optional[Dict[str, Any]] = None, k: int = 5) -> List[Document]:
        """Search survey data in ChromaDB"""
        try:
            results = self.survey_db.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata
            )
            logger.info(f"Found {len(results)} survey documents for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching survey data in ChromaDB: {e}")
            raise
    
    async def search_student_data(self, query: str, filter_metadata: Optional[Dict[str, Any]] = None, k: int = 5) -> List[Document]:
        """Search student data in ChromaDB"""
        try:
            results = self.student_db.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata
            )
            logger.info(f"Found {len(results)} student documents for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching student data in ChromaDB: {e}")
            raise
    
    async def search_chat_history(self, query: str, filter_metadata: Optional[Dict[str, Any]] = None, k: int = 5) -> List[Document]:
        """Search chat history in ChromaDB"""
        try:
            results = self.chat_history_db.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata
            )
            logger.info(f"Found {len(results)} chat history documents for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching chat history in ChromaDB: {e}")
            raise

# Singleton instance
_chroma_manager = None

def get_chroma_manager() -> ChromaManager:
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager