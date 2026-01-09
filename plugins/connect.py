import logging
import asyncio
from telethon.errors import (
    SessionPasswordNeededError, 
    PhoneCodeInvalidError, 
    PhoneNumberInvalidError,
    FloodWaitError
)
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)
from config import OWNER_ID

# Setup logging
logger = logging.getLogger(__name__)

# Conversation states
PHONE, CODE, PASSWORD = range(3)

# Store pending login attempts
pending_logins = {}

def setup(bot: Application, user_client):
    """Setup the connect plugin"""
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
        user_id = update.effective_user.id
        
        # Check if user is owner
        if user_id != OWNER_ID:
            await update.message.reply_text(
                "🚫 Akses ditolak! Hanya owner yang bisa menggunakan bot ini."
            )
            return ConversationHandler.END
        
        # Check if already logged in
        if await user_client.is_user_authorized():
            await update.message.reply_text(
                "✅ Anda sudah login sebagai UserBot!\n\n"
                "Gunakan /logout untuk login dengan akun lain"
            )
            return ConversationHandler.END
        
        # Request phone number
        keyboard = [[
            KeyboardButton("📱 Bagikan Nomor Telepon", request_contact=True)
        ]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "📲 Silakan bagikan nomor telepon Anda:\n\n"
            "Gunakan tombol di bawah atau ketik nomor dengan format +62xxxxxxxxxx",
            reply_markup=reply_markup
        )
        
        return PHONE
    
    async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone number input"""
        user_id = update.effective_user.id
        
        # Get phone number from contact or text
        if update.message.contact:
            phone = f"+{update.message.contact.phone_number}"
        else:
            phone = update.message.text.strip()
        
        # Validate phone format
        if not phone.startswith('+') or len(phone) < 10:
            await update.message.reply_text(
                "❌ Format nomor tidak valid!\n"
                "Gunakan format internasional: +62xxxxxxxxxx"
            )
            return PHONE
        
        try:
            # Send verification code
            sent = await user_client.send_code_request(phone)
            
            # Store login data
            pending_logins[user_id] = {
                'phone': phone,
                'phone_code_hash': sent.phone_code_hash,
                'attempts': 0
            }
            
            await update.message.reply_text(
                "📲 Kode verifikasi telah dikirim!\n\n"
                "Silakan balas dengan format:\n"
                "`1 2 3 4 5`\n\n"
                "Jangan lupa beri spasi antara angka!",
                parse_mode='Markdown'
            )
            
            return CODE
            
        except PhoneNumberInvalidError:
            await update.message.reply_text("❌ Nomor telepon tidak valid!")
            return PHONE
        except FloodWaitError as e:
            await update.message.reply_text(
                f"⏳ Terlalu banyak percobaan. Tunggu {e.seconds} detik"
            )
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error sending code: {e}")
            await update.message.reply_text("⚠️ Gagal mengirim kode verifikasi")
            return ConversationHandler.END
    
    async def code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle OTP code input"""
        user_id = update.effective_user.id
        
        if user_id not in pending_logins:
            await update.message.reply_text("❌ Tidak ada permintaan login aktif")
            return ConversationHandler.END
        
        # Extract digits from message
        code = ''.join(filter(str.isdigit, update.message.text))
        if len(code) != 5:
            await update.message.reply_text(
                "❌ Kode harus 5 digit!\n"
                "Contoh: `1 2 3 4 5`",
                parse_mode='Markdown'
            )
            return CODE
        
        login_data = pending_logins[user_id]
        
        try:
            # Sign in with code
            await user_client.sign_in(
                phone=login_data['phone'],
                code=code,
                phone_code_hash=login_data['phone_code_hash']
            )
            
            # Login successful
            del pending_logins[user_id]
            await update.message.reply_text(
                "✅ Login berhasil!\n"
                "UserBot siap digunakan. 🚀"
            )
            
            return ConversationHandler.END
            
        except SessionPasswordNeededError:
            # 2FA required
            await update.message.reply_text(
                "🔐 Akun Anda memiliki 2FA.\n"
                "Silakan masukkan password 2FA:"
            )
            return PASSWORD
            
        except PhoneCodeInvalidError:
            login_data['attempts'] += 1
            
            if login_data['attempts'] >= 3:
                del pending_logins[user_id]
                await update.message.reply_text(
                    "❌ Terlalu banyak percobaan gagal.\n"
                    "Silakan mulai ulang dengan /start"
                )
                return ConversationHandler.END
            else:
                remaining = 3 - login_data['attempts']
                await update.message.reply_text(
                    f"❌ Kode salah. Percobaan {login_data['attempts']}/3\n\n"
                    f"Sisa percobaan: {remaining}\n"
                    f"Coba kirim ulang kode: `1 2 3 4 5`",
                    parse_mode='Markdown'
                )
                return CODE
                
        except Exception as e:
            logger.error(f"Error during sign in: {e}")
            await update.message.reply_text("⚠️ Gagal login")
            return ConversationHandler.END
    
    async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 2FA password"""
        user_id = update.effective_user.id
        
        if user_id not in pending_logins:
            await update.message.reply_text("❌ Tidak ada permintaan login aktif")
            return ConversationHandler.END
        
        password = update.message.text
        
        try:
            # Sign in with password
            await user_client.sign_in(password=password)
            
            # Login successful
            del pending_logins[user_id]
            await update.message.reply_text(
                "✅ Login 2FA berhasil!\n"
                "UserBot siap digunakan. 🚀"
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error 2FA: {e}")
            await update.message.reply_text("❌ Password 2FA salah!")
            return PASSWORD
    
    async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /logout command"""
        user_id = update.effective_user.id
        
        if user_id != OWNER_ID:
            await update.message.reply_text("🚫 Akses ditolak!")
            return
        
        # Disconnect and delete session
        if user_client.is_connected():
            await user_client.disconnect()
        
        # Clear pending logins
        if user_id in pending_logins:
            del pending_logins[user_id]
        
        await update.message.reply_text(
            "✅ Berhasil logout!\n"
            "Gunakan /start untuk login dengan akun lain"
        )
    
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        user_id = update.effective_user.id
        
        if user_id in pending_logins:
            del pending_logins[user_id]
        
        await update.message.reply_text(
            "❌ Login dibatalkan.\n"
            "Gunakan /start untuk memulai lagi"
        )
        
        return ConversationHandler.END
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE: [
                MessageHandler(filters.CONTACT, phone_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)
            ],
            CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, code_handler)
            ],
            PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers to bot
    bot.add_handler(conv_handler)
    bot.add_handler(CommandHandler('logout', logout))
    
    logger.info("✅ Connect plugin loaded")