import time
import json
import os
from telethon import events
from config import OWNER_ID

# ==================== AFK MODULE ====================

# File untuk menyimpan data AFK
AFK_FILE = 'data/afk.json'
# Cooldown untuk mencegah spam (dalam detik)
COOLDOWN_TIME = 60  # 1 menit
# Dictionary untuk menyimpan waktu terakhir notifikasi per user
last_notification = {}

def get_afk_data():
    """Mengambil data AFK dari file"""
    try:
        with open(AFK_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        default_data = {
            'is_afk': False,
            'reason': '',
            'start_time': None,
            'mentions': 0
        }
        with open(AFK_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data

def save_afk_data(data):
    """Menyimpan data AFK ke file"""
    os.makedirs('data', exist_ok=True)
    with open(AFK_FILE, 'w') as f:
        json.dump(data, f)

def format_afk_time(start_timestamp):
    """Format waktu AFK menjadi human readable"""
    if not start_timestamp:
        return "Unknown"
    
    duration = int(time.time() - start_timestamp)
    days, remainder = divmod(duration, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    
    return ' '.join(parts)

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

def setup(bot, user):
    
    # ========== AFK COMMAND HANDLERS ==========
    @user.on(events.NewMessage())
    async def afk_command_handler(event):
        """Handle AFK commands"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check for .afk command
        if current_prefix != "no":
            if message.startswith(current_prefix):
                cmd_text = message[len(current_prefix):].strip().lower()
                
                # AFK command
                if cmd_text.startswith('afk'):
                    reason = cmd_text[3:].strip()
                    if not reason:
                        reason = "No reason provided"
                    
                    afk_data = {
                        'is_afk': True,
                        'reason': reason,
                        'start_time': time.time(),
                        'mentions': 0
                    }
                    
                    save_afk_data(afk_data)
                    
                    await event.respond(
                        f"<blockquote>✘ ɪ'ᴍ ɴᴏᴡ ᴀғᴋ\n"
                        f"✞ ʀᴇᴀsᴏɴ: <b>{reason}</b></blockquote>",
                        parse_mode='html'
                    )
                
                # UNAFK command
                elif cmd_text == 'unafk':
                    afk_data = get_afk_data()
                    if afk_data['is_afk']:
                        afk_duration = format_afk_time(afk_data['start_time'])
                        mentions = afk_data['mentions']
                        
                        # Reset AFK data
                        afk_data['is_afk'] = False
                        afk_data['reason'] = ''
                        afk_data['start_time'] = None
                        afk_data['mentions'] = 0
                        save_afk_data(afk_data)
                        
                        await event.respond(
                            f"<blockquote>⛧ ɪ'ᴍ ʙᴀᴄᴋ ɴᴏᴡ!\n"
                            f"✞ ᴀғᴋ ғᴏʀ: <b>{afk_duration}</b>\n"
                            f"✘ ᴍᴇɴᴛɪᴏɴs: <b>{mentions}</b></blockquote>",
                            parse_mode='html'
                        )
        else:
            # For "no" prefix mode
            if message.lower().startswith('afk '):
                reason = message[4:].strip()
                if not reason:
                    reason = "No reason provided"
                
                afk_data = {
                    'is_afk': True,
                    'reason': reason,
                    'start_time': time.time(),
                    'mentions': 0
                }
                
                save_afk_data(afk_data)
                
                await event.respond(
                    f"<blockquote>✘ ɪ'ᴍ ɴᴏᴡ ᴀғᴋ\n"
                    f"✞ ʀᴇᴀsᴏɴ: <b>{reason}</b></blockquote>",
                    parse_mode='html'
                )
            
            elif message.lower() == 'unafk':
                afk_data = get_afk_data()
                if afk_data['is_afk']:
                    afk_duration = format_afk_time(afk_data['start_time'])
                    mentions = afk_data['mentions']
                    
                    # Reset AFK data
                    afk_data['is_afk'] = False
                    afk_data['reason'] = ''
                    afk_data['start_time'] = None
                    afk_data['mentions'] = 0
                    save_afk_data(afk_data)
                    
                    await event.respond(
                        f"<blockquote>⛧ ɪ'ᴍ ʙᴀᴄᴋ ɴᴏᴡ!\n"
                        f"✞ ᴀғᴋ ғᴏʀ: <b>{afk_duration}</b>\n"
                        f"✘ ᴍᴇɴᴛɪᴏɴs: <b>{mentions}</b></blockquote>",
                        parse_mode='html'
                    )

    # ========== MENTION/REPLY HANDLER ==========
    @user.on(events.NewMessage())
    async def afk_mention_handler(event):
        """Handle mentions and replies when AFK"""
        afk_data = get_afk_data()
        
        if not afk_data['is_afk'] or event.sender_id == OWNER_ID:
            return
        
        # Cek apakah pesan mention/reply ke owner
        is_mention = False
        
        # Cek jika ada reply ke pesan owner
        if event.reply_to_msg_id:
            try:
                replied_msg = await event.get_reply_message()
                if replied_msg.sender_id == OWNER_ID:
                    is_mention = True
            except:
                pass
        
        # Cek jika ada mention username owner
        if not is_mention and event.message.entities:
            me = await user.get_me()
            for entity in event.message.entities:
                if hasattr(entity, 'user_id') and entity.user_id == OWNER_ID:
                    is_mention = True
                    break
        
        if not is_mention:
            return
        
        # Cek cooldown untuk mencegah spam
        current_time = time.time()
        sender_id = event.sender_id
        
        if sender_id in last_notification:
            time_since_last = current_time - last_notification[sender_id]
            if time_since_last < COOLDOWN_TIME:
                return  # Skip notifikasi jika masih dalam cooldown
        
        # Update cooldown dan jumlah mentions
        last_notification[sender_id] = current_time
        afk_data['mentions'] += 1
        save_afk_data(afk_data)
        
        # Format waktu AFK
        afk_duration = format_afk_time(afk_data['start_time'])
        
        # Kirim notifikasi AFK
        await event.reply(
            f"<blockquote>✘ ᴏᴡɴᴇʀ ɪs ᴀғᴋ\n"
            f"✞ sɪɴᴄᴇ: <b>{afk_duration}</b>\n"
            f"⛧ ʀᴇᴀsᴏɴ: <b>{afk_data['reason']}</b>\n"
            f"✞ ᴍᴇɴᴛɪᴏɴs: <b>{afk_data['mentions']}</b></blockquote>",
            parse_mode='html'
        )