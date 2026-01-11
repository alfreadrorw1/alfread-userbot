# [file name]: grab.py
import re
import asyncio
import os
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
        
        temp_files = []  # Untuk menyimpan file sementara
        
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
                    # Download file terlebih dahulu untuk menghindari protected content error
                    await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢᴜɴᴅᴜʜ ғɪʟᴇ...</blockquote>", parse_mode='html')
                    
                    # Create temp directory if not exists
                    if not os.path.exists('temp'):
                        os.makedirs('temp')
                    
                    # Download file
                    file_path = await msg.download_media(file='temp/')
                    temp_files.append(file_path)
                    
                    if file_path:
                        if isinstance(msg.media, MessageMediaPhoto):
                            await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴘʜᴏᴛᴏ...</blockquote>", parse_mode='html')
                            await user.send_file(
                                event.chat_id,
                                file_path,
                                caption=caption if caption else None,
                                parse_mode='html',
                                force_document=False
                            )
                        
                        elif isinstance(msg.media, MessageMediaDocument):
                            # Check document type
                            attributes = msg.media.document.attributes
                            is_video = any(attr.__class__.__name__ == 'DocumentAttributeVideo' for attr in attributes)
                            is_audio = any(attr.__class__.__name__ == 'DocumentAttributeAudio' for attr in attributes)
                            is_sticker = any(attr.__class__.__name__ == 'DocumentAttributeSticker' for attr in attributes)
                            is_gif = any(attr.__class__.__name__ == 'DocumentAttributeAnimated' for attr in attributes)
                            
                            # Determine file type
                            if is_video:
                                await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴠɪᴅᴇᴏ...</blockquote>", parse_mode='html')
                                force_doc = False
                            elif is_audio:
                                await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴀᴜᴅɪᴏ...</blockquote>", parse_mode='html')
                                force_doc = False
                            elif is_sticker:
                                await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ sᴛɪᴄᴋᴇʀ...</blockquote>", parse_mode='html')
                                force_doc = False
                                caption = None  # Sticker tidak support caption
                            elif is_gif:
                                await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ɢɪғ...</blockquote>", parse_mode='html')
                                force_doc = False
                            else:
                                await processing_msg.edit("<blockquote>⛧ ᴍᴇɴɢɪʀɪᴍ ᴅᴏᴋᴜᴍᴇɴ...</blockquote>", parse_mode='html')
                                force_doc = True
                            
                            await user.send_file(
                                event.chat_id,
                                file_path,
                                caption=caption if caption else None,
                                parse_mode='html' if caption else None,
                                force_document=force_doc,
                                attributes=attributes if not force_doc else None
                            )
                        
                        # Cleanup temp file
                        try:
                            os.remove(file_path)
                            temp_files.remove(file_path)
                        except:
                            pass
                        
                    else:
                        await processing_msg.edit(
                            "<blockquote>✘ ɢᴀɢᴀʟ ᴍᴇɴɢᴜɴᴅᴜʜ ғɪʟᴇ</blockquote>",
                            parse_mode='html'
                        )
                        return
                
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
        finally:
            # Cleanup temp files jika ada
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
    
    # Handler untuk bulk grab (multiple messages)
    @user.on(events.NewMessage())
    async def multigrab_handler(event):
        """Ambil multiple konten dari range pesan"""
        if event.sender_id != OWNER_ID:
            return
        
        message = event.raw_text.strip()
        
        # Command pendek: .mgrab atau hanya "mgrab" (untuk mode no prefix)
        cmd_prefix = '.'  # prefix default
        try:
            import json
            with open('data/prefix.json', 'r') as f:
                cmd_prefix = json.load(f).get('prefix', '.')
        except:
            pass
        
        # Cek apakah ini command mgrab (multi grab)
        is_mgrab_command = False
        grab_args = ""
        
        if cmd_prefix == "no" and message.lower().startswith('mgrab '):
            is_mgrab_command = True
            grab_args = message[6:].strip()
        elif cmd_prefix != "no" and message.startswith(cmd_prefix):
            cmd_part = message[len(cmd_prefix):].strip()
            if cmd_part.lower().startswith('mgrab '):
                is_mgrab_command = True
                grab_args = cmd_part[6:].strip()
        
        if not is_mgrab_command:
            return
        
        if not grab_args:
            await event.reply(
                "<blockquote>✘ ᴜsᴀɢᴇ: mgrab &lt;ᴜʀʟ_ᴀᴡᴀʟ&gt; &lt;ᴜʀʟ_ᴀᴋʜɪʀ&gt;\n"
                "✓ ᴄᴏɴᴛᴏʜ: mgrab https://t.me/channel/100 https://t.me/channel/120\n"
                "✘ ᴀᴛᴀᴜ: mgrab https://t.me/channel/100-120</blockquote>",
                parse_mode='html'
            )
            return
        
        # Parsing range atau multiple URLs
        urls = grab_args.split()
        
        if len(urls) == 1 and '-' in urls[0]:
            # Format: https://t.me/channel/100-120
            base_url = re.sub(r'/(\d+)-(\d+)$', '', urls[0])
            match = re.search(r'/(\d+)-(\d+)$', urls[0])
            if match:
                start_id = int(match.group(1))
                end_id = int(match.group(2))
                # Extract channel name
                channel_match = re.search(r't\.me/(c/)?([^/]+)', base_url)
                if channel_match:
                    chat_username = channel_match.group(2)
                    message_ids = list(range(min(start_id, end_id), max(start_id, end_id) + 1))
                else:
                    await event.reply("<blockquote>✘ ғᴏʀᴍᴀᴛ ᴜʀʟ sᴀʟᴀʜ</blockquote>", parse_mode='html')
                    return
        elif len(urls) >= 2:
            # Multiple individual URLs
            message_ids = []
            chat_username = None
            
            for url in urls[:10]:  # Limit to 10 URLs max
                match = re.search(r't\.me/(c/)?([^/]+)/(\d+)', url)
                if match:
                    if not chat_username:
                        chat_username = match.group(2)
                    message_ids.append(int(match.group(3)))
            
            if not message_ids:
                await event.reply("<blockquote>✘ ᴛɪᴅᴀᴋ ᴀᴅᴀ ɪᴅ ᴘᴇsᴀɴ ʏᴀɴɢ ᴠᴀʟɪᴅ</blockquote>", parse_mode='html')
                return
        else:
            await event.reply(
                "<blockquote>✘ ғᴏʀᴍᴀᴛ sᴀʟᴀʜ!\n"
                "✓ ᴜsᴀɢᴇ: mgrab &lt;ᴜʀʟ_ᴀᴡᴀʟ&gt; &lt;ᴜʀʟ_ᴀᴋʜɪʀ&gt;</blockquote>",
                parse_mode='html'
            )
            return
        
        if len(message_ids) > 10:
            await event.reply(
                f"<blockquote>✘ ᴛᴇʀʟᴀʟᴜ ʙᴀɴʏᴀᴋ! ᴍᴀᴋsɪᴍᴀʟ 10 ᴘᴇsᴀɴ\n"
                f"✓ ʀᴇǫᴜᴇsᴛ: {len(message_ids)}</blockquote>",
                parse_mode='html'
            )
            return
        
        processing_msg = await event.reply(
            f"<blockquote>⛧ ᴍᴇɴɢᴀᴍʙɪʟ {len(message_ids)} ᴋᴏɴᴛᴇɴ...\n"
            f"✘ ᴍᴏʜᴏɴ ᴛᴜɴɢɢᴜ</blockquote>",
            parse_mode='html'
        )
        
        try:
            # Get chat entity
            if chat_username.startswith('-'):  # ID numeric
                chat = await user.get_entity(int(chat_username))
            else:
                chat = await user.get_entity(chat_username)
            
            successful = 0
            failed = 0
            
            for i, msg_id in enumerate(message_ids):
                try:
                    await processing_msg.edit(
                        f"<blockquote>⛧ ᴍᴇɴɢᴀᴍʙɪʟ {len(message_ids)} ᴋᴏɴᴛᴇɴ...\n"
                        f"✘ sᴇᴅᴀɴɢ: {i+1}/{len(message_ids)}\n"
                        f"✓ ʙᴇʀʜᴀsɪʟ: {successful} | ɢᴀɢᴀʟ: {failed}</blockquote>",
                        parse_mode='html'
                    )
                    
                    msg = await user.get_messages(chat, ids=msg_id)
                    
                    if msg and msg.media:
                        # Download file
                        file_path = await msg.download_media(file='temp/')
                        if file_path:
                            # Send file
                            await user.send_file(
                                event.chat_id,
                                file_path,
                                caption=f"<blockquote>✓ ᴅᴀʀɪ: {getattr(chat, 'title', 'Unknown')}\n✘ ɪᴅ: {msg_id}</blockquote>",
                                parse_mode='html'
                            )
                            successful += 1
                            
                            # Cleanup
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        else:
                            failed += 1
                    elif msg and msg.text:
                        await event.respond(
                            f"<blockquote>✓ ᴅᴀʀɪ: {getattr(chat, 'title', 'Unknown')}\n✘ ɪᴅ: {msg_id}</blockquote>\n\n{msg.text}",
                            parse_mode='html'
                        )
                        successful += 1
                    else:
                        failed += 1
                    
                    await asyncio.sleep(1)  # Delay antar pesan
                    
                except Exception as e:
                    failed += 1
            
            await processing_msg.edit(
                f"<blockquote>✓ ᴘʀᴏsᴇs sᴇʟᴇsᴀɪ!\n"
                f"✘ ᴛᴏᴛᴀʟ: {len(message_ids)}\n"
                f"✓ ʙᴇʀʜᴀsɪʟ: {successful}\n"
                f"✘ ɢᴀɢᴀʟ: {failed}</blockquote>",
                parse_mode='html'
            )
            
        except Exception as e:
            await processing_msg.edit(
                f"<blockquote>✘ ɢᴀɢᴀʟ ᴍᴜʟᴛɪɢʀᴀʙ\n"
                f"✓ ᴇʀʀᴏʀ: {str(e)[:100]}</blockquote>",
                parse_mode='html'
            )