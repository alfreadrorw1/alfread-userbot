import logging
from telethon import TelegramClient
import asyncio
import os
import importlib
import inspect
from config import *

# Setup folders
os.makedirs('cache', exist_ok=True)
os.makedirs('data', exist_ok=True)

logging.basicConfig(level=logging.WARNING)

# Clients
bot = TelegramClient('cache/bot', API_ID, API_HASH)
user = TelegramClient('cache/user', API_ID, API_HASH)

async def load_plugins():
    plugins_dir = 'plugins'
    if not os.path.isdir(plugins_dir):
        return
    
    for fname in os.listdir(plugins_dir):
        if fname.endswith('.py') and not fname.startswith('_'):
            module_name = fname[:-3]
            try:
                module = importlib.import_module(f'plugins.{module_name}')
                if hasattr(module, 'setup'):
                    setup_func = module.setup
                    if inspect.iscoroutinefunction(setup_func):
                        await setup_func(bot, user)
                    else:
                        setup_func(bot, user)
                print(f"Loaded: {module_name}")
            except Exception as e:
                print(f"Error: {module_name} - {e}")

async def main():
    # Start bot
    await bot.start(bot_token=BOT_TOKEN)
    print("Bot started")
    
    # Start user client
    await user.connect()
    if await user.is_user_authorized():
        print("User client ready")
    
    # Load plugins
    await load_plugins()
    
    print("Bot running")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
    finally:
        if bot.is_connected():
            bot.disconnect()
        if user.is_connected():
            user.disconnect()
        print("Shutdown complete")