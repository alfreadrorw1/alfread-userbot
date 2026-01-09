"""
Connect Plugin untuk Alfread UserBot - Railway Compatible
Sistem connect sederhana untuk UserBot
"""

import logging
import asyncio
from telethon import events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from config import Config
from plugins.mongodb import db

logger = logging.getLogger(__name__)

# In-memory storage untuk pending logins (hanya untuk sementara)
pending_logins = {}
active_sessions = {}

async def register_plugin(client):
    """Register plugin connect"""
    
    @client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        """Handler untuk command /start"""
        user_id = event.sender_id
        
        # Cek apakah sudah login
        if user_id in active_sessions:
            await event.reply(
                "✅ **Anda sudah terhubung dengan UserBot!**\n\n"
                "Gunakan perintah `.help` untuk melihat daftar perintah yang tersedia."
            )
            return
        
        # Kirim menu connect
        buttons = [
            [Button.inline("🔗 Connect UserBot", data="connect_userbot")],
            [Button.inline("ℹ️ Bantuan", data="help_info")]
        ]
        
        await event.reply(
            "🤖 **Selamat datang di Alfread UserBot!**\n\n"
            "Saya adalah assistant bot untuk mengelola UserBot premium Anda.\n\n"
            "**Fitur Utama:**\n"
            "• Multi-session support\n"
            "• Plugin system modular\n"
            "• MongoDB database\n"
            "• Ready for Railway deployment\n\n"
            "Klik tombol di bawah untuk mulai:",
            buttons=buttons
        )
    
    @client.on(events.CallbackQuery(data=b'connect_userbot'))
    async def connect_handler(event):
        """Handler untuk tombol connect"""
        user_id = event.sender_id
        
        # Cek apakah user adalah owner
        if user_id != Config.OWNER_ID:
            await event.answer(
                "❌ Hanya owner yang bisa connect UserBot!",
                alert=True
            )
            return
        
        # Kirim instruksi login
        await event.edit(
            "🔑 **Login ke UserBot**\n\n"
            "Silakan pilih metode login:\n\n"
            "1. **Metode 1:** Kirim nomor telepon Anda\n"
            "   Contoh: `+6281234567890`\n\n"
            "2. **Metode 2:** Jika sudah punya session string,\n"
            "   kirim dengan format:\n"
            "   `.session your_session_string_here`\n\n"
            "Ketik `.cancel` untuk membatalkan.",
            buttons=[
                [Button.inline("❌ Batal", data="cancel_login")]
            ]
        )
        
        # Simpan state
        pending_logins[user_id] = {'state': 'awaiting_input'}
    
    @client.on(events.NewMessage(pattern=r'^\.cancel$'))
    async def cancel_handler(event):
        """Handler untuk cancel login"""
        user_id = event.sender_id
        
        if user_id in pending_logins:
            del pending_logins[user_id]
            await event.reply("❌ **Login dibatalkan.**")
    
    @client.on(events.NewMessage(pattern=r'^\+(?:[0-9] ?){6,14}[0-9]$'))
    async def phone_handler(event):
        """Handler untuk nomor telepon"""
        user_id = event.sender_id
        
        # Cek apakah user sedang dalam proses login
        if user_id not in pending_logins or pending_logins[user_id]['state'] != 'awaiting_input':
            return
        
        if user_id != Config.OWNER_ID:
            await event.reply("❌ Hanya owner yang bisa connect UserBot!")
            return
        
        phone = event.raw_text.strip()
        await process_phone_login(event, user_id, phone)
    
    @client.on(events.NewMessage(pattern=r'^\.session (.+)$'))
    async def session_handler(event):
        """Handler untuk session string"""
        user_id = event.sender_id
        
        if user_id != Config.OWNER_ID:
            await event.reply("❌ Hanya owner yang bisa connect UserBot!")
            return
        
        session_string = event.pattern_match.group(1)
        await process_session_string(event, user_id, session_string)
    
    @client.on(events.CallbackQuery(data=b'cancel_login'))
    async def cancel_callback_handler(event):
        """Handler untuk tombol cancel"""
        user_id = event.sender_id
        
        if user_id in pending_logins:
            del pending_logins[user_id]
        
        await event.edit(
            "❌ **Login dibatalkan.**\n\n"
            "Ketik /start untuk memulai lagi."
        )
    
    @client.on(events.CallbackQuery(data=b'help_info'))
    async def help_handler(event):
        """Handler untuk bantuan"""
        help_text = (
            "📖 **Bantuan Alfread UserBot**\n\n"
            "**Cara Connect UserBot:**\n"
            "1. Klik tombol 'Connect UserBot'\n"
            "2. Kirim nomor telepon (format internasional)\n"
            "   Contoh: +6281234567890\n"
            "3. Masukkan kode OTP yang dikirim ke Telegram Anda\n"
            "4. Jika ada 2FA, masukkan password 2FA\n\n"
            "**Perintah yang tersedia:**\n"
            "• `/start` - Mulai bot\n"
            "• `.ping` - Cek status bot\n"
            "• `.help` - Tampilkan bantuan\n\n"
            "**Untuk Railway Deployment:**\n"
            "Gunakan session string yang sudah digenerate:\n"
            "`.session your_session_string`"
        )
        
        await event.edit(
            help_text,
            buttons=[
                [Button.inline("🔙 Kembali", data="back_to_start")]
            ]
        )
    
    @client.on(events.CallbackQuery(data=b'back_to_start'))
    async def back_handler(event):
        """Handler untuk kembali ke start"""
        await start_handler(event)

async def process_phone_login(event, user_id, phone):
    """Proses login dengan nomor telepon"""
    try:
        # Buat client baru
        temp_client = event.client
        
        # Kirim code request
        sent = await temp_client.send_code_request(phone)
        
        # Simpan data pending
        pending_logins[user_id] = {
            'state': 'awaiting_otp',
            'phone': phone,
            'phone_code_hash': sent.phone_code_hash,
            'client': temp_client
        }
        
        await event.reply(
            f"📲 **Kode OTP telah dikirim ke {phone}**\n\n"
            "Silakan masukkan kode OTP yang Anda terima:\n"
            "**Format:** `12345` (5 digit tanpa spasi)\n\n"
            "Ketik `.cancel` untuk membatalkan."
        )
        
    except Exception as e:
        logger.error(f"Error sending code: {e}")
        await event.reply(f"❌ **Error:** {str(e)}")
        if user_id in pending_logins:
            del pending_logins[user_id]

async def process_session_string(event, user_id, session_string):
    """Proses login dengan session string"""
    try:
        # Buat client dengan session string
        from telethon.sessions import StringSession
        
        client = event.client
        temp_client = TelegramClient(
            StringSession(session_string),
            Config.API_ID,
            Config.API_HASH
        )
        
        await temp_client.connect()
        
        # Cek apakah session valid
        if not await temp_client.is_user_authorized():
            await event.reply("❌ **Session string tidak valid atau telah expired!**")
            await temp_client.disconnect()
            return
        
        # Simpan session ke database
        collection = db["user_sessions"]
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "session_string": session_string,
                "phone": "session_string",
                "connected_at": "datetime.now()",
                "updated_at": "datetime.now()"
            }},
            upsert=True
        )
        
        # Simpan di memory
        active_sessions[user_id] = {
            'client': temp_client,
            'connected_at': "datetime.now()"
        }
        
        me = await temp_client.get_me()
        await event.reply(
            f"✅ **Login berhasil dengan session string!**\n\n"
            f"**Nama:** {me.first_name}\n"
            f"**ID:** {me.id}\n"
            f"**Username:** @{me.username if me.username else 'Tidak ada'}\n\n"
            "UserBot sekarang siap digunakan!"
        )
        
        logger.info(f"User {user_id} connected via session string")
        
    except Exception as e:
        logger.error(f"Error processing session string: {e}")
        await event.reply(f"❌ **Error:** {str(e)}")

# Handler untuk OTP
@client.on(events.NewMessage(pattern=r'^\d{5}$'))
async def otp_handler(event):
    """Handler untuk kode OTP"""
    user_id = event.sender_id
    
    if user_id not in pending_logins or pending_logins[user_id]['state'] != 'awaiting_otp':
        return
    
    try:
        otp_code = event.raw_text.strip()
        data = pending_logins[user_id]
        
        # Coba sign in dengan OTP
        temp_client = data['client']
        
        try:
            await temp_client.sign_in(
                phone=data['phone'],
                code=otp_code,
                phone_code_hash=data['phone_code_hash']
            )
            
            # Success - dapatkan session string
            session_string = temp_client.session.save()
            
            # Simpan ke database
            collection = db["user_sessions"]
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "session_string": session_string,
                    "phone": data['phone'],
                    "connected_at": "datetime.now()",
                    "updated_at": "datetime.now()"
                }},
                upsert=True
            )
            
            # Simpan di memory
            active_sessions[user_id] = {
                'client': temp_client,
                'connected_at': "datetime.now()"
            }
            
            me = await temp_client.get_me()
            await event.reply(
                f"✅ **Login berhasil!**\n\n"
                f"**Nama:** {me.first_name}\n"
                f"**ID:** {me.id}\n"
                f"**Username:** @{me.username if me.username else 'Tidak ada'}\n\n"
                "UserBot sekarang siap digunakan!\n"
                "Gunakan `.help` untuk melihat perintah yang tersedia."
            )
            
            logger.info(f"User {user_id} successfully logged in")
            
        except SessionPasswordNeededError:
            # Butuh password 2FA
            pending_logins[user_id]['state'] = 'awaiting_password'
            await event.reply(
                "🔒 **Akun Anda memiliki 2FA**\n\n"
                "Silakan masukkan password 2FA:\n\n"
                "Ketik `.cancel` untuk membatalkan."
            )
            return
            
    except Exception as e:
        logger.error(f"Error during OTP verification: {e}")
        await event.reply(f"❌ **Error:** {str(e)}")
    
    finally:
        # Hapus pending state
        if user_id in pending_logins:
            del pending_logins[user_id]

# Handler untuk password 2FA
@client.on(events.NewMessage())
async def password_handler(event):
    """Handler untuk password 2FA"""
    user_id = event.sender_id
    
    if user_id not in pending_logins or pending_logins[user_id]['state'] != 'awaiting_password':
        return
    
    if event.raw_text.strip() == '.cancel':
        if user_id in pending_logins:
            del pending_logins[user_id]
        await event.reply("❌ **Login dibatalkan.**")
        return
    
    try:
        password = event.raw_text.strip()
        data = pending_logins[user_id]
        temp_client = data['client']
        
        # Coba sign in dengan password
        await temp_client.sign_in(password=password)
        
        # Success - dapatkan session string
        session_string = temp_client.session.save()
        
        # Simpan ke database
        collection = db["user_sessions"]
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "session_string": session_string,
                "phone": data['phone'],
                "connected_at": "datetime.now()",
                "updated_at": "datetime.now()",
                "has_2fa": True
            }},
            upsert=True
        )
        
        # Simpan di memory
        active_sessions[user_id] = {
            'client': temp_client,
            'connected_at': "datetime.now()"
        }
        
        me = await temp_client.get_me()
        await event.reply(
            f"✅ **Login dengan 2FA berhasil!**\n\n"
            f"**Nama:** {me.first_name}\n"
            f"**ID:** {me.id}\n"
            f"**Username:** @{me.username if me.username else 'Tidak ada'}\n\n"
            "UserBot sekarang siap digunakan!"
        )
        
        logger.info(f"User {user_id} successfully logged in with 2FA")
        
    except Exception as e:
        logger.error(f"Error during 2FA verification: {e}")
        await event.reply(f"❌ **Error:** Password salah atau {str(e)}")
    
    finally:
        # Hapus pending state
        if user_id in pending_logins:
            del pending_logins[user_id]

logger.info("✅ Connect plugin loaded")