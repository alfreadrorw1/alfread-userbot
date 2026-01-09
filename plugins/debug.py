"""
Debug Plugin untuk Alfread UserBot
Command untuk debugging dan info system
"""

import logging
import platform
import sys
from datetime import datetime
from telethon import events
from config import Config

logger = logging.getLogger(__name__)

async def register_plugin(client):
    """Register plugin debug"""
    
    @client.on(events.NewMessage(pattern=r'^/debug$', outgoing=False))
    async def handler(event):
        """Command /debug untuk melihat info system"""
        
        logger.info(f"Received /debug command from {event.sender_id}")
        
        # Get system info
        python_version = sys.version
        platform_info = platform.platform()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get bot info
        me = await client.get_me()
        bot_name = me.first_name
        bot_id = me.id
        bot_username = f"@{me.username}" if me.username else "No username"
        
        debug_info = f"""
🤖 **Alfread UserBot Debug Info**

**System Info:**
• Python: {python_version.split()[0]}
• Platform: {platform_info}
• Time: {current_time}

**Bot Info:**
• Name: {bot_name}
• ID: {bot_id}
• Username: {bot_username}
• Owner ID: {Config.OWNER_ID}

**Database:**
• MongoDB: {'✅ Connected' if Config.MONGO_URI else '❌ Not connected'}

**Status:**
• Running on Railway: {'✅ Yes' if Config.RAILWAY_ENVIRONMENT else '❌ No'}
• Plugins loaded: Check logs
"""
        
        await event.reply(debug_info)
    
    @client.on(events.NewMessage(pattern=r'^/help$', outgoing=False))
    async def help_handler(event):
        """Command /help untuk bantuan"""
        
        logger.info(f"Received /help command from {event.sender_id}")
        
        help_text = """
📖 **Alfread UserBot Commands**

**Basic Commands:**
• `/start` - Start bot dan menu utama
• `/ping` - Test bot latency
• `/debug` - System debug information
• `/help` - Show this help message

**UserBot Commands (Owner Only):**
• `/connect` - Connect user account to bot
• `/disconnect` - Disconnect user account
• `/session` - Check session status

**Plugin System:**
• Modular plugin architecture
• MongoDB database support
• Railway deployment ready
"""
        
        await event.reply(help_text)
    
    logger.info("✅ Debug plugin loaded (prefix: /)")