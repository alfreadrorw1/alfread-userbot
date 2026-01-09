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
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "")
    
    # UserBot
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    SESSION_NAME = os.getenv("SESSION_NAME", "alfread")
    
    # Railway
    RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "")
    RAILWAY_SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME", "")
    
    # Plugin Config
    PLUGINS_DIR = "plugins"
    
    @classmethod
    def validate(cls):
        """Validasi konfigurasi untuk Railway"""
        errors = []
        
        if not cls.API_ID:
            errors.append("API_ID tidak ditemukan")
        if not cls.API_HASH:
            errors.append("API_HASH tidak ditemukan")
        
        # Cek apakah di Railway
        is_railway = cls.RAILWAY_ENVIRONMENT or cls.RAILWAY_SERVICE_NAME
        
        if is_railway:
            # Di Railway, butuh SESSION_STRING atau BOT_TOKEN
            if not cls.SESSION_STRING and not cls.BOT_TOKEN:
                errors.append("Di Railway butuh SESSION_STRING atau BOT_TOKEN")
        
        if errors:
            raise ValueError(f"Konfigurasi tidak lengkap: {', '.join(errors)}")
        
        return True

# Validasi saat import
try:
    Config.validate()
    print("✅ Konfigurasi valid")
except ValueError as e:
    print(f"⚠️  Peringatan: {e}")