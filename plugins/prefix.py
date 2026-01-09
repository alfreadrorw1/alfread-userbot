import json
import re
from telethon import events
from telethon.tl.custom import Button
from plugins.connect import active_sessions

# Collection untuk prefix di MongoDB
from plugins.connect import sessions_collection

async def setup_prefix_handler():
    """Setup handler untuk mengatur prefix"""
    
    async def prefix_handler(event, client):
        """Handler untuk command prefix di userbot"""
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
        
        # Cek apakah ini command prefix
        is_prefix_command = False
        is_setprefix_command = False
        
        # Get current prefix dari MongoDB
        current_prefix = await get_prefix_from_mongo(user_id)
        
        if current_prefix == "no":
            if message_text.lower() == "prefix":
                is_prefix_command = True
            elif message_text.lower().startswith("setprefix"):
                is_setprefix_command = True
        elif message_text.startswith(current_prefix):
            cmd = message_text[len(current_prefix):].strip().split()[0].lower()
            if cmd == "prefix":
                is_prefix_command = True
            elif cmd == "setprefix":
                is_setprefix_command = True
        
        if not is_prefix_command and not is_setprefix_command:
            return
        
        # Handler untuk .prefix
        if is_prefix_command:
            prefix_text = "`no prefix`" if current_prefix == "no" else f"`{current_prefix}`"
            await event.reply(
                f"**Current Prefix:** {prefix_text}\n\n"
                f"**Usage:**\n"
                f"• `{current_prefix if current_prefix != 'no' else ''}ping` - Test connection\n"
                f"• `{current_prefix if current_prefix != 'no' else ''}setprefix [new_prefix]` - Change prefix\n"
                f"• `{current_prefix if current_prefix != 'no' else ''}prefix` - Show current prefix\n\n"
                f"**Note:** Use 'no' to disable prefix (commands without prefix)"
            )
            return
        
        # Handler untuk .setprefix
        if is_setprefix_command:
            # Extract new prefix from message
            parts = message_text.split()
            
            if len(parts) < 2:
                await event.reply(
                    "**Usage:**\n"
                    f"`{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} [new_prefix]`\n\n"
                    f"**Examples:**\n"
                    f"• `{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} .`\n"
                    f"• `{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} !`\n"
                    f"• `{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} no` (disable prefix)\n\n"
                    f"**Current:** `{current_prefix if current_prefix != 'no' else 'no prefix'}`"
                )
                return
            
            new_prefix = parts[1].strip()
            
            # Validasi prefix
            if len(new_prefix) > 3:
                await event.reply("❌ **Error:** Prefix maksimal 3 karakter!")
                return
            
            if new_prefix.lower() == "no":
                new_prefix = "no"
            
            # Simpan ke MongoDB
            success = await save_prefix_to_mongo(user_id, new_prefix)
            
            if success:
                prefix_display = "`no prefix`" if new_prefix == "no" else f"`{new_prefix}`"
                await event.reply(
                    f"✅ **Prefix berhasil diubah!**\n\n"
                    f"**New Prefix:** {prefix_display}\n"
                    f"**Example:** `{new_prefix if new_prefix != 'no' else ''}ping`\n\n"
                    f"Perubahan akan berlaku untuk semua command."
                )
            else:
                await event.reply("❌ **Error:** Gagal menyimpan prefix ke database!")

    return prefix_handler

async def get_prefix_from_mongo(user_id):
    """Ambil prefix dari MongoDB"""
    try:
        if sessions_collection:
            user_data = sessions_collection.find_one({"user_id": str(user_id), "type": "prefix"})
            if user_data and "prefix" in user_data:
                return user_data["prefix"]
        
        # Fallback ke file jika MongoDB tidak tersedia
        return get_prefix_from_file(user_id)
    except:
        return get_prefix_from_file(user_id)

async def save_prefix_to_mongo(user_id, prefix):
    """Simpan prefix ke MongoDB"""
    try:
        if sessions_collection:
            from datetime import datetime
            sessions_collection.update_one(
                {
                    "user_id": str(user_id),
                    "type": "prefix"
                },
                {
                    "$set": {
                        "prefix": prefix,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            return True
        
        # Fallback ke file jika MongoDB tidak tersedia
        return save_prefix_to_file(user_id, prefix)
    except Exception as e:
        print(f"❌ Error saving prefix to MongoDB: {e}")
        return save_prefix_to_file(user_id, prefix)

def get_prefix_from_file(user_id):
    """Ambil prefix dari file (fallback)"""
    try:
        with open('data/prefix.json', 'r') as f:
            data = json.load(f)
            return data.get(str(user_id), '.')
    except:
        return '.'

def save_prefix_to_file(user_id, prefix):
    """Simpan prefix ke file (fallback)"""
    try:
        import os
        os.makedirs('data', exist_ok=True)
        
        try:
            with open('data/prefix.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        data[str(user_id)] = prefix
        
        with open('data/prefix.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except:
        return False

# Fungsi untuk menambahkan handler ke userbot baru
async def add_prefix_handler_to_client(client, user_id):
    """Add prefix handler ke userbot client"""
    prefix_handler_func = await setup_prefix_handler()
    
    try:
        @client.on(events.NewMessage())
        async def handler(event):
            await prefix_handler_func(event, client)
        
        print(f"✅ Added prefix handler to user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error adding prefix handler to user {user_id}: {e}")
        return False

# Export functions
__all__ = [
    'add_prefix_handler_to_client',
    'get_prefix_from_mongo'
]