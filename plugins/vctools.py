# vctools.py
import asyncio
from telethon import events, types
from telethon.errors import ChatAdminRequiredError
from config import OWNER_ID
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import GroupCallNotFoundError, AlreadyJoinedError

# Dictionary untuk melacak status VC
vc_sessions = {}

def setup(bot, user):
    # Inisialisasi PyTgCalls
    pytgcalls = PyTgCalls(user)
    
    @pytgcalls.on_stream_end()
    async def on_stream_end(client: PyTgCalls, update: types.Update):
        """Handler ketika stream berakhir"""
        chat_id = update.chat_id
        if chat_id in vc_sessions:
            try:
                await pytgcalls.leave_group_call(chat_id)
                vc_sessions.pop(chat_id, None)
            except:
                pass
    
    @pytgcalls.on_closed_voice_chat()
    async def on_closed_voice_chat(client: PyTgCalls, chat_id: int):
        """Handler ketika voice chat ditutup"""
        if chat_id in vc_sessions:
            vc_sessions.pop(chat_id, None)
    
    # Start PyTgCalls
    @user.on(events.NewMessage(pattern=r'^/startbot$'))
    async def start_vc_handler(event):
        """Start VC handler (dijalankan sekali di awal)"""
        if event.sender_id != OWNER_ID:
            return
            
        if not pytgcalls.is_connected:
            await pytgcalls.start()
            await event.reply("<blockquote>✅ VC Handler started!</blockquote>", parse_mode='html')
    
    @user.on(events.NewMessage())
    async def vc_command_handler(event):
        """Handle VC commands"""
        if event.sender_id != OWNER_ID:
            return
        
        message = (event.raw_text or '').strip().lower()
        
        # JVC / JOINVC command
        if message in ['jvc', 'joinvc']:
            await handle_join_vc(event, pytgcalls)
        
        # LVC / LEAVEVC command
        elif message in ['lvc', 'leavevc']:
            await handle_leave_vc(event, pytgcalls)
    
    async def handle_join_vc(event, pytgcalls):
        """Handle join voice chat"""
        chat = await event.get_chat()
        
        # Jika ada link dalam pesan
        if ' ' in event.raw_text:
            link = event.raw_text.split(' ', 1)[1].strip()
            try:
                # Coba ekstrak chat ID dari link
                if 't.me/' in link:
                    if '+' in link:
                        # Link invite
                        chat_entity = await user.get_entity(link)
                        chat_id = chat_entity.id
                    else:
                        # Username link
                        if '/' in link.split('t.me/')[1]:
                            username = link.split('t.me/')[1].split('/')[0]
                        else:
                            username = link.split('t.me/')[1]
                        chat_entity = await user.get_entity(username)
                        chat_id = chat_entity.id
                else:
                    # Anggap sebagai chat ID langsung
                    chat_id = int(link) if link.lstrip('-').isdigit() else chat.id
            except Exception as e:
                await event.reply(f"<blockquote>❌ Invalid link: {str(e)}</blockquote>", parse_mode='html')
                return
        else:
            # Gunakan chat saat ini
            chat_id = chat.id
        
        try:
            # Cek apakah sudah ada di VC
            if chat_id in vc_sessions:
                await event.reply(
                    "<blockquote>⛧ Already in voice chat!</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Pastikan PyTgCalls sudah start
            if not pytgcalls.is_connected:
                await pytgcalls.start()
                await asyncio.sleep(1)
            
            # Dapatkan info chat
            try:
                chat_entity = await user.get_entity(chat_id)
                chat_name = getattr(chat_entity, 'title', getattr(chat_entity, 'first_name', 'Voice Chat'))
            except:
                chat_name = "Voice Chat"
            
            # Kirim notifikasi
            status_msg = await event.reply(
                f"<blockquote>⛧ Joining voice chat...\n"
                f"✓ Chat: {chat_name}</blockquote>",
                parse_mode='html'
            )
            
            # Cek apakah ada active voice chat
            try:
                # Dapatkan group call yang aktif
                full_chat = await user.get_full_entity(chat_id)
                
                if hasattr(full_chat, 'call') and full_chat.call:
                    call = full_chat.call
                    await join_existing_call(pytgcalls, chat_id, call)
                else:
                    # Buat voice chat baru
                    await create_new_call(pytgcalls, chat_id)
                
            except GroupCallNotFoundError:
                # Buat voice chat baru jika tidak ada
                await create_new_call(pytgcalls, chat_id)
            except Exception as e:
                await status_msg.edit(
                    f"<blockquote>❌ Error: {str(e)[:100]}</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Simpan session
            vc_sessions[chat_id] = {
                'chat_id': chat_id,
                'chat_name': chat_name,
                'join_time': asyncio.get_event_loop().time(),
                'muted': True  # Default muted
            }
            
            await status_msg.edit(
                f"<blockquote>✅ Joined voice chat!\n"
                f"⛧ Chat: {chat_name}\n"
                f"✓ Status: 🔇 Muted</blockquote>",
                parse_mode='html'
            )
            
        except ChatAdminRequiredError:
            await event.reply(
                "<blockquote>❌ I need admin rights to manage voice chats!</blockquote>",
                parse_mode='html'
            )
        except AlreadyJoinedError:
            await event.reply(
                "<blockquote>⛧ Already in this voice chat!</blockquote>",
                parse_mode='html'
            )
        except Exception as e:
            await event.reply(
                f"<blockquote>❌ Failed to join: {str(e)[:100]}</blockquote>",
                parse_mode='html'
            )
    
    async def join_existing_call(pytgcalls, chat_id, call):
        """Join existing voice chat"""
        # Gunakan stream audio silent
        await pytgcalls.join_group_call(
            chat_id,
            MediaStream(
                'http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4',  # Stream audio/video (bisa diganti dengan file audio)
                video_flags=MediaStream.IGNORE,  # Abaikan video
            ),
            invite_hash=call.invite_hash if hasattr(call, 'invite_hash') else None
        )
        
        # Mute microphone secara otomatis
        await asyncio.sleep(2)  # Tunggu sebentar
        try:
            await pytgcalls.change_volume(
                chat_id,
                0  # Volume 0 = mute
            )
        except:
            pass
    
    async def create_new_call(pytgcalls, chat_id):
        """Create new voice chat"""
        # Buat group call baru
        await user(
            types.functions.phone.CreateGroupCallRequest(
                peer=await user.get_input_entity(chat_id),
                random_id=user.rnd_id(),
                title="Bot VC"
            )
        )
        
        # Tunggu sebentar untuk call dibuat
        await asyncio.sleep(3)
        
        # Join call yang baru dibuat
        await pytgcalls.join_group_call(
            chat_id,
            MediaStream(
                'http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4',
                video_flags=MediaStream.IGNORE,
            )
        )
        
        # Mute microphone
        await asyncio.sleep(2)
        try:
            await pytgcalls.change_volume(chat_id, 0)
        except:
            pass
    
    async def handle_leave_vc(event, pytgcalls):
        """Handle leave voice chat"""
        # Cari chat ID dari argumen atau chat saat ini
        message = event.raw_text.strip()
        if ' ' in message:
            target = message.split(' ', 1)[1].strip()
            try:
                if target.lstrip('-').isdigit():
                    chat_id = int(target)
                elif 't.me/' in target:
                    # Ekstrak dari link
                    if '+' in target:
                        chat_entity = await user.get_entity(target)
                    else:
                        username = target.split('t.me/')[1].split('/')[0]
                        chat_entity = await user.get_entity(username)
                    chat_id = chat_entity.id
                else:
                    chat_id = event.chat_id
            except:
                chat_id = event.chat_id
        else:
            chat_id = event.chat_id
        
        # Cek apakah ada di VC
        if chat_id not in vc_sessions:
            await event.reply(
                "<blockquote>❌ Not in any voice chat in this chat!</blockquote>",
                parse_mode='html'
            )
            return
        
        try:
            chat_info = vc_sessions[chat_id]
            chat_name = chat_info['chat_name']
            
            # Leave voice chat
            await pytgcalls.leave_group_call(chat_id)
            
            # Hapus dari session
            vc_sessions.pop(chat_id, None)
            
            await event.reply(
                f"<blockquote>✅ Left voice chat!\n"
                f"⛧ Chat: {chat_name}</blockquote>",
                parse_mode='html'
            )
            
        except Exception as e:
            await event.reply(
                f"<blockquote>❌ Failed to leave: {str(e)[:100]}</blockquote>",
                parse_mode='html'
            )
    
    # Handler untuk cek status VC
    @user.on(events.NewMessage(pattern=r'^/vcstatus$'))
    async def vc_status_handler(event):
        """Check VC status"""
        if event.sender_id != OWNER_ID:
            return
        
        if not vc_sessions:
            await event.reply(
                "<blockquote>⛧ Not in any voice chats</blockquote>",
                parse_mode='html'
            )
            return
        
        status_lines = ["<blockquote>📞 Active Voice Chats:"]
        for chat_id, session in vc_sessions.items():
            duration = int(asyncio.get_event_loop().time() - session['join_time'])
            mins, secs = divmod(duration, 60)
            hours, mins = divmod(mins, 60)
            
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
            muted_status = "🔇" if session['muted'] else "🔈"
            
            status_lines.append(
                f"  • {session['chat_name']}\n"
                f"    ID: <code>{chat_id}</code>\n"
                f"    Time: {time_str} | Status: {muted_status}"
            )
        
        status_lines.append(f"\nTotal: {len(vc_sessions)} active")
        status_lines.append("</blockquote>")
        
        await event.reply("\n".join(status_lines), parse_mode='html')