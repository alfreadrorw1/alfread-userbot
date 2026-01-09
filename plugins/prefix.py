import json
import re
from datetime import datetime
from telethon import events
from telethon.tl.custom import Button
from plugins.connect import active_sessions, sessions_collection

async def add_prefix_handler_to_client(client, user_id):
    """Add prefix handler ke userbot client - AUTO-LOAD FUNCTION"""
    
    async def get_prefix_from_mongo():
        """Ambil prefix dari MongoDB"""
        try:
            if sessions_collection:
                session_data = sessions_collection.find_one({"user_id": str(user_id)})
                
                if session_data and "prefix" in session_data:
                    return session_data["prefix"]
                else:
                    # Default prefix
                    default_prefix = "."
                    await save_prefix_to_mongo(default_prefix)
                    return default_prefix
            
            return "."
        except Exception as e:
            print(f"❌ Error getting prefix from MongoDB: {e}")
            return "."
    
    async def save_prefix_to_mongo(prefix):
        """Simpan prefix ke MongoDB"""
        try:
            if sessions_collection:
                result = sessions_collection.update_one(
                    {"user_id": str(user_id)},
                    {
                        "$set": {
                            "prefix": prefix,
                            "updated_at": datetime.now()
                        }
                    },
                    upsert=True
                )
                return result.acknowledged
            return False
        except Exception as e:
            print(f"❌ Error saving prefix to MongoDB: {e}")
            return False
    
    async def prefix_handler(event):
        """Handler untuk command prefix di userbot"""
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
        current_prefix = await get_prefix_from_mongo()
        
        # Cek apakah ini command prefix
        is_prefix_command = False
        is_setprefix_command = False
        
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
            
            response = (
                "<blockquote>"
                "<b>⚙️ <i>Current Prefix</i></b>\n\n"
                f"<b>• Prefix:</b> {prefix_text}\n\n"
                "<b>📝 <i>Usage:</i></b>\n"
                f"• <code>{current_prefix if current_prefix != 'no' else ''}ping</code> - Test connection\n"
                f"• <code>{current_prefix if current_prefix != 'no' else ''}setprefix [new_prefix]</code> - Change prefix\n"
                f"• <code>{current_prefix if current_prefix != 'no' else ''}prefix</code> - Show current prefix\n\n"
                "<i>Note: Use 'no' to disable prefix (commands without prefix)</i>"
                "</blockquote>"
            )
            
            await event.reply(response, parse_mode='html')
            return
        
        # Handler untuk .setprefix
        if is_setprefix_command:
            # Extract new prefix from message
            parts = message_text.split()
            
            if len(parts) < 2:
                help_text = (
                    "<blockquote>"
                    "<b>📖 <i>Usage:</i></b>\n"
                    f"<code>{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} [new_prefix]</code>\n\n"
                    "<b>💡 <i>Examples:</i></b>\n"
                    f"• <code>{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} .</code>\n"
                    f"• <code>{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} !</code>\n"
                    f"• <code>{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} ?</code>\n"
                    f"• <code>{'setprefix' if current_prefix == 'no' else current_prefix + 'setprefix'} no</code> (disable prefix)\n\n"
                    f"<b>Current:</b> <code>{current_prefix if current_prefix != 'no' else 'no prefix'}</code>"
                    "</blockquote>"
                )
                await event.reply(help_text, parse_mode='html')
                return
            
            new_prefix = parts[1].strip()
            
            # Validasi prefix
            if len(new_prefix) > 3:
                await event.reply("<blockquote>❌ <b>Error:</b> Prefix maksimal 3 karakter!</blockquote>", parse_mode='html')
                return
            
            if new_prefix.lower() == "no":
                new_prefix = "no"
            
            # Simpan ke MongoDB
            success = await save_prefix_to_mongo(new_prefix)
            
            if success:
                prefix_display = "no prefix" if new_prefix == "no" else new_prefix
                example_cmd = "ping" if new_prefix == "no" else f"{new_prefix}ping"
                
                response = (
                    "<blockquote>"
                    "<b>✅ <i>Prefix berhasil diubah!</i></b>\n\n"
                    f"<b>• New Prefix:</b> <code>{prefix_display}</code>\n"
                    f"<b>• Example:</b> <code>{example_cmd}</code>\n\n"
                    "<i>Perubahan akan berlaku untuk semua command.</i>"
                    "</blockquote>"
                )
                
                await event.reply(response, parse_mode='html')
            else:
                await event.reply("<blockquote>❌ <b>Error:</b> Gagal menyimpan prefix ke database!</blockquote>", parse_mode='html')
    
    # Register handler
    client.add_event_handler(prefix_handler, events.NewMessage(outgoing=True))
    
    print(f"✅ Added prefix handler to user {user_id}")
    return True

# Export functions
__all__ = ['add_prefix_handler_to_client']