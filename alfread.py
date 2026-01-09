#!/usr/bin/env python3
"""
Alfread UserBot - Telegram UserBot dengan MongoDB dan Plugin System
Dengan file lock untuk mencegah multiple instances
"""

import asyncio
import logging
import sys
import os
import time
import fcntl
import atexit
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

# File lock untuk mencegah multiple instances
LOCK_FILE = "alfread.lock"
lock_file = None

def acquire_lock():
    """Acquire file lock untuk mencegah multiple instances"""
    global lock_file
    
    try:
        lock_file = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # Tulis PID ke file
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        
        logger.info(f"🔒 File lock acquired (PID: {os.getpid()})")
        return True
        
    except (IOError, BlockingIOError):
        logger.error("❌ Bot sudah berjalan di instance lain!")
        logger.error("   Jika yakin tidak ada, hapus file: alfread.lock")
        return False

def release_lock():
    """Release file lock"""
    global lock_file
    
    if lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            os.remove(LOCK_FILE)
            logger.info("🔓 File lock released")
        except:
            pass

# Register release lock saat exit
atexit.register(release_lock)

async def main():
    """Fungsi utama untuk menjalankan UserBot"""
    try:
        # Cek file lock dulu
        if not acquire_lock():
            sys.exit(1)
        
        # Import config
        from config import Config
        logger.info("📱 Alfread UserBot Starting...")
        logger.info(f"PID: {os.getpid()}")
        
        # Cek environment variables
        required_envs = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'OWNER_ID']
        for env in required_envs:
            if not hasattr(Config, env) or not getattr(Config, env):
                logger.error(f"❌ Missing required environment: {env}")
                sys.exit(1)
        
        logger.info(f"Owner ID: {Config.OWNER_ID}")
        
        # Inisialisasi Telethon Client untuk bot
        from telethon import TelegramClient
        from telethon.errors import FloodWaitError
        
        # Buat client bot utama dengan session yang unique
        session_name = f"alfread_bot_{Config.OWNER_ID}"
        bot_client = TelegramClient(
            session=session_name,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        
        # Set unique client attributes untuk tracking
        bot_client.session_id = f"bot_{session_name}"
        
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
                
                if wait_time > 300:
                    logger.error(f"❌ FloodWait terlalu lama ({wait_time} detik)")
                    sys.exit(1)
                
                logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time + 5)
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
            logger.warning("⚠️ No plugins loaded!")
        
        # Keep running
        logger.info("🤖 UserBot is now running. Press Ctrl+C to stop.")
        await bot_client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down UserBot...")
    except Exception as e:
        logger.error(f"❌ Error in UserBot: {e}", exc_info=True)
    finally:
        release_lock()

if __name__ == "__main__":
    # Jalankan event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)