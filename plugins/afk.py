import asyncio
import time
from datetime import datetime
from telethon import events
from plugins.prefix import get_prefix_from_mongo
from plugins.connect import active_sessions

# Dictionary untuk menyimpan status AFK
afk_users = {}  # Format: {user_id: {"reason": "", "time": timestamp, "client": client}}

async def setup_afk_handler():
    """Setup handler untuk fitur AFK"""
    
    async def afk_handler(event, client):
        """Handler untuk command AFK"""
        user_id = event.sender_id
        
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
        
        # Cek apakah ini command afk atau unafk
        is_afk_command = False
        is_unafk_command = False
        afk_reason = ""
        
        if current_prefix == "no":
            if message_text.lower().startswith("afk"):
                is_afk_command = True
                if len(message_text.split()) > 1:
                    afk_reason = message_text[4:].strip()
            elif message_text.lower() == "unafk":
                is_unafk_command = True
        elif message_text.startswith(current_prefix):
            cmd = message_text[len(current_prefix):].strip().split()[0].lower()
            rest_of_message = message_text[len(current_prefix):].strip()[len(cmd):].strip()
            
            if cmd == "afk":
                is_afk_command = True
                afk_reason = rest_of_message
            elif cmd == "unafk":
                is_unafk_command = True
        
        # Handler untuk .unafk
        if is_unafk_command:
            if user_id in afk_users:
                afk_data = afk_users.pop(user_id)
                afk_duration = time.time() - afk_data["time"]
                
                # Format duration
                hours, remainder = divmod(int(afk_duration), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                duration_text = ""
                if hours: duration_text += f"{hours} jam "
                if minutes: duration_text += f"{minutes} menit "
                if seconds or not duration_text: duration_text += f"{seconds} detik"
                
                response = (
                    "<blockquote>"
                    "<b>✅ <i>Kembali aktif!</i></b>\n\n"
                    f"<b>• Durasi AFK:</b> <code>{duration_text}</code>\n"
                    f"<b>• Alasan:</b> <i>{afk_data.get('reason', 'Tidak ada alasan')}</i>"
                    "</blockquote>"
                )
                
                await event.reply(response, parse_mode='html')
            else:
                response = "<blockquote>ℹ️ <i>Anda tidak sedang dalam mode AFK</i></blockquote>"
                await event.reply(response, parse_mode='html')
            return
        
        # Handler untuk .afk
        if is_afk_command:
            # Simpan status AFK
            afk_users[user_id] = {
                "reason": afk_reason if afk_reason else "Tidak ada alasan",
                "time": time.time(),
                "client": client
            }
            
            reason_text = f"<code>{afk_reason}</code>" if afk_reason else "<i>Tidak ada alasan</i>"
            
            response = (
                "<blockquote>"
                "<b>⏸️ <i>Mode AFK diaktifkan!</i></b>\n\n"
                f"<b>• Alasan:</b> {reason_text}\n"
                f"<b>• Waktu:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
                "<i>Gunakan command <code>unafk</code> untuk kembali aktif.</i>"
                "</blockquote>"
            )
            
            await event.reply(response, parse_mode='html')
            return
    
    return afk_handler

async def setup_afk_notification_handler():
    """Setup handler untuk notifikasi ketika ada yang mention user AFK"""
    
    async def afk_notification_handler(event, client):
        """Handler untuk notifikasi AFK"""
        user_id = event.sender_id
        
        # Cek apakah ada user AFK yang di-mention
        if event.is_private:
            return
        
        # Cek mentions dalam pesan
        if event.mentions:
            for mentioned_user in event.mentions:
                mentioned_id = mentioned_user.id
                
                if mentioned_id in afk_users:
                    afk_data = afk_users[mentioned_id]
                    
                    # Hitung durasi AFK
                    afk_duration = time.time() - afk_data["time"]
                    hours, remainder = divmod(int(afk_duration), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    duration_text = ""
                    if hours: duration_text += f"{hours} jam "
                    if minutes: duration_text += f"{minutes} menit "
                    if seconds or not duration_text: duration_text += f"{seconds} detik"
                    
                    # Format waktu AFK
                    afk_time = datetime.fromtimestamp(afk_data["time"]).strftime("%H:%M:%S")
                    
                    response = (
                        "<blockquote>"
                        "<b>⏸️ <i>User sedang AFK!</i></b>\n\n"
                        f"<b>• User:</b> {mentioned_user.first_name}\n"
                        f"<b>• Alasan:</b> <i>{afk_data['reason']}</i>\n"
                        f"<b>• Durasi:</b> <code>{duration_text}</code>\n"
                        f"<b>• Sejak:</b> <code>{afk_time}</code>"
                        "</blockquote>"
                    )
                    
                    await event.reply(response, parse_mode='html')
                    break
    
    return afk_notification_handler

# Fungsi untuk menambahkan handler ke userbot baru
async def add_afk_handler_to_client(client, user_id):
    """Add AFK handler ke userbot client"""
    afk_handler_func = await setup_afk_handler()
    afk_notification_func = await setup_afk_notification_handler()
    
    try:
        @client.on(events.NewMessage(pattern=r'^(\.|!|\?|,|;|:|/|\\|@|#|\$|%|\^|&|\*|\+|=)?(afk|unafk)', outgoing=True))
        async def handler(event):
            await afk_handler_func(event, client)
        
        @client.on(events.NewMessage(incoming=True))
        async def notification_handler(event):
            await afk_notification_func(event, client)
        
        print(f"✅ Added AFK handler to user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error adding AFK handler to user {user_id}: {e}")
        return False

# Export functions
__all__ = ['add_afk_handler_to_client']