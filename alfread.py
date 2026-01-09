#!/usr/bin/env python3
"""
Alfread UserBot - Telegram UserBot dengan MongoDB dan Plugin System
Entry point utama
"""

import asyncio
import logging
import sys
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
        
        # Inisialisasi Telethon Client
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        
        # Buat client
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
        
        # Mulai client
        logger.info("🚀 Connecting to Telegram...")
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