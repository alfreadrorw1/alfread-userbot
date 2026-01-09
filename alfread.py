#!/usr/bin/env python3
"""
Alfread UserBot - Telegram UserBot dengan MongoDB dan Plugin System
Entry point utama - Railway Compatible
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tambahkan path project
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Fungsi utama untuk menjalankan UserBot"""
    try:
        # Import config
        from config import Config
        logger.info("📱 Alfread UserBot Starting...")
        
        # Cek environment Railway
        IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") == "production" or os.getenv("RAILWAY_SERVICE_NAME") is not None
        
        # Inisialisasi Telethon Client
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        
        # Buat client dengan session string jika ada
        session_string = os.getenv("SESSION_STRING", "")
        
        client = TelegramClient(
            session=Config.SESSION_NAME,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            device_model="Alfread UserBot",
            system_version="Python 3.10+",
            app_version="1.0.0"
        )
        
        # Load plugins
        from plugins import load_plugins
        await load_plugins(client)
        
        # Mulai client dengan cara yang berbeda untuk Railway
        logger.info("🚀 Connecting to Telegram...")
        
        if IS_RAILWAY:
            logger.info("⚡ Running in Railway environment")
            
            # Coba gunakan bot token jika ada
            if Config.BOT_TOKEN:
                await client.start(bot_token=Config.BOT_TOKEN)
                logger.info("🤖 Started as Bot")
            else:
                # Cek jika session sudah ada
                if not os.path.exists(f"{Config.SESSION_NAME}.session"):
                    logger.error("❌ No session file found for Railway deployment")
                    logger.info("ℹ️ Please create session locally first, then upload to Railway")
                    sys.exit(1)
                
                await client.start()
        else:
            # Local environment - bisa minta input
            await client.start()
        
        # Get bot info
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (ID: {me.id})")
        
        # Keep running
        logger.info("🤖 UserBot is now running. Press Ctrl+C to stop.")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Error starting UserBot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Jalankan event loop
    asyncio.run(main())