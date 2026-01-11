# [file name]: grab.py
import re
import asyncio
from telethon import events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.tl.functions.messages import ImportChatInviteRequest
from config import OWNER_ID

def setup(bot, user):
    
    @user.on(events.NewMessage())
    async def grab_handler(event):
        """Ambil konten dari channel private menggunakan link"""
        if event.sender_id != OWNER_ID:
            return
        
        message = event.raw_text.strip()
        
        # Command pendek: .grab atau hanya "grab" (untuk mode no prefix)
        cmd_prefix = '.'  # prefix default
        try:
            import json
            with open('data/prefix.json', 'r') as f:
                cmd_prefix = json.load(f).get('prefix', '.')
        except:
            pass
        
        # Cek apakah ini command grab
        is_grab_command = False
        grab_args = ""
        
        if cmd_prefix == "no" and message.lower().startswith('grab '):
            is_grab_command = True
            grab_args = message[5:].strip()
        elif cmd_prefix != "no" and message.startswith(cmd_prefix):
            cmd_part = message[len(cmd_prefix):].strip()
            if cmd_part.lower().startswith('grab '):
                is_grab_command = True
                grab_args = cmd_part[5:].strip()
        
        if not is_grab_command:
            return
        
        if not grab_args:
            await event.reply(
                "<blockquote>✘ ᴜsᴀɢᴇ: grab &lt;ᴜʀʟ&gt;\n"
                "✓ ᴄᴏɴᴛᴏʜ: grab https://t.me/privatechannel/123\n"
                "✘ sᴜᴘᴘᴏʀᴛs: ᴠɪᴅᴇᴏ, ᴛᴇxᴛ, ᴀᴜᴅɪᴏ, sᴛɪᴄᴋᴇʀ, ᴘʜᴏᴛᴏ</blockquote>",
                parse_mode='html'
            )
            return
        
        # Parsing URL
        url_patterns = [
            r't\.me/(c/)?([^/]+)/(\d+)',  # t.me/channel/123 atau t.me/c/channel/123
            r'(?:https?://)?t\.me/joinchat/([a-zA-Z0-9_-]+)'  # Link invite
        ]
        
        chat_username = None
        message_id = None
        invite_hash = None
        
        for pattern in url_patterns:
            match = re.search(pattern, grab_args)
            if match:
                if len(match.groups()) == 3:  # t.me/format
                    chat_username = match.group(2)
                    message_id = int(match.group(3))
                else:  # invite link
                    invite_hash = match.group(1)
                break
        
        if not chat_username and not invite_hash:
            await event.reply(
                "<blockquote>✘ ɪɴᴠᴀʟɪᴅ ᴜʀʟ!\n"
                "✓ ᴘᴀsᴛᴇᴋᴀɴ ʟɪɴᴋ ᴘᴏsᴛɪɴɢᴀɴ ᴅᴀʀɪ ᴄʜᴀɴɴᴇʟ</blockquote>",
                parse_mode='html'
            )
            return
        
        processing_msg = await event.reply(
            "<blockquote>⛧ ᴍᴇɴɢᴀᴍʙɪʟ ᴋᴏɴᴛᴇɴ...\n"
            "✘ ᴍᴏʜᴏɴ ᴛᴜɴɢɢᴜ</blockquote>",
            parse_mode='html'
        )
        
        try:
            # Handle invite link
            if invite_hash:
                try:
                    # Join channel via invite
                    await user(ImportChatInviteRequest(invite_hash))
                    # Get the chat from recent dialogs
                    await asyncio.sleep(2)
                    dialogs = await user.get_dialogs(limit=1)
                    if dialogs:
                        chat = dialogs[0].entity
                        chat_username = getattr(chat, 'username', None) or chat.id
                        # Untuk invite link, kita ambil pesan terakhir
                        async for msg in user.iter_messages(chat, limit=1):
                            message_id = msg.id
                            break
                except Exception as e:
                    await processing_msg.edit(
                        f"<blockquote>✘ ɢᴀɢᴀʟ ɢᴀʙᴜɴɢ ᴄʜᴀɴɴᴇʟ\n"
                        f"✓ ᴇʀʀᴏʀ: {str(e)[:100]}</blockquote>",
                        parse_mode='html'
                    )
                    return
            
            # Get the message
            try:
                if chat_username.startswith('-'):  # ID numeric
                    chat = await user.get_entity(int(chat_username))
                else:
                    chat = await user.get_entity(chat_username)
                
                msg = await user.get_messages(chat, ids=message_id)
                
                if not msg:
                    await processing_msg.edit(
                        "<blockquote>✘ ᴘᴇsᴀɴ ᴛɪᴅᴀᴋ ᴅɪᴛᴇᴍᴜᴋᴀɴ</blockquote>",
                        parse_mode='html'
                    )
                    return
                
                # Prepare caption with source info
                caption = f"<blockquote>✓ ᴅɪᴀᴍʙɪʟ ᴅᴀʀɪ: {getattr(chat, 'title', 'Unknown')}\n"
                caption += f"✘ ʟɪɴᴋ: https://t.me/{getattr(chat, 'username', '')}/{message_id}</blockquote>\n\n"
                
                if msg.text:
                    caption += msg.text
                
                # Send based on media type
                if msg.media:
                    if isinstance(msg.media, MessageMediaPhoto):
                        await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴘʜᴏᴛᴏ...</blockquote>", parse_mode='html')
                        await user.send_file(
                            event.chat_id,
                            msg.media,
                            caption=caption if caption else None,
                            parse_mode='html'
                        )
                    
                    elif isinstance(msg.media, MessageMediaDocument):
                        # Check document type
                        attributes = msg.media.document.attributes
                        is_video = any(attr.__class__.__name__ == 'DocumentAttributeVideo' for attr in attributes)
                        is_audio = any(attr.__class__.__name__ == 'DocumentAttributeAudio' for attr in attributes)
                        is_sticker = any(attr.__class__.__name__ == 'DocumentAttributeSticker' for attr in attributes)
                        
                        if is_video:
                            await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴠɪᴅᴇᴏ...</blockquote>", parse_mode='html')
                        elif is_audio:
                            await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴀᴜᴅɪᴏ...</blockquote>", parse_mode='html')
                        elif is_sticker:
                            await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ sᴛɪᴄᴋᴇʀ...</blockquote>", parse_mode='html')
                        else:
                            await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴅᴏᴋᴜᴍᴇɴ...</blockquote>", parse_mode='html')
                        
                        await user.send_file(
                            event.chat_id,
                            msg.media,
                            caption=caption if caption and not is_sticker else None,
                            parse_mode='html' if not is_sticker else None
                        )
                    
                    else:
                        await user.send_file(event.chat_id, msg.media)
                
                elif msg.text:
                    await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴛᴇxᴛ...</blockquote>", parse_mode='html')
                    await event.respond(caption, parse_mode='html')
                
                await processing_msg.edit(
                    "<blockquote>✓ ᴋᴏɴᴛᴇɴ ʙᴇʀʜᴀsɪʟ ᴅɪᴀᴍʙɪʟ!</blockquote>",
                    parse_mode='html'
                )
                
            except Exception as e:
                await processing_msg.edit(
                    f"<blockquote>✘ ɢᴀɢᴀʟ ᴍᴇɴɢᴀᴍʙɪʟ\n"
                    f"✓ ᴇʀʀᴏʀ: {str(e)[:100]}</blockquote>",
                    parse_mode='html'
                )
                
        except Exception as e:
            await processing_msg.edit(
                f"<blockquote>✘ ᴛᴇʀᴊᴀᴅɪ ᴋᴇsᴀʟᴀʜᴀɴ\n"
                f"✓ ᴇʀʀᴏʀ: {str(e)[:100]}</blockquote>",
                parse_mode='html'
            )