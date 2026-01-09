import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import config

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB connection manager"""
    
    _client: Optional[AsyncIOMotorClient] = None
    _db = None
    
    @classmethod
    async def connect(cls):
        """Establish MongoDB connection"""
        try:
            if cls._client is None:
                logger.info("🔄 Connecting to MongoDB...")
                cls._client = AsyncIOMotorClient(
                    config.mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000
                )
                
                # Test connection
                await cls._client.admin.command('ping')
                cls._db = cls._client[config.db_name]
                
                logger.info("✅ MongoDB connected successfully")
                return True
                
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            cls._client = None
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected MongoDB error: {e}")
            return False
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            logger.info("🔌 MongoDB disconnected")
    
    @classmethod
    def get_db(cls):
        """Get database instance"""
        if cls._db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls._db
    
    @classmethod
    async def get_collection(cls, name: str):
        """Get collection from database"""
        db = cls.get_db()
        return db[name]
    
    @classmethod
    async def is_connected(cls) -> bool:
        """Check if MongoDB is connected"""
        try:
            if cls._client:
                await cls._client.admin.command('ping')
                return True
        except:
            pass
        return False

# Global MongoDB instance
mongodb = MongoDB()