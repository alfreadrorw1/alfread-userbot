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
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_alfread")

# Owner ID
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# Validate required config
if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH must be set in .env file")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")