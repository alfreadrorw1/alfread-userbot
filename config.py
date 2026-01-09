"""
Configuration Module for Alfread UserBot
Railway Optimized
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Konfigurasi UserBot dari environment variables"""
    
    # Telegram API (WAJIB)
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # MongoDB (WAJIB)
    MONGO_URI = os.getenv("MONGO_URI", "")
    
    # UserBot Owner
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    
    # Session
    SESSION_NAME = os.getenv("SESSION_NAME", "alfread")
    
    # Railway Detection
    RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "")
    RAILWAY_SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME", "")
    
    # Plugin Config
    PLUGINS_DIR = "plugins"
    
    @classmethod
    def validate(cls):
        """Validasi konfigurasi untuk Railway"""
        errors = []
        
        if not cls.API_ID or cls.API_ID == 0:
            errors.append("API_ID tidak ditemukan atau 0")
        
        if not cls.API_HASH:
            errors.append("API_HASH tidak ditemukan")
            
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN tidak ditemukan (diperlukan untuk Railway)")
            
        if not cls.MONGO_URI:
            errors.append("MONGO_URI tidak ditemukan")
            
        if errors:
            error_msg = "Konfigurasi tidak lengkap:\n" + "\n".join(f"• {e}" for e in errors)
            raise ValueError(error_msg)
        
        logger = logging.getLogger(__name__)
        logger.info("✅ Configuration validated successfully")
        return True

# Setup logging untuk config
import logging
logging.basicConfig(level=logging.INFO)

# Validasi saat import
try:
    Config.validate()
except ValueError as e:
    print(f"❌ {e}")
    print("\n📋 Pastikan environment variables sudah diisi di Railway:")
    print("1. Buka project di Railway Dashboard")
    print("2. Pergi ke tab 'Variables'")
    print("3. Tambahkan variables yang diperlukan:")
    print("   • API_ID, API_HASH, BOT_TOKEN")
    print("   • MONGO_URI, OWNER_ID")
    print("\n4. Redeploy aplikasi")
    # Jangan exit di Railway, biarkan bisa berjalan dengan config partial
    # sys.exit(1)