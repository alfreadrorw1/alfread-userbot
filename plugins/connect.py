"""
Connect Plugin untuk Alfread UserBot
Command untuk menghubungkan akun user Telegram
"""

import logging
import asyncio
from telethon import TelegramClient, events, errors, Button
from telethon.tl.types import MessageEntityPhone
from config import Config
from plugins.utils import is_owner
from plugins.mongodb import save_user_session, get_user_session

logger = logging.getLogger(__name__)

# State management
user_clients = {}  # {owner_id: user_client}
pending_logins = {}  # {owner_id: login_data}

async def register_plugin(bot_client):
    """Register plugin connect"""
    
    @bot_client.on(events.NewMessage(pattern=r'^\.connect$', outgoing=True))
    async def connect_handler(event):
        """Command .connect untuk menghubungkan user account"""
        
        if not await is_owner(event):
            await event.reply("❌ Hanya owner yang bisa menggunakan command ini!")
            return
        
        owner_id = event.sender_id
        
        # Cek apakah sudah ada client untuk owner ini
        if owner_id in user_clients:
            try:
                if await user_clients[owner_id].is_user_authorized():
                    await event.reply("✅ Anda sudah terhubung sebagai user!\n\n"
                                     "Gunakan `.disconnect` untuk memutuskan koneksi.")
                    return
            except:
                pass
        
        # Minta nomor telepon
        await event.reply("📱 **Hubungkan Akun User**\n\n"
                         "Silakan kirim nomor telepon Anda dalam format internasional:\n"
                         "Contoh: `+6281234567890`\n\n"
                         "Atau gunakan tombol di bawah untuk membagikan kontak:",
                         buttons=[
                             [Button.request_phone("📱 Bagikan Nomor", resize=True)],
                             [Button.inline("❌ Batal", b"cancel_login")]
                         ])
        
        pending_logins[owner_id] = {
            'state': 'awaiting_phone',
            'bot_event': event
        }
    
    @bot_client.on(events.CallbackQuery(pattern=b"cancel_login"))
    async def cancel_login_handler(event):
        """Batalkan proses login"""
        owner_id = event.sender_id
        
        if owner_id in pending_logins:
            del pending_logins[owner_id]
            await event.answer("✅ Login dibatalkan")
            await event.delete()
        else:
            await event.answer("❌ Tidak ada login yang aktif")
    
    @bot_client.on(events.NewMessage(func=lambda e: e.message.contact))
    async def contact_handler(event):
        """Handle shared phone contact"""
        owner_id = event.sender_id
        
        if owner_id not in pending_logins:
            return
        
        if pending_logins[owner_id]['state'] != 'awaiting_phone':
            return
        
        contact = event.message.contact
        if contact.user_id == owner_id:
            phone_number = f"+{contact.phone_number}"
            await process_phone_number(owner_id, phone_number, event)
    
    @bot_client.on(events.NewMessage(pattern=r'^\+[\d\s\-]+$', outgoing=True))
    async def phone_number_handler(event):
        """Handle manual phone number input"""
        owner_id = event.sender_id
        
        if owner_id not in pending_logins:
            return
        
        if pending_logins[owner_id]['state'] != 'awaiting_phone':
            return
        
        phone_number = event.raw_text.strip()
        await process_phone_number(owner_id, phone_number, event)
    
    async def process_phone_number(owner_id, phone_number, event):
        """Proses nomor telepon untuk login"""
        try:
            # Buat session string yang unik
            session_name = f"user_session_{owner_id}"
            
            # Buat client user baru
            user_client = TelegramClient(
                session=session_name,
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                device_model="Alfread UserBot",
                system_version="Linux",
                app_version="1.0.0"
            )
            
            # Koneksikan client
            await user_client.connect()
            
            # Kirim kode OTP
            sent_code = await user_client.send_code_request(phone_number)
            
            pending_logins[owner_id].update({
                'state': 'awaiting_code',
                'user_client': user_client,
                'phone_number': phone_number,
                'phone_code_hash': sent_code.phone_code_hash
            })
            
            await event.reply(f"📲 **Kode OTP Dikirim!**\n\n"
                             f"Nomor: `{phone_number}`\n\n"
                             "Silakan kirim kode OTP yang diterima (format: `12345`):")
            
        except errors.PhoneNumberInvalidError:
            await event.reply("❌ **Nomor telepon tidak valid!**\n\n"
                             "Pastikan format internasional (contoh: +6281234567890)")
            if owner_id in pending_logins:
                del pending_logins[owner_id]
        
        except errors.PhoneNumberBannedError:
            await event.reply("❌ **Nomor telepon diblokir oleh Telegram!**")
            if owner_id in pending_logins:
                del pending_logins[owner_id]
        
        except errors.PhoneNumberFloodError:
            await event.reply("⚠️ **Terlalu banyak permintaan!**\n\n"
                             "Tunggu beberapa saat sebelum mencoba lagi.")
            if owner_id in pending_logins:
                del pending_logins[owner_id]
        
        except Exception as e:
            logger.error(f"Error sending code: {e}")
            await event.reply(f"❌ **Error:** {str(e)}")
            if owner_id in pending_logins:
                del pending_logins[owner_id]
    
    @bot_client.on(events.NewMessage(pattern=r'^\d{5}$', outgoing=True))
    async def otp_handler(event):
        """Handle OTP code"""
        owner_id = event.sender_id
        
        if owner_id not in pending_logins:
            return
        
        if pending_logins[owner_id]['state'] != 'awaiting_code':
            return
        
        otp_code = event.raw_text.strip()
        login_data = pending_logins[owner_id]
        
        try:
            # Sign in dengan OTP
            await login_data['user_client'].sign_in(
                phone=login_data['phone_number'],
                code=otp_code,
                phone_code_hash=login_data['phone_code_hash']
            )
            
            # Dapatkan session string
            session_string = await login_data['user_client'].session.save()
            
            # Simpan ke MongoDB
            save_user_session(
                user_id=owner_id,
                session_string=session_string,
                phone=login_data['phone_number']
            )
            
            # Simpan client ke dictionary
            user_clients[owner_id] = login_data['user_client']
            
            # Dapatkan info user
            me = await login_data['user_client'].get_me()
            
            await event.reply(f"✅ **Login Berhasil!**\n\n"
                             f"👤 **User:** {me.first_name}\n"
                             f"📱 **Phone:** `{login_data['phone_number']}`\n"
                             f"🆔 **ID:** `{me.id}`\n\n"
                             f"✅ **Sekarang Anda bisa menggunakan command `.ping`!**")
            
            # Hapus dari pending
            del pending_logins[owner_id]
            
        except errors.SessionPasswordNeededError:
            # Butuh 2FA password
            pending_logins[owner_id]['state'] = 'awaiting_2fa'
            await event.reply("🔐 **Diperlukan 2FA Password**\n\n"
                             "Silakan kirim password 2FA Anda:")
        
        except errors.PhoneCodeInvalidError:
            await event.reply("❌ **Kode OTP salah!**\n\n"
                             "Silakan coba lagi:")
        
        except errors.PhoneCodeExpiredError:
            await event.reply("❌ **Kode OTP kadaluarsa!**\n\n"
                             "Gunakan `.connect` lagi untuk memulai ulang.")
            if owner_id in pending_logins:
                if 'user_client' in pending_logins[owner_id]:
                    await pending_logins[owner_id]['user_client'].disconnect()
                del pending_logins[owner_id]
        
        except Exception as e:
            logger.error(f"Error signing in: {e}")
            await event.reply(f"❌ **Error:** {str(e)}")
            if owner_id in pending_logins:
                if 'user_client' in pending_logins[owner_id]:
                    await pending_logins[owner_id]['user_client'].disconnect()
                del pending_logins[owner_id]
    
    @bot_client.on(events.NewMessage(pattern=r'^[\w\d@#$%^&*()!]{6,}$', outgoing=True))
    async def twofa_handler(event):
        """Handle 2FA password"""
        owner_id = event.sender_id
        
        if owner_id not in pending_logins:
            return
        
        if pending_logins[owner_id]['state'] != 'awaiting_2fa':
            return
        
        password = event.raw_text.strip()
        login_data = pending_logins[owner_id]
        
        try:
            # Sign in dengan password 2FA
            await login_data['user_client'].sign_in(password=password)
            
            # Dapatkan session string
            session_string = await login_data['user_client'].session.save()
            
            # Simpan ke MongoDB
            save_user_session(
                user_id=owner_id,
                session_string=session_string,
                phone=login_data['phone_number']
            )
            
            # Simpan client ke dictionary
            user_clients[owner_id] = login_data['user_client']
            
            # Dapatkan info user
            me = await login_data['user_client'].get_me()
            
            await event.reply(f"✅ **Login 2FA Berhasil!**\n\n"
                             f"👤 **User:** {me.first_name}\n"
                             f"📱 **Phone:** `{login_data['phone_number']}`\n"
                             f"🆔 **ID:** `{me.id}`\n\n"
                             f"✅ **Sekarang Anda bisa menggunakan command `.ping`!**")
            
            # Hapus dari pending
            del pending_logins[owner_id]
            
        except Exception as e:
            logger.error(f"Error 2FA: {e}")
            await event.reply(f"❌ **Password 2FA salah!**\n\n"
                             "Silakan coba lagi:")
    
    @bot_client.on(events.NewMessage(pattern=r'^\.disconnect$', outgoing=True))
    async def disconnect_handler(event):
        """Disconnect user session"""
        if not await is_owner(event):
            return
        
        owner_id = event.sender_id
        
        if owner_id in user_clients:
            try:
                await user_clients[owner_id].disconnect()
                del user_clients[owner_id]
                
                # Update MongoDB
                from plugins.mongodb import disconnect_user_session
                disconnect_user_session(owner_id)
                
                await event.reply("✅ **Disconnected!**\n\n"
                                 "Sesi user telah diputuskan.")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
                await event.reply(f"❌ **Error:** {str(e)}")
        else:
            await event.reply("ℹ️ **Tidak ada koneksi aktif**")
    
    @bot_client.on(events.NewMessage(pattern=r'^\.session$', outgoing=True))
    async def session_handler(event):
        """Cek status session"""
        if not await is_owner(event):
            return
        
        owner_id = event.sender_id
        
        if owner_id in user_clients:
            try:
                me = await user_clients[owner_id].get_me()
                status = "✅ **Connected**"
                user_info = f"👤 **User:** {me.first_name}\n🆔 **ID:** `{me.id}`"
            except:
                status = "❌ **Disconnected**"
                user_info = ""
        else:
            status = "❌ **Tidak ada session aktif**"
            user_info = ""
        
        await event.reply(f"🔍 **Session Status**\n\n{status}\n{user_info}")
    
    logger.info("✅ Connect plugin loaded")