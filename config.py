import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
SESSION_NAME = os.getenv("SESSION_NAME", "alfread")

# Validation
if not all([BOT_TOKEN, API_ID, API_HASH, OWNER_ID]):
    raise ValueError("Please set all required environment variables in .env file")