"""
Utility functions untuk Alfread UserBot
Helper functions yang digunakan oleh berbagai plugin
"""

import logging
from datetime import datetime
from telethon import events
from config import Config

logger = logging.getLogger(__name__)

async def is_owner(event):
    """Cek apakah user adalah owner"""
    return event.sender_id == Config.OWNER_ID

def format_time(dt=None):
    """Format waktu menjadi string"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_duration(seconds):
    """Format durasi dalam detik ke string"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def log_command(command, user_id, success=True):
    """Log command execution"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Command: {command} | User: {user_id} | Status: {status}")

async def reply_error(event, error_message):
    """Reply dengan format error yang konsisten"""
    await event.reply(f"❌ **Error:** {error_message}")

async def reply_success(event, message):
    """Reply dengan format success yang konsisten"""
    await event.reply(f"✅ **Success:** {message}")

async def delete_message_after(event, seconds):
    """Hapus pesan setelah beberapa detik"""
    await asyncio.sleep(seconds)
    try:
        await event.delete()
    except:
        pass

async def register_plugin(client):
    """Register plugin utils"""
    logger.info("✅ Utils plugin loaded")
    # Tidak ada handler event khusus untuk utils