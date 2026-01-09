import time
import random
import asyncio
from datetime import datetime
from telethon import events
from plugins.connect import active_sessions
from plugins.utils import get_prefix_from_mongo, format_time

# List random icons untuk ping
PING_ICONS = [
    "✘", "☾", "☽", "✞", "⛧", "⚝", "✦", "✧", "★", "☆", 
    "✮", "✯", "✰", "❋", "❊", "❉", "❈", "❇", "✢", "✣",
    "✤", "✥", "✺", "✹", "✸", "✷", "✶", "✵", "✴", "✳",
    "✲", "✱", "✧", "✦", "⭑", "⭒", "⚝", "☀", "☼", "☽"
]

# Global variable untuk menyimpan waktu mulai bot
bot_start_time = datetime.now()

def get_random_icon(icon_list=None):
    """Mendapatkan icon random"""
    if icon_list is None:
        icon_list = PING_ICONS
    return random.choice(icon_list)

def get_bot_uptime():
    """Calculate bot uptime sejak pertama kali dijalankan"""
    try:
        current_time = datetime.now()
        uptime_seconds = (current_time - bot_start_time).total_seconds()
        return format_time(uptime_seconds)
    except Exception as e:
        print(f"Error calculating uptime: {e}")
        return "Unknown"

def get_session_uptime(user_id):
    """Calculate session uptime untuk user tertentu"""
    try:
        from plugins.connect import sessions_collection
        if sessions_collection:
            session_data = sessions_collection.find_one({"user_id": str(user_id)})
            if session_data and "created_at" in session_data:
                created_at = session_data["created_at"]
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                session_age_seconds = (datetime.now() - created_at).total_seconds()
                return format_time(session_age_seconds)
        return "Unknown"
    except Exception as e:
        print(f"Error calculating session uptime: {e}")
        return "Unknown"

async def add_ping_handler_to_client(client, user_id):
    """Add ping handler ke userbot client - AUTO-LOAD FUNCTION"""
    
    async def ping_handler(event):
        """Handler untuk command ping di userbot"""
        # Cek apakah user memiliki session aktif
        if user_id not in active_sessions:
            return
        
        # Cek apakah event berasal dari userbot client yang sama
        current_client = active_sessions[user_id]
        if current_client != client:
            return
        
        # Get message text
        message_text = (event.raw_text or '').strip()
        
        # Get current prefix dari MongoDB
        current_prefix = await get_prefix_from_mongo(user_id)
        
        # Cek apakah ini command ping dengan pattern yang tepat
        is_ping = False
        
        if current_prefix == "no":
            if message_text.lower() == "ping":
                is_ping = True
        elif message_text.startswith(current_prefix):
            cmd = message_text[len(current_prefix):].strip().lower()
            if cmd == "ping":
                is_ping = True
        
        if not is_ping:
            return

        # Start timing
        start_time = time.perf_counter()
        
        # Kirim pesan pinging dengan icon random
        pinging_icon = get_random_icon()
        ping_msg = await event.reply(f"<blockquote>{pinging_icon} ᴘɪɴɢɪɴɢ...</blockquote>", parse_mode='html')
        
        # End timing
        end_time = time.perf_counter()
        
        # Calculate latency
        latency = (end_time - start_time) * 1000  # Convert to ms
        
        # Get bot uptime
        bot_uptime = get_bot_uptime()
        
        # Get session uptime
        session_uptime = get_session_uptime(user_id)
        
        # Get user info
        try:
            me = await client.get_me()
            user_name = me.first_name
            username = f"@{me.username}" if me.username else "No Username"
        except:
            user_name = "User"
            username = "No Username"
        
        # Generate random response dengan icons yang berbeda
        icon1 = get_random_icon()
        icon2 = get_random_icon()
        icon3 = get_random_icon()
        icon4 = get_random_icon()
        
        # Format response dengan quote blocks
        response = (
            f"<blockquote>{icon1} ᴘᴏɴɢ: <code>{latency:.2f}ᴍs</code>\n"
            f"{icon2} ʙᴏᴛ ᴜᴘᴛɪᴍᴇ: <code>{bot_uptime}</code>\n"
            f"{icon3} sᴇssɪᴏɴ ᴜᴘᴛɪᴍᴇ: <code>{session_uptime}</code>\n"
            f"<blockquote>{icon4} ᴏᴡɴᴇʀ: Vantzxx</blockquote>\n"
            f"<blockquote>☾. USERBOT @Vantzxx</blockquote>\n\n"
        )
        
        await ping_msg.edit(response, parse_mode='html')
    
    # Register handler dengan pattern yang spesifik
    client.add_event_handler(ping_handler, events.NewMessage(
        outgoing=True,
        pattern=r'^(\.|!|\?|,|;|:|/|\\|@|#|\$|%|\^|&|\*|\+|=)?ping$'
    ))
    
    print(f"✅ Added ping handler to user {user_id}")
    return True

# Export functions
__all__ = ['add_ping_handler_to_client', 'get_bot_uptime', 'get_session_uptime']