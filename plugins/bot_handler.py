import json
import os
import re
import time
from datetime import datetime
from telethon import events, Button
from telethon.errors import SessionPasswordNeededError
from pymongo import MongoClient
from plugins.connect import (
    create_userbot_client,
    save_session_to_mongo,
    delete_session_from_mongo,
    pending_verifications,
    active_sessions,
    login_attempts,
    sessions_collection  # Import dari connect.py
)
from config import BOT_TOKEN, OWNER_ID, MONGO_URI

# Setup koneksi MongoDB tambahan untuk user data
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.get_database()
users_collection = db['users']  # Untuk menyimpan data pengguna
security_collection = db['security']  # Untuk data keamanan

def format_time_remaining(seconds):
    """Format waktu tersisa menjadi format yang mudah dibaca"""
    if seconds <= 0:
        return "waktu habis"
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if seconds > 0:
        parts.append(f"{seconds} detik")
    
    return " ".join(parts)

def save_user_data(user_id, phone=None, username=None):
    """Menyimpan data pengguna ke MongoDB"""
    try:
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {
                "phone": phone,
                "username": username,
                "last_login": datetime.now(),
                "updated_at": datetime.now()
            }},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"❌ Error saving user data: {e}")
        return False

def get_user_data(user_id):
    """Mengambil data pengguna dari MongoDB"""
    try:
        data = users_collection.find_one({"user_id": str(user_id)})
        return data or {}
    except:
        return {}

def save_security_data(user_id, login_method='phone', ip_address=None, user_agent=None):
    """Menyimpan data keamanan ke MongoDB"""
    try:
        security_collection.insert_one({
            "user_id": str(user_id),
            "login_method": login_method,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "login_time": datetime.now(),
            "timestamp": time.time()
        })
        return True
    except Exception as e:
        print(f"❌ Error saving security data: {e}")
        return False

def get_login_attempts_count(user_id, time_window=1800):
    """Menghitung jumlah percobaan login dalam waktu tertentu"""
    try:
        count = security_collection.count_documents({
            "user_id": str(user_id),
            "timestamp": {"$gt": time.time() - time_window},
            "event_type": "login_attempt"
        })
        return count
    except:
        return 0

def record_login_attempt(user_id):
    """Mencatat percobaan login"""
    try:
        security_collection.insert_one({
            "user_id": str(user_id),
            "event_type": "login_attempt",
            "timestamp": time.time(),
            "created_at": datetime.now()
        })
        return True
    except:
        return False

def get_session_info(user_id):
    """Mengambil info session dari MongoDB"""
    try:
        session_data = sessions_collection.find_one({"user_id": str(user_id)})
        if session_data:
            created_at = session_data.get('created_at', datetime.now())
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            age_seconds = (datetime.now() - created_at).total_seconds()
            hours = int(age_seconds // 3600)
            minutes = int((age_seconds % 3600) // 60)
            
            return {
                "age": f"{hours}h {minutes}m",
                "created_at": created_at,
                "is_valid": True
            }
    except Exception as e:
        print(f"❌ Error getting session info: {e}")
    
    return {"age": "Unknown", "created_at": None, "is_valid": False}

async def setup_bot_handlers(bot):
    """Setup semua handler untuk bot koneksi"""
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        user_id = event.sender_id
        
        # Cek apakah user sudah memiliki session aktif
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client and client.is_connected():
                buttons = [
                    [Button.inline("🔌 Disconnect", data="disconnect")],
                    [Button.inline("📊 Status", data="status")],
                    [Button.inline("🛠️ Commands", data="help_commands")]
                ]
                await event.reply(
                    "✅ **Anda sudah terhubung dengan UserBot!**\n\n"
                    "Gunakan command `.help` di UserBot untuk melihat perintah yang tersedia.\n"
                    "Command `.ping` untuk test koneksi.",
                    buttons=buttons
                )
                return
        
        # Menu utama
        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")],
            [Button.inline("📋 Daftar Perintah", data="help")],
            [Button.inline("ℹ️ Tentang", data="about")]
        ]
        
        await event.reply(
            "🤖 **UserBot Connection Bot**\n\n"
            "Gunakan bot ini untuk menghubungkan akun Telegram Anda sebagai UserBot.\n"
            "Pilih opsi di bawah:",
            buttons=buttons
        )

    @bot.on(events.NewMessage(pattern='/login'))
    async def login_command_handler(event):
        """Handler untuk command /login"""
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client and client.is_connected():
                await event.reply("⚠️ **Anda sudah login!**\nGunakan /status untuk melihat status.")
                return
        
        # Cek percobaan login
        attempts = get_login_attempts_count(user_id)
        if attempts >= 3:
            await event.reply("🚫 **Terlalu banyak percobaan login!**\nCoba lagi dalam 30 menit.")
            return
        
        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")],
            [Button.inline("↩️ Kembali", data="back_to_main")]
        ]
        
        await event.reply(
            "🔑 **Login UserBot**\n\n"
            "Pilih metode login:",
            buttons=buttons
        )

    @bot.on(events.NewMessage(pattern='/logout'))
    async def logout_command_handler(event):
        """Handler untuk command /logout"""
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            try:
                await client.disconnect()
            except:
                pass
            del active_sessions[user_id]
        
        # Hapus session dari MongoDB
        delete_session_from_mongo(user_id)
        
        await event.reply("✅ **Berhasil logout!**\nUserBot telah terputus.")

    @bot.on(events.NewMessage(pattern='/status'))
    async def status_command_handler(event):
        """Handler untuk command /status"""
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client and client.is_connected():
                try:
                    me = await client.get_me()
                    user_name = me.first_name
                    username = f"@{me.username}" if me.username else "No Username"
                except:
                    user_name = "Unknown"
                    username = "Unknown"
                
                # Get session info dari MongoDB
                session_info = get_session_info(user_id)
                
                status_msg = (
                    "📊 **Status UserBot**\n\n"
                    f"🟢 **Status:** Connected\n"
                    f"👤 **Nama:** {user_name}\n"
                    f"📱 **Username:** {username}\n"
                    f"⏰ **Session Age:** {session_info['age']}\n"
                    f"🆔 **User ID:** `{user_id}`"
                )
            else:
                status_msg = "📊 **Status UserBot**\n\n🔴 **Status:** Disconnected"
        else:
            status_msg = "📊 **Status UserBot**\n\n🔴 **Status:** Not logged in"
        
        await event.reply(status_msg)

    @bot.on(events.CallbackQuery(data=b'phone_login'))
    async def phone_login_handler(event):
        user_id = event.sender_id
        
        # Cek cooldown login attempts
        attempts = get_login_attempts_count(user_id)
        if attempts >= 3:
            await event.answer("🚫 Terlalu banyak percobaan! Coba lagi dalam 30 menit.", alert=True)
            return
        
        buttons = [
            [Button.inline("📱 Bagikan Nomor Telepon", data="share_phone")],
            [Button.inline("↩️ Kembali", data="back_to_main")]
        ]
        
        await event.edit(
            "📱 **Login dengan Nomor Telepon**\n\n"
            "Silakan klik tombol di bawah untuk berbagi nomor telepon Anda:",
            buttons=buttons
        )

    @bot.on(events.CallbackQuery(data=b'share_phone'))
    async def share_phone_handler(event):
        user_id = event.sender_id
        
        # Cek percobaan login
        attempts = get_login_attempts_count(user_id)
        if attempts >= 3:
            await event.answer("🚫 Terlalu banyak percobaan! Coba lagi dalam 30 menit.", alert=True)
            return
        
        # Catat percobaan login
        record_login_attempt(user_id)
        
        # Kirim pesan dengan request phone button
        await event.edit(
            "🔑 **Premium UserBot Connect**\n\n"
            "Silakan bagikan nomor telepon Anda untuk memulai:",
            buttons=[Button.request_phone("📱 Bagikan Nomor", resize=True)]
        )
        
        pending_verifications[user_id] = {
            'method': 'phone',
            'attempts': 0,
            'timestamp': time.time()
        }

    @bot.on(events.CallbackQuery(data=b'disconnect'))
    async def disconnect_handler(event):
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            try:
                await client.disconnect()
            except:
                pass
            del active_sessions[user_id]
        
        # Hapus session dari MongoDB
        delete_session_from_mongo(user_id)
        
        await event.edit("✅ **UserBot telah terputus!**\nGunakan /start untuk login kembali.")

    @bot.on(events.CallbackQuery(data=b'status'))
    async def status_handler(event):
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            status = "🟢 Terhubung" if client.is_connected() else "🔴 Terputus"
            
            # Get session info
            session_info = get_session_info(user_id)
            
            message = (
                f"📊 **Status UserBot**\n\n"
                f"🟢 Status: {status}\n"
                f"⏰ Session Age: {session_info['age']}"
            )
        else:
            message = "📊 **Status UserBot**\n\n🔴 Status: Tidak ada session aktif"
        
        buttons = [
            [Button.inline("🔌 Disconnect", data="disconnect")],
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(message, buttons=buttons)

    @bot.on(events.CallbackQuery(data=b'help_commands'))
    async def help_commands_handler(event):
        help_text = (
            "🛠️ **UserBot Commands**\n\n"
            "**Basic Commands:**\n"
            "`.ping` - Cek kecepatan koneksi\n"
            "`.alive` - Cek status userbot\n"
            "`.help` - Tampilkan semua perintah\n\n"
            "**Utility Commands:**\n"
            "`.id` - Dapatkan ID chat/user\n"
            "`.info` - Info tentang user\n"
            "`.stats` - Statistik userbot\n\n"
            "**Bot Commands:**\n"
            "/start - Mulai bot\n"
            "/login - Login ke userbot\n"
            "/logout - Logout dari userbot\n"
            "/status - Cek status koneksi"
        )
        
        buttons = [
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(help_text, buttons=buttons)

    @bot.on(events.CallbackQuery(data=b'help'))
    async def help_handler(event):
        help_text = (
            "📋 **Daftar Perintah**\n\n"
            "**Bot Commands:**\n"
            "/start - Memulai bot\n"
            "/login - Mulai proses login\n"
            "/logout - Keluar dari userbot\n"
            "/status - Cek status userbot\n"
            "/ping - Cek kecepatan bot\n\n"
            "**UserBot Commands:**\n"
            ".help - Tampilkan bantuan userbot\n"
            ".ping - Cek kecepatan userbot\n"
            ".alive - Cek status userbot\n"
            ".id - Dapatkan ID chat/user\n\n"
            "**Login Guide:**\n"
            "1. Klik 'Login dengan Nomor'\n"
            "2. Bagikan nomor telepon\n"
            "3. Masukkan kode OTP\n"
            "4. Selesai! UserBot siap"
        )
        
        buttons = [
            [Button.inline("🛠️ UserBot Commands", data="help_commands")],
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(help_text, buttons=buttons)

    @bot.on(events.CallbackQuery(data=b'about'))
    async def about_handler(event):
        about_text = (
            "🤖 **Alfread UserBot**\n\n"
            "**Versi:** 1.0.0\n"
            "**Developer:** AlfreadRorw\n"
            "**Framework:** Telethon\n"
            "**Database:** MongoDB\n\n"
            "**Fitur:**\n"
            "• Multi-user support\n"
            "• MongoDB session storage\n"
            "• Auto-reconnect\n"
            "• Plugin system\n"
            "• Premium features\n\n"
            "**Support:** @AlfreadRorw"
        )
        
        buttons = [
            [Button.url("💬 Support", "https://t.me/AlfreadRorw")],
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(about_text, buttons=buttons)

    @bot.on(events.CallbackQuery(data=b'back_to_main'))
    async def back_to_main_handler(event):
        user_id = event.sender_id
        
        # Cek status login
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client and client.is_connected():
                buttons = [
                    [Button.inline("🔌 Disconnect", data="disconnect")],
                    [Button.inline("📊 Status", data="status")],
                    [Button.inline("🛠️ Commands", data="help_commands")]
                ]
                await event.edit(
                    "✅ **Anda sudah terhubung dengan UserBot!**\n\n"
                    "Gunakan command `.help` di UserBot untuk melihat perintah yang tersedia.\n"
                    "Command `.ping` untuk test koneksi.",
                    buttons=buttons
                )
                return
        
        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")],
            [Button.inline("📋 Daftar Perintah", data="help")],
            [Button.inline("ℹ️ Tentang", data="about")]
        ]
        
        await event.edit(
            "🤖 **UserBot Connection Bot**\n\n"
            "Gunakan bot ini untuk menghubungkan akun Telegram Anda sebagai UserBot.\n"
            "Pilih opsi di bawah:",
            buttons=buttons
        )

    @bot.on(events.NewMessage(func=lambda e: e.message.contact))
    async def contact_handler(event):
        user_id = event.sender_id
        contact = event.message.contact
        
        if contact.user_id == user_id:
            phone = f"+{contact.phone_number}"
            
            try:
                await event.delete()
            except:
                pass
            
            if user_id not in pending_verifications:
                await event.reply("⚠️ **Sesi login telah kadaluarsa!**\nGunakan /start untuk memulai ulang.")
                return
            
            # Simpan data user ke MongoDB
            save_user_data(user_id, phone=phone)
            
            # Proses login
            await process_phone_login(event, phone, user_id)

    async def process_phone_login(event, phone, user_id):
        try:
            # Buat client baru
            client = create_userbot_client(user_id)
            await client.connect()
            
            # Kirim kode OTP
            sent_code = await client.send_code_request(phone)
            
            # Simpan data verifikasi
            pending_verifications[user_id].update({
                'client': client,
                'phone': phone,
                'phone_code_hash': sent_code.phone_code_hash,
                'timestamp': time.time()
            })
            
            await event.reply(
                "📲 **Kode verifikasi terkirim!**\n\n"
                "Masukkan kode OTP yang diterima via Telegram dengan format:\n"
                "`1 2 3 4 5` (5 digit dipisahkan spasi)\n\n"
                "⚠️ **Catatan:**\n"
                "• Kode OTP hanya berlaku 5 menit\n"
                "• Jika akun memiliki 2FA, masukkan sandi setelah OTP berhasil"
            )
            
        except Exception as e:
            await event.reply(f"❌ **Error:** {str(e)}")

    @bot.on(events.NewMessage(func=lambda e: e.is_private))
    async def message_handler(event):
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        if event.message.contact:
            return
        
        # Cek apakah ini OTP code
        if user_id in pending_verifications and re.match(r'^\d{1} \d{1} \d{1} \d{1} \d{1}$', text):
            await handle_otp_code(event, text, user_id)
        # Cek apakah ini password 2FA
        elif user_id in pending_verifications and pending_verifications[user_id].get('needs_password'):
            await handle_password(event, text, user_id)
        elif text.lower() == '/logout':
            await logout_command_handler(event)
        elif text.lower() == '/status':
            await status_command_handler(event)
        elif text.lower() == '/ping':
            # Bot ping handler
            start_time = time.time()
            msg = await event.reply("🏓 Pinging...")
            latency = (time.time() - start_time) * 1000
            await msg.edit(f"🏓 **Pong!**\n⚡ Speed: {latency:.2f} ms")

    async def handle_otp_code(event, text, user_id):
        code = ''.join(text.split())
        verification = pending_verifications[user_id]
        
        try:
            client = verification['client']
            await client.sign_in(
                phone=verification['phone'],
                code=code,
                phone_code_hash=verification['phone_code_hash']
            )
            
            # Login berhasil
            await complete_login(event, user_id, client)
            
        except SessionPasswordNeededError:
            verification['needs_password'] = True
            await event.reply(
                "🔒 **Akun Anda memiliki verifikasi 2 langkah**\n\n"
                "Silakan masukkan sandi verifikasi 2 langkah Anda:"
            )
        except Exception as e:
            verification['attempts'] += 1
            
            if verification['attempts'] >= 3:
                # Reset login attempts
                del pending_verifications[user_id]
                await event.reply(
                    "🚫 **Terlalu banyak percobaan OTP gagal!**\n\n"
                    "Silakan mulai ulang dengan /start"
                )
            else:
                await event.reply(
                    f"❌ **Kode OTP salah!**\n"
                    f"Percobaan {verification['attempts']} dari 3"
                )

    async def handle_password(event, text, user_id):
        verification = pending_verifications[user_id]
        
        try:
            client = verification['client']
            await client.sign_in(password=text)
            
            # Login berhasil
            await complete_login(event, user_id, client)
            
        except Exception as e:
            verification['attempts'] += 1
            
            if verification['attempts'] >= 3:
                del pending_verifications[user_id]
                await event.reply(
                    "🚫 **Terlalu banyak percobaan sandi gagal!**\n\n"
                    "Silakan mulai ulang dengan /start"
                )
            else:
                await event.reply(
                    f"❌ **Sandi salah!**\n"
                    f"Percobaan {verification['attempts']} dari 3"
                )

    async def complete_login(event, user_id, client):
        try:
            # Simpan session string ke MongoDB
            session_string = client.session.save()
            save_session_to_mongo(user_id, session_string)
            
            # Simpan ke active sessions
            active_sessions[user_id] = client
            
            # Add ping handler ke client yang baru connect
            from plugins.ping import add_ping_handler_to_client
            await add_ping_handler_to_client(client, user_id)
            
            # Simpan data keamanan ke MongoDB
            save_security_data(user_id, login_method='phone')
            
            # Simpan data user lengkap
            try:
                me = await client.get_me()
                save_user_data(user_id, 
                             phone=pending_verifications[user_id]['phone'],
                             username=me.username)
            except:
                pass
            
            # Hapus pending verification
            del pending_verifications[user_id]
            
            buttons = [
                [Button.inline("🔌 Disconnect", data="disconnect")],
                [Button.inline("📊 Status", data="status")],
                [Button.inline("🛠️ Commands", data="help_commands")]
            ]
            
            await event.reply(
                "✅ **Login berhasil!**\n\n"
                "UserBot sekarang aktif dan siap digunakan.\n"
                "Gunakan command `.help` untuk melihat daftar perintah.\n"
                "Command `.ping` untuk test koneksi userbot.",
                buttons=buttons
            )
            
        except Exception as e:
            await event.reply(f"❌ **Error saat menyelesaikan login:** {str(e)}")