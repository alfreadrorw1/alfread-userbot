import time
from telethon import events
from plugins.connect import client, userbot_client
from config import MODE

async def get_active_client():
    """Get active client based on mode"""
    if MODE == "userbot" and userbot_client:
        return userbot_client
    return client

@client.on(events.NewMessage(pattern='^(\.ping|/ping)$'))
async def ping_handler(event):
    active_client = await get_active_client()
    
    # Skip if userbot not logged in
    if MODE == "userbot" and not userbot_client:
        await event.reply("⚠️ Userbot belum login! Gunakan /start untuk login.")
        return
    
    start = time.time()
    message = await event.reply("🏓 Pong!")
    end = time.time()
    latency = round((end - start) * 1000, 2)
    
    mode_text = "Userbot" if MODE == "userbot" else "Bot"
    await message.edit(f"Pong! 🏓\nMode: {mode_text}\nSpeed: {latency} ms")