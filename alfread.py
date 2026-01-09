import asyncio
import sys
from plugins.connect import client, userbot_client
from config import MODE, BOT_TOKEN
import plugins

async def run_userbot():
    """Run userbot client if logged in"""
    if userbot_client and not userbot_client.is_connected():
        print("Starting userbot client...")
        await userbot_client.start()
        await userbot_client.run_until_disconnected()

async def main():
    try:
        print(f"Starting in {MODE} mode...")
        
        if MODE == "userbot":
            # Start bot interface for login
            await client.start(bot_token=BOT_TOKEN)
            print("Bot login interface started!")
            
            # Check if userbot already logged in
            from pymongo import MongoClient
            from config import MONGO_URI, SESSION_NAME
            
            mongo = MongoClient(MONGO_URI)
            session_data = mongo.get_database()["telethon_sessions"].find_one({"session": SESSION_NAME})
            
            if session_data and b"main" in session_data:
                print("Userbot session found, starting userbot...")
                # Start userbot in background
                asyncio.create_task(run_userbot())
            
            print("Waiting for login via bot...")
            print("Use /start in bot to login")
            
            await client.run_until_disconnected()
        
        elif MODE == "bot":
            await client.start(bot_token=BOT_TOKEN)
            print("Bot started successfully!")
            await client.run_until_disconnected()
        
        else:
            print(f"Error: Invalid MODE '{MODE}'")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())