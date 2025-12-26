"""
Configuration Settings
======================
Central configuration file for all application settings.
Contains database credentials, API settings, and environment variables.
"""

import os
from typing import Optional

class Settings:
    """Application settings and configuration."""
    
    # Application Settings
    APP_NAME: str = "NSE Broker Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server Settings
    HOST: str = "192.168.119.183"
    PORT: int = 8755
    
    # MongoDB Settings
    MONGO_URI: str = "mongodb://sa:963852@192.168.102.120:27017/"
    MONGO_DB_NAME: str = "WEB_SCRAPING"
    MONGO_COLLECTION_LIST: str = "Broker_list_details"
    MONGO_CONNECTION_TIMEOUT: int = 5000  # milliseconds
    
    # API Settings
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://192.168.119.183:3000",
        "http://192.168.119.183:5500",
        "*"  # Allow all origins in development
    ]
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Cache Settings (for future implementation)
    CACHE_TTL: int = 300  # seconds
    
    @classmethod
    def get_mongo_uri(cls) -> str:
        """Get MongoDB connection URI."""
        return cls.MONGO_URI
    
    @classmethod
    def get_database_name(cls) -> str:
        """Get database name."""
        return cls.MONGO_DB_NAME
    
    @classmethod
    def get_collection_name(cls) -> str:
        """Get main collection name."""
        return cls.MONGO_COLLECTION_LIST


# Create settings instance
settings = Settings()
