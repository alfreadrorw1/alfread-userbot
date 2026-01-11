import json
import os
import time
import asyncio
from telethon import events
from telethon.tl.types import Channel, Chat, User
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
        await client.send_message('SpamBot', '/start')
        await asyncio.sleep(1)
        
        async for message in client.iter_messages('SpamBot', limit=1):
            if message.sender_id == 178220800:
                return message.text
        
        return "Tidak dapat mengambil informasi limit dari SpamBot"
    except Exception as e:
        return f"Error: {str(e)}"

def setup(bot, user):
    
    @user.on(events.NewMessage())
    async def info_command_handler(event):
        """Handle info commands (id, info, limit)"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Helper function untuk mendapatkan informasi chat
        async def get_chat_info(event):
            chat = await event.get_chat()
            info = {}
            
            if event.is_private:
                # Chat pribadi (User)
                info['type'] = "Private"
                info['id'] = chat.id
                
                # Nama dengan link
                if chat.username:
                    info['name'] = f'<a href="https://t.me/{chat.username}">{chat.first_name or ""} {chat.last_name or ""}</a>'
                else:
                    full_name = f'{chat.first_name or ""} {chat.last_name or ""}'.strip()
                    info['name'] = f'<b>{full_name}</b>' if full_name else '<b>No Name</b>'
                
                # Informasi tambahan untuk user
                info['username'] = f'@{chat.username}' if chat.username else 'None'
                info['is_bot'] = chat.bot
                info['is_verified'] = chat.verified
                info['is_scam'] = chat.scam
                info['is_fake'] = chat.fake
                info['is_premium'] = getattr(chat, 'premium', False)
                info['dc_id'] = getattr(chat, 'dc_id', 'Unknown')
                
            else:
                # Group atau Channel
                info['id'] = chat.id
                info['title'] = chat.title or "Unknown"
                
                # Link untuk grup/channel
                if hasattr(chat, 'username') and chat.username:
                    info['link'] = f'https://t.me/{chat.username}'
                    info['name_with_link'] = f'<a href="https://t.me/{chat.username}">{chat.title}</a>'
                else:
                    info['link'] = 'No Public Link'
                    info['name_with_link'] = f'<b>{chat.title}</b>'
                
                # Tipe chat
                if isinstance(chat, Channel):
                    if chat.broadcast:
                        info['type'] = "Channel"
                        info['is_public'] = hasattr(chat, 'username') and chat.username is not None
                    else:
                        info['type'] = "Supergroup"
                        info['is_public'] = hasattr(chat, 'username') and chat.username is not None
                else:
                    info['type'] = "Group"
                
                # Informasi tambahan untuk grup/channel
                info['participants_count'] = getattr(chat, 'participants_count', 'Unknown')
                info['is_verified'] = getattr(chat, 'verified', False)
                info['is_scam'] = getattr(chat, 'scam', False)
                info['is_fake'] = getattr(chat, 'fake', False)
                info['is_restricted'] = getattr(chat, 'restricted', False)
                info['dc_id'] = getattr(chat, 'dc_id', 'Unknown')
                info['date_created'] = getattr(chat, 'date', 'Unknown')
            
            return info
        
        # ========== ID COMMAND ==========
        if current_prefix != "no":
            if message.startswith(current_prefix):
                cmd_text = message[len(current_prefix):].strip().lower()
                
                # ID command
                if cmd_text == 'id':
                    chat_info = await get_chat_info(event)
                    
                    response = "<blockquote>Informasi Chat:\n"
                    response += f"├ ID: <code>{chat_info['id']}</code>\n"
                    
                    if event.is_private:
                        response += f"├ Tipe: {chat_info['type']}\n"
                        response += f"├ Nama: {chat_info['name']}\n"
                        response += f"├ Username: {chat_info['username']}\n"
                        response += f"├ Bot: {chat_info['is_bot']}\n"
                        response += f"├ Verified: {chat_info['is_verified']}\n"
                        response += f"├ Scam: {chat_info['is_scam']}\n"
                        response += f"├ Fake: {chat_info['is_fake']}\n"
                        response += f"├ Premium: {chat_info['is_premium']}\n"
                        response += f"└ DC ID: {chat_info['dc_id']}</blockquote>"
                    else:
                        response += f"├ Tipe: {chat_info['type']}\n"
                        response += f"├ Nama: {chat_info['name_with_link']}\n"
                        response += f"├ Link: {chat_info['link']}\n"
                        response += f"├ Public: {chat_info['is_public']}\n"
                        response += f"├ Verified: {chat_info['is_verified']}\n"
                        response += f"├ Scam: {chat_info['is_scam']}\n"
                        response += f"├ Fake: {chat_info['is_fake']}\n"
                        response += f"├ Restricted: {chat_info['is_restricted']}\n"
                        response += f"├ Participants: {chat_info['participants_count']}\n"
                        response += f"└ DC ID: {chat_info['dc_id']}</blockquote>"
                    
                    await event.respond(response, parse_mode='html')
                
                # INFO command
                elif cmd_text == 'info':
                    me = await user.get_me()
                    uptime = get_uptime()
                    
                    # Get bot info
                    bot_info = f"├ ID: <code>{me.id}</code>\n"
                    bot_info += f"├ Username: @{me.username}\n" if me.username else "├ Username: None\n"
                    bot_info += f"├ First Name: {me.first_name}\n"
                    bot_info += f"├ Last Name: {me.last_name}\n" if me.last_name else ""
                    bot_info += f"├ Bot: {me.bot}\n"
                    bot_info += f"├ Verified: {me.verified}\n"
                    bot_info += f"├ Scam: {me.scam}\n"
                    bot_info += f"├ Fake: {me.fake}\n"
                    bot_info += f"├ DC ID: {me.dc_id}\n"
                    bot_info += f"└ Uptime: <b>{uptime}</b>"
                    
                    await event.respond(
                        f"<blockquote>Informasi Bot:\n{bot_info}</blockquote>",
                        parse_mode='html'
                    )
                
                # LIMIT command
                elif cmd_text == 'limit':
                    msg = await event.respond("<blockquote>Mengambil informasi limit dari @SpamBot...</blockquote>", parse_mode='html')
                    
                    try:
                        limit_info = await check_spam_limit(user)
                        
                        await msg.edit(
                            f"<blockquote>Informasi Limit Spam:\n"
                            f"<code>{limit_info}</code></blockquote>",
                            parse_mode='html'
                        )
                    except Exception as e:
                        await msg.edit(
                            f"<blockquote>Error:\n"
                            f"<code>{str(e)}</code></blockquote>",
                            parse_mode='html'
                        )
        else:
            # For "no" prefix mode
            # ID command
            if message.lower() == 'id':
                chat_info = await get_chat_info(event)
                
                response = "<blockquote>Informasi Chat:\n"
                response += f"├ ID: <code>{chat_info['id']}</code>\n"
                
                if event.is_private:
                    response += f"├ Tipe: {chat_info['type']}\n"
                    response += f"├ Nama: {chat_info['name']}\n"
                    response += f"├ Username: {chat_info['username']}\n"
                    response += f"├ Bot: {chat_info['is_bot']}\n"
                    response += f"├ Verified: {chat_info['is_verified']}\n"
                    response += f"├ Scam: {chat_info['is_scam']}\n"
                    response += f"├ Fake: {chat_info['is_fake']}\n"
                    response += f"├ Premium: {chat_info['is_premium']}\n"
                    response += f"└ DC ID: {chat_info['dc_id']}</blockquote>"
                else:
                    response += f"├ Tipe: {chat_info['type']}\n"
                    response += f"├ Nama: {chat_info['name_with_link']}\n"
                    response += f"├ Link: {chat_info['link']}\n"
                    response += f"├ Public: {chat_info['is_public']}\n"
                    response += f"├ Verified: {chat_info['is_verified']}\n"
                    response += f"├ Scam: {chat_info['is_scam']}\n"
                    response += f"├ Fake: {chat_info['is_fake']}\n"
                    response += f"├ Restricted: {chat_info['is_restricted']}\n"
                    response += f"├ Participants: {chat_info['participants_count']}\n"
                    response += f"└ DC ID: {chat_info['dc_id']}</blockquote>"
                
                await event.respond(response, parse_mode='html')
            
            # INFO command
            elif message.lower() == 'info':
                me = await user.get_me()
                uptime = get_uptime()
                
                # Get bot info
                bot_info = f"├ ID: <code>{me.id}</code>\n"
                bot_info += f"├ Username: @{me.username}\n" if me.username else "├ Username: None\n"
                bot_info += f"├ First Name: {me.first_name}\n"
                bot_info += f"├ Last Name: {me.last_name}\n" if me.last_name else ""
                bot_info += f"├ Bot: {me.bot}\n"
                bot_info += f"├ Verified: {me.verified}\n"
                bot_info += f"├ Scam: {me.scam}\n"
                bot_info += f"├ Fake: {me.fake}\n"
                bot_info += f"├ DC ID: {me.dc_id}\n"
                bot_info += f"└ Uptime: <b>{uptime}</b>"
                
                await event.respond(
                    f"<blockquote>Informasi Bot:\n{bot_info}</blockquote>",
                    parse_mode='html'
                )
            
            # LIMIT command
            elif message.lower() == 'limit':
                msg = await event.respond("<blockquote>Mengambil informasi limit dari @SpamBot...</blockquote>", parse_mode='html')
                
                try:
                    limit_info = await check_spam_limit(user)
                    
                    await msg.edit(
                        f"<blockquote>Informasi Limit Spam:\n"
                        f"<code>{limit_info}</code></blockquote>",
                        parse_mode='html'
                    )
                except Exception as e:
                    await msg.edit(
                        f"<blockquote>Error:\n"
                        f"<code>{str(e)}</code></blockquote>",
                        parse_mode='html'
                    )