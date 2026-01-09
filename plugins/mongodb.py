"""
MongoDB Connection Handler untuk Alfread UserBot
Menggunakan PyMongo dengan async support
"""

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from config import Config

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB Connection Manager"""
    
    _client = None
    _db = None
    
    @classmethod
    def get_client(cls):
        """Dapatkan MongoDB client (singleton)"""
        if cls._client is None:
            try:
                logger.info("🔗 Connecting to MongoDB Atlas...")
                cls._client = MongoClient(
                    Config.MONGO_URI,
                    maxPoolSize=50,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    retryWrites=True
                )
                
                # Test connection
                cls._client.admin.command('ping')
                logger.info("✅ MongoDB Connected successfully!")
                
            except ConnectionFailure as e:
                logger.error(f"❌ MongoDB Connection failed: {e}")
                raise
            except ConfigurationError as e:
                logger.error(f"❌ MongoDB Configuration error: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Unexpected MongoDB error: {e}")
                raise
        
        return cls._client
    
    @classmethod
    def get_database(cls, db_name="alfread_bot"):
        """Dapatkan database instance"""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[db_name]
        
        return cls._db
    
    @classmethod
    def get_collection(cls, collection_name):
        """Dapatkan collection instance"""
        db = cls.get_database()
        return db[collection_name]
    
    @classmethod
    def close(cls):
        """Tutup koneksi MongoDB"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("👋 MongoDB Connection closed")

# Global database instance
db = MongoDB.get_database()

# Helper functions
async def save_user_session(user_id, session_data):
    """Simpan session user ke MongoDB"""
    try:
        sessions = MongoDB.get_collection("user_sessions")
        result = await sessions.update_one(
            {"user_id": user_id},
            {"$set": {
                "session_data": session_data,
                "updated_at": "datetime.now()"
            }},
            upsert=True
        )
        return result.acknowledged
    except Exception as e:
        logger.error(f"Error saving session: {e}")
        return False

async def get_user_session(user_id):
    """Dapatkan session user dari MongoDB"""
    try:
        sessions = MongoDB.get_collection("user_sessions")
        session = await sessions.find_one({"user_id": user_id})
        return session.get("session_data") if session else None
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return None

async def register_plugin(client):
    """Register plugin MongoDB"""
    # Test connection saat startup
    try:
        MongoDB.get_client()
        logger.info("✅ MongoDB plugin initialized")
    except Exception as e:
        logger.error(f"❌ MongoDB plugin failed: {e}")