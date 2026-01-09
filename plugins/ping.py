"""
Ping Plugin untuk Alfread UserBot
Command /ping untuk mengecek latency dari BOT dan USER
"""

import logging
import time
from telethon import events
from plugins.utils import is_owner

logger = logging.getLogger(__name__)

# Handler tracker
_ping_handler = None

async def register_plugin(client):
    """Register plugin ping - dipanggil sekali saja"""
    global _ping_handler
    
    # Remove existing handler if any
    if _ping_handler:
        client.remove_event_handler(_ping_handler)
    
    @client.on(events.NewMessage(pattern=r'^/ping$'))
    async def handler(event):
        """Command /ping untuk mengecek latency bot dan user"""
        
        logger.info(f"Received /ping command from {event.sender_id}")
        
        # Cek owner
        if not await is_owner(event):
            await event.reply("❌ Hanya owner yang bisa menggunakan command ini!")
            return
        
        owner_id = event.sender_id
        
        # Get user_clients from connect plugin
        try:
            from plugins.connect import manager
            user_clients = manager.user_clients
        except ImportError:
            user_clients = {}
        
        # Latency dari bot
        start_time = time.time()
        message = await event.reply("🏓 **Testing...**")
        bot_latency = round((time.time() - start_time) * 1000, 2)
        
        # Latency dari user (jika terkoneksi)
        user_latency = None
        if owner_id in user_clients:
            try:
                user_start = time.time()
                await user_clients[owner_id].get_me()
                user_latency = round((time.time() - user_start) * 1000, 2)
                logger.info(f"User latency for {owner_id}: {user_latency}ms")
            except Exception as e:
                logger.error(f"Error getting user latency: {e}")
                user_latency = "❌ Not connected"
        else:
            logger.info(f"No user client for {owner_id}")
        
        # Format response
        response = f"🏓 **Pong!**\n\n"
        response += f"🤖 **Bot Latency:** `{bot_latency} ms`\n"
        
        if user_latency:
            if isinstance(user_latency, str):
                response += f"👤 **User Latency:** {user_latency}\n"
            else:
                response += f"👤 **User Latency:** `{user_latency} ms`\n"
        else:
            response += f"👤 **User Status:** ❌ Not connected\n"
            response += f"   _Gunakan `/connect` untuk menghubungkan akun user_\n"
        
        response += f"\n📡 **System:** Alfread UserBot v1.0"
        
        await message.edit(response)
        
        logger.info(f"Ping command - Bot: {bot_latency}ms, User: {user_latency}")
    
    _ping_handler = handler
    logger.info("✅ Ping plugin loaded")