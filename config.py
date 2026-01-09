import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
SESSION_NAME = os.getenv("SESSION_NAME", "telegram_session")
MODE = os.getenv("MODE", "bot").lower()
OWNER_ID = int(os.getenv("OWNER_ID", 0))

if not all([API_ID, API_HASH, MONGO_URI, SESSION_NAME, BOT_TOKEN]):
    raise ValueError("Missing required environment variables")