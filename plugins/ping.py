import time
import json
import os
from datetime import datetime
from telethon import events
from plugins.connect import active_sessions

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

async def setup_userbot_ping():
    """Setup ping handler untuk userbot yang sudah connect"""
    
    async def ping_handler(event, client):
        """Handler untuk command ping di userbot"""
        user_id = event.sender_id
        
        # Cek apakah user memiliki session aktif
        if user_id not in active_sessions:
            return
        
        # Cek apakah event berasal dari userbot client yang sama
        current_client = active_sessions[user_id]
        if current_client != client:
            return
        
        # Get current prefix
        current_prefix = get_prefix()
        message_text = (event.raw_text or '').strip()
        
        # Check if message is a ping command
        is_ping = False
        
        if current_prefix == "no" and message_text.lower() == "ping":
            is_ping = True
        elif message_text.startswith(current_prefix):
            cmd = message_text[len(current_prefix):].strip().lower()
            if cmd == "ping":
                is_ping = True
        
        if not is_ping:
            return

        start_time = time.perf_counter()
        ping_msg = await event.reply("<blockquote>ᴘɪɴɢɪɴɢ...</blockquote>", parse_mode='html')
        end_time = time.perf_counter()

        latency = (end_time - start_time) * 1000  # Convert to ms
        uptime_str = get_uptime()
        
        # Get user info
        try:
            me = await client.get_me()
            user_name = me.first_name
        except:
            user_name = "User"
        
        # Get connection status
        connection_status = "🟢 Connected" if client.is_connected() else "🔴 Disconnected"
        
        # Get session age (jika ada)
        session_age = ""
        try:
            with open('data/sessions.json', 'r') as f:
                sessions = json.load(f)
                if str(user_id) in sessions:
                    login_time = sessions[str(user_id)].get('login_time', time.time())
                    age_seconds = time.time() - login_time
                    hours = int(age_seconds // 3600)
                    minutes = int((age_seconds % 3600) // 60)
                    session_age = f"{hours}h {minutes}m"
        except:
            pass
        
        # Format response
        response = (
            f"<blockquote>𝗽𝗼𝗻𝗴: <b>{latency:.2f} ms</b>\n"
            f"𝗨𝗽𝘁𝗶𝗺𝗲: <b>{uptime_str}</b>\n"
            f"𝗦𝘁𝗮𝘁𝘂𝘀: <b>{connection_status}</b>\n"
            f"𝗨𝘀𝗲𝗿𝗯𝗼𝘁 :<b>AlfreadRorw</b></blockquote>\n\n"
        )
        
        if session_age:
            response += f"<blockquote>⏰ <b>Session Age:</b> {session_age}</blockquote>\n\n"
        
        response += f"<blockquote><i>👤 Owner: {user_name}</i></blockquote>"
        
        await ping_msg.edit(response, parse_mode='html')
    
    return ping_handler

# Setup event handlers untuk setiap active session
async def setup_all_ping_handlers():
    """Setup ping handler untuk semua active sessions"""
    ping_handler_func = await setup_userbot_ping()
    
    for user_id, client in list(active_sessions.items()):
        try:
            # Hapus handler lama jika ada
            client.remove_event_handler(ping_handler_func)
            
            # Tambahkan handler baru
            @client.on(events.NewMessage())
            async def handler(event):
                # Kirim ke ping_handler dengan client yang sesuai
                await ping_handler_func(event, client)
            
            print(f"✅ Ping handler setup for user {user_id}")
        except Exception as e:
            print(f"❌ Error setting up ping for user {user_id}: {e}")

# Fungsi untuk menambahkan handler ke userbot baru
async def add_ping_handler_to_client(client, user_id):
    """Add ping handler ke userbot client yang baru connect"""
    ping_handler_func = await setup_userbot_ping()
    
    try:
        @client.on(events.NewMessage())
        async def handler(event):
            await ping_handler_func(event, client)
        
        print(f"✅ Added ping handler to user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error adding ping handler to user {user_id}: {e}")
        return False