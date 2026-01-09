import os
from dotenv import load_dotenv

load_dotenv()

# Telethon config
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

# Bot config
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# MongoDB config
MONGO_URI = os.getenv("MONGO_URI", "")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_sessions")

# Owner ID
OWNER_ID = int(os.getenv("OWNER_ID", 0))