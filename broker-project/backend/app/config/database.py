"""
Database Configuration
======================
MongoDB connection management and database operations.
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
import logging

from .settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB database manager - Singleton pattern."""
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection."""
        if self._client is None:
            self.connect()
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._client = MongoClient(
                settings.get_mongo_uri(),
                serverSelectionTimeoutMS=settings.MONGO_CONNECTION_TIMEOUT
            )
            # Test connection
            self._client.server_info()
            self._db = self._client[settings.get_database_name()]
            logger.info(f"✅ Connected to MongoDB: {settings.get_database_name()}")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self._client = None
            self._db = None
            return False
    
    def get_database(self) -> Optional[Database]:
        """
        Get database instance.
        
        Returns:
            Database: MongoDB database instance or None
        """
        if self._db is None:
            self.connect()
        return self._db
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """
        Get collection from database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection: MongoDB collection instance or None
        """
        db = self.get_database()
        if db is not None:
            return db[collection_name]
        return None
    
    def get_broker_collection(self) -> Optional[Collection]:
        """
        Get the main broker list collection.
        
        Returns:
            Collection: Broker list collection or None
        """
        return self.get_collection(settings.get_collection_name())
    
    def close(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            logger.info("🔌 MongoDB connection closed")
            self._client = None
            self._db = None
    
    def is_connected(self) -> bool:
        """
        Check if database is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            if self._client:
                self._client.server_info()
                return True
        except Exception:
            pass
        return False


# Create global database manager instance
db_manager = DatabaseManager()


def get_db() -> Optional[Database]:
    """
    Dependency function to get database instance.
    Use this in route handlers.
    
    Returns:
        Database: MongoDB database instance
    """
    return db_manager.get_database()


def get_broker_collection() -> Optional[Collection]:
    """
    Dependency function to get broker collection.
    Use this in controllers.
    
    Returns:
        Collection: Broker collection instance
    """
    return db_manager.get_broker_collection()
