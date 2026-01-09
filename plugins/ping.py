import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telethon import TelegramClient
from telethon.errors import RPCError
import config
import time

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /ping command"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != config.OWNER_ID:
        await update.message.reply_text("❌ Maaf, hanya owner yang bisa menggunakan perintah ini.")
        return
    
    # Initialize Telethon client
    client = TelegramClient(
        config.SESSION_NAME,
        config.API_ID,
        config.API_HASH
    )
    
    try:
        # Connect to Telegram
        await client.connect()
        
        # Check if user is authorized
        if not await client.is_user_authorized():
            await update.message.reply_text(
                "🔴 **Userbot Offline**\n"
                "Session tidak ditemukan atau belum login.\n"
                "Gunakan /start untuk login."
            )
            await client.disconnect()
            return
        
        # Measure ping
        start_time = time.time()
        await client.get_me()
        end_time = time.time()
        
        ping_ms = round((end_time - start_time) * 1000, 2)
        
        # Get user info
        me = await client.get_me()
        username = f"@{me.username}" if me.username else "No username"
        
        await update.message.reply_text(
            f"🟢 **Userbot Online**\n"
            f"👤 **User:** {me.first_name} {me.last_name or ''}\n"
            f"📱 **Username:** {username}\n"
            f"⚡ **Ping:** {ping_ms} ms\n"
            f"🆔 **ID:** {me.id}"
        )
        
        await client.disconnect()
        
    except RPCError as e:
        await update.message.reply_text(
            f"🔴 **Userbot Error**\n"
            f"Error: {str(e)}\n"
            f"Silakan login ulang dengan /start"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Error:** {str(e)}"
        )
        try:
            await client.disconnect()
        except:
            pass

# Create handler
ping_handler = CommandHandler('ping', ping)