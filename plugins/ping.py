import time
import random
from telethon import events
from config import OWNER_ID

# Karakter khusus tanpa emoji
PING_ICONS = ["☆", "★", "✪", "✯", "✦", "✧", "❂", "❈", "❖", "✶", "✷", "✸", "✹", "✺", "✻", "✼", "✽", "✾", "✿", "❀"]
SPEED_ICONS = ["⌛", "⏱", "⏲", "⏰", "‰", "‱", "⁂", "⁃", "⁄", "⁇", "⁈", "⁉", "⁊", "⁋", "⁌", "⁍", "⁎", "⁏", "⁐", "⁑"]
OWNER_ICONS = ["○", "●", "◎", "◇", "◆", "□", "■", "▢", "▣", "▤", "▥", "▦", "▧", "▨", "▩", "▪", "▫", "▬", "▭", "▮"]

async def setup(bot, user):
    """Setup ping command"""
    
    @bot.on(events.NewMessage(pattern=r'^\.ping$'))
    async def ping_handler(event):
        """Handle .ping command"""
        start_time = time.time()
        
        # Kirim pesan awal
        msg = await event.reply("`Pinging...`")
        
        # Hitung ping
        end_time = time.time()
        ping_time = (end_time - start_time) * 1000
        
        # Pilih icon random
        ping_icon = random.choice(PING_ICONS)
        speed_icon = random.choice(SPEED_ICONS)
        owner_icon = random.choice(OWNER_ICONS)
        
        # Ambil info owner
        try:
            owner_entity = await bot.get_entity(OWNER_ID)
            owner_name = owner_entity.first_name if hasattr(owner_entity, 'first_name') else "Owner"
            owner_link = f'<a href="tg://user?id={OWNER_ID}">{owner_name}</a>'
        except:
            owner_link = f'<a href="tg://user?id={OWNER_ID}">Owner</a>'
        
        # Format pesan dengan HTML blockquote
        message = (
            f"<blockquote>{ping_icon} ᴘᴏɴɢ: {ping_time:.2f}ᴍs\n"
            f"{speed_icon} sᴘᴇᴇᴅ: {random.uniform(200, 600):.2f}ᴍs\n"
            f"{owner_icon} ᴏᴡɴʀ: — {owner_link}</blockquote>\n\n"
            f"<blockquote>© USERBOT @ApckUbot</blockquote>"
        )
        
        # Edit pesan
        await msg.edit(message, parse_mode="html")