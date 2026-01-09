import json
import os
import time
import asyncio
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession, MemorySession
from telethon.errors import SessionPasswordNeededError, AuthKeyError
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
            {"$set": {"session_data": data, "last_update": datetime.now(), "is_active": True}},
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
        config.API_HASH,
        device_model="Alfread UserBot",
        system_version="4.16.30-vxCUSTOM",
        app_version="1.0.0",
        lang_code="en",
        system_lang_code="en-US"
    )
    return client

# Fungsi untuk menyimpan session ke MongoDB
def save_session_to_mongo(user_id, session_string, auto_connect=False):
    """Menyimpan session string ke MongoDB"""
    session_data = {
        "user_id": str(user_id),
        "session_string": session_string,
        "created_at": datetime.now(),
        "last_used": datetime.now(),
        "auto_connect": auto_connect,  # Flag untuk auto-connect
        "is_active": True
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

# Fungsi untuk mendapatkan semua session yang aktif
def get_all_active_sessions():
    """Mendapatkan semua session yang aktif dari MongoDB"""
    try:
        sessions = sessions_collection.find({"is_active": True})
        return list(sessions)
    except:
        return []

# Fungsi untuk mendapatkan session user tertentu
def get_user_session(user_id):
    """Mendapatkan session user dari MongoDB"""
    try:
        return sessions_collection.find_one({"user_id": str(user_id), "is_active": True})
    except:
        return None

# Fungsi untuk mengupdate status koneksi
def update_session_status(user_id, is_connected):
    """Update status koneksi session di MongoDB"""
    try:
        sessions_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"is_connected": is_connected, "last_checked": datetime.now()}}
        )
        return True
    except:
        return False

# Fungsi untuk auto-restore koneksi saat restart
async def auto_restore_connections(bot):
    """Auto-restore semua koneksi yang aktif saat restart"""
    print("🔄 Memulai auto-restore koneksi...")
    
    active_sessions_data = get_all_active_sessions()
    restored_count = 0
    
    for session_data in active_sessions_data:
        user_id = int(session_data["user_id"])
        
        # Skip jika user adalah bot sendiri
        if user_id == bot.me.id:
            continue
            
        # Skip jika session tidak memiliki string
        if "session_string" not in session_data:
            continue
        
        # Cek apakah user ingin auto-connect
        if not session_data.get("auto_connect", False):
            continue
            
        try:
            print(f"🔄 Mencoba restore koneksi untuk user {user_id}...")
            
            # Buat client dari session string
            client = create_userbot_client(user_id, session_data["session_string"])
            
            # Coba connect
            await client.connect()
            
            # Verifikasi koneksi
            if await client.is_user_authorized():
                # Simpan ke active sessions
                active_sessions[user_id] = client
                
                # Load plugins untuk client ini
                from plugins.loader import load_plugins_for_client
                await load_plugins_for_client(client, user_id)
                
                # Tambahkan ping handler
                from plugins.ping import add_ping_handler_to_client
                await add_ping_handler_to_client(client, user_id)
                
                # Update status di MongoDB
                update_session_status(user_id, True)
                
                print(f"✅ Berhasil restore koneksi untuk user {user_id}")
                restored_count += 1
                
                # Coba kirim notifikasi ke owner
                try:
                    me = await client.get_me()
                    await bot.send_message(
                        config.OWNER_ID,
                        f"🔄 **Auto-reconnect Berhasil**\n\n"
                        f"✅ UserBot berhasil di-restore otomatis\n"
                        f"👤 User: {me.first_name}\n"
                        f"📱 ID: {user_id}\n"
                        f"⏰ Waktu: {datetime.now().strftime('%H:%M:%S')}"
                    )
                except:
                    pass
                    
            else:
                print(f"❌ Session tidak valid untuk user {user_id}")
                # Mark session as inactive
                sessions_collection.update_one(
                    {"user_id": str(user_id)},
                    {"$set": {"is_active": False}}
                )
                
        except AuthKeyError:
            print(f"❌ Session expired untuk user {user_id}")
            # Mark session as inactive
            sessions_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {"is_active": False}}
            )
        except Exception as e:
            print(f"❌ Error restoring connection untuk user {user_id}: {e}")
    
    print(f"✅ Auto-restore selesai: {restored_count} koneksi berhasil di-restore")
    return restored_count

# Export functions
__all__ = [
    'create_userbot_client',
    'save_session_to_mongo',
    'delete_session_from_mongo',
    'get_all_active_sessions',
    'get_user_session',
    'update_session_status',
    'auto_restore_connections',
    'pending_verifications',
    'active_sessions',
    'login_attempts',
    'sessions_collection'
]