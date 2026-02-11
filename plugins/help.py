import json
import os
import asyncio
from telethon import events, Button
from telethon.tl.custom import Message
from config import OWNER_ID

# ==================== HELP CONFIGURATION ====================

# Dictionary lengkap fitur dan cara penggunaannya
# Format: "Nama Modul": "Isi bantuan (support HTML)"
HELP_COMMANDS = {
    "Start": (
        "<b>⛧ ᴀʟғʀᴇᴀᴅ ᴜsᴇʀʙᴏᴛ ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
        "<blockquote>✘ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʜᴇʟᴘ ᴄᴇɴᴛᴇʀ.\n"
        "✞ ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ\n"
        "✓ ᴛʜʀᴏᴜɢʜ ᴀᴠᴀɪʟᴀʙʟᴇ ᴍᴏᴅᴜʟᴇs.</blockquote>\n\n"
        "<b>✞ sʏsᴛᴇᴍ ɪɴғᴏ:</b>\n"
        "• ᴘʏᴛʜᴏɴ ʙᴀsᴇᴅ (ᴛᴇʟᴇᴛʜᴏɴ)\n"
        "• ᴅᴀʀᴋ ᴘʀᴇᴍɪᴜᴍ ᴛʜᴇᴍᴇ\n"
        "• ᴍᴏᴅᴜʟᴀʀ ᴘʟᴜɢɪɴ sʏsᴛᴇᴍ"
    ),
    "Afk": (
        "<b>💤 ᴀғᴋ (ᴀᴡᴀʏ ғʀᴏᴍ ᴋᴇʏʙᴏᴀʀᴅ)</b>\n\n"
        "<blockquote>✘ ᴍᴏᴅᴜʟᴇ ᴛᴏ ʜᴀɴᴅʟᴇ ᴀᴜᴛᴏ-ʀᴇᴘʟɪᴇs ᴡʜᴇɴ\n"
        "✞ ʏᴏᴜ ᴀʀᴇ ʙᴜsʏ ᴏʀ ᴏғғʟɪɴᴇ.</blockquote>\n\n"
        "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "<code>{p}afk [reason]</code>\n"
        "• ᴀᴄᴛɪᴠᴀᴛᴇ ᴀғᴋ ᴍᴏᴅᴇ ᴡɪᴛʜ ᴏᴘᴛɪᴏɴᴀʟ ʀᴇᴀsᴏɴ.\n\n"
        "<code>{p}unafk</code>\n"
        "• ᴅɪsᴀʙʟᴇ ᴀғᴋ ᴍᴏᴅᴇ ᴀɴᴅ sʜᴏᴡ sᴛᴀᴛs.\n\n"
        "<b>✘ ɴᴏᴛᴇ:</b>\n"
        "• ʀᴇᴘʟɪᴇs ᴛᴏ ᴍᴇɴᴛɪᴏɴs/ᴘᴍs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.\n"
        "• ɪɴᴄʟᴜᴅᴇs sᴘᴀᴍ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ (ᴄᴏᴏʟᴅᴏᴡɴ)."
    ),
    "Broadcast": (
        "<b>📢 ʙʀᴏᴀᴅᴄᴀsᴛ & ʙʟᴀᴄᴋʟɪsᴛ</b>\n\n"
        "<blockquote>✘ ᴀᴅᴠᴀɴᴄᴇᴅ ᴛᴏᴏʟs ғᴏʀ ᴍᴀss ᴍᴇssᴀɢɪɴɢ\n"
        "✞ ᴀɴᴅ ᴍᴀɴᴀɢɪɴɢ ʙʟᴏᴄᴋᴇᴅ ᴇɴᴛɪᴛɪᴇs.</blockquote>\n\n"
        "<b>✞ ɢʟᴏʙᴀʟ ᴄᴀsᴛ:</b>\n"
        "<code>{p}gcast [msg/reply]</code>\n"
        "• ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ɢʀᴏᴜᴘs.\n"
        "<code>{p}ucast [msg/reply]</code>\n"
        "• ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛs (ɴᴏ ʙᴏᴛs).\n\n"
        "<b>✞ ʙʟᴀᴄᴋʟɪsᴛ ᴍᴀɴᴀɢᴇʀ:</b>\n"
        "<code>{p}addbl</code> (ʀᴇᴘʟʏ/ɪɴ ɢʀᴏᴜᴘ)\n"
        "• ᴀᴅᴅ ᴜsᴇʀ/ɢʀᴏᴜᴘ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ (sᴋɪᴘᴘᴇᴅ ɪɴ ɢᴄᴀsᴛ).\n"
        "<code>{p}delbl [id]</code>\n"
        "• ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ʙʟᴀᴄᴋʟɪsᴛ.\n"
        "<code>{p}listbl</code>\n"
        "• sʜᴏᴡ ᴀʟʟ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴇɴᴛɪᴛɪᴇs."
    ),
    "Grabber": (
        "<b>📥 ᴄᴏɴᴛᴇɴᴛ ɢʀᴀʙʙᴇʀ</b>\n\n"
        "<blockquote>✘ sᴛᴇᴀʟ ᴄᴏɴᴛᴇɴᴛ ғʀᴏᴍ ʀᴇsᴛʀɪᴄᴛᴇᴅ\n"
        "✞ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs.</blockquote>\n\n"
        "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "<code>{p}grab [link]</code>\n"
        "• sᴀᴠᴇ ᴍᴇᴅɪᴀ/ᴛᴇxᴛ ғʀᴏᴍ ᴀ ᴘᴏsᴛ ʟɪɴᴋ.\n\n"
        "<code>{p}mgrab [link1] [link2]</code>\n"
        "• ʙᴜʟᴋ ɢʀᴀʙ (ᴍᴀx 10). sᴜᴘᴘᴏʀᴛs ʀᴀɴɢᴇ.\n"
        "• Ex: <code>{p}mgrab .../100 .../105</code>\n\n"
        "<b>✘ sᴜᴘᴘᴏʀᴛs:</b>\n"
        "• ᴘʜᴏᴛᴏ, ᴠɪᴅᴇᴏ, ᴅᴏᴄᴜᴍᴇɴᴛ, sᴛɪᴄᴋᴇʀ, ᴀᴜᴅɪᴏ."
    ),
    "System": (
        "<b>⚙️ sʏsᴛᴇᴍ & ᴜᴛɪʟɪᴛʏ</b>\n\n"
        "<blockquote>✘ ʙᴀsɪᴄ ᴜᴛɪʟɪᴛɪᴇs ᴛᴏ ᴍᴀɴᴀɢᴇ ᴛʜᴇ\n"
        "✞ ʙᴏᴛ ᴀɴᴅ ᴄʜᴇᴄᴋ sᴛᴀᴛᴜs.</blockquote>\n\n"
        "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "<code>{p}ping</code>\n"
        "• ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ ᴀɴᴅ ᴜᴘᴛɪᴍᴇ.\n"
        "<code>{p}id</code>\n"
        "• ɢᴇᴛ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ ɪᴅ ᴀɴᴅ ɪɴғᴏ.\n"
        "<code>{p}info</code>\n"
        "• sʜᴏᴡ ʙᴏᴛ ᴘʀᴏғɪʟᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ.\n"
        "<code>{p}limit</code>\n"
        "• ᴄʜᴇᴄᴋ ᴀᴄᴄᴏᴜɴᴛ sᴘᴀᴍ sᴛᴀᴛᴜs via @SpamBot."
    ),
    "Config": (
        "<b>🔧 ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ</b>\n\n"
        "<blockquote>✘ ᴄᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ\n"
        "✞ ʙᴇʜᴀᴠɪᴏʀ.</blockquote>\n\n"
        "<b>✞ ᴘʀᴇғɪx sᴇᴛᴛɪɴɢs:</b>\n"
        "<code>{p}setprefix [symbol]</code>\n"
        "• ᴄʜᴀɴɢᴇ ᴄᴏᴍᴍᴀɴᴅ ᴘʀᴇғɪx (e.g., . / ! ?).\n"
        "• ᴜsᴇ <code>setprefix no</code> ғᴏʀ ɴᴏ-ᴘʀᴇғɪx ᴍᴏᴅᴇ.\n\n"
        "<code>{p}prefix</code>\n"
        "• ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ᴘʀᴇғɪx."
    )
}

# Konversi keys ke list untuk indexing
MODULE_LIST = list(HELP_COMMANDS.keys())

# ==================== HELPER FUNCTIONS ====================

def get_prefix():
    """Mengambil prefix saat ini dari file config"""
    try:
        with open('data/prefix.json', 'r') as f:
            p = json.load(f).get('prefix', '.')
            # Jika prefix 'no', kita return string kosong untuk display command
            return "" if p == "no" else p
    except:
        return "."

def render_help_message(page_index):
    """
    Generate pesan help dan tombol berdasarkan index halaman.
    page_index: int (0 untuk halaman pertama)
    """
    current_prefix = get_prefix()
    
    # Pastikan index valid (wrap around)
    total_pages = len(MODULE_LIST)
    if page_index >= total_pages:
        page_index = 0
    elif page_index < 0:
        page_index = total_pages - 1
        
    module_name = MODULE_LIST[page_index]
    help_text = HELP_COMMANDS[module_name]
    
    # Format text dengan prefix yang benar
    formatted_text = help_text.format(p=current_prefix)
    
    # Tambahkan footer halaman
    formatted_text += f"\n\n<code>❬ ᴘᴀɢᴇ {page_index + 1}/{total_pages} ❭</code>"

    # Buat tombol navigasi
    # Logic: [PREV] [NAME] [NEXT]
    #        [      CLOSE       ]
    
    prev_index = page_index - 1
    next_index = page_index + 1
    
    buttons = [
        [
            Button.inline("❮ ᴘʀᴇᴠ", data=f"help_prev_{prev_index}"),
            Button.inline(f"⛧ {module_name} ⛧", data="help_dummy"),
            Button.inline("ɴᴇxᴛ ❯", data=f"help_next_{next_index}")
        ],
        [
            Button.inline("✘ ᴄʟᴏsᴇ ᴍᴇɴᴜ ✘", data="help_close")
        ]
    ]
    
    return formatted_text, buttons

# ==================== MAIN SETUP ====================

def setup(bot, user):
    
    # ---------- USERBOT HANDLER (.help) ----------
    @user.on(events.NewMessage())
    async def user_help_handler(event):
        """Menangkap command .help dari UserBot"""
        if event.sender_id != OWNER_ID:
            return
            
        # Cek command prefix
        msg = (event.raw_text or '').strip()
        
        # Load real prefix for checking
        try:
            with open('data/prefix.json', 'r') as f:
                real_prefix = json.load(f).get('prefix', '.')
        except:
            real_prefix = '.'
            
        is_command = False
        if real_prefix == "no" and msg.lower() == "help":
            is_command = True
        elif msg.startswith(real_prefix) and msg[len(real_prefix):].strip().lower() == "help":
            is_command = True
            
        if not is_command:
            return

        # Efek loading
        loading = await event.reply("<blockquote>⛧ ᴏᴘᴇɴɪɴɢ ʜᴇʟᴘ ᴍᴇɴᴜ...</blockquote>", parse_mode='html')
        
        try:
            # Kita gunakan BOT client untuk mengirim pesan dengan button
            # karena UserBot tidak bisa kirim button ke chat biasa.
            
            # Generate halaman pertama (Index 0)
            text, buttons = render_help_message(0)
            
            # Kirim menu menggunakan BOT client ke chat yang sama
            await bot.send_message(
                event.chat_id,
                text,
                buttons=buttons,
                parse_mode='html'
            )
            
            # Hapus pesan "Opening..." dan pesan command user agar bersih
            await loading.delete()
            await event.delete()
            
        except Exception as e:
            await loading.edit(
                f"<blockquote>✘ ᴇʀʀᴏʀ: ᴄᴀɴɴᴏᴛ sᴇɴᴅ ʙᴜᴛᴛᴏɴs.\n"
                f"✓ ᴍᴀᴋᴇ sᴜʀᴇ ʙᴏᴛ ᴛᴏᴋᴇɴ ɪs ᴄᴏʀʀᴇᴄᴛ.\n"
                f"✘ ᴅᴇᴛᴀɪʟs: {e}</blockquote>", 
                parse_mode='html'
            )

    # ---------- BOT HANDLER (Callbacks) ----------
    @bot.on(events.CallbackQuery())
    async def help_callback_handler(event):
        """Menangani klik tombol Next/Prev/Close"""
        # Decode data
        data = event.data.decode('utf-8')
        
        # Security: Pastikan yang klik adalah Owner
        if event.sender_id != OWNER_ID:
            await event.answer("✘ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ᴏᴡɴᴇʀ!", alert=True)
            return

        if data == "help_close":
            await event.delete()
            return
            
        if data == "help_dummy":
            await event.answer("⛧ ᴀʟғʀᴇᴀᴅ ᴜsᴇʀʙᴏᴛ")
            return

        # Handle Navigasi
        if data.startswith("help_prev_") or data.startswith("help_next_"):
            try:
                # Ambil index dari data (contoh: help_next_2 -> index 2)
                target_index = int(data.split("_")[-1])
                
                # Render halaman baru
                new_text, new_buttons = render_help_message(target_index)
                
                # Edit pesan
                await event.edit(
                    new_text,
                    buttons=new_buttons,
                    parse_mode='html'
                )
            except Exception as e:
                print(f"Help Error: {e}")
                await event.answer("❌ Error loading page")
