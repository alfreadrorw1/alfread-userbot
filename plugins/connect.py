import asyncio
import logging
from typing import Optional

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import config
from plugins.mongodb import mongodb
from plugins.utils import is_owner, UserbotManager, log_to_owner

logger = logging.getLogger(__name__)

class ConnectHandler:
    """Handle userbot connection commands"""
    
    def __init__(self):
        self.phone_code_hash: Optional[str] = None
        self.phone_number: Optional[str] = None
    
    async def save_session_to_db(self, session_string: str):
        """Save Telethon session to MongoDB"""
        try:
            collection = await mongodb.get_collection("userbot_sessions")
            
            session_data = {
                "_id": "current_session",
                "session_string": session_string,
                "updated_at": asyncio.get_event_loop().time(),
                "phone_number": self.phone_number
            }
            
            await collection.update_one(
                {"_id": "current_session"},
                {"$set": session_data},
                upsert=True
            )
            
            logger.info("✅ Session saved to MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")
            return False
    
    async def load_session_from_db(self) -> Optional[str]:
        """Load Telethon session from MongoDB"""
        try:
            collection = await mongodb.get_collection("userbot_sessions")
            session_data = await collection.find_one({"_id": "current_session"})
            
            if session_data and "session_string" in session_data:
                logger.info("✅ Session loaded from MongoDB")
                return session_data["session_string"]
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load session: {e}")
            return None
    
    @is_owner()
    async def connect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /connect command"""
        message = update.message
        
        if UserbotManager.is_userbot_ready():
            await message.reply_text("✅ Userbot is already connected!")
            return
        
        await message.reply_text(
            "🔌 *Connecting Userbot...*\n\n"
            "Please send your phone number (with country code):\n"
            "Example: `+6281234567890`",
            parse_mode="Markdown"
        )
        
        # Store state for phone number
        context.user_data["awaiting_phone"] = True
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle interactive connection process"""
        message = update.message
        text = message.text.strip()
        
        if not context.user_data.get("awaiting_phone"):
            return
        
        # Handle phone number input
        if context.user_data.get("awaiting_phone"):
            self.phone_number = text
            context.user_data["awaiting_phone"] = False
            context.user_data["awaiting_code"] = True
            
            await message.reply_text(
                f"📱 Phone number: `{text}`\n\n"
                "Now please send the verification code you received on Telegram:",
                parse_mode="Markdown"
            )
            return
        
        # Handle verification code
        if context.user_data.get("awaiting_code"):
            code = text
            context.user_data["awaiting_code"] = False
            
            await message.reply_text("🔄 Verifying code...")
            
            # Try to load existing session first
            session_string = await self.load_session_from_db()
            
            if session_string:
                # Try to connect with existing session
                try:
                    client = TelegramClient(
                        StringSession(session_string),
                        config.api_id,
                        config.api_hash
                    )
                    
                    await client.connect()
                    
                    if not await client.is_user_authorized():
                        await message.reply_text("⚠️ Session expired. Starting fresh login...")
                        session_string = None
                    else:
                        UserbotManager.set_userbot(client)
                        await message.reply_text("✅ Userbot reconnected with saved session!")
                        await log_to_owner(f"Userbot connected with saved session", context)
                        return
                        
                except Exception as e:
                    logger.error(f"Session connection failed: {e}")
                    session_string = None
            
            # New login
            if not session_string:
                try:
                    client = TelegramClient(
                        StringSession(),
                        config.api_id,
                        config.api_hash,
                        device_model="Alfread UserBot",
                        system_version="Python 3.10",
                        app_version="1.0.0"
                    )
                    
                    await client.connect()
                    
                    # Send code
                    sent = await client.send_code_request(self.phone_number)
                    self.phone_code_hash = sent.phone_code_hash
                    
                    # Try to sign in
                    try:
                        await client.sign_in(
                            phone=self.phone_number,
                            code=code,
                            phone_code_hash=self.phone_code_hash
                        )
                    except SessionPasswordNeededError:
                        await message.reply_text(
                            "🔐 Two-factor authentication enabled.\n"
                            "Please send your password:"
                        )
                        context.user_data["awaiting_password"] = True
                        return
                    
                    # Save session
                    session_string = client.session.save()
                    await self.save_session_to_db(session_string)
                    
                    UserbotManager.set_userbot(client)
                    await message.reply_text("✅ Userbot connected successfully!")
                    await log_to_owner(f"Userbot connected with phone: {self.phone_number}", context)
                    
                except PhoneCodeInvalidError:
                    await message.reply_text("❌ Invalid verification code. Please try /connect again.")
                except Exception as e:
                    logger.error(f"Connection error: {e}", exc_info=True)
                    await message.reply_text(f"❌ Connection failed: {str(e)}")
            
            return
        
        # Handle 2FA password
        if context.user_data.get("awaiting_password"):
            password = text
            context.user_data["awaiting_password"] = False
            
            try:
                client = TelegramClient(
                    StringSession(),
                    config.api_id,
                    config.api_hash
                )
                
                await client.connect()
                await client.sign_in(password=password)
                
                # Save session
                session_string = client.session.save()
                await self.save_session_to_db(session_string)
                
                UserbotManager.set_userbot(client)
                await message.reply_text("✅ Userbot connected with 2FA!")
                await log_to_owner("Userbot connected with 2FA", context)
                
            except Exception as e:
                logger.error(f"2FA login error: {e}")
                await message.reply_text(f"❌ 2FA login failed: {str(e)}")

def setup_handlers(application):
    """Setup command handlers"""
    handler = ConnectHandler()
    
    # Command handlers
    application.add_handler(CommandHandler("connect", handler.connect_command))
    
    # Message handler for interactive login
    from telegram.ext import MessageHandler, filters
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handler.handle_message
        )
    )