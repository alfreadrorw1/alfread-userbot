import os
from dotenv import load_dotenv

load_dotenv()

# Telethon config
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")

# Bot config
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# MongoDB config
MONGO_URI = os.getenv("MONGO_URI", "")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_sessions")

# Owner ID
OWNER_ID = os.getenv("OWNER_ID", "")

# Validate required config
def validate_config():
    errors = []
    
    if not API_ID:
        errors.append("API_ID must be set in .env file")
    else:
        try:
            API_ID = int(API_ID)
        except ValueError:
            errors.append("API_ID must be a number")
    
    if not API_HASH:
        errors.append("API_HASH must be set in .env file")
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN must be set in .env file")
    
    if not MONGO_URI:
        errors.append("MONGO_URI must be set in .env file")
    
    if not OWNER_ID:
        errors.append("OWNER_ID must be set in .env file")
    else:
        try:
            OWNER_ID = int(OWNER_ID)
        except ValueError:
            errors.append("OWNER_ID must be a number")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        raise ValueError("Invalid configuration. Please check your .env file")
    
    print("✅ Configuration validated successfully")

# Panggil validasi saat module diimport
try:
    validate_config()
except Exception as e:
    print(f"❌ Configuration error: {e}")