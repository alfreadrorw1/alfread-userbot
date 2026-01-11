import json
import os
import time
from telethon import events
from datetime import datetime
from config import OWNER_ID

def get_prefix():
    """Get current prefix from config (supports 'no' prefix mode)"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def get_uptime():
    """Calculate bot uptime in human-readable format"""
    try:
        with open('data/uptime.json', 'r') as f:
            start_time = json.load(f).get('start_time', time.time())
    except (FileNotFoundError, json.JSONDecodeError):
        start_time = time.time()
        os.makedirs('data', exist_ok=True)
        with open('data/uptime.json', 'w') as f:
            json.dump({'start_time': start_time}, f)
    
    uptime = int(time.time() - start_time)
    days, remainder = divmod(uptime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    
    return ' '.join(parts)

async def check_spam_limit(client):
    """Check spam limit from @SpamBot"""
    try:
        # Kirim pesan ke @SpamBot
        await client.send_message('SpamBot', '/start')
        await asyncio.sleep(1)  # Tunggu respon
        
        # Ambil pesan terakhir dari @SpamBot
        async for message in client.iter_messages('SpamBot', limit=1):
            if message.sender_id == 178220800:  # ID @SpamBot
                return message.text
        
        return "✘ ɢᴀɢᴀʟ ᴍᴇɴɢᴀᴍʙɪʟ ɪɴғᴏ ʟɪᴍɪᴛ"
    except Exception as e:
        return f"✘ ᴇʀʀᴏʀ: {str(e)}"

def setup(bot, user):
    
    @user.on(events.NewMessage())
    async def info_command_handler(event):
        """Handle info commands (id, info, limit)"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # ========== ID COMMAND ==========
        if current_prefix != "no":
            if message.startswith(current_prefix):
                cmd_text = message[len(current_prefix):].strip().lower()
                
                # ID command
                if cmd_text == 'id':
                    if event.is_private:
                        # Chat pribadi
                        chat_id = event.chat_id
                        chat_title = "Private Chat"
                        chat_type = "PM"
                    else:
                        # Grup/channel
                        chat_id = event.chat_id
                        chat_title = event.chat.title if event.chat.title else "Unknown"
                        chat_type = "Group" if event.is_group else "Channel"
                    
                    await event.respond(
                        f"<blockquote>✘ ᴄʜᴀᴛ ɪɴғᴏ:\n"
                        f"✞ ᴛɪᴛʟᴇ: <b>{chat_title}</b>\n"
                        f"⛧ ɪᴅ: <code>{chat_id}</code>\n"
                        f"✞ ᴛʏᴘᴇ: <b>{chat_type}</b></blockquote>",
                        parse_mode='html'
                    )
                
                # INFO command
                elif cmd_text == 'info':
                    me = await user.get_me()
                    uptime = get_uptime()
                    
                    # Get bot info
                    bot_info = f"⛧ ɪᴅ: <code>{me.id}</code>\n"
                    bot_info += f"✘ ᴜsᴇʀɴᴀᴍᴇ: @{me.username}\n" if me.username else "✘ ᴜsᴇʀɴᴀᴍᴇ: None\n"
                    bot_info += f"✞ ғɪʀsᴛ ɴᴀᴍᴇ: {me.first_name}\n"
                    bot_info += f"✘ ʟᴀsᴛ ɴᴀᴍᴇ: {me.last_name}\n" if me.last_name else ""
                    bot_info += f"⛧ ᴜᴘᴛɪᴍᴇ: <b>{uptime}</b>"
                    
                    await event.respond(
                        f"<blockquote>✘ ʙᴏᴛ ɪɴғᴏ:\n{bot_info}</blockquote>",
                        parse_mode='html'
                    )
                
                # LIMIT command
                elif cmd_text == 'limit':
                    msg = await event.respond("<blockquote>✞ ᴍᴇɴɢʜᴜʙᴜɴɢɪ @sᴘᴀᴍʙᴏᴛ...</blockquote>", parse_mode='html')
                    
                    try:
                        # Import asyncio untuk sleep
                        import asyncio
                        
                        # Kirim pesan ke @SpamBot
                        await user.send_message('SpamBot', '/start')
                        await asyncio.sleep(2)  # Tunggu respon
                        
                        # Ambil pesan terakhir dari @SpamBot
                        limit_info = "✘ ɢᴀɢᴀʟ ᴍᴇɴɢᴀᴍʙɪʟ ɪɴғᴏ ʟɪᴍɪᴛ"
                        async for message in user.iter_messages('SpamBot', limit=1):
                            if message.sender_id == 178220800:  # ID @SpamBot
                                limit_info = message.text
                                break
                        
                        # Format pesan limit
                        await msg.edit(
                            f"<blockquote>✘ sᴘᴀᴍ ʟɪᴍɪᴛ ɪɴғᴏ:\n"
                            f"<code>{limit_info}</code></blockquote>",
                            parse_mode='html'
                        )
                    except Exception as e:
                        await msg.edit(
                            f"<blockquote>✘ ᴇʀʀᴏʀ:\n"
                            f"<code>{str(e)}</code></blockquote>",
                            parse_mode='html'
                        )
        else:
            # For "no" prefix mode
            # ID command
            if message.lower() == 'id':
                if event.is_private:
                    # Chat pribadi
                    chat_id = event.chat_id
                    chat_title = "Private Chat"
                    chat_type = "PM"
                else:
                    # Grup/channel
                    chat_id = event.chat_id
                    chat_title = event.chat.title if event.chat.title else "Unknown"
                    chat_type = "Group" if event.is_group else "Channel"
                
                await event.respond(
                    f"<blockquote>✘ ᴄʜᴀᴛ ɪɴғᴏ:\n"
                    f"✞ ᴛɪᴛʟᴇ: <b>{chat_title}</b>\n"
                    f"⛧ ɪᴅ: <code>{chat_id}</code>\n"
                    f"✞ ᴛʏᴘᴇ: <b>{chat_type}</b></blockquote>",
                    parse_mode='html'
                )
            
            # INFO command
            elif message.lower() == 'info':
                me = await user.get_me()
                uptime = get_uptime()
                
                # Get bot info
                bot_info = f"⛧ ɪᴅ: <code>{me.id}</code>\n"
                bot_info += f"✘ ᴜsᴇʀɴᴀᴍᴇ: @{me.username}\n" if me.username else "✘ ᴜsᴇʀɴᴀᴍᴇ: None\n"
                bot_info += f"✞ ғɪʀsᴄ ɴᴀᴍᴇ: {me.first_name}\n"
                bot_info += f"✘ ʟᴀsᴛ ɴᴀᴍᴇ: {me.last_name}\n" if me.last_name else ""
                bot_info += f"⛧ ᴜᴘᴛɪᴍᴇ: <b>{uptime}</b>"
                
                await event.respond(
                    f"<blockquote>✘ ʙᴏᴛ ɪɴғᴏ:\n{bot_info}</blockquote>",
                    parse_mode='html'
                )
            
            # LIMIT command
            elif message.lower() == 'limit':
                msg = await event.respond("<blockquote>✞ ᴍᴇɴɢʜᴜʙᴜɴɢɪ @sᴘᴀᴍʙᴏᴛ...</blockquote>", parse_mode='html')
                
                try:
                    # Import asyncio untuk sleep
                    import asyncio
                    
                    # Kirim pesan ke @SpamBot
                    await user.send_message('SpamBot', '/start')
                    await asyncio.sleep(2)  # Tunggu respon
                    
                    # Ambil pesan terakhir dari @SpamBot
                    limit_info = "✘ ɢᴀɢᴀʟ ᴍᴇɴɢᴀᴍʙɪʟ ɪɴғᴏ ʟɪᴍɪᴛ"
                    async for message in user.iter_messages('SpamBot', limit=1):
                        if message.sender_id == 178220800:  # ID @SpamBot
                            limit_info = message.text
                            break
                    
                    # Format pesan limit
                    await msg.edit(
                        f"<blockquote>✘ sᴘᴀᴍ ʟɪᴍɪᴛ ɪɴғᴏ:\n"
                        f"<code>{limit_info}</code></blockquote>",
                        parse_mode='html'
                    )
                except Exception as e:
                    await msg.edit(
                        f"<blockquote>✘ ᴇʀʀᴏʀ:\n"
                        f"<code>{str(e)}</code></blockquote>",
                        parse_mode='html'
                    )