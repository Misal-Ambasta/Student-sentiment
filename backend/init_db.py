import os
import sys
from loguru import logger

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models
from database import Base, engine, get_db

def init_db():
    """Initialize the database by creating all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Verify tables were created
        db = next(get_db())
        result = db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in result]
        logger.info(f"Tables in database: {tables}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    # Set up logging
    logger.add("logs/init_db.log", rotation="10 MB", level="INFO")
    
    # Initialize database
    success = init_db()
    
    if success:
        print("Database initialized successfully")
        sys.exit(0)
    else:
        print("Failed to initialize database")
        sys.exit(1)