import asyncio
import sys
import os
from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN
from plugins.connect import (
    create_userbot_client,
    sessions_collection,
    active_sessions
)
from plugins.bot_handler import setup_bot_handlers

async def restore_sessions():
    """Memulihkan session aktif dari MongoDB"""
    try:
        if not sessions_collection:
            print("❌ sessions_collection tidak tersedia")
            return
            
        sessions = sessions_collection.find({"is_active": True})
        restored_count = 0
        
        for session_data in sessions:
            user_id = int(session_data['user_id'])
            session_string = session_data.get('session_string')
            
            if session_string:
                try:
                    client = create_userbot_client(user_id, session_string)
                    await client.connect()
                    
                    # Cek jika client masih valid
                    if await client.is_user_authorized():
                        active_sessions[user_id] = client
                        
                        # AUTO-LOAD SEMUA PLUGINS menggunakan sistem baru
                        from plugins import auto_load_all_plugins_for_client
                        await auto_load_all_plugins_for_client(client, user_id)
                        
                        print(f"✅ Restored session for user: {user_id}")
                        restored_count += 1
                    else:
                        # Hapus session yang tidak valid
                        sessions_collection.delete_one({"user_id": str(user_id)})
                        print(f"❌ Invalid session for user: {user_id}")
                        
                except Exception as e:
                    print(f"❌ Error restoring session for {user_id}: {e}")
                    # Hapus session yang error
                    sessions_collection.delete_one({"user_id": str(user_id)})
                    
    except Exception as e:
        print(f"❌ Error restoring sessions: {e}")
    
    return restored_count

async def main():
    print("🤖 Starting UserBot System...")
    
    # 1. Mulai Bot untuk koneksi
    print("🔧 Starting Connection Bot...")
    bot = TelegramClient('connection_bot', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)
    bot_me = await bot.get_me()
    print(f"✅ Bot started: @{bot_me.username}")
    
    # 2. Setup bot handlers
    await setup_bot_handlers(bot)
    
    # 3. Restore active sessions dari MongoDB dan auto load plugins
    print("🔄 Restoring sessions from MongoDB...")
    restored_count = await restore_sessions()
    
    print(f"🚀 UserBot system is ready!")
    print(f"📊 Active sessions: {restored_count} restored")
    
    # Jalankan bot dan userbot
    try:
        await bot.run_until_disconnected()
    finally:
        # Cleanup semua userbot sessions
        for user_id, client in list(active_sessions.items()):
            try:
                await client.disconnect()
            except:
                pass
        print("👋 UserBot system stopped")

if __name__ == "__main__":
    asyncio.run(main())