#!/usr/bin/env python3
"""
Alfread UserBot - Telegram UserBot dengan MongoDB dan Plugin System
Railway Compatible Version
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tambahkan path project
sys.path.insert(0, str(Path(__file__).parent))

async def load_sessions_from_db():
    """Load sessions dari MongoDB saat startup"""
    try:
        from plugins.mongodb import get_active_sessions
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from config import Config
        
        active_sessions = await get_active_sessions()
        logger.info(f"📂 Found {len(active_sessions)} active sessions in database")
        
        clients = []
        for session_data in active_sessions:
            try:
                user_id = session_data.get("user_id")
                session_string = session_data.get("session_string")
                
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
                    
                    clients.append(client)
                    logger.info(f"✅ Loaded session for user {user_id}")
                else:
                    await client.disconnect()
                    logger.warning(f"❌ Session expired for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error loading session: {e}")
                continue
        
        return clients
        
    except Exception as e:
        logger.error(f"Error loading sessions from DB: {e}")
        return []

async def main():
    """Fungsi utama untuk menjalankan UserBot"""
    try:
        # Import config
        from config import Config
        logger.info("📱 Alfread UserBot Starting...")
        
        # Cek environment Railway
        IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") == "production" or os.getenv("RAILWAY_SERVICE_NAME") is not None
        
        # Inisialisasi Telethon Client untuk bot
        from telethon import TelegramClient
        
        if IS_RAILWAY:
            logger.info("⚡ Running in Railway environment")
        
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
            logger.error("❌ BOT_TOKEN is required for Railway deployment")
            sys.exit(1)
        
        # Load sessions dari database
        user_clients = await load_sessions_from_db()
        logger.info(f"👥 Loaded {len(user_clients)} user sessions")
        
        # Load plugins untuk bot
        from plugins import load_plugins
        await load_plugins(bot_client)
        
        # Keep running
        logger.info("🤖 UserBot is now running. Press Ctrl+C to stop.")
        
        # Jalankan semua clients
        tasks = [bot_client.run_until_disconnected()]
        for client in user_clients:
            tasks.append(client.run_until_disconnected())
        
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"❌ Error starting UserBot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Jalankan event loop
    asyncio.run(main())