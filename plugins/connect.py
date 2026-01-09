import json
import os
import time
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession, MemorySession
from telethon.errors import SessionPasswordNeededError
from pymongo import MongoClient
import config
import pickle

# MongoDB Session Storage
class MongoSession(MemorySession):
    def __init__(self, collection, session_name):
        super().__init__()
        self.collection = collection
        self.session_name = session_name
        self.load_session()

    def load_session(self):
        data = self.collection.find_one({"user_id": self.session_name})
        if data and "session_data" in data:
            try:
                self._dc_id, self._server_address, self._port, self._auth_key = pickle.loads(data["session_data"])
            except:
                pass

    def save(self):
        data = pickle.dumps((self._dc_id, self._server_address, self._port, self._auth_key))
        self.collection.update_one(
            {"user_id": self.session_name},
            {"$set": {"session_data": data, "last_update": datetime.now()}},
            upsert=True
        )

    def delete(self):
        self.collection.delete_one({"user_id": self.session_name})

# Setup MongoDB connection
mongo_client = MongoClient(config.MONGO_URI)
db = mongo_client[config.SESSION_NAME]
sessions_collection = db["sessions"]

# Global dictionaries untuk menyimpan data
pending_verifications = {}
active_sessions = {}
login_attempts = {}

# Fungsi untuk membuat userbot client
def create_userbot_client(user_id, session_string=None):
    """Membuat TelegramClient untuk userbot"""
    if session_string:
        # Gunakan session string yang disimpan
        session = StringSession(session_string)
    else:
        # Buat session baru dengan MongoDB
        session = MongoSession(sessions_collection, str(user_id))
    
    client = TelegramClient(
        session,
        config.API_ID,
        config.API_HASH
    )
    return client

# Fungsi untuk menyimpan session ke MongoDB
def save_session_to_mongo(user_id, session_string):
    """Menyimpan session string ke MongoDB"""
    session_data = {
        "user_id": str(user_id),
        "session_string": session_string,
        "created_at": datetime.now(),
        "last_used": datetime.now()
    }
    sessions_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": session_data},
        upsert=True
    )

# Fungsi untuk menghapus session dari MongoDB
def delete_session_from_mongo(user_id):
    """Menghapus session dari MongoDB"""
    sessions_collection.delete_one({"user_id": str(user_id)})

# Export hanya MongoDB utilities
__all__ = [
    'create_userbot_client',
    'save_session_to_mongo', 
    'delete_session_from_mongo',
    'pending_verifications',
    'active_sessions',
    'login_attempts',
    'sessions_collection'
]