#!/usr/bin/env python3
import logging
import asyncio
import os
import importlib
import sys
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
        self.bot_app = None
        self.user_client = None
        
    async def initialize(self):
        """Initialize bot and user clients"""
        try:
            # Initialize Telegram Bot Application
            self.bot_app = Application.builder().token(BOT_TOKEN).build()
            
            # Initialize Telethon User Client
            session_file = f"{SESSION_NAME}.session"
            self.user_client = TelegramClient(session_file, API_ID, API_HASH)
            
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
                    # Import module
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        os.path.join(plugins_dir, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Call setup function if exists
                    if hasattr(module, 'setup'):
                        # Pass both bot_app and user_client
                        setup_func = module.setup
                        if asyncio.iscoroutinefunction(setup_func):
                            await setup_func(self.bot_app, self.user_client)
                        else:
                            setup_func(self.bot_app, self.user_client)
                        
                        loaded.append(module_name)
                        logger.info(f"✅ Loaded plugin: {module_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to load {module_name}: {e}")
                    import traceback
                    traceback.print_exc()
        
        logger.info(f"📦 Total plugins loaded: {len(loaded)}")
        return loaded
    
    async def start(self):
        """Start the bot system"""
        try:
            logger.info("🚀 Starting UserBot-Alfread...")
            
            # Initialize clients
            if not await self.initialize():
                logger.error("❌ Failed to initialize clients")
                return
            
            # Connect user client
            await self.user_client.connect()
            logger.info("✅ User client connected")
            
            # Check if user is already authorized
            if not await self.user_client.is_user_authorized():
                logger.info("ℹ️ User not logged in, awaiting login via bot...")
            else:
                me = await self.user_client.get_me()
                logger.info(f"✅ User already logged in as: {me.first_name} (@{me.username})")
            
            # Load plugins
            await self.load_plugins()
            
            # Initialize bot (update handlers)
            await self.bot_app.initialize()
            
            # Start bot polling
            logger.info("🤖 Bot is running...")
            await self.bot_app.start()
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
                
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Clean shutdown"""
        logger.info("🔌 Shutting down...")
        
        if self.bot_app:
            try:
                await self.bot_app.stop()
                await self.bot_app.shutdown()
                logger.info("✅ Bot application stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping bot: {e}")
        
        if self.user_client and self.user_client.is_connected():
            await self.user_client.disconnect()
            logger.info("✅ User client disconnected")
        
        logger.info("👋 Shutdown completed")

def main():
    """Main entry point"""
    bot_system = UserBotAlfread()
    
    # Get or create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run the bot
    try:
        loop.run_until_complete(bot_system.start())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    finally:
        loop.close()

if __name__ == '__main__':
    main()