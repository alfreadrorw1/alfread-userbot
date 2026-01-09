"""
Configuration Module for Alfread UserBot
Load environment variables and provide configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Konfigurasi UserBot dari environment variables"""
    
    # Telegram API
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "")
    
    # UserBot
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    SESSION_NAME = os.getenv("SESSION_NAME", "alfread")
    
    # Plugin Config
    PLUGINS_DIR = "plugins"
    
    @classmethod
    def validate(cls):
        """Validasi konfigurasi"""
        errors = []
        
        if not cls.API_ID:
            errors.append("API_ID tidak ditemukan")
        if not cls.API_HASH:
            errors.append("API_HASH tidak ditemukan")
        if not cls.MONGO_URI:
            errors.append("MONGO_URI tidak ditemukan")
        if not cls.OWNER_ID:
            errors.append("OWNER_ID tidak ditemukan")
            
        if errors:
            raise ValueError(f"Konfigurasi tidak lengkap: {', '.join(errors)}")
        
        return True

# Validasi saat import
try:
    Config.validate()
    print("✅ Konfigurasi valid")
except ValueError as e:
    print(f"⚠️  Peringatan: {e}")
    print("ℹ️  Pastikan file .env sudah diisi dengan benar")