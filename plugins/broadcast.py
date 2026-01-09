import time
import json
import os
import asyncio
from telethon import events
from telethon.tl.types import User, Chat, Channel, UserEmpty
from telethon.errors import FloodWaitError, ChannelPrivateError
from config import OWNER_ID

# File untuk menyimpan blacklist
BLACKLIST_FILE = 'data/blacklist.json'

def get_prefix():
    """Get current prefix from config"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def load_blacklist():
    """Load blacklist data"""
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            data = json.load(f)
            # Pastikan semua key ada
            if 'group_dates' not in data:
                data['group_dates'] = {}
            if 'user_dates' not in data:
                data['user_dates'] = {}
            if 'group_names' not in data:
                data['group_names'] = {}
            if 'user_names' not in data:
                data['user_names'] = {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        default_data = {
            'groups': [],
            'users': [],
            'group_names': {},
            'user_names': {},
            'group_dates': {},
            'user_dates': {}
        }
        os.makedirs('data', exist_ok=True)
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data

def save_blacklist(data):
    """Save blacklist data"""
    os.makedirs('data', exist_ok=True)
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_to_blacklist(entity_id, entity_type, entity_name):
    """Add entity to blacklist"""
    data = load_blacklist()
    
    if entity_type == 'group':
        if entity_id not in data['groups']:
            data['groups'].append(entity_id)
            data['group_names'][str(entity_id)] = entity_name
            data['group_dates'][str(entity_id)] = time.time()
    elif entity_type == 'user':
        if entity_id not in data['users']:
            data['users'].append(entity_id)
            data['user_names'][str(entity_id)] = entity_name
            data['user_dates'][str(entity_id)] = time.time()
    
    save_blacklist(data)
    return True

def remove_from_blacklist(entity_id, entity_type):
    """Remove entity from blacklist"""
    data = load_blacklist()
    
    if entity_type == 'group':
        if entity_id in data['groups']:
            data['groups'].remove(entity_id)
            data['group_names'].pop(str(entity_id), None)
            data['group_dates'].pop(str(entity_id), None)
    elif entity_type == 'user':
        if entity_id in data['users']:
            data['users'].remove(entity_id)
            data['user_names'].pop(str(entity_id), None)
            data['user_dates'].pop(str(entity_id), None)
    
    save_blacklist(data)
    return True

def is_bot_user(user):
    """Check if a user is a bot"""
    return getattr(user, 'bot', False)

def format_time(timestamp):
    """Format timestamp to readable time"""
    if not timestamp:
        return "Unknown"
    
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")

def setup(bot, user):
    
    # ========== GCAST COMMAND ==========
    @user.on(events.NewMessage())
    async def gcast_handler(event):
        """Broadcast message to all groups"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check for gcast command
        is_gcast = False
        command_text = ""
        
        if current_prefix == "no" and message.lower().startswith('gcast '):
            is_gcast = True
            command_text = message[6:]
        elif current_prefix != "no" and message.startswith(current_prefix):
            cmd_part = message[len(current_prefix):].strip()
            if cmd_part.lower().startswith('gcast '):
                is_gcast = True
                command_text = cmd_part[6:]
        
        if not is_gcast:
            return
        
        # Get the message to broadcast
        broadcast_msg = command_text.strip()
        
        if event.is_reply:
            try:
                replied = await event.get_reply_message()
                if replied.text or replied.media:
                    replied_msg = replied
                else:
                    replied_msg = None
            except:
                replied_msg = None
        else:
            replied_msg = None
        
        if not broadcast_msg and not replied_msg:
            await event.reply(
                "<blockquote>✘ ᴜsᴀɢᴇ: gcast &lt;ᴍᴇssᴀɢᴇ&gt;\n"
                "✓ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ ɢᴄᴀsᴛ</blockquote>",
                parse_mode='html'
            )
            return
        
        # Start broadcasting
        processing_msg = await event.reply(
            "<blockquote>⛧ sᴛᴀʀᴛɪɴɢ ɢʀᴏᴜᴘ ʙʀᴏᴀᴅᴄᴀsᴛ...\n"
            "✘ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</blockquote>",
            parse_mode='html'
        )
        
        blacklist_data = load_blacklist()
        dialogs = await user.get_dialogs()
        
        groups_sent = 0
        groups_failed = 0
        total_groups = 0
        
        # Count total groups first
        for dialog in dialogs:
            if dialog.is_group and dialog.entity.id not in blacklist_data['groups']:
                total_groups += 1
        
        if total_groups == 0:
            await processing_msg.edit(
                "<blockquote>✘ ɴᴏ ɢʀᴏᴜᴘs ғᴏᴜɴᴅ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ\n"
                "⛧ ᴄʜᴇᴄᴋ ɪғ ᴀʟʟ ɢʀᴏᴜᴘs ᴀʀᴇ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ</blockquote>",
                parse_mode='html'
            )
            return
        
        await processing_msg.edit(
            f"<blockquote>⛧ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {total_groups} ɢʀᴏᴜᴘs...\n"
            f"✘ 0/{total_groups} sᴇɴᴛ\n"
            f"✓ 0 ғᴀɪʟᴇᴅ</blockquote>",
            parse_mode='html'
        )
        
        # Send to groups
        for dialog in dialogs:
            if dialog.is_group and dialog.entity.id not in blacklist_data['groups']:
                try:
                    if replied_msg and replied_msg.media:
                        await user.send_message(dialog.entity, broadcast_msg, file=replied_msg.media)
                    elif replied_msg:
                        await user.send_message(dialog.entity, replied_msg.text)
                    else:
                        await user.send_message(dialog.entity, broadcast_msg)
                    
                    groups_sent += 1
                    
                    # Update progress every 5 groups
                    if groups_sent % 5 == 0:
                        await processing_msg.edit(
                            f"<blockquote>⛧ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {total_groups} ɢʀᴏᴜᴘs...\n"
                            f"✘ {groups_sent}/{total_groups} sᴇɴᴛ\n"
                            f"✓ {groups_failed} ғᴀɪʟᴇᴅ</blockquote>",
                            parse_mode='html'
                        )
                    
                    # Small delay to avoid flood
                    await asyncio.sleep(0.5)
                    
                except FloodWaitError as e:
                    await processing_msg.edit(
                        f"<blockquote>⛧ ғʟᴏᴏᴅ ᴡᴀɪᴛ: {e.seconds}s\n"
                        f"✘ ᴡᴀɪᴛɪɴɢ...</blockquote>",
                        parse_mode='html'
                    )
                    await asyncio.sleep(e.seconds)
                    try:
                        if replied_msg and replied_msg.media:
                            await user.send_message(dialog.entity, broadcast_msg, file=replied_msg.media)
                        elif replied_msg:
                            await user.send_message(dialog.entity, replied_msg.text)
                        else:
                            await user.send_message(dialog.entity, broadcast_msg)
                        groups_sent += 1
                    except Exception as e:
                        groups_failed += 1
                except Exception as e:
                    groups_failed += 1
        
        # Final result
        await processing_msg.edit(
            f"<blockquote>✓ ɢʀᴏᴜᴘ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!\n"
            f"✘ ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs: {total_groups}\n"
            f"✓ sᴜᴄᴄᴇssғᴜʟ: {groups_sent}\n"
            f"✘ ғᴀɪʟᴇᴅ: {groups_failed}</blockquote>",
            parse_mode='html'
        )
    
    # ========== UCAST COMMAND ==========
    @user.on(events.NewMessage())
    async def ucast_handler(event):
        """Broadcast message to all users (excluding bots)"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check for ucast command
        is_ucast = False
        command_text = ""
        
        if current_prefix == "no" and message.lower().startswith('ucast '):
            is_ucast = True
            command_text = message[6:]
        elif current_prefix != "no" and message.startswith(current_prefix):
            cmd_part = message[len(current_prefix):].strip()
            if cmd_part.lower().startswith('ucast '):
                is_ucast = True
                command_text = cmd_part[6:]
        
        if not is_ucast:
            return
        
        # Get the message to broadcast
        broadcast_msg = command_text.strip()
        
        if event.is_reply:
            try:
                replied = await event.get_reply_message()
                if replied.text or replied.media:
                    replied_msg = replied
                else:
                    replied_msg = None
            except:
                replied_msg = None
        else:
            replied_msg = None
        
        if not broadcast_msg and not replied_msg:
            await event.reply(
                "<blockquote>✘ ᴜsᴀɢᴇ: ucast &lt;ᴍᴇssᴀɢᴇ&gt;\n"
                "✓ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ ucast</blockquote>",
                parse_mode='html'
            )
            return
        
        # Start broadcasting
        processing_msg = await event.reply(
            "<blockquote>⛧ sᴛᴀʀᴛɪɴɢ ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ...\n"
            "✘ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ (sᴋɪᴘᴘɪɴɢ ʙᴏᴛs)...</blockquote>",
            parse_mode='html'
        )
        
        blacklist_data = load_blacklist()
        dialogs = await user.get_dialogs()
        
        users_sent = 0
        users_failed = 0
        bots_skipped = 0
        total_users = 0
        
        # Count total users first (excluding bots, owner, and blacklisted)
        for dialog in dialogs:
            if dialog.is_user:
                try:
                    user_entity = dialog.entity
                    # Skip if: owner, blacklisted, bot, or empty user
                    if (user_entity.id == OWNER_ID or 
                        user_entity.id in blacklist_data['users'] or
                        isinstance(user_entity, UserEmpty)):
                        continue
                    
                    # Check if it's a bot
                    if is_bot_user(user_entity):
                        bots_skipped += 1
                        continue
                    
                    total_users += 1
                except:
                    continue
        
        if total_users == 0:
            await processing_msg.edit(
                "<blockquote>✘ ɴᴏ ᴜsᴇʀs ғᴏᴜɴᴅ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ\n"
                f"✓ ʙᴏᴛs sᴋɪᴘᴘᴇᴅ: {bots_skipped}</blockquote>",
                parse_mode='html'
            )
            return
        
        await processing_msg.edit(
            f"<blockquote>⛧ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {total_users} ᴜsᴇʀs...\n"
            f"✘ 0/{total_users} sᴇɴᴛ\n"
            f"✓ 0 ғᴀɪʟᴇᴅ | ʙᴏᴛs: {bots_skipped}</blockquote>",
            parse_mode='html'
        )
        
        # Send to users
        for dialog in dialogs:
            if dialog.is_user:
                try:
                    user_entity = dialog.entity
                    
                    # Skip conditions
                    if (user_entity.id == OWNER_ID or 
                        user_entity.id in blacklist_data['users'] or
                        isinstance(user_entity, UserEmpty)):
                        continue
                    
                    # Skip bots
                    if is_bot_user(user_entity):
                        continue
                    
                    # Send message
                    if replied_msg and replied_msg.media:
                        await user.send_message(user_entity, broadcast_msg, file=replied_msg.media)
                    elif replied_msg:
                        await user.send_message(user_entity, replied_msg.text)
                    else:
                        await user.send_message(user_entity, broadcast_msg)
                    
                    users_sent += 1
                    
                    # Update progress every 10 users
                    if users_sent % 10 == 0:
                        await processing_msg.edit(
                            f"<blockquote>⛧ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {total_users} ᴜsᴇʀs...\n"
                            f"✘ {users_sent}/{total_users} sᴇɴᴛ\n"
                            f"✓ {users_failed} ғᴀɪʟᴇᴅ | ʙᴏᴛs: {bots_skipped}</blockquote>",
                            parse_mode='html'
                        )
                    
                    # Small delay to avoid flood
                    await asyncio.sleep(0.3)
                    
                except FloodWaitError as e:
                    await processing_msg.edit(
                        f"<blockquote>⛧ ғʟᴏᴏᴅ ᴡᴀɪᴛ: {e.seconds}s\n"
                        f"✘ ᴡᴀɪᴛɪɴɢ...</blockquote>",
                        parse_mode='html'
                    )
                    await asyncio.sleep(e.seconds)
                    try:
                        if replied_msg and replied_msg.media:
                            await user.send_message(user_entity, broadcast_msg, file=replied_msg.media)
                        elif replied_msg:
                            await user.send_message(user_entity, replied_msg.text)
                        else:
                            await user.send_message(user_entity, broadcast_msg)
                        users_sent += 1
                    except:
                        users_failed += 1
                except (ChannelPrivateError, ValueError):
                    # Skip private/deleted users
                    users_failed += 1
                except Exception:
                    users_failed += 1
        
        # Final result
        await processing_msg.edit(
            f"<blockquote>✓ ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!\n"
            f"✘ ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total_users}\n"
            f"✓ sᴜᴄᴄᴇssғᴜʟ: {users_sent}\n"
            f"✘ ғᴀɪʟᴇᴅ: {users_failed}\n"
            f"✓ ʙᴏᴛs sᴋɪᴘᴘᴇᴅ: {bots_skipped}</blockquote>",
            parse_mode='html'
        )
    
    # ========== ADDBL COMMAND ==========
    @user.on(events.NewMessage())
    async def addbl_handler(event):
        """Add user/group to blacklist (multiple methods)"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check for addbl command
        is_addbl = False
        command_text = ""
        
        # Method 1: With prefix
        if current_prefix != "no" and message.startswith(current_prefix):
            cmd_part = message[len(current_prefix):].strip()
            if cmd_part.lower().startswith('addbl'):
                is_addbl = True
                command_text = cmd_part[5:].strip()
        
        # Method 2: Without prefix
        elif current_prefix == "no" and message.lower().startswith('addbl'):
            is_addbl = True
            command_text = message[5:].strip()
        
        if not is_addbl:
            return
        
        # Method A: Jika ada reply ke pesan user
        if event.is_reply:
            try:
                replied = await event.get_reply_message()
                if replied.sender_id:
                    # Ini adalah pesan dari user dalam group
                    user_entity = await user.get_entity(replied.sender_id)
                    
                    if isinstance(user_entity, User):
                        entity_type = 'user'
                        entity_name = f"{user_entity.first_name or ''} {user_entity.last_name or ''}".strip() or f"User {user_entity.id}"
                        entity_id = user_entity.id
                        
                        # Tambahkan ke blacklist
                        add_to_blacklist(entity_id, entity_type, entity_name)
                        
                        await event.reply(
                            f"<blockquote>✓ ᴜsᴇʀ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ!\n"
                            f"✘ ɪᴅ: <code>{entity_id}</code>\n"
                            f"✓ ɴᴀᴍᴇ: {entity_name}\n"
                            f"✘ ᴅᴀᴛᴇ: {format_time(time.time())}</blockquote>",
                            parse_mode='html'
                        )
                        return
            except Exception as e:
                # Jika gagal, lanjut ke method lain
                pass
        
        # Method B: Jika dalam group dan tidak ada reply -> blacklist groupnya
        try:
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            if isinstance(chat, (Chat, Channel)) and not isinstance(chat, User):
                # Ini adalah group/channel
                entity_type = 'group'
                entity_name = chat.title or f"Group {chat_id}"
                
                # Tambahkan ke blacklist
                add_to_blacklist(chat_id, entity_type, entity_name)
                
                await event.reply(
                    f"<blockquote>✓ ɢʀᴏᴜᴘ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ!\n"
                    f"✘ ɪᴅ: <code>{chat_id}</code>\n"
                    f"✓ ɴᴀᴍᴇ: {entity_name}\n"
                    f"✘ ᴅᴀᴛᴇ: {format_time(time.time())}</blockquote>",
                    parse_mode='html'
                )
                return
                
            elif isinstance(chat, User):
                # Ini adalah chat pribadi dengan user
                entity_type = 'user'
                entity_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip() or f"User {chat_id}"
                
                # Tambahkan ke blacklist
                add_to_blacklist(chat_id, entity_type, entity_name)
                
                await event.reply(
                    f"<blockquote>✓ ᴜsᴇʀ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ!\n"
                    f"✘ ɪᴅ: <code>{chat_id}</code>\n"
                    f"✓ ɴᴀᴍᴇ: {entity_name}\n"
                    f"✘ ᴅᴀᴛᴇ: {format_time(time.time())}</blockquote>",
                    parse_mode='html'
                )
                return
                
        except Exception as e:
            await event.reply(
                f"<blockquote>✘ ᴇʀʀᴏʀ: {str(e)[:100]}</blockquote>",
                parse_mode='html'
            )
            return
        
        # Jika semua method gagal
        await event.reply(
            "<blockquote>✘ ᴄᴏᴜʟᴅ ɴᴏᴛ ɪᴅᴇɴᴛɪғʏ ᴇɴᴛɪᴛʏ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ\n"
            "✓ ᴜsᴀɢᴇ ɪɴ ɢʀᴏᴜᴘ: ᴀᴅᴅʙʟ (ʙʟᴀᴄᴋʟɪsᴛs ᴛʜᴇ ɢʀᴏᴜᴘ)\n"
            "✘ ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ: ᴀᴅᴅʙʟ (ʙʟᴀᴄᴋʟɪsᴛs ᴛʜᴇ ᴜsᴇʀ)</blockquote>",
            parse_mode='html'
        )
    
    # ========== DELBL COMMAND ==========
    @user.on(events.NewMessage())
    async def delbl_handler(event):
        """Remove user/group from blacklist"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check for delbl command
        is_delbl = False
        command_text = ""
        
        # Method 1: With prefix
        if current_prefix != "no" and message.startswith(current_prefix):
            cmd_part = message[len(current_prefix):].strip()
            if cmd_part.lower().startswith('delbl'):
                is_delbl = True
                command_text = cmd_part[5:].strip()
        
        # Method 2: Without prefix
        elif current_prefix == "no" and message.lower().startswith('delbl'):
            is_delbl = True
            command_text = message[5:].strip()
        
        if not is_delbl:
            return
        
        if not command_text:
            await event.reply(
                "<blockquote>✘ ᴜsᴀɢᴇ: delbl &lt;ɪᴅ&gt;\n"
                "✓ ɢᴇᴛ ɪᴅ ғʀᴏᴍ ʟɪsᴛʙʟ</blockquote>",
                parse_mode='html'
            )
            return
        
        # Parse entity ID
        try:
            entity_id = int(command_text)
        except ValueError:
            await event.reply(
                "<blockquote>✘ ɪɴᴠᴀʟɪᴅ ɪᴅ! ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴜᴍᴇʀɪᴄ ɪᴅ</blockquote>",
                parse_mode='html'
            )
            return
        
        # Try to remove from blacklist
        blacklist_data = load_blacklist()
        entity_type = ""
        entity_name = ""
        removed = False
        
        if entity_id in blacklist_data['groups']:
            entity_type = 'group'
            entity_name = blacklist_data['group_names'].get(str(entity_id), "Unknown Group")
            remove_from_blacklist(entity_id, 'group')
            removed = True
        
        if entity_id in blacklist_data['users']:
            entity_type = 'user'
            entity_name = blacklist_data['user_names'].get(str(entity_id), "Unknown User")
            remove_from_blacklist(entity_id, 'user')
            removed = True
        
        if not removed:
            await event.reply(
                f"<blockquote>✘ ɪᴅ <code>{entity_id}</code> ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ʙʟᴀᴄᴋʟɪsᴛ</blockquote>",
                parse_mode='html'
            )
            return
        
        await event.reply(
            f"<blockquote>✓ {entity_type.upper()} ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ʙʟᴀᴄᴋʟɪsᴛ!\n"
            f"✘ ɪᴅ: <code>{entity_id}</code>\n"
            f"✓ ɴᴀᴍᴇ: {entity_name}</blockquote>",
            parse_mode='html'
        )
    
    # ========== LISTBL COMMAND ==========
    @user.on(events.NewMessage())
    async def listbl_handler(event):
        """List all blacklisted entities"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check for listbl command
        is_listbl = False
        
        if current_prefix == "no" and message == 'listbl':
            is_listbl = True
        elif current_prefix != "no" and message.startswith(current_prefix):
            cmd_part = message[len(current_prefix):].strip()
            if cmd_part == 'listbl':
                is_listbl = True
        
        if not is_listbl:
            return
        
        blacklist_data = load_blacklist()
        
        total_groups = len(blacklist_data['groups'])
        total_users = len(blacklist_data['users'])
        total = total_groups + total_users
        
        if total == 0:
            await event.reply(
                "<blockquote>⛧ ʙʟᴀᴄᴋʟɪsᴛ ɪs ᴇᴍᴘᴛʏ!\n"
                "✓ ɴᴏ ɢʀᴏᴜᴘs ᴏʀ ᴜsᴇʀs ʙʟᴀᴄᴋʟɪsᴛᴇᴅ</blockquote>",
                parse_mode='html'
            )
            return
        
        # Create message parts
        message_parts = []
        
        # Header
        message_parts.append(
            f"<blockquote>⛧ ʙʟᴀᴄᴋʟɪsᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
            f"✘ ɢʀᴏᴜᴘs: {total_groups}\n"
            f"✓ ᴜsᴇʀs: {total_users}\n"
            f"✘ ᴛᴏᴛᴀʟ: {total}\n\n"
        )
        
        # Groups section
        if total_groups > 0:
            message_parts.append("📁 <b>ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ɢʀᴏᴜᴘs:</b>\n")
            for group_id in blacklist_data['groups'][:15]:  # Limit to 15
                group_name = blacklist_data['group_names'].get(str(group_id), "Unknown Group")
                added_date = blacklist_data['group_dates'].get(str(group_id))
                date_str = format_time(added_date) if added_date else "Unknown"
                message_parts.append(f"  • <code>{group_id}</code> - {group_name} ({date_str})")
            
            if total_groups > 15:
                message_parts.append(f"  ... ᴀɴᴅ {total_groups - 15} ᴍᴏʀᴇ ɢʀᴏᴜᴘs")
            message_parts.append("")
        
        # Users section
        if total_users > 0:
            message_parts.append("👤 <b>ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴜsᴇʀs:</b>\n")
            for user_id in blacklist_data['users'][:15]:  # Limit to 15
                user_name = blacklist_data['user_names'].get(str(user_id), "Unknown User")
                added_date = blacklist_data['user_dates'].get(str(user_id))
                date_str = format_time(added_date) if added_date else "Unknown"
                message_parts.append(f"  • <code>{user_id}</code> - {user_name} ({date_str})")
            
            if total_users > 15:
                message_parts.append(f"  ... ᴀɴᴅ {total_users - 15} ᴍᴏʀᴇ ᴜsᴇʀs")
        
        message_parts.append("\n✘ ᴜsᴇ <code>delbl &lt;ɪᴅ&gt;</code> ᴛᴏ ʀᴇᴍᴏᴠᴇ")
        message_parts.append("</blockquote>")
        
        full_message = "\n".join(message_parts)
        
        # Split message if too long
        if len(full_message) > 4000:
            # Send in parts
            part1 = "\n".join(message_parts[:len(message_parts)//2])
            part2 = "\n".join(message_parts[len(message_parts)//2:])
            
            await event.reply(part1, parse_mode='html')
            await asyncio.sleep(1)
            await event.reply(part2, parse_mode='html')
        else:
            await event.reply(full_message, parse_mode='html')