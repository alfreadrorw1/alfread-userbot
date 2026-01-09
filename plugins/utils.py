"""
Utility functions untuk Alfread UserBot
Helper functions yang digunakan oleh berbagai plugin
"""

import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

async def is_owner(event):
    """Cek apakah user adalah owner"""
    try:
        return event.sender_id == Config.OWNER_ID
    except:
        return False

def format_time(dt=None):
    """Format waktu menjadi string"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

async def register_plugin(client):
    """Register plugin utils - WAJIB ADA fungsi ini!"""
    logger.info("✅ Utils plugin loaded")