#!/usr/bin/env python3
"""
Alfread UserBot - Main Entry Point
A modular Telegram UserBot with MongoDB backend
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from telethon import TelegramClient, events
from telegram.ext import Application, CommandHandler
from telegram import Update

from config import config
from plugins.mongodb import mongodb
from plugins.utils import UserbotManager, log_to_owner
from plugins import discover_plugins

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('alfread.log')
    ]
)
logger = logging.getLogger(__name__)

class AlfreadBot:
    """Main bot class"""
    
    def __init__(self):
        self.bot_app: Optional[Application] = None
        self.userbot: Optional[TelegramClient] = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize bot components"""
        logger.info("🚀 Starting Alfread UserBot...")
        
        # Connect to MongoDB
        if not await mongodb.connect():
            logger.error("Failed to connect to MongoDB. Exiting...")
            sys.exit(1)
        
        # Initialize Telegram Bot
        try:
            self.bot_app = Application.builder().token(config.bot_token).build()
            logger.info("✅ Bot application initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            sys.exit(1)
        
        # Load all plugins
        plugins = discover_plugins()
        
        # Setup handlers from plugins
        for plugin in plugins:
            if hasattr(plugin, 'setup_handlers'):
                try:
                    plugin.setup_handlers(self.bot_app)
                    logger.info(f"✅ Setup handlers from {plugin.__name__}")
                except Exception as e:
                    logger.error(f"❌ Failed to setup handlers from {plugin.__name__}: {e}")
        
        # Add default handlers
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("help", self.help_command))
        
        # Try to load and connect userbot from saved session
        await self.try_connect_userbot()
        
        # Setup userbot event handlers
        if self.userbot:
            await self.setup_userbot_events()
    
    async def try_connect_userbot(self):
        """Try to connect userbot from saved session"""
        try:
            from plugins.connect import ConnectHandler
            handler = ConnectHandler()
            
            session_string = await handler.load_session_from_db()
            if session_string:
                logger.info("🔄 Attempting to reconnect userbot from saved session...")
                
                from telethon.sessions import StringSession
                self.userbot = TelegramClient(
                    StringSession(session_string),
                    config.api_id,
                    config.api_hash
                )
                
                await self.userbot.connect()
                
                if await self.userbot.is_user_authorized():
                    UserbotManager.set_userbot(self.userbot)
                    logger.info("✅ Userbot reconnected successfully")
                    
                    # Send notification to owner
                    if self.bot_app:
                        await log_to_owner("UserBot automatically reconnected", self.bot_app)
                else:
                    logger.warning("Session expired. Manual login required.")
                    await self.userbot.disconnect()
                    self.userbot = None
                    
        except Exception as e:
            logger.error(f"❌ Failed to reconnect userbot: {e}")
            self.userbot = None
    
    async def setup_userbot_events(self):
        """Setup userbot event handlers"""
        
        @self.userbot.on(events.NewMessage(outgoing=True))
        async def handle_outgoing_message(event):
            """Handle outgoing messages"""
            UserbotManager.update_ping()
            logger.debug(f"Outgoing message: {event.text}")
        
        @self.userbot.on(events.NewMessage(incoming=True))
        async def handle_incoming_message(event):
            """Handle incoming messages"""
            UserbotManager.update_ping()
            logger.debug(f"Incoming message from {event.sender_id}: {event.text}")
    
    async def start_command(self, update: Update, context):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_text = (
            "🤖 *Welcome to Alfread UserBot!*\n\n"
            "A modular Telegram UserBot with MongoDB backend.\n\n"
            "*Available Commands:*\n"
            "• /start - Show this message\n"
            "• /help - Show help\n"
            "• /ping - Check bot status\n"
            "• /status - Quick status check\n"
            "• /connect - Connect userbot (owner only)\n\n"
            "*Owner:* @{username}\n"
            "*UserBot Status:* {status}"
        ).format(
            username=user.username or "N/A",
            status="🟢 Online" if UserbotManager.is_userbot_ready() else "🔴 Offline"
        )
        
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context):
        """Handle /help command"""
        help_text = (
            "📚 *Alfread UserBot Help*\n\n"
            "*Owner Commands:*\n"
            "• /connect - Connect your Telegram account as userbot\n"
            "• /ping - Detailed status and ping information\n"
            "• /status - Quick status check\n\n"
            "*General Commands:*\n"
            "• /start - Welcome message\n"
            "• /help - This help message\n\n"
            "*Features:*\n"
            "• Modular plugin system\n"
            "• MongoDB session storage\n"
            "• Automatic reconnection\n"
            "• Production-ready architecture\n\n"
            "🔧 *Configuration:*\n"
            "Make sure all environment variables are set correctly."
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def start(self):
        """Start the bot"""
        if self.is_running:
            return
        
        await self.initialize()
        self.is_running = True
        
        # Start the bot
        await self.bot_app.initialize()
        await self.bot_app.start()
        
        # Start userbot if connected
        if self.userbot and not self.userbot.is_connected():
            await self.userbot.start()
        
        logger.info("✅ Alfread UserBot is now running!")
        print("\n" + "="*50)
        print("🤖 Alfread UserBot Started Successfully!")
        print(f"👤 Owner ID: {config.owner_id}")
        print(f"🗄️ Database: {config.db_name}")
        print(f"🔌 UserBot: {'Connected' if UserbotManager.is_userbot_ready() else 'Disconnected'}")
        print("="*50 + "\n")
        
        # Send startup notification
        if self.bot_app:
            await log_to_owner("Alfread UserBot started successfully", self.bot_app)
        
        # Run until stopped
        await self.bot_app.updater.start_polling()
        
        # Keep running
        while self.is_running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the bot gracefully"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping Alfread UserBot...")
        self.is_running = False
        
        # Stop userbot
        if self.userbot and self.userbot.is_connected():
            await self.userbot.disconnect()
            logger.info("🔌 UserBot disconnected")
        
        # Stop bot application
        if self.bot_app:
            await self.bot_app.stop()
            await self.bot_app.shutdown()
            logger.info("🤖 Bot application stopped")
        
        # Disconnect MongoDB
        await mongodb.disconnect()
        
        logger.info("👋 Alfread UserBot stopped gracefully")

def handle_signal(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(bot.stop())

async def main():
    """Main entry point"""
    global bot
    
    bot = AlfreadBot()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()
        logger.info("Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())