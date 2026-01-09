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

def setup(bot_app: Application, user_client):
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
            me = await user_client.get_me()
            await update.message.reply_text(
                f"✅ Anda sudah login sebagai:\n"
                f"👤 {me.first_name}\n"
                f"📞 +{me.phone}\n\n"
                "Gunakan /logout untuk login dengan akun lain"
            )
            return ConversationHandler.END
        
        # Request phone number
        keyboard = [[
            KeyboardButton("📱 Bagikan Nomor Telepon", request_contact=True)
        ]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "📲 **LOGIN USERBOT**\n\n"
            "Silakan bagikan nomor telepon Anda:\n\n"
            "• Gunakan tombol di bawah ATAU\n"
            "• Ketik nomor dengan format: +62xxxxxxxxxx",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return PHONE
    
    async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone number input"""
        user_id = update.effective_user.id
        
        # Get phone number from contact or text
        phone = ""
        if update.message.contact:
            phone = f"+{update.message.contact.phone_number}"
            logger.info(f"Phone from contact: {phone}")
        elif update.message.text:
            phone = update.message.text.strip()
            logger.info(f"Phone from text: {phone}")
        
        # Validate phone format
        if not phone.startswith('+') or len(phone) < 10:
            await update.message.reply_text(
                "❌ **Format nomor tidak valid!**\n\n"
                "Gunakan format internasional:\n"
                "`+62xxxxxxxxxx`\n\n"
                "Contoh: `+6281234567890`",
                parse_mode='Markdown'
            )
            return PHONE
        
        try:
            # Ensure client is connected
            if not user_client.is_connected():
                await user_client.connect()
            
            # Send verification code
            logger.info(f"Sending code to {phone}")
            sent = await user_client.send_code_request(phone)
            
            # Store login data
            pending_logins[user_id] = {
                'phone': phone,
                'phone_code_hash': sent.phone_code_hash,
                'attempts': 0
            }
            
            await update.message.reply_text(
                "✅ **Kode verifikasi telah dikirim!**\n\n"
                "Silakan balas dengan format:\n"
                "```\n1 2 3 4 5\n```\n"
                "*(beri spasi antara angka)*",
                parse_mode='Markdown'
            )
            
            return CODE
            
        except PhoneNumberInvalidError:
            await update.message.reply_text("❌ **Nomor telepon tidak valid!**")
            return PHONE
        except FloodWaitError as e:
            minutes = e.seconds // 60
            await update.message.reply_text(
                f"⏳ **Terlalu banyak percobaan.**\n\n"
                f"Tunggu {minutes} menit sebelum mencoba lagi.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error sending code: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ **Gagal mengirim kode verifikasi**\n\n"
                "Coba lagi beberapa saat."
            )
            return ConversationHandler.END
    
    async def code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle OTP code input"""
        user_id = update.effective_user.id
        
        if user_id not in pending_logins:
            await update.message.reply_text("❌ Tidak ada permintaan login aktif")
            return ConversationHandler.END
        
        # Extract digits from message
        code = ''.join(filter(str.isdigit, update.message.text))
        logger.info(f"Received code: {code}")
        
        if len(code) != 5:
            await update.message.reply_text(
                "❌ **Kode harus 5 digit!**\n\n"
                "Contoh format:\n"
                "```\n1 2 3 4 5\n```\n"
                "```\n12345\n```",
                parse_mode='Markdown'
            )
            return CODE
        
        login_data = pending_logins[user_id]
        
        try:
            # Sign in with code
            logger.info(f"Attempting sign in for {login_data['phone']}")
            await user_client.sign_in(
                phone=login_data['phone'],
                code=code,
                phone_code_hash=login_data['phone_code_hash']
            )
            
            # Get user info
            me = await user_client.get_me()
            
            # Login successful
            del pending_logins[user_id]
            await update.message.reply_text(
                f"🎉 **LOGIN BERHASIL!**\n\n"
                f"👤 **Nama:** {me.first_name}\n"
                f"📞 **Nomor:** +{me.phone}\n"
                f"🆔 **ID:** `{me.id}`\n\n"
                f"UserBot siap digunakan! 🚀",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except SessionPasswordNeededError:
            # 2FA required
            logger.info("2FA required")
            await update.message.reply_text(
                "🔐 **Akun Anda memiliki 2FA.**\n\n"
                "Silakan masukkan password 2FA:",
                parse_mode='Markdown'
            )
            return PASSWORD
            
        except PhoneCodeInvalidError:
            login_data['attempts'] += 1
            logger.warning(f"Invalid code attempt {login_data['attempts']}")
            
            if login_data['attempts'] >= 3:
                del pending_logins[user_id]
                await update.message.reply_text(
                    "❌ **Terlalu banyak percobaan gagal.**\n\n"
                    "Silakan mulai ulang dengan /start",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            else:
                remaining = 3 - login_data['attempts']
                await update.message.reply_text(
                    f"❌ **Kode salah.** Percobaan {login_data['attempts']}/3\n\n"
                    f"**Sisa percobaan:** {remaining}\n\n"
                    f"Coba kirim ulang kode:\n"
                    f"```\n1 2 3 4 5\n```",
                    parse_mode='Markdown'
                )
                return CODE
                
        except Exception as e:
            logger.error(f"Error during sign in: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ **Gagal login**\n\n"
                "Coba mulai ulang dengan /start"
            )
            return ConversationHandler.END
    
    async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 2FA password"""
        user_id = update.effective_user.id
        
        if user_id not in pending_logins:
            await update.message.reply_text("❌ Tidak ada permintaan login aktif")
            return ConversationHandler.END
        
        password = update.message.text
        logger.info(f"Processing 2FA password")
        
        try:
            # Sign in with password
            await user_client.sign_in(password=password)
            
            # Get user info
            me = await user_client.get_me()
            
            # Login successful
            del pending_logins[user_id]
            await update.message.reply_text(
                f"🔓 **2FA BERHASIL!**\n\n"
                f"✅ Login berhasil sebagai:\n"
                f"👤 {me.first_name}\n"
                f"📞 +{me.phone}\n\n"
                f"UserBot siap digunakan! 🚀",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error 2FA: {e}")
            await update.message.reply_text(
                "❌ **Password 2FA salah!**\n\n"
                "Coba masukkan password lagi:"
            )
            return PASSWORD
    
    async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /logout command"""
        user_id = update.effective_user.id
        
        if user_id != OWNER_ID:
            await update.message.reply_text("🚫 Akses ditolak!")
            return
        
        # Clear pending logins
        if user_id in pending_logins:
            del pending_logins[user_id]
        
        # Disconnect and delete session
        if user_client.is_connected():
            await user_client.disconnect()
        
        # Delete session file
        import os
        session_file = f"{user_client.session.filename if hasattr(user_client.session, 'filename') else 'alfread.session'}"
        if os.path.exists(session_file):
            os.remove(session_file)
            logger.info(f"Deleted session file: {session_file}")
        
        await update.message.reply_text(
            "✅ **Berhasil logout!**\n\n"
            "Session telah dihapus.\n"
            "Gunakan /start untuk login dengan akun lain",
            parse_mode='Markdown'
        )
    
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        user_id = update.effective_user.id
        
        if user_id in pending_logins:
            del pending_logins[user_id]
        
        await update.message.reply_text(
            "❌ **Login dibatalkan.**\n\n"
            "Gunakan /start untuk memulai lagi",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /status command"""
        user_id = update.effective_user.id
        
        if user_id != OWNER_ID:
            await update.message.reply_text("🚫 Akses ditolak!")
            return
        
        status_messages = []
        
        # Check connection status
        if user_client.is_connected():
            status_messages.append("🔗 **Koneksi:** Terhubung")
        else:
            status_messages.append("🔗 **Koneksi:** Terputus")
        
        # Check login status
        try:
            is_auth = await user_client.is_user_authorized()
            status_messages.append("🔐 **Login:** " + ("✅" if is_auth else "❌"))
            
            if is_auth:
                me = await user_client.get_me()
                status_messages.append(f"👤 **User:** {me.first_name}")
                status_messages.append(f"📞 **Nomor:** +{me.phone}")
        except:
            status_messages.append("🔐 **Login:** Tidak diketahui")
        
        # Check pending logins
        status_messages.append(f"⏳ **Pending logins:** {len(pending_logins)}")
        
        response = "📊 **STATUS SISTEM**\n\n" + "\n".join(status_messages)
        await update.message.reply_text(response, parse_mode='Markdown')
    
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
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    # Add handlers to bot
    bot_app.add_handler(conv_handler)
    bot_app.add_handler(CommandHandler('logout', logout))
    bot_app.add_handler(CommandHandler('status', status))
    
    logger.info("✅ Connect plugin loaded")