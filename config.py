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
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan di environment variables")
if not API_ID:
    raise ValueError("API_ID tidak ditemukan di environment variables")
if not API_HASH:
    raise ValueError("API_HASH tidak ditemukan di environment variables")
if not OWNER_ID:
    raise ValueError("OWNER_ID tidak ditemukan di environment variables")

print(f"✅ Config loaded: Bot Token: {'*' * 10}{BOT_TOKEN[-5:] if BOT_TOKEN else ''}")
print(f"✅ API ID: {API_ID}")
print(f"✅ Owner ID: {OWNER_ID}")