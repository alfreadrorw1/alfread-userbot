import json
import os
import re
import time
from telethon import events, Button, TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH

# File untuk menyimpan data
SESSION_FILE = 'data/sessions.json'

def load_sessions():
    """Load saved sessions from file"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_sessions(data):
    """Save sessions to file"""
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f, indent=2)

async def setup(bot, user):
    """Setup connect plugin"""
    
    active_sessions = {}
    pending_logins = {}
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client.is_connected():
                await event.reply(
                    "<blockquote>✅ <b>Anda sudah terhubung dengan UserBot!</b></blockquote>\n\n"
                    "<blockquote>Gunakan command <code>.help</code> untuk melihat daftar perintah.</blockquote>",
                    parse_mode="html"
                )
                return
        
        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")]
        ]
        
        await event.reply(
            "<blockquote>🔑 <b>UserBot Connect System</b></blockquote>\n\n"
            "<blockquote>Pilih metode login:</blockquote>",
            buttons=buttons,
            parse_mode="html"
        )

    @bot.on(events.CallbackQuery(data=b'phone_login'))
    async def phone_login_handler(event):
        user_id = event.sender_id
        
        await event.delete()
        
        await event.reply(
            "<blockquote>📱 <b>Login dengan Nomor Telepon</b></blockquote>\n\n"
            "<blockquote>Silakan bagikan nomor telepon Anda:</blockquote>",
            buttons=[Button.request_phone("📱 Bagikan Nomor", resize=True)],
            parse_mode="html"
        )
        
        pending_logins[user_id] = {'method': 'phone'}

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
            
            await event.reply(
                "<blockquote>⏳ <b>Mengirim kode OTP, tunggu sebentar...</b></blockquote>",
                parse_mode="html"
            )
            
            await process_phone_number(event, phone, user_id)

    async def process_phone_number(event, phone, user_id):
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            
            sent_code = await client.send_code_request(phone)
            
            pending_logins[user_id] = {
                'client': client,
                'phone': phone,
                'phone_code_hash': sent_code.phone_code_hash,
                'attempts': 0
            }
            
            await event.reply(
                "<blockquote>📲 <b>Kode verifikasi terkirim!</b></blockquote>\n\n"
                "<blockquote>Masukkan kode OTP yang diterima via Telegram</blockquote>\n\n"
                "<blockquote><b>Format:</b> <code>1 2 3 4 5</code> (5 digit dipisahkan spasi)</blockquote>\n\n"
                "<blockquote>⚠️ <b>Perhatian:</b>\n"
                "• Kode OTP hanya berlaku 5 menit\n"
                "• Jangan bagikan kode kepada siapapun</blockquote>",
                parse_mode="html"
            )
            
        except Exception as e:
            await event.reply(
                f"<blockquote>⚠️ <b>Error:</b> {str(e)}</blockquote>",
                parse_mode="html"
            )

    @bot.on(events.NewMessage(func=lambda e: e.is_private))
    async def message_handler(event):
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        if event.message.contact:
            return
        
        if user_id not in pending_logins:
            return
        
        if re.match(r'^\d{1} \d{1} \d{1} \d{1} \d{1}$', text):
            await handle_otp_code(event, text, user_id)
        else:
            await event.reply(
                "<blockquote>❌ <b>Format tidak dikenali!</b></blockquote>\n\n"
                "<blockquote>Untuk kode OTP, gunakan format: <code>1 2 3 4 5</code></blockquote>",
                parse_mode="html"
            )

    async def handle_otp_code(event, text, user_id):
        code = ''.join(text.split())
        login_data = pending_logins[user_id]
        
        await event.reply(
            "<blockquote>⏳ <b>Memverifikasi kode OTP, tunggu sebentar...</b></blockquote>",
            parse_mode="html"
        )
        
        try:
            client = login_data['client']
            await client.sign_in(
                phone=login_data['phone'],
                code=code,
                phone_code_hash=login_data['phone_code_hash']
            )
            
            await complete_login(event, user_id, login_data)
                
        except SessionPasswordNeededError:
            login_data['needs_password'] = True
            await event.reply(
                "<blockquote>🔒 <b>Akun Anda memiliki verifikasi 2 langkah</b></blockquote>\n\n"
                "<blockquote>Silakan masukkan sandi verifikasi 2 langkah Anda:</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            login_data['attempts'] += 1
            
            if login_data['attempts'] >= 3:
                del pending_logins[user_id]
                await event.reply(
                    "<blockquote>🚫 <b>Terlalu banyak percobaan OTP gagal!</b></blockquote>\n\n"
                    "<blockquote>Silakan mulai ulang dengan command <code>/start</code></blockquote>",
                    parse_mode="html"
                )
            else:
                await event.reply(
                    f"<blockquote>❌ <b>Error:</b> {str(e)}</blockquote>\n\n"
                    f"<blockquote>Percobaan {login_data['attempts']} dari 3</blockquote>",
                    parse_mode="html"
                )

    @bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id in pending_logins))
    async def password_handler(event):
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        if user_id in pending_logins and pending_logins[user_id].get('needs_password'):
            login_data = pending_logins[user_id]
            
            await event.reply(
                "<blockquote>⏳ <b>Memverifikasi sandi, tunggu sebentar...</b></blockquote>",
                parse_mode="html"
            )
            
            try:
                client = login_data['client']
                await client.sign_in(password=text)
                await complete_login(event, user_id, login_data)
                    
            except Exception as e:
                login_data['attempts'] += 1
                
                if login_data['attempts'] >= 3:
                    del pending_logins[user_id]
                    await event.reply(
                        "<blockquote>🚫 <b>Terlalu banyak percobaan sandi gagal!</b></blockquote>\n\n"
                        "<blockquote>Silakan mulai ulang dengan command <code>/start</code></blockquote>",
                        parse_mode="html"
                    )
                else:
                    await event.reply(
                        f"<blockquote>❌ <b>Error:</b> {str(e)}</blockquote>\n\n"
                        f"<blockquote>Percobaan {login_data['attempts']} dari 3</blockquote>",
                        parse_mode="html"
                    )

    async def complete_login(event, user_id, login_data):
        try:
            client = login_data['client']
            session_str = client.session.save()
            
            # Save session to file
            sessions = load_sessions()
            sessions[str(user_id)] = session_str
            save_sessions(sessions)
            
            active_sessions[user_id] = client
            
            del pending_logins[user_id]
            
            await event.reply(
                "<blockquote>✅ <b>Login berhasil!</b></blockquote>\n\n"
                "<blockquote>UserBot sekarang siap digunakan.</blockquote>\n\n"
                "<blockquote>Gunakan command <code>.help</code> untuk melihat daftar perintah.</blockquote>",
                parse_mode="html"
            )
            
        except Exception as e:
            await event.reply(
                f"<blockquote>❌ <b>Error saat login:</b> {str(e)}</blockquote>",
                parse_mode="html"
            )

    @bot.on(events.NewMessage(pattern='/disconnect'))
    async def disconnect_handler(event):
        user_id = event.sender_id
        
        if user_id in active_sessions:
            client = active_sessions[user_id]
            if client.is_connected():
                await client.disconnect()
            del active_sessions[user_id]
            
            # Remove from saved sessions
            sessions = load_sessions()
            if str(user_id) in sessions:
                del sessions[str(user_id)]
                save_sessions(sessions)
            
            await event.reply(
                "<blockquote>✅ <b>Koneksi diputuskan!</b></blockquote>",
                parse_mode="html"
            )
        else:
            await event.reply(
                "<blockquote>⚠️ <b>Anda tidak terhubung dengan UserBot</b></blockquote>",
                parse_mode="html"
            )