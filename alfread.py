import logging
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio
import os
import sys
import json
import re
import time
import random
from config import *

# Setup folders
os.makedirs('cache', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Logging
logging.basicConfig(level=logging.WARNING)

# Clients
bot = TelegramClient('cache/bot', API_ID, API_HASH)
user = TelegramClient('cache/user', API_ID, API_HASH)

async def load_plugins():
    """Load plugins dengan cara sederhana"""
    plugins_dir = 'plugins'
    if not os.path.isdir(plugins_dir):
        return
    
    print("📦 Loading plugins...")
    
    for fname in os.listdir(plugins_dir):
        if fname.endswith('.py') and not fname.startswith('_'):
            module_name = fname[:-3]
            plugin_path = os.path.join(plugins_dir, fname)
            
            try:
                # Baca file plugin
                with open(plugin_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Buat dictionary dengan semua import yang diperlukan
                exec_globals = {
                    # Telethon
                    'events': events,
                    'Button': Button,
                    'TelegramClient': TelegramClient,
                    'StringSession': StringSession,
                    'SessionPasswordNeededError': SessionPasswordNeededError,
                    
                    # Clients
                    'bot': bot,
                    'user': user,
                    
                    # Standard library
                    'asyncio': asyncio,
                    'json': json,
                    'os': os,
                    're': re,
                    'time': time,
                    'random': random,
                    'sys': sys,
                    
                    # Config
                    'OWNER_ID': OWNER_ID,
                    'API_ID': API_ID,
                    'API_HASH': API_HASH,
                    'BOT_TOKEN': BOT_TOKEN,
                    
                    # Module name
                    '__name__': f'plugins.{module_name}'
                }
                
                # Execute kode plugin
                exec(code, exec_globals)
                
                # Panggil fungsi setup jika ada
                if 'setup' in exec_globals:
                    setup_func = exec_globals['setup']
                    if asyncio.iscoroutinefunction(setup_func):
                        await setup_func(bot, user)
                    else:
                        setup_func(bot, user)
                
                print(f"✅ {module_name}")
                
            except Exception as e:
                print(f"❌ {module_name}: {e}")
                import traceback
                traceback.print_exc()

async def main():
    print("🚀 Starting UserBot...")
    
    # Start clients
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 Bot client started")
    
    await user.connect()
    print("👤 User client connected")
    
    # Load plugins
    await load_plugins()
    
    print("\n" + "="*40)
    print("✅ Bot is running!")
    print("="*40 + "\n")
    
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 Disconnecting...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if bot.is_connected():
                loop.run_until_complete(bot.disconnect())
                print("✅ Bot disconnected")
            if user.is_connected():
                loop.run_until_complete(user.disconnect())
                print("✅ User disconnected")
        except:
            pass
        print("\n👋 Shutdown complete")