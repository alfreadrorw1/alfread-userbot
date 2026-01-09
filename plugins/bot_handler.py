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
    sessions_collection,
    auto_restore_connections,
    get_user_session
)
from config import BOT_TOKEN, OWNER_ID, MONGO_URI

# Setup koneksi MongoDB tambahan untuk user data
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.get_database()
users_collection = db['users']

def save_user_data(user_id, phone=None, username=None, auto_connect=False):
    """Menyimpan data pengguna ke MongoDB"""
    try:
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {
                "phone": phone,
                "username": username,
                "last_login": datetime.now(),
                "updated_at": datetime.now(),
                "auto_connect": auto_connect
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
                "is_valid": True,
                "auto_connect": session_data.get('auto_connect', False)
            }
    except Exception as e:
        print(f"❌ Error getting session info: {e}")
    
    return {"age": "Unknown", "created_at": None, "is_valid": False, "auto_connect": False}

async def setup_bot_handlers(bot):
    """Setup semua handler untuk bot koneksi"""
    
    # Auto-restore saat bot dimulai
    print("🚀 Memulai auto-restore koneksi...")
    await auto_restore_connections(bot)
    
    # Variabel untuk melacak pesan yang sedang diproses
    processing_messages = set()
    
    @bot.on(events.NewMessage(pattern=r'^/start$'))  # Pattern yang lebih spesifik
    async def start_handler(event):
        """Handler untuk /start command"""
        message_id = (event.chat_id, event.id)
        
        # Cek apakah pesan sedang diproses
        if message_id in processing_messages:
            return
        processing_messages.add(message_id)
        
        try:
            user_id = event.sender_id
            
            # Cek apakah user sudah memiliki session aktif
            if user_id in active_sessions:
                client = active_sessions[user_id]
                if client and client.is_connected():
                    # Get session info
                    session_info = get_session_info(user_id)
                    auto_status = "✅ AKTIF" if session_info.get('auto_connect') else "❌ NON-AKTIF"
                    
                    buttons = [
                        [Button.inline("🔌 Disconnect", data="disconnect")],
                        [Button.inline("📊 Status", data="status")],
                        [Button.inline("⚙️ Pengaturan", data="settings")],
                        [Button.inline("🛠️ Commands", data="help_commands")]
                    ]
                    
                    # Gunakan respond bukan reply untuk menghindari double
                    await event.respond(
                        f"✅ **Anda sudah terhubung dengan UserBot!**\n\n"
                        f"**Auto-connect:** {auto_status}\n"
                        f"Gunakan command `.help` di UserBot untuk melihat perintah yang tersedia.\n"
                        f"Command `.ping` untuk test koneksi.",
                        buttons=buttons
                    )
                    return
            
            # Menu utama
            buttons = [
                [Button.inline("📱 Login dengan Nomor", data="phone_login")],
                [Button.inline("📋 Daftar Perintah", data="help")],
                [Button.inline("ℹ️ Tentang", data="about")]
            ]
            
            await event.respond(
                "🤖 **UserBot Connection Bot**\n\n"
                "Gunakan bot ini untuk menghubungkan akun Telegram Anda sebagai UserBot.\n"
                "Pilih opsi di bawah:",
                buttons=buttons
            )
            
        finally:
            # Hapus dari processing setelah selesai
            if message_id in processing_messages:
                processing_messages.remove(message_id)

    @bot.on(events.NewMessage(pattern=r'^/login$'))
    async def login_command_handler(event):
        """Handler untuk command /login"""
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client and client.is_connected():
                await event.respond("⚠️ **Anda sudah login!**\nGunakan /status untuk melihat status.")
                return
        
        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")],
            [Button.inline("↩️ Kembali", data="back_to_main")]
        ]
        
        await event.respond(
            "🔑 **Login UserBot**\n\n"
            "Pilih metode login:",
            buttons=buttons
        )

    @bot.on(events.NewMessage(pattern=r'^/logout$'))
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
        
        await event.respond("✅ **Berhasil logout!**\nUserBot telah terputus.")

    @bot.on(events.NewMessage(pattern=r'^/status$'))
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
                auto_status = "🟢 AKTIF" if session_info.get('auto_connect') else "🔴 NON-AKTIF"
                
                auto_text = f"\n🔄 **Auto-connect:** {auto_status}"
                
                status_msg = (
                    f"📊 **Status UserBot**{auto_text}\n\n"
                    f"🟢 **Status:** Connected\n"
                    f"👤 **Nama:** {user_name}\n"
                    f"📱 **Username:** {username}\n"
                    f"⏰ **Session Age:** {session_info['age']}\n"
                    f"🆔 **User ID:** `{user_id}`"
                )
            else:
                status_msg = "📊 **Status UserBot**\n\n🔴 **Status:** Disconnected"
        else:
            # Cek apakah ada session di database
            session_data = get_user_session(user_id)
            if session_data:
                status_msg = "📊 **Status UserBot**\n\n🟡 **Status:** Session tersimpan (tidak aktif)\nGunakan /login untuk menghubungkan kembali."
            else:
                status_msg = "📊 **Status UserBot**\n\n🔴 **Status:** Not logged in"
        
        await event.respond(status_msg)

    @bot.on(events.NewMessage(pattern=r'^/autoconnect$'))
    async def autoconnect_handler(event):
        """Handler untuk mengatur auto-connect"""
        user_id = event.sender_id
        
        if user_id not in active_sessions:
            await event.respond("❌ **Anda belum login!**\nLogin terlebih dahulu dengan /login")
            return
        
        # Get current auto-connect status
        user_data = get_user_data(user_id)
        current_status = user_data.get('auto_connect', False)
        
        if current_status:
            # Matikan auto-connect
            save_user_data(user_id, auto_connect=False)
            sessions_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {"auto_connect": False}}
            )
            await event.respond("✅ **Auto-connect dimatikan!**\nUserBot tidak akan otomatis terhubung saat restart.")
        else:
            # Aktifkan auto-connect
            save_user_data(user_id, auto_connect=True)
            sessions_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {"auto_connect": True}}
            )
            await event.respond("✅ **Auto-connect diaktifkan!**\nUserBot akan otomatis terhubung saat bot restart.")

    @bot.on(events.CallbackQuery(data=b'phone_login'))
    async def phone_login_handler(event):
        user_id = event.sender_id
        
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
        
        await event.edit(
            "🔑 **Premium UserBot Connect**\n\n"
            "Silakan bagikan nomor telepon Anda untuk memulai:",
            buttons=[Button.request_phone("📱 Bagikan Nomor", resize=True)]
        )
        
        pending_verifications[user_id] = {
            'method': 'phone',
            'attempts': 0,
            'timestamp': time.time(),
            'auto_connect': False
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
            auto_status = "✅ AKTIF" if session_info.get('auto_connect') else "❌ NON-AKTIF"
            
            auto_text = f"\n🔄 **Auto-connect:** {auto_status}"
            
            message = (
                f"📊 **Status UserBot**{auto_text}\n\n"
                f"🟢 Status: {status}\n"
                f"⏰ Session Age: {session_info['age']}"
            )
        else:
            message = "📊 **Status UserBot**\n\n🔴 Status: Tidak ada session aktif"
        
        buttons = [
            [Button.inline("🔌 Disconnect", data="disconnect")],
            [Button.inline("🔄 Auto-connect", data="toggle_autoconnect")],
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(message, buttons=buttons)

    @bot.on(events.CallbackQuery(data=b'toggle_autoconnect'))
    async def toggle_autoconnect_handler(event):
        user_id = event.sender_id
        
        if user_id not in active_sessions:
            await event.answer("❌ Anda belum terhubung!", alert=True)
            return
        
        # Get current status
        user_data = get_user_data(user_id)
        current_status = user_data.get('auto_connect', False)
        
        if current_status:
            # Matikan auto-connect
            save_user_data(user_id, auto_connect=False)
            sessions_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {"auto_connect": False}}
            )
            await event.answer("✅ Auto-connect dimatikan!", alert=True)
        else:
            # Aktifkan auto-connect
            save_user_data(user_id, auto_connect=True)
            sessions_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {"auto_connect": True}}
            )
            await event.answer("✅ Auto-connect diaktifkan!", alert=True)
        
        # Refresh status view
        await status_handler(event)

    @bot.on(events.CallbackQuery(data=b'settings'))
    async def settings_handler(event):
        user_id = event.sender_id
        
        # Get current settings
        user_data = get_user_data(user_id)
        auto_connect_status = user_data.get('auto_connect', False)
        auto_text = "✅ AKTIF" if auto_connect_status else "❌ NON-AKTIF"
        
        settings_text = (
            f"⚙️ **Pengaturan UserBot**\n\n"
            f"🔄 **Auto-connect:** {auto_text}\n"
            f"• UserBot akan otomatis terhubung saat restart\n\n"
            f"📱 **Session:** {len(active_sessions)} aktif\n\n"
            f"**Commands:**\n"
            f"/autoconnect - Toggle auto-connect\n"
            f"/status - Lihat status lengkap"
        )
        
        buttons = [
            [Button.inline("🔄 Toggle Auto-connect", data="toggle_autoconnect")],
            [Button.inline("📊 Status", data="status")],
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(settings_text, buttons=buttons)

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
            "/status - Cek status koneksi\n"
            "/autoconnect - Atur auto-connect"
        )
        
        buttons = [
            [Button.inline("⚙️ Pengaturan", data="settings")],
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
            "/ping - Cek kecepatan bot\n"
            "/autoconnect - Atur koneksi otomatis\n\n"
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
            [Button.inline("⚙️ Pengaturan", data="settings")],
            [Button.inline("🔙 Kembali", data="back_to_main")]
        ]
        
        await event.edit(help_text, buttons=buttons)

    @bot.on(events.CallbackQuery(data=b'about'))
    async def about_handler(event):
        about_text = (
            "🤖 **Alfread UserBot**\n\n"
            "**Versi:** 2.0.0\n"
            "**Developer:** AlfreadRorw\n"
            "**Framework:** Telethon\n"
            "**Database:** MongoDB\n\n"
            "**Fitur Baru:**\n"
            "• Auto-connect system\n"
            "• Session persistence\n"
            "• Multi-user support\n"
            "• MongoDB session storage\n"
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
                # Get session info
                session_info = get_session_info(user_id)
                auto_status = "✅ AKTIF" if session_info.get('auto_connect') else "❌ NON-AKTIF"
                
                buttons = [
                    [Button.inline("🔌 Disconnect", data="disconnect")],
                    [Button.inline("📊 Status", data="status")],
                    [Button.inline("⚙️ Pengaturan", data="settings")],
                    [Button.inline("🛠️ Commands", data="help_commands")]
                ]
                
                await event.edit(
                    f"✅ **Anda sudah terhubung dengan UserBot!**\n\n"
                    f"**Auto-connect:** {auto_status}\n"
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
                await event.respond("⚠️ **Sesi login telah kadaluarsa!**\nGunakan /start untuk memulai ulang.")
                return
            
            # Dapatkan auto-connect setting dari pending verification
            auto_connect = pending_verifications[user_id].get('auto_connect', False)
            
            # Simpan data user ke MongoDB
            save_user_data(user_id, phone=phone, auto_connect=auto_connect)
            
            # Proses login
            await process_phone_login(event, phone, user_id, auto_connect)

    async def process_phone_login(event, phone, user_id, auto_connect=False):
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
                'timestamp': time.time(),
                'auto_connect': auto_connect
            })
            
            await event.respond(
                "📲 **Kode verifikasi terkirim!**\n\n"
                "Masukkan kode OTP yang diterima via Telegram dengan format:\n"
                "`1 2 3 4 5` (5 digit dipisahkan spasi)\n\n"
                "⚠️ **Catatan:**\n"
                "• Kode OTP hanya berlaku 5 menit\n"
                "• Jika akun memiliki 2FA, masukkan sandi setelah OTP berhasil"
            )
            
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}")

    # Handler untuk pesan privat dengan pattern yang lebih spesifik
    @bot.on(events.NewMessage(
        pattern=r'^\d{1} \d{1} \d{1} \d{1} \d{1}$',  # Pattern untuk OTP
        func=lambda e: e.is_private
    ))
    async def otp_handler(event):
        """Handler khusus untuk OTP code"""
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        if user_id in pending_verifications:
            await handle_otp_code(event, text, user_id)
    
    @bot.on(events.NewMessage(
        pattern=r'.+',  # Pattern umum
        func=lambda e: e.is_private and not e.message.contact
    ))
    async def private_message_handler(event):
        """Handler untuk semua pesan privat lainnya"""
        user_id = event.sender_id
        text = event.raw_text.strip().lower()
        
        # Skip jika ini OTP (sudah ditangani oleh otp_handler)
        if re.match(r'^\d{1} \d{1} \d{1} \d{1} \d{1}$', text):
            return
        
        # Cek apakah ini password 2FA
        if user_id in pending_verifications and pending_verifications[user_id].get('needs_password'):
            await handle_password(event, text, user_id)
        elif text == '/logout':
            await logout_command_handler(event)
        elif text == '/status':
            await status_command_handler(event)
        elif text == '/ping':
            # Bot ping handler
            start_time = time.time()
            msg = await event.respond("🏓 Pinging...")
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
            await complete_login(event, user_id, client, verification)
            
        except SessionPasswordNeededError:
            verification['needs_password'] = True
            await event.respond(
                "🔒 **Akun Anda memiliki verifikasi 2 langkah**\n\n"
                "Silakan masukkan sandi verifikasi 2 langkah Anda:"
            )
        except Exception as e:
            verification['attempts'] += 1
            
            if verification['attempts'] >= 3:
                # Reset login attempts
                del pending_verifications[user_id]
                await event.respond(
                    "🚫 **Terlalu banyak percobaan OTP gagal!**\n\n"
                    "Silakan mulai ulang dengan /start"
                )
            else:
                await event.respond(
                    f"❌ **Kode OTP salah!**\n"
                    f"Percobaan {verification['attempts']} dari 3"
                )

    async def handle_password(event, text, user_id):
        verification = pending_verifications[user_id]
        
        try:
            client = verification['client']
            await client.sign_in(password=text)
            
            # Login berhasil
            await complete_login(event, user_id, client, verification)
            
        except Exception as e:
            verification['attempts'] += 1
            
            if verification['attempts'] >= 3:
                del pending_verifications[user_id]
                await event.respond(
                    "🚫 **Terlalu banyak percobaan sandi gagal!**\n\n"
                    "Silakan mulai ulang dengan /start"
                )
            else:
                await event.respond(
                    f"❌ **Sandi salah!**\n"
                    f"Percobaan {verification['attempts']} dari 3"
                )

    async def complete_login(event, user_id, client, verification):
        try:
            # Dapatkan auto-connect setting
            auto_connect = verification.get('auto_connect', False)
            
            # Simpan session string ke MongoDB dengan auto-connect flag
            session_string = client.session.save()
            save_session_to_mongo(user_id, session_string, auto_connect)
            
            # Simpan ke active sessions
            active_sessions[user_id] = client
            
            # AUTO-LOAD SEMUA PLUGINS menggunakan sistem baru
            from plugins import auto_load_all_plugins_for_client
            await auto_load_all_plugins_for_client(client, user_id)
            
            # Simpan data user lengkap
            try:
                me = await client.get_me()
                save_user_data(user_id, 
                             phone=verification['phone'],
                             username=me.username,
                             auto_connect=auto_connect)
            except:
                pass
            
            # Hapus pending verification
            del pending_verifications[user_id]
            
            auto_text = "\n🔄 **Auto-connect: AKTIF**" if auto_connect else ""
            
            buttons = [
                [Button.inline("🔌 Disconnect", data="disconnect")],
                [Button.inline("📊 Status", data="status")],
                [Button.inline("⚙️ Pengaturan", data="settings")],
                [Button.inline("🛠️ Commands", data="help_commands")]
            ]
            
            await event.respond(
                f"✅ **Login berhasil!**{auto_text}\n\n"
                "UserBot sekarang aktif dan siap digunakan.\n"
                "Gunakan command `.help` untuk melihat daftar perintah.\n"
                "Command `.ping` untuk test koneksi userbot.",
                buttons=buttons
            )
                
        except Exception as e:
            await event.respond(f"❌ **Error saat menyelesaikan login:** {str(e)}")