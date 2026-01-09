import re
from pymongo import MongoClient
from telethon import events
from plugins.connect import client, login_userbot_via_bot
from config import OWNER_ID, SESSION_NAME, MODE

# Temporary storage for login state
login_states = {}

class LoginState:
    def __init__(self, user_id):
        self.user_id = user_id
        self.phone = None
        self.phone_code_hash = None
        self.waiting_for = "phone"  # phone, code, password

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != OWNER_ID:
        await event.reply("❌ Kamu bukan owner")
        return
    
    if MODE == "bot":
        await event.reply("🤖 Bot mode aktif!\nGunakan /ping untuk test")
        return
    
    # Userbot mode - check if already logged in
    mongo = MongoClient(login_states.get("MONGO_URI"))
    session_data = mongo.get_database()["telethon_sessions"].find_one({"session": SESSION_NAME})
    
    if session_data and b"main" in session_data:
        await event.reply("✅ Userbot sudah login dan aktif!")
    else:
        login_states[event.sender_id] = LoginState(event.sender_id)
        await event.reply(
            "🔐 **Login Userbot**\n\n"
            "Kirim nomor Telegram kamu dengan format:\n"
            "`+628xxxxxxxxx`\n\n"
            "Contoh: `+6281234567890`"
        )

@client.on(events.NewMessage(pattern=r'^\+[1-9]\d{9,14}$'))
async def phone_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    state = login_states.get(event.sender_id)
    if not state or state.waiting_for != "phone":
        return
    
    phone = event.text.strip()
    
    # Validate phone format
    if not re.match(r'^\+[1-9]\d{9,14}$', phone):
        await event.reply("❌ Format nomor salah! Gunakan format: +628xxxxxxxxx")
        return
    
    # Store phone and request OTP
    state.phone = phone
    state.waiting_for = "code"
    
    result = await login_userbot_via_bot(phone=phone)
    
    if result == "code_sent":
        await event.reply(
            "📱 **OTP Dikirim**\n\n"
            "Kode OTP sudah dikirim ke nomor kamu.\n"
            "Kirim OTP dengan format:\n"
            "`1 2 3 4 5`\n\n"
            "Contoh: `1 2 3 4 5 6`"
        )
    else:
        await event.reply(f"❌ Gagal mengirim OTP: {result}")
        del login_states[event.sender_id]

@client.on(events.NewMessage(pattern=r'^(\d\s?){5,6}$'))
async def otp_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    state = login_states.get(event.sender_id)
    if not state or state.waiting_for != "code":
        return
    
    # Clean OTP (remove spaces)
    otp = re.sub(r'\s+', '', event.text.strip())
    
    if len(otp) not in [5, 6]:
        await event.reply("❌ OTP harus 5 atau 6 digit!")
        return
    
    # Try to login with OTP
    result = await login_userbot_via_bot(
        phone=state.phone,
        code=otp
    )
    
    if result == "success":
        await event.reply(
            "✅ **Login Berhasil!**\n\n"
            "Userbot telah terhubung dan aktif.\n"
            "Sekarang bisa menggunakan command userbot."
        )
        del login_states[event.sender_id]
    elif "password" in str(result).lower():
        state.waiting_for = "password"
        await event.reply(
            "🔐 **2FA Required**\n\n"
            "Akun ini menggunakan 2FA.\n"
            "Silakan kirim password 2FA kamu:"
        )
    else:
        await event.reply(f"❌ Login gagal: {result}")
        del login_states[event.sender_id]

@client.on(events.NewMessage(pattern=r'^[^\s].{3,}$'))
async def password_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    state = login_states.get(event.sender_id)
    if not state or state.waiting_for != "password":
        return
    
    password = event.text.strip()
    
    # Try to login with password
    result = await login_userbot_via_bot(
        phone=state.phone,
        code=None,
        password=password
    )
    
    if result == "success":
        await event.reply(
            "✅ **Login Berhasil!**\n\n"
            "Userbot telah terhubung dan aktif.\n"
            "Sekarang bisa menggunakan command userbot."
        )
    else:
        await event.reply(f"❌ Login gagal: {result}")
    
    del login_states[event.sender_id]

@client.on(events.NewMessage(pattern='/logout'))
async def logout_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    if MODE != "userbot":
        await event.reply("❌ Hanya tersedia di mode userbot")
        return
    
    # Clear session from MongoDB
    mongo = MongoClient()
    mongo.get_database()["telethon_sessions"].delete_one({"session": SESSION_NAME})
    
    # Clear login states
    if event.sender_id in login_states:
        del login_states[event.sender_id]
    
    await event.reply("✅ Logout berhasil! Sesi userbot telah dihapus.")