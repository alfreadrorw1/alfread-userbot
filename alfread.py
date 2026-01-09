#!/usr/bin/env python3
import asyncio
import logging
import importlib
import sys
import os
from pathlib import Path

from telegram import Bot
from telegram.ext import Application
from telethon import TelegramClient

import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AlfreadBot:
    def __init__(self):
        self.bot_app = None
        self.userbot_client = None
        
    async def load_plugins(self):
        """Load all plugins from plugins directory"""
        plugins_dir = Path("plugins")
        
        # Import all Python files in plugins directory
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name != "__init__.py":
                module_name = f"plugins.{plugin_file.stem}"
                
                try:
                    # Import module
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        plugin_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Check if module has handlers
                    if hasattr(module, 'login_handler'):
                        self.bot_app.add_handler(module.login_handler)
                        logger.info(f"Loaded plugin: {plugin_file.name} (login_handler)")
                    
                    if hasattr(module, 'ping_handler'):
                        self.bot_app.add_handler(module.ping_handler)
                        logger.info(f"Loaded plugin: {plugin_file.name} (ping_handler)")
                        
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_file.name}: {e}")
    
    async def connect_userbot(self):
        """Connect Telethon userbot client"""
        client = TelegramClient(
            config.SESSION_NAME,
            config.API_ID,
            config.API_HASH
        )
        
        try:
            await client.connect()
            
            if await client.is_user_authorized():
                logger.info("Userbot connected successfully")
                self.userbot_client = client
                return True
            else:
                logger.info("Userbot not authorized. Please login with /start")
                await client.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect userbot: {e}")
            return False
    
    async def error_handler(self, update, context):
        """Handle errors"""
        logger.error(f"Exception while handling update: {context.error}")
        
        if update and hasattr(update, 'effective_user'):
            try:
                await update.effective_user.send_message(
                    "❌ Terjadi error saat memproses permintaan Anda."
                )
            except:
                pass
    
    async def start(self):
        """Start the bot application"""
        # Create Application
        self.bot_app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Load plugins
        await self.load_plugins()
        
        # Connect userbot if session exists
        await self.connect_userbot()
        
        # Add error handler
        self.bot_app.add_error_handler(self.error_handler)
        
        # Start bot
        await self.bot_app.initialize()
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()
        
        logger.info("Bot started successfully")
        
        # Keep running
        await asyncio.Event().wait()
    
    async def stop(self):
        """Stop the bot application"""
        if self.bot_app:
            await self.bot_app.stop()
            await self.bot_app.shutdown()
        
        if self.userbot_client and self.userbot_client.is_connected():
            await self.userbot_client.disconnect()

async def main():
    """Main function"""
    bot = AlfreadBot()
    
    try:
        logger.info("Starting Alfread Userbot...")
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run main function
    asyncio.run(main())