import asyncio
import glob
import importlib
import os
from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN
from plugins.connect import (
    create_userbot_client,
    sessions_collection,
    active_sessions
)
from plugins.bot_handler import setup_bot_handlers
from plugins.ping import setup_all_ping_handlers, add_ping_handler_to_client

# Load semua plugins
async def load_plugins():
    plugin_files = glob.glob("plugins/*.py")
    for plugin_file in plugin_files:
        if plugin_file.endswith("__init__.py") or plugin_file.endswith("connect.py") or plugin_file.endswith("bot_handler.py") or plugin_file.endswith("ping.py"):
            continue
        
        module_name = os.path.basename(plugin_file)[:-3]
        try:
            importlib.import_module(f"plugins.{module_name}")
            print(f"✅ Loaded plugin: {module_name}")
        except Exception as e:
            print(f"❌ Failed to load {module_name}: {e}")

# Restore active sessions dari MongoDB
async def restore_sessions():
    """Memulihkan session aktif dari MongoDB"""
    try:
        sessions = sessions_collection.find({})
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
                        
                        # Add ping handler ke client
                        await add_ping_handler_to_client(client, user_id)
                        
                        print(f"✅ Restored session for user: {user_id}")
                    else:
                        # Hapus session yang tidak valid
                        sessions_collection.delete_one({"user_id": str(user_id)})
                        print(f"❌ Invalid session for user: {user_id}")
                        
                except Exception as e:
                    print(f"❌ Error restoring session for {user_id}: {e}")
                    
    except Exception as e:
        print(f"❌ Error restoring sessions: {e}")

async def main():
    print("🤖 Starting UserBot System...")
    
    # 1. Mulai Bot untuk koneksi
    print("🔧 Starting Connection Bot...")
    bot = TelegramClient('connection_bot', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ Bot started: @{(await bot.get_me()).username}")
    
    # 2. Setup bot handlers
    await setup_bot_handlers(bot)
    
    # 3. Load semua plugins
    await load_plugins()
    
    # 4. Setup ping handlers untuk semua sessions
    await setup_all_ping_handlers()
    
    # 5. Restore active sessions dari MongoDB
    await restore_sessions()
    
    print("🚀 UserBot system is ready!")
    print(f"📊 Active sessions: {len(active_sessions)}")
    
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