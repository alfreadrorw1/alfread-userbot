"""
MongoDB Connection Handler untuk Alfread UserBot
"""

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
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
            except Exception as e:
                logger.error(f"❌ Unexpected MongoDB error: {e}")
                raise
        
        return cls._client
    
    @classmethod
    def get_database(cls, db_name="alfread_userbot"):
        """Dapatkan database instance"""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[db_name]
            
            # Buat indeks untuk koleksi user_sessions
            try:
                cls._db.user_sessions.create_index("user_id", unique=True)
                cls._db.user_sessions.create_index("connected_at")
                logger.debug("✅ MongoDB indexes created")
            except Exception as e:
                logger.warning(f"⚠️ Could not create indexes: {e}")
        
        return cls._db
    
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

async def register_plugin(client):
    """Register plugin MongoDB - WAJIB ADA fungsi ini!"""
    try:
        # Test connection saat startup
        MongoDB.get_client()
        logger.info("✅ MongoDB plugin initialized")
    except Exception as e:
        logger.error(f"❌ MongoDB plugin failed: {e}")