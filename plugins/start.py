"""
Start Plugin untuk Alfread UserBot
Command /start untuk memulai bot
"""

import logging
from telethon import events, Button
from config import Config
from plugins.utils import is_owner

logger = logging.getLogger(__name__)

async def register_plugin(client):
    """Register plugin start"""
    
    @client.on(events.NewMessage(pattern=r'^/start$', outgoing=False))
    async def start_handler(event):
        """Command /start untuk memulai bot"""
        
        logger.info(f"Received /start command from {event.sender_id}")
        
        welcome_text = """
🤖 **Selamat Datang di Alfread UserBot!**

**Fitur Utama:**
• UserBot dengan Plugin System
• MongoDB Database Support
• Multi-User Support (Owner only)
• Railway Deployment Ready

**Commands:**
• `/help` - Lihat semua command
• `/connect` - Hubungkan akun user
• `/ping` - Test latency
• `/debug` - System info

**Owner:** @{owner_username}
**Version:** 1.0.0
""".format(owner_username=Config.OWNER_USERNAME if hasattr(Config, 'OWNER_USERNAME') else "Unknown")
        
        # Tambahkan button untuk help
        buttons = [
            [Button.inline("📚 Help", b"show_help")],
            [Button.inline("🔗 Connect", b"show_connect")]
        ]
        
        await event.reply(welcome_text, buttons=buttons)
    
    @client.on(events.CallbackQuery(pattern=b"show_help"))
    async def show_help_handler(event):
        """Show help via callback"""
        help_text = """
📖 **Available Commands:**

**Basic:**
`/start` - Start bot
`/ping` - Check latency
`/debug` - System info
`/help` - This message

**UserBot (Owner):**
`/connect` - Connect user account
`/disconnect` - Disconnect user
`/session` - Check status
"""
        await event.edit(help_text)
    
    @client.on(events.CallbackQuery(pattern=b"show_connect"))
    async def show_connect_handler(event):
        """Show connect info via callback"""
        connect_text = """
🔗 **Connect User Account:**

1. Kirim `/connect`
2. Bagikan nomor telepon
3. Masukkan kode OTP
4. (Opsional) Password 2FA

**Note:** Hanya owner yang bisa menggunakan fitur ini.
"""
        await event.edit(connect_text)
    
    logger.info("✅ Start plugin loaded")