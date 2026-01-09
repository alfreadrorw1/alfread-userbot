import re
import json
import os
from telethon import events
from config import OWNER_ID

current_prefix = '.'  # Default

def ensure_data_dir():
    # Buat folder data jika belum ada
    if not os.path.exists("data"):
        os.makedirs("data")

def load_prefix():
    global current_prefix
    ensure_data_dir()  # Pastikan folder data ada
    try:
        with open('data/prefix.json', 'r') as f:
            data = json.load(f)
            current_prefix = data.get('prefix', '.')
    except FileNotFoundError:
        current_prefix = '.'
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': current_prefix}, f)

def save_prefix(new_prefix):
    global current_prefix
    ensure_data_dir()  # Pastikan folder data ada
    current_prefix = new_prefix
    with open('data/prefix.json', 'w') as f:
        json.dump({'prefix': new_prefix}, f)

def setup(bot, user):
    load_prefix()

    # Handler untuk ganti prefix
    @user.on(events.NewMessage())
    async def setprefix_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        message = (event.raw_text or '').strip()
        
        # Cek apakah ini command setprefix
        if message.lower().startswith('setprefix '):
            input_prefix = message[10:].strip().lower()
            
            if input_prefix == "no":
                save_prefix("no")
                await event.reply("<blockquote>⛧ ᴘʀᴇғɪx ᴅɪɴᴏɴᴀᴋᴛɪғᴋᴀɴ!\n✘ ɢᴜɴᴀᴋᴀɴ ᴄᴏᴍᴍᴀɴᴅ ᴛᴀɴᴘᴀ ᴘʀᴇғɪx.</blockquote>", parse_mode='html')
            elif len(input_prefix) == 1:
                save_prefix(input_prefix)
                await event.reply(f"<blockquote>✞ ᴘʀᴇғɪx ᴅɪᴜʙᴀʜ ᴋᴇ: <b>`{input_prefix}`</b></blockquote>", parse_mode='html')
            else:
                await event.reply("<blockquote>✘ ᴘᴀɴᴊᴀɴɢ ᴘʀᴇғɪx ʜᴀʀᴜs 1 ᴋᴀʀᴀᴋᴛᴇʀ\n⛧ ᴀᴛᴀᴜ `sᴇᴛᴘʀᴇғɪx ɴᴏ`!</blockquote>", parse_mode='html')
        
        # Cek apakah ini command prefix
        elif message.lower() == 'prefix':
            status = "ᴛɪᴅᴀᴋ ᴀᴅᴀ" if current_prefix == "no" else f"`{current_prefix}`"
            await event.reply(f"<blockquote>✘ ᴘʀᴇғɪx sᴀᴀᴛ ɪɴɪ: <b>{status}</b></blockquote>", parse_mode='html')

    # Handler untuk prefix check dengan prefix
    @user.on(events.NewMessage())
    async def prefix_check_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        message = (event.raw_text or '').strip()
        
        # Cek apakah ini command prefix dengan prefix
        if current_prefix != "no" and message.startswith(current_prefix):
            cmd_text = message[len(current_prefix):].strip().lower()
            
            if cmd_text == 'prefix':
                status = "ᴛɪᴅᴀᴋ ᴀᴅᴀ" if current_prefix == "no" else f"`{current_prefix}`"
                await event.reply(f"<blockquote>✘ ᴘʀᴇғɪx sᴀᴀᴛ ɪɴɪ: <b>{status}</b></blockquote>", parse_mode='html')
            
            elif cmd_text.startswith('setprefix'):
                input_prefix = cmd_text[9:].strip()
                
                if input_prefix == "no":
                    save_prefix("no")
                    await event.reply("<blockquote>⛧ ᴘʀᴇғɪx ᴅɪɴᴏɴᴀᴋᴛɪғᴋᴀɴ!\n✘ ɢᴜɴᴀᴋᴀɴ ᴄᴏᴍᴍᴀɴᴅ ᴛᴀɴᴘᴀ ᴘʀᴇғɪx.</blockquote>", parse_mode='html')
                elif len(input_prefix) == 1:
                    save_prefix(input_prefix)
                    await event.reply(f"<blockquote>✞ ᴘʀᴇғɪx ᴅɪᴜʙᴀʜ ᴋᴇ: <b>`{input_prefix}`</b></blockquote>", parse_mode='html')
                else:
                    await event.reply("<blockquote>✘ ᴘᴀɴᴊᴀɴɢ ᴘʀᴇғɪx ʜᴀʀᴜs 1 ᴋᴀʀᴀᴋᴛᴇʀ\n⛧ ᴀᴛᴀᴜ `sᴇᴛᴘʀᴇғɪx ɴᴏ`!</blockquote>", parse_mode='html')