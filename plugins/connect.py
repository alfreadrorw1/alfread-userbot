"""
Connect/Login Plugin untuk Alfread UserBot
Hanya owner yang bisa menggunakan command ini
"""

import logging
from telethon import events
from telethon.errors import SessionPasswordNeededError
from config import Config

logger = logging.getLogger(__name__)

async def register_plugin(client):
    """Register plugin connect"""
    
    @client.on(events.NewMessage(pattern=r'^\.connect$', outgoing=True))
    async def handler(event):
        """Command untuk connect/login userbot"""
        
        # Cek apakah user adalah owner
        if event.sender_id != Config.OWNER_ID:
            await event.reply("❌ Hanya owner yang bisa menggunakan command ini!")
            return
        
        try:
            # Kirim instruksi
            await event.reply(
                "🔑 **Login UserBot**\n\n"
                "Silakan lanjutkan proses login:\n"
                "1. Masukkan nomor telepon (format internasional, contoh: +6281234567890)\n"
                "2. Masukkan kode verifikasi yang dikirim ke Telegram Anda\n"
                "3. Jika ada 2FA, masukkan password 2FA\n\n"
                "Ketik `.cancel` untuk membatalkan."
            )
            
            # Minta nomor telepon
            await event.respond("📱 **Masukkan nomor telepon Anda:**")
            
            # Handler untuk input nomor telepon
            @client.on(events.NewMessage(from_users=Config.OWNER_ID))
            async def phone_handler(phone_event):
                if phone_event.raw_text == '.cancel':
                    await phone_event.reply("❌ Login dibatalkan")
                    client.remove_event_handler(phone_handler)
                    return
                
                phone = phone_event.raw_text
                
                try:
                    # Kirim kode OTP
                    await client.send_code_request(phone)
                    await phone_event.reply(
                        f"📲 Kode OTP telah dikirim ke {phone}\n"
                        f"**Masukkan kode OTP:** (format: 1 2 3 4 5)"
                    )
                    
                    # Handler untuk input OTP
                    @client.on(events.NewMessage(from_users=Config.OWNER_ID))
                    async def code_handler(code_event):
                        if code_event.raw_text == '.cancel':
                            await code_event.reply("❌ Login dibatalkan")
                            client.remove_event_handler(code_handler)
                            return
                        
                        code = code_event.raw_text.replace(" ", "")
                        
                        try:
                            # Coba login dengan kode
                            await client.sign_in(phone=phone, code=code)
                            
                            # Login sukses
                            await code_event.reply(
                                "✅ **Login berhasil!**\n"
                                f"UserBot siap digunakan.\n"
                                f"Owner: {Config.OWNER_ID}"
                            )
                            
                            # Simpan session ke MongoDB jika diperlukan
                            try:
                                from plugins.mongodb import save_user_session
                                session_data = client.session.save()
                                await save_user_session(Config.OWNER_ID, session_data)
                                logger.info("Session saved to MongoDB")
                            except Exception as e:
                                logger.error(f"Failed to save session: {e}")
                            
                            client.remove_event_handler(code_handler)
                            
                        except SessionPasswordNeededError:
                            # Minta password 2FA
                            await code_event.reply(
                                "🔒 **Akun memiliki 2FA**\n"
                                "Masukkan password 2FA:"
                            )
                            
                            # Handler untuk password 2FA
                            @client.on(events.NewMessage(from_users=Config.OWNER_ID))
                            async def password_handler(pass_event):
                                if pass_event.raw_text == '.cancel':
                                    await pass_event.reply("❌ Login dibatalkan")
                                    client.remove_event_handler(password_handler)
                                    return
                                
                                password = pass_event.raw_text
                                
                                try:
                                    await client.sign_in(password=password)
                                    await pass_event.reply(
                                        "✅ **Login dengan 2FA berhasil!**\n"
                                        "UserBot siap digunakan."
                                    )
                                    
                                    # Simpan session
                                    try:
                                        from plugins.mongodb import save_user_session
                                        session_data = client.session.save()
                                        await save_user_session(Config.OWNER_ID, session_data)
                                        logger.info("Session saved to MongoDB")
                                    except Exception as e:
                                        logger.error(f"Failed to save session: {e}")
                                    
                                    client.remove_event_handler(password_handler)
                                    
                                except Exception as e:
                                    await pass_event.reply(f"❌ Gagal login: {str(e)}")
                                    client.remove_event_handler(password_handler)
                        
                        except Exception as e:
                            await code_event.reply(f"❌ Gagal login: {str(e)}")
                            client.remove_event_handler(code_handler)
                    
                except Exception as e:
                    await phone_event.reply(f"❌ Error: {str(e)}")
                    client.remove_event_handler(phone_handler)
        
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
    
    logger.info("✅ Connect plugin loaded")