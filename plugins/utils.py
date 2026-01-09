import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Callable, Any, Optional

from telethon import TelegramClient
from telegram import Update
from telegram.ext import ContextTypes

from config import config

logger = logging.getLogger(__name__)

class UserbotManager:
    """Manage userbot instances"""
    
    _userbot: Optional[TelegramClient] = None
    _userbot_ready: bool = False
    _last_ping: float = 0
    
    @classmethod
    def set_userbot(cls, client: TelegramClient):
        """Set the active userbot instance"""
        cls._userbot = client
        cls._userbot_ready = True
        logger.info("🤖 Userbot instance set")
    
    @classmethod
    def get_userbot(cls) -> Optional[TelegramClient]:
        """Get the active userbot instance"""
        return cls._userbot
    
    @classmethod
    def is_userbot_ready(cls) -> bool:
        """Check if userbot is ready"""
        return cls._userbot_ready and cls._userbot is not None
    
    @classmethod
    def update_ping(cls):
        """Update last ping timestamp"""
        cls._last_ping = time.time()
    
    @classmethod
    def get_last_ping(cls) -> float:
        """Get last ping timestamp"""
        return cls._last_ping

def is_owner() -> Callable:
    """Decorator to check if user is owner"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            if user_id != config.owner_id:
                await update.message.reply_text("⛔ This command is only available for the owner.")
                logger.warning(f"Unauthorized access attempt from user {user_id}")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def format_time(seconds: float) -> str:
    """Format seconds to human readable time"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format timestamp to readable date"""
    if timestamp is None:
        timestamp = time.time()
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def safe_event(func: Callable) -> Callable:
    """Decorator for safe event handling with error logging"""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        try:
            return await func(event, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            try:
                await event.reply(f"❌ Error: {str(e)}")
            except:
                pass
    return wrapper

def calculate_ping(start_time: float) -> str:
    """Calculate ping in milliseconds"""
    ping_ms = (time.time() - start_time) * 1000
    return f"{ping_ms:.2f}ms"

async def log_to_owner(message: str, context: ContextTypes.DEFAULT_TYPE):
    """Send log message to owner"""
    try:
        await context.bot.send_message(
            chat_id=config.owner_id,
            text=f"📢 {message}"
        )
    except Exception as e:
        logger.error(f"Failed to send log to owner: {e}")