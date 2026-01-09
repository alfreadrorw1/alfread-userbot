#!/usr/bin/env python3
"""
Alfread UserBot - Telegram UserBot dengan MongoDB dan Plugin System
Railway Compatible Version dengan FloodWait handling
"""

import asyncio
import logging
import sys
import os
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('alfread.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Fungsi utama untuk menjalankan UserBot"""
    try:
        # Import config
        from config import Config
        logger.info("📱 Alfread UserBot Starting...")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Working dir: {os.getcwd()}")
        
        # Inisialisasi Telethon Client untuk bot
        from telethon import TelegramClient
        from telethon.errors import FloodWaitError
        
        # Buat client bot utama
        bot_client = TelegramClient(
            session="alfread_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        
        # Mulai sebagai bot dengan retry mechanism
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if Config.BOT_TOKEN:
                    await bot_client.start(bot_token=Config.BOT_TOKEN)
                    me = await bot_client.get_me()
                    logger.info(f"🤖 Bot started as: @{me.username} (ID: {me.id})")
                    break
                else:
                    logger.error("❌ BOT_TOKEN is required")
                    sys.exit(1)
                    
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"⏳ FloodWait: Need to wait {wait_time} seconds")
                
                if wait_time > 300:  # Jika lebih dari 5 menit
                    logger.error(f"❌ FloodWait terlalu lama ({wait_time} detik). Bot akan exit.")
                    sys.exit(1)
                
                logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time + 5)  # Tunggu + buffer 5 detik
                retry_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error starting bot: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"⏳ Retry {retry_count}/{max_retries} in 10 seconds...")
                    await asyncio.sleep(10)
                else:
                    raise
        
        # Test MongoDB connection
        try:
            from plugins.mongodb import MongoDB
            MongoDB.get_client()
            logger.info("✅ MongoDB connection test passed")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection issue: {e}")
        
        # Load plugins untuk bot - HANYA SEKALI
        logger.info("🔄 Loading plugins...")
        from plugins import load_plugins
        loaded_plugins = await load_plugins(bot_client)
        
        if loaded_plugins:
            logger.info(f"✅ {len(loaded_plugins)} plugins loaded successfully")
        else:
            logger.warning("⚠️ No plugins loaded! Check plugin directory structure")
        
        # Keep running
        logger.info("🤖 UserBot is now running. Press Ctrl+C to stop.")
        await bot_client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down UserBot...")
    except Exception as e:
        logger.error(f"❌ Error in UserBot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Jalankan event loop - HANYA SEKALI
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")