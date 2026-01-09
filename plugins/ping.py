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

def setup(bot, user_client):
    """Setup the ping plugin"""
    
    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /ping command"""
        user_id = update.effective_user.id
        
        # Check if user is owner
        if user_id != OWNER_ID:
            await update.message.reply_text("🚫 Akses ditolak!")
            return
        
        # Check if userbot is connected
        if not user_client.is_connected():
            await update.message.reply_text("❌ UserBot tidak terhubung!")
            return
        
        # Check login status
        is_authorized = await user_client.is_user_authorized()
        
        # Measure ping
        start_time = time.time()
        msg = await update.message.reply_text("🔄 Mengukur ping...")
        end_time = time.time()
        
        ping_ms = (end_time - start_time) * 1000
        
        # Get user info
        try:
            me = await user_client.get_me()
            user_info = f"{me.first_name} (@{me.username})" if me.username else me.first_name
        except:
            user_info = "Tidak diketahui"
        
        # Prepare response
        status = "🟢 ONLINE" if is_authorized else "🔴 OFFLINE"
        
        response = (
            f"🤖 **STATUS USERBOT**\n\n"
            f"**Status:** {status}\n"
            f"**Ping:** `{ping_ms:.2f} ms`\n"
            f"**Uptime:** `{ping_system.get_uptime()}`\n"
            f"**Akun:** {user_info}\n\n"
            f"**Owner ID:** `{OWNER_ID}`"
        )
        
        await msg.edit_text(response, parse_mode='Markdown')
    
    # Add handler to bot
    bot.add_handler(CommandHandler('ping', ping))
    
    logger.info("✅ Ping plugin loaded")