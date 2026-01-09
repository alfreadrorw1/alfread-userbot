import asyncio
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import config
from plugins.utils import is_owner, UserbotManager, calculate_ping, format_timestamp

logger = logging.getLogger(__name__)

class PingHandler:
    """Handle ping commands and userbot status"""
    
    @is_owner()
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command"""
        start_time = time.time()
        message = update.message
        
        # Check MongoDB connection
        from plugins.mongodb import mongodb
        mongo_status = await mongodb.is_connected()
        
        # Check userbot status
        userbot = UserbotManager.get_userbot()
        userbot_status = UserbotManager.is_userbot_ready()
        
        # Calculate ping
        ping_telegram = calculate_ping(start_time)
        
        # Build status message
        status_lines = [
            "🤖 *Alfread UserBot Status*",
            "",
            "📊 *System Status:*",
            f"• 🤖 UserBot: {'🟢 Online' if userbot_status else '🔴 Offline'}",
            f"• 🗄️ MongoDB: {'🟢 Connected' if mongo_status else '🔴 Disconnected'}",
            f"• ⚡ Ping: `{ping_telegram}`",
            "",
            "📈 *UserBot Info:*"
        ]
        
        if userbot_status and userbot:
            try:
                me = await userbot.get_me()
                status_lines.extend([
                    f"• 👤 Name: `{me.first_name}`",
                    f"• 📞 Phone: `{me.phone}`" if me.phone else "• 📞 Phone: `Hidden`",
                    f"• 🆔 ID: `{me.id}`",
                    f"• 📝 Username: @{me.username}" if me.username else "• 📝 Username: `None`",
                ])
            except Exception as e:
                status_lines.append(f"• ❌ Error getting user info: `{str(e)}`")
        
        status_lines.extend([
            "",
            "⏰ *Last Activity:*",
            f"• 🕒 {format_timestamp(UserbotManager.get_last_ping())}",
            "",
            "🔧 *Commands:*",
            "• /ping - Check status",
            "• /connect - Connect userbot",
            "• /help - Show help"
        ])
        
        await message.reply_text(
            "\n".join(status_lines),
            parse_mode="Markdown"
        )
        
        # Update last ping time
        UserbotManager.update_ping()
    
    @is_owner()
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command (quick status)"""
        userbot_status = UserbotManager.is_userbot_ready()
        
        if userbot_status:
            await update.message.reply_text(
                "🟢 *UserBot Online*\n"
                "The userbot is connected and ready!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔴 *UserBot Offline*\n"
                "Use /connect to start the userbot",
                parse_mode="Markdown"
            )

def setup_handlers(application):
    """Setup command handlers"""
    handler = PingHandler()
    
    application.add_handler(CommandHandler("ping", handler.ping_command))
    application.add_handler(CommandHandler("status", handler.status_command))