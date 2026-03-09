"""MongoDB connection management."""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    database = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB."""
        if cls.client is None:
            mongo_url = os.getenv("MONGODB_URL", "mongodb://llm_benchmark_user:llm_benchmark_pass@localhost:27017")
            db_name = os.getenv("MONGODB_DB_NAME", "llm_benchmark")
            
            logger.info(f"Connecting to MongoDB at {mongo_url}")
            cls.client = AsyncIOMotorClient(mongo_url)
            cls.database = cls.client[db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {db_name}")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.database = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls):
        """Get the database instance."""
        if cls.database is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls.database
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if database is connected."""
        return cls.database is not None and cls.client is not None

