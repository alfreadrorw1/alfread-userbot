"""
Ping Plugin untuk Alfread UserBot
Command .ping untuk mengecek latency
"""

import logging
import time
from telethon import events
from plugins.utils import is_owner

logger = logging.getLogger(__name__)

async def register_plugin(client):
    """Register plugin ping"""
    
    @client.on(events.NewMessage(pattern=r'^\.ping$', outgoing=True))
    async def handler(event):
        """Command .ping untuk mengecek latency"""
        
        # Cek owner (opsional, bisa dihapus jika ingin publik)
        if not await is_owner(event):
            return
        
        start_time = time.time()
        
        # Kirim pesan awal
        message = await event.reply("🏓 Pong!")
        
        end_time = time.time()
        latency = round((end_time - start_time) * 1000, 2)
        
        # Edit dengan latency
        await message.edit(f"🏓 **Pong!**\n"
                          f"⚡ **Latency:** `{latency} ms`\n"
                          f"🤖 **UserBot:** Alfread v1.0")
        
        logger.info(f"Ping command executed - Latency: {latency}ms")
    
    logger.info("✅ Ping plugin loaded")