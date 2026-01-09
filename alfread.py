#!/usr/bin/env python3
import logging
import asyncio
import os
import importlib
from telethon import TelegramClient
from telegram.ext import Application
from config import BOT_TOKEN, API_ID, API_HASH, SESSION_NAME

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UserBotAlfread:
    def __init__(self):
        self.bot = None
        self.user = None
        
    async def initialize(self):
        """Initialize bot and user clients"""
        try:
            # Initialize Telegram Bot
            self.bot = Application.builder().token(BOT_TOKEN).build()
            
            # Initialize Telethon User Client
            session_file = f"{SESSION_NAME}.session"
            self.user = TelegramClient(session_file, API_ID, API_HASH)
            
            logger.info("✅ Clients initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def load_plugins(self):
        """Load all plugins from plugins directory"""
        plugins_dir = 'plugins'
        
        if not os.path.exists(plugins_dir):
            logger.warning(f"Plugins directory '{plugins_dir}' not found")
            return
        
        loaded = []
        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'plugins.{module_name}')
                    
                    # Call setup function if exists
                    if hasattr(module, 'setup'):
                        await module.setup(self.bot, self.user)
                        loaded.append(module_name)
                        logger.info(f"✅ Loaded plugin: {module_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to load {module_name}: {e}")
        
        logger.info(f"📦 Total plugins loaded: {len(loaded)}")
        return loaded
    
    async def start(self):
        """Start the bot system"""
        try:
            logger.info("🚀 Starting UserBot-Alfread...")
            
            # Initialize clients
            if not await self.initialize():
                return
            
            # Connect user client
            await self.user.connect()
            logger.info("✅ User client connected")
            
            # Check if user is already authorized
            if not await self.user.is_user_authorized():
                logger.info("ℹ️ User not logged in, awaiting login via bot...")
            else:
                logger.info("✅ User already logged in")
            
            # Load plugins
            await self.load_plugins()
            
            # Start bot polling
            logger.info("🤖 Bot is running...")
            await self.bot.run_polling(allowed_updates=['message'])
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Clean shutdown"""
        logger.info("🔌 Shutting down...")
        
        if self.user and self.user.is_connected():
            await self.user.disconnect()
            logger.info("✅ User client disconnected")
        
        logger.info("👋 Shutdown completed")

async def main():
    """Main entry point"""
    bot_system = UserBotAlfread()
    await bot_system.start()

if __name__ == '__main__':
    asyncio.run(main())