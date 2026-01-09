import asyncio
from pymongo import MongoClient
from telethon import TelegramClient
from telethon.sessions import MemorySession
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, SESSION_NAME, MODE

class MongoStorage:
    def __init__(self, mongo_uri, collection_name="telethon_sessions"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_database()
        self.collection = self.db[collection_name]
    
    def __getitem__(self, key):
        doc = self.collection.find_one({"session": SESSION_NAME})
        return doc.get(key, b"") if doc else b""
    
    def __setitem__(self, key, value):
        self.collection.update_one(
            {"session": SESSION_NAME},
            {"$set": {key: value}},
            upsert=True
        )
    
    def __delitem__(self, key):
        self.collection.update_one(
            {"session": SESSION_NAME},
            {"$unset": {key: ""}}
        )
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

# Global userbot client
userbot_client = None

async def get_or_create_client():
    global userbot_client
    
    if MODE == "bot":
        # Bot mode - create simple bot client
        client = TelegramClient(
            MemorySession(),
            api_id=API_ID,
            api_hash=API_HASH
        ).start(bot_token=BOT_TOKEN)
        client.storage = MongoStorage(MONGO_URI)
        return client
    
    elif MODE == "userbot":
        # Userbot mode - try to load existing session
        storage = MongoStorage(MONGO_URI)
        client = TelegramClient(
            MemorySession(),
            api_id=API_ID,
            api_hash=API_HASH
        )
        client.storage = storage
        
        try:
            # Check if session exists in MongoDB
            session_data = storage.collection.find_one({"session": SESSION_NAME})
            if session_data and b"main" in session_data:
                await client.start()
                userbot_client = client
                print("Userbot session loaded from MongoDB")
                return client
            else:
                print("No session found in MongoDB, waiting for login via bot...")
                # Return bot client for login interface
                return await create_bot_client()
        except Exception as e:
            print(f"Error loading session: {e}")
            return await create_bot_client()
    
    else:
        raise ValueError(f"Invalid MODE: {MODE}")

async def create_bot_client():
    """Create bot client for login interface"""
    client = TelegramClient(
        MemorySession(),
        api_id=API_ID,
        api_hash=API_HASH
    ).start(bot_token=BOT_TOKEN)
    client.storage = MongoStorage(MONGO_URI)
    return client

async def login_userbot_via_bot(phone, code=None, password=None, mongo_client=None):
    """Login userbot using provided credentials"""
    global userbot_client
    
    storage = MongoStorage(MONGO_URI)
    client = TelegramClient(
        MemorySession(),
        api_id=API_ID,
        api_hash=API_HASH
    )
    client.storage = storage
    
    try:
        if not client.is_connected():
            await client.connect()
        
        if code and not password:
            # First step: send code request
            await client.send_code_request(phone)
            return "code_sent"
        
        elif code and password:
            # Second step: sign in with code
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                # Third step: sign in with password
                await client.sign_in(password=password)
        
        elif code:
            # Sign in with code only
            await client.sign_in(phone, code)
        
        # Store session in MongoDB
        await client.start()
        userbot_client = client
        
        # Save session to MongoDB
        session_data = client.session.save()
        storage.collection.update_one(
            {"session": SESSION_NAME},
            {"$set": {"auth_key": session_data}},
            upsert=True
        )
        
        return "success"
    
    except Exception as e:
        return f"error: {str(e)}"

# Create client instance
client = asyncio.run(get_or_create_client())