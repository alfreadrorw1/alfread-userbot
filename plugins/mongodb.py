"""
MongoDB Connection Handler untuk Alfread UserBot
"""

import logging
from datetime import datetime
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
    def get_collection(cls, collection_name):
        """Dapatkan collection instance"""
        db = cls.get_database()
        return db[collection_name]
    
    @classmethod
    def save_user_session(cls, user_id, session_string, phone=None):
        """Simpan session user ke MongoDB"""
        try:
            collection = cls.get_collection("user_sessions")
            result = collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "session_string": session_string,
                    "phone": phone,
                    "updated_at": datetime.now(),
                    "connected": True
                }},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    @classmethod
    def get_user_session(cls, user_id):
        """Dapatkan session user dari MongoDB"""
        try:
            collection = cls.get_collection("user_sessions")
            session = collection.find_one({"user_id": user_id})
            return session.get("session_string") if session else None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    @classmethod
    def disconnect_user_session(cls, user_id):
        """Mark session sebagai disconnected"""
        try:
            collection = cls.get_collection("user_sessions")
            result = collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "connected": False,
                    "disconnected_at": datetime.now()
                }}
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error disconnecting session: {e}")
            return False
    
    @classmethod
    def get_active_sessions(cls):
        """Dapatkan semua session yang aktif"""
        try:
            collection = cls.get_collection("user_sessions")
            active = list(collection.find({"connected": True}))
            return active
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
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

# Export helper functions untuk backward compatibility
save_user_session = MongoDB.save_user_session
get_user_session = MongoDB.get_user_session
disconnect_user_session = MongoDB.disconnect_user_session
get_active_sessions = MongoDB.get_active_sessions

async def register_plugin(client):
    """Register plugin MongoDB"""
    try:
        # Test connection saat startup
        MongoDB.get_client()
        logger.info("✅ MongoDB plugin initialized")
    except Exception as e:
        logger.error(f"❌ MongoDB plugin failed: {e}")