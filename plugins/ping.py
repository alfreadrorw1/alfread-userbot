import time
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import OWNER_ID

logger = logging.getLogger(__name__)

class PingSystem:
    def __init__(self):
        self.start_time = time.time()
    
    def get_uptime(self):
        """Get formatted uptime"""
        uptime = int(time.time() - self.start_time)
        
        days, remainder = divmod(uptime, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        if seconds or not parts: parts.append(f"{seconds}s")
        
        return ' '.join(parts)

ping_system = PingSystem()

def setup(bot_app, user_client):
    """Setup the ping plugin"""
    
    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /ping command"""
        user_id = update.effective_user.id
        
        # Check if user is owner
        if user_id != OWNER_ID:
            await update.message.reply_text("🚫 Akses ditolak!")
            return
        
        # Start measuring ping
        start_time = time.time()
        msg = await update.message.reply_text("🔄 Mengukur ping...")
        end_time = time.time()
        
        ping_ms = (end_time - start_time) * 1000
        
        # Check connection status
        is_connected = user_client.is_connected()
        is_authorized = False
        user_info = "Tidak diketahui"
        
        if is_connected:
            try:
                is_authorized = await user_client.is_user_authorized()
                if is_authorized:
                    me = await user_client.get_me()
                    user_info = f"{me.first_name or 'No name'}"
                    if me.username:
                        user_info += f" (@{me.username})"
            except Exception as e:
                logger.error(f"Error getting user info: {e}")
        
        # Prepare response
        status_emoji = "🟢" if is_authorized else "🔴"
        status_text = "ONLINE" if is_authorized else "OFFLINE"
        
        response = (
            f"🤖 **PING USERBOT**\n\n"
            f"**Status:** {status_emoji} {status_text}\n"
            f"**Ping:** `{ping_ms:.2f} ms`\n"
            f"**Uptime:** `{ping_system.get_uptime()}`\n"
            f"**Akun:** {user_info}\n"
            f"**Koneksi:** {'✅' if is_connected else '❌'}\n\n"
            f"**Owner ID:** `{OWNER_ID}`"
        )
        
        await msg.edit_text(response, parse_mode='Markdown')
    
    # Add handler to bot
    bot_app.add_handler(CommandHandler('ping', ping))
    
    logger.info("✅ Ping plugin loaded")