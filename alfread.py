#!/usr/bin/env python3
"""
Alfread UserBot - Telegram UserBot dengan MongoDB dan Plugin System
Railway Compatible Version - Simplified
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
        
        # Inisialisasi Telethon Client untuk bot
        from telethon import TelegramClient
        
        # Buat client bot utama
        bot_client = TelegramClient(
            session="alfread_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        
        # Mulai sebagai bot
        if Config.BOT_TOKEN:
            await bot_client.start(bot_token=Config.BOT_TOKEN)
            me = await bot_client.get_me()
            logger.info(f"🤖 Bot started as: @{me.username}")
        else:
            logger.error("❌ BOT_TOKEN is required")
            sys.exit(1)
        
        # Load plugins untuk bot
        from plugins import load_plugins
        await load_plugins(bot_client)
        
        # Cek dan load sessions dari database
        await load_sessions_from_db()
        
        # Keep running
        logger.info("🤖 UserBot is now running. Press Ctrl+C to stop.")
        await bot_client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Error starting UserBot: {e}")
        sys.exit(1)

async def load_sessions_from_db():
    """Load sessions dari MongoDB saat startup"""
    try:
        from plugins.mongodb import db
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from config import Config
        
        collection = db["user_sessions"]
        active_sessions = collection.find({"connected": True})
        
        count = 0
        async for session in active_sessions:  # Note: async for jika menggunakan motor
            try:
                user_id = session.get("user_id")
                session_string = session.get("session_string")
                
                if not session_string:
                    continue
                
                # Buat client dari session string
                client = TelegramClient(
                    StringSession(session_string),
                    Config.API_ID,
                    Config.API_HASH
                )
                
                await client.connect()
                
                # Cek apakah session masih valid
                if await client.is_user_authorized():
                    # Load plugins untuk client ini
                    from plugins import load_plugins
                    await load_plugins(client)
                    
                    # Start client di background
                    asyncio.create_task(client.run_until_disconnected())
                    
                    count += 1
                    logger.info(f"✅ Loaded session for user {user_id}")
                else:
                    await client.disconnect()
                    # Update status di database
                    collection.update_one(
                        {"user_id": user_id},
                        {"$set": {"connected": False}}
                    )
                    logger.warning(f"❌ Session expired for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error loading session: {e}")
                continue
        
        logger.info(f"📂 Loaded {count} active sessions from database")
        
    except Exception as e:
        logger.error(f"Error loading sessions from DB: {e}")

if __name__ == "__main__":
    # Jalankan event loop
    asyncio.run(main())