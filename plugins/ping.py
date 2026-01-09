"""
Ping Plugin untuk Alfread UserBot
Command .ping untuk mengecek latency dari BOT dan USER
"""

import logging
import time
from telethon import events
from plugins.utils import is_owner

logger = logging.getLogger(__name__)

# Import user_clients dari connect.py
try:
    from plugins.connect import user_clients
except ImportError:
    user_clients = {}

async def register_plugin(client):
    """Register plugin ping"""
    
    @client.on(events.NewMessage(pattern=r'^\.ping$', outgoing=True))
    async def handler(event):
        """Command .ping untuk mengecek latency bot dan user"""
        
        # Cek owner
        if not await is_owner(event):
            return
        
        owner_id = event.sender_id
        
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
            except:
                user_latency = "❌ Not connected"
        
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
            response += f"   _Gunakan `.connect` untuk menghubungkan akun user_\n"
        
        response += f"\n📡 **System:** Alfread UserBot v1.0"
        
        await message.edit(response)
        
        logger.info(f"Ping command - Bot: {bot_latency}ms, User: {user_latency}")
    
    logger.info("✅ Ping plugin loaded (with userbot support)")