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
        
        # Cek struktur file
        logger.info("📁 Checking project structure...")
        plugins_dir = Path(__file__).parent / "plugins"
        logger.info(f"Plugin directory: {plugins_dir}")
        logger.info(f"Plugin directory exists: {plugins_dir.exists()}")
        
        if plugins_dir.exists():
            plugin_files = list(plugins_dir.glob("*.py"))
            logger.info(f"Found {len(plugin_files)} Python files in plugins directory:")
            for pf in plugin_files:
                logger.info(f"  - {pf.name}")
        
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
            logger.info(f"🤖 Bot started as: @{me.username} (ID: {me.id})")
        else:
            logger.error("❌ BOT_TOKEN is required")
            sys.exit(1)
        
        # Test MongoDB connection
        try:
            from plugins.mongodb import MongoDB
            MongoDB.get_client()
            logger.info("✅ MongoDB connection test passed")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection issue: {e}")
        
        # Load plugins untuk bot
        logger.info("🔄 Loading plugins...")
        from plugins import load_plugins
        loaded_count = await load_plugins(bot_client)
        
        if loaded_count == 0:
            logger.warning("⚠️ No plugins loaded! Check plugin directory structure")
            # Try manual load as fallback
            await manual_load_plugins(bot_client)
        
        # Keep running
        logger.info("🤖 UserBot is now running. Press Ctrl+C to stop.")
        await bot_client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down UserBot...")
    except Exception as e:
        logger.error(f"❌ Error starting UserBot: {e}")
        sys.exit(1)

async def manual_load_plugins(client):
    """Manual load plugins as fallback"""
    logger.info("🔄 Trying manual plugin load...")
    
    plugins_to_load = [
        "mongodb",
        "connect", 
        "ping",
        "utils"
    ]
    
    for plugin_name in plugins_to_load:
        try:
            module = __import__(f"plugins.{plugin_name}", fromlist=[''])
            if hasattr(module, 'register_plugin'):
                await module.register_plugin(client)
                logger.info(f"✅ Manually loaded: {plugin_name}")
        except Exception as e:
            logger.error(f"❌ Failed to manually load {plugin_name}: {e}")

if __name__ == "__main__":
    # Jalankan event loop
    asyncio.run(main())