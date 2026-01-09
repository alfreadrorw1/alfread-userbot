from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import config
import asyncio
import re
import logging

# States for conversation
PHONE, OTP, PASSWORD = range(3)

# Store temporary data
user_data = {}

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != config.OWNER_ID:
        await update.message.reply_text("❌ Maaf, bot ini hanya untuk owner.")
        return ConversationHandler.END
    
    # Check if session already exists
    try:
        client = TelegramClient(
            config.SESSION_NAME,
            config.API_ID,
            config.API_HASH
        )
        
        await client.connect()
        
        if await client.is_user_authorized():
            await update.message.reply_text(
                "✅ Session sudah aktif!\n"
                "Userbot sudah terhubung dengan akun Anda.\n"
                "Gunakan /ping untuk mengecek status."
            )
            await client.disconnect()
            return ConversationHandler.END
        else:
            await client.disconnect()
    except Exception as e:
        logger.error(f"Error checking session: {e}")
    
    # Start login process
    keyboard = [[InlineKeyboardButton("Batal", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔑 **Login Userbot**\n\n"
        "Masukkan nomor Telegram Anda (format internasional):\n"
        "Contoh: +6281234567890\n\n"
        "Ketik /cancel untuk membatalkan.",
        reply_markup=reply_markup
    )
    
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get phone number from user"""
    phone = update.message.text.strip()
    
    # Validate phone number format
    phone_pattern = r'^\+\d{10,15}$'
    if not re.match(phone_pattern, phone):
        await update.message.reply_text(
            "❌ Format nomor tidak valid!\n"
            "Gunakan format internasional: +6281234567890\n"
            "Silakan coba lagi:"
        )
        return PHONE
    
    # Store phone number
    user_data[update.effective_user.id] = {
        'phone': phone,
        'client': None
    }
    
    # Initialize Telethon client
    client = TelegramClient(
        config.SESSION_NAME,
        config.API_ID,
        config.API_HASH
    )
    
    await client.connect()
    user_data[update.effective_user.id]['client'] = client
    
    try:
        # Send code request
        sent_code = await client.send_code_request(phone)
        user_data[update.effective_user.id]['phone_code_hash'] = sent_code.phone_code_hash
        
        await update.message.reply_text(
            "📱 **Kode OTP Dikirim**\n\n"
            "OTP telah dikirim ke Telegram Anda.\n"
            "Masukkan kode OTP dengan format:\n"
            "`1 2 3 4 5` (pisahkan dengan spasi)\n\n"
            "Ketik /cancel untuk membatalkan."
        )
        
        return OTP
    except Exception as e:
        logger.error(f"Error sending code: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n"
            "Silakan coba lagi dengan /start"
        )
        await client.disconnect()
        return ConversationHandler.END

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get OTP from user"""
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        await update.message.reply_text("❌ Sesi tidak ditemukan. Gunakan /start")
        return ConversationHandler.END
    
    otp_code = update.message.text.strip()
    
    # Validate OTP format (accept with or without spaces)
    if not re.match(r'^(\d\s?){5,}$', otp_code):
        await update.message.reply_text(
            "❌ Format OTP tidak valid!\n"
            "Masukkan kode dengan format:\n"
            "`1 2 3 4 5` (pisahkan dengan spasi)\n"
            "Atau `12345` (tanpa spasi)\n\n"
            "Silakan coba lagi:"
        )
        return OTP
    
    # Clean OTP (remove spaces)
    otp_code = otp_code.replace(' ', '')
    
    client = user_data[user_id]['client']
    phone_code_hash = user_data[user_id]['phone_code_hash']
    phone = user_data[user_id]['phone']
    
    try:
        # Sign in with OTP
        await client.sign_in(
            phone=phone,
            code=otp_code,
            phone_code_hash=phone_code_hash
        )
        
        await update.message.reply_text(
            "✅ **Login Berhasil!**\n\n"
            "Userbot sekarang terhubung dengan akun Anda.\n"
            "Session tersimpan di: `alfread.session`\n\n"
            "Gunakan /ping untuk mengecek status."
        )
        
        await client.disconnect()
        del user_data[user_id]
        
        return ConversationHandler.END
        
    except SessionPasswordNeededError:
        await update.message.reply_text(
            "🔒 **2FA Ditemukan**\n\n"
            "Akun Anda memiliki Two-Factor Authentication.\n"
            "Masukkan password 2FA Anda:\n\n"
            "Ketik /cancel untuk membatalkan."
        )
        return PASSWORD
        
    except Exception as e:
        logger.error(f"Error signing in: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n"
            "Silakan coba lagi dengan /start"
        )
        await client.disconnect()
        del user_data[user_id]
        return ConversationHandler.END

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get 2FA password from user"""
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        await update.message.reply_text("❌ Sesi tidak ditemukan. Gunakan /start")
        return ConversationHandler.END
    
    password = update.message.text.strip()
    client = user_data[user_id]['client']
    
    try:
        # Sign in with password
        await client.sign_in(password=password)
        
        await update.message.reply_text(
            "✅ **Login Berhasil!**\n\n"
            "Userbot sekarang terhubung dengan akun Anda.\n"
            "Session tersimpan di: `alfread.session`\n\n"
            "Gunakan /ping untuk mengecek status."
        )
        
        await client.disconnect()
        del user_data[user_id]
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error with 2FA: {e}")
        await update.message.reply_text(
            f"❌ Error: Password salah atau terjadi masalah.\n"
            "Silakan coba lagi dengan /start"
        )
        await client.disconnect()
        del user_data[user_id]
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    user_id = update.effective_user.id
    
    if user_id in user_data and user_data[user_id].get('client'):
        await user_data[user_id]['client'].disconnect()
        del user_data[user_id]
    
    await update.message.reply_text("❌ Proses login dibatalkan.")
    return ConversationHandler.END

# Create conversation handler
login_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_otp)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)