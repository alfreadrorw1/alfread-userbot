import json
import asyncio
from telethon import events, Button, errors
from config import OWNER_ID, BOT_TOKEN

# ==================== DATA CONFIG ====================

def get_prefix():
    """Mengambil prefix aktif agar panduan akurat"""
    try:
        with open('data/prefix.json', 'r') as f:
            p = json.load(f).get('prefix', '.')
            return "" if p == "no" else p
    except:
        return "."

# Dictionary Konten Help
# Key: Judul Halaman
# Value: Isi Panduan
def get_help_content(prefix):
    return {
        "Start": (
            "<b>🔮 ᴀʟғʀᴇᴀᴅ ᴜsᴇʀʙᴏᴛ ᴍᴇɴᴜ</b>\n\n"
            "<blockquote>✘ ʜᴀʟᴏ ᴛᴜᴀɴ! ɪɴɪ ᴀᴅᴀʟᴀʜ ᴘᴜsᴀᴛ ʙᴀɴᴛᴜᴀɴ.\n"
            "✞ ɢᴜɴᴀᴋᴀɴ ᴛᴏᴍʙᴏʟ ᴅɪ ʙᴀᴡᴀʜ ᴜɴᴛᴜᴋ ᴍᴇʟɪʜᴀᴛ\n"
            "✓ ғɪᴛᴜʀ-ғɪᴛᴜʀ ʏᴀɴɢ ᴛᴇʀsᴇᴅɪᴀ.</blockquote>\n\n"
            "<b>✞ ɪɴғᴏ sɪsᴛᴇᴍ:</b>\n"
            "• sᴛᴀᴛᴜs: <b>ᴀᴄᴛɪᴠᴇ</b>\n"
            "• ᴘʀᴇғɪx: <b>{p}</b>\n"
            "• ᴛʜᴇᴍᴇ: ᴅᴀʀᴋ ᴘᴜʀᴘʟᴇ"
        ),
        "Afk": (
            "<b>💤 ᴀғᴋ ᴍᴏᴅᴜʟᴇ</b>\n\n"
            "<blockquote>✘ ғɪᴛᴜʀ ᴜɴᴛᴜᴋ ᴍᴇɴᴀɴᴅᴀɪ ᴅɪʀɪ ᴀɴᴅᴀ\n"
            "✞ sᴇᴅᴀɴɢ sɪʙᴜᴋ/ᴛɪᴅᴀᴋ ᴀᴅᴀ.</blockquote>\n\n"
            "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
            "<code>{p}afk [alasan]</code>\n"
            "• ᴀᴋᴛɪғᴋᴀɴ ᴍᴏᴅᴇ ᴀғᴋ.\n"
            "• ᴄᴏɴᴛᴏʜ: <code>{p}afk tidur dulu</code>\n\n"
            "<code>{p}unafk</code>\n"
            "• ᴋᴇᴍʙᴀʟɪ ᴅᴀʀɪ ᴀғᴋ.\n\n"
            "<b>✘ ɴᴏᴛᴇ:</b>\n"
            "• ᴏᴛᴏᴍᴀᴛɪs ᴍᴇᴍʙᴀʟᴀs ᴊɪᴋᴀ ᴅɪ-ᴛᴀɢ/ᴘᴍ."
        ),
        "Broadcast": (
            "<b>📢 ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏᴏʟs</b>\n\n"
            "<blockquote>✘ ᴀʟᴀᴛ ᴜɴᴛᴜᴋ ᴍᴇɴɢɪʀɪᴍ ᴘᴇsᴀɴ ᴋᴇ\n"
            "✞ ʙᴀɴʏᴀᴋ ᴄʜᴀᴛ sᴇᴋᴀʟɪɢᴜs.</blockquote>\n\n"
            "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
            "<code>{p}gcast [pesan/reply]</code>\n"
            "• ᴋɪʀɪᴍ ᴘᴇsᴀɴ ᴋᴇ sᴇᴍᴜᴀ ɢʀᴜᴘ.\n\n"
            "<code>{p}ucast [pesan/reply]</code>\n"
            "• ᴋɪʀɪᴍ ᴘᴇsᴀɴ ᴋᴇ sᴇᴍᴜᴀ ᴘᴍ (ɴᴏ ʙᴏᴛ).\n\n"
            "<b>✞ ʙʟᴀᴄᴋʟɪsᴛ:</b>\n"
            "<code>{p}addbl</code> (reply/di grup) - ʙʟᴏᴋɪʀ ɢᴄᴀsᴛ ᴋᴇ sɪɴɪ.\n"
            "<code>{p}delbl [id]</code> - ʜᴀᴘᴜs ᴅᴀʀɪ ʙʟᴀᴄᴋʟɪsᴛ.\n"
            "<code>{p}listbl</code> - ʟɪʜᴀᴛ ᴅᴀғᴛᴀʀ ʙʟᴀᴄᴋʟɪsᴛ."
        ),
        "Grabber": (
            "<b>📥 ᴄᴏɴᴛᴇɴᴛ ɢʀᴀʙʙᴇʀ</b>\n\n"
            "<blockquote>✘ ᴍᴇɴɢᴀᴍʙɪʟ ᴋᴏɴᴛᴇɴ ᴅᴀʀɪ ᴄʜᴀɴɴᴇʟ\n"
            "✞ ᴘʀɪᴠᴀᴛᴇ ᴀᴛᴀᴜ ᴅɪ-ᴘʀᴏᴛᴇᴄᴛ.</blockquote>\n\n"
            "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
            "<code>{p}grab [link]</code>\n"
            "• ᴀᴍʙɪʟ 1 ᴘᴏsᴛɪɴɢᴀɴ (ғᴏᴛᴏ/ᴠɪᴅᴇᴏ/ᴛᴇxᴛ).\n\n"
            "<code>{p}mgrab [link1] [link2]</code>\n"
            "• ᴀᴍʙɪʟ ʙᴀɴʏᴀᴋ ᴘᴏsᴛɪɴɢᴀɴ (ᴍᴀx 10).\n\n"
            "<b>✘ sᴜᴘᴘᴏʀᴛ:</b>\n"
            "• ʙɪsᴀ ᴍᴇɴɢᴀᴍʙɪʟ ᴅᴀʀɪ ʟɪɴᴋ ᴊᴏɪɴ ᴘʀɪᴠᴀᴛᴇ."
        ),
        "System": (
            "<b>⚙️ sʏsᴛᴇᴍ & ɪɴғᴏ</b>\n\n"
            "<blockquote>✘ ᴜᴛɪʟɪᴛᴀs ᴅᴀsᴀʀ ᴜɴᴛᴜᴋ ᴄᴇᴋ\n"
            "✞ sᴛᴀᴛᴜs ʙᴏᴛ ᴅᴀɴ ᴀᴋᴜɴ.</blockquote>\n\n"
            "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
            "<code>{p}ping</code>\n"
            "• ᴄᴇᴋ ᴋᴇᴄᴇᴘᴀᴛᴀɴ ʀᴇsᴘᴏɴ ʙᴏᴛ.\n\n"
            "<code>{p}id</code>\n"
            "• ʟɪʜᴀᴛ ɪᴅ ɢʀᴜᴘ ᴀᴛᴀᴜ ᴜsᴇʀ.\n\n"
            "<code>{p}info</code>\n"
            "• ʟɪʜᴀᴛ ɪɴғᴏʀᴍᴀsɪ ᴘʀᴏғɪʟ ᴀɴᴅᴀ.\n\n"
            "<code>{p}limit</code>\n"
            "• ᴄᴇᴋ sᴛᴀᴛᴜs sᴘᴀᴍ/ʙᴀɴ ᴀᴋᴜɴ (@SpamBot)."
        ),
        "Config": (
            "<b>🔧 ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ</b>\n\n"
            "<blockquote>✘ ᴘᴇɴɢᴀᴛᴜʀᴀɴ ᴜsᴇʀʙᴏᴛ.</blockquote>\n\n"
            "<b>✞ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
            "<code>{p}setprefix [simbol]</code>\n"
            "• ɢᴀɴᴛɪ ᴘʀᴇғɪx (ᴄᴏɴᴛᴏʜ: . , ! ?).\n"
            "• ᴋᴇᴛɪᴋ <code>{p}setprefix no</code> ᴜɴᴛᴜᴋ ᴛᴀɴᴘᴀ ᴘʀᴇғɪx.\n\n"
            "<code>{p}prefix</code>\n"
            "• ʟɪʜᴀᴛ ᴘʀᴇғɪx ʏᴀɴɢ sᴇᴅᴀɴɢ ᴀᴋᴛɪғ."
        )
    }

# Urutan Halaman
PAGES = ["Start", "Afk", "Broadcast", "Grabber", "System", "Config"]

# ==================== LOGIC ====================

def get_page_data(index):
    """Generate text dan buttons untuk halaman tertentu"""
    current_prefix = get_prefix()
    content_dict = get_help_content(current_prefix)
    
    # Pastikan index valid (looping)
    if index >= len(PAGES): index = 0
    if index < 0: index = len(PAGES) - 1
    
    page_name = PAGES[index]
    text = content_dict[page_name].format(p=current_prefix)
    
    # Footer
    text += f"\n\n<code>❬ ʜᴀʟᴀᴍᴀɴ {index + 1}/{len(PAGES)} ❭</code>"
    
    # Logic Tombol
    prev_idx = index - 1
    next_idx = index + 1
    
    buttons = [
        [
            Button.inline("❮ ᴘʀᴇᴠ", data=f"help_goto_{prev_idx}"),
            Button.inline(f"⛧ {page_name} ⛧", data="help_noop"),
            Button.inline("ɴᴇxᴛ ❯", data=f"help_goto_{next_idx}")
        ],
        [Button.inline("✘ ᴄʟᴏsᴇ", data="help_close")]
    ]
    
    return text, buttons

async def setup(bot, user):
    
    # ---------- USERBOT TRIGGER ----------
    @user.on(events.NewMessage())
    async def help_command(event):
        # Cek apakah owner
        if event.sender_id != OWNER_ID:
            return
            
        # Cek command
        msg = (event.raw_text or '').strip()
        prefix = get_prefix()
        
        is_help = False
        if prefix == "" and msg.lower() == "help":
            is_help = True
        elif prefix != "" and msg.startswith(prefix) and msg[len(prefix):].strip().lower() == "help":
            is_help = True
            
        if not is_help:
            return

        # Hapus pesan user
        try:
            await event.delete()
        except:
            pass
            
        # Cek apakah di DM Bot (Penyebab Error Utama)
        chat = await event.get_chat()
        if event.is_private and getattr(chat, 'bot', False):
            # Kirim pesan teks biasa jika di DM bot
            await event.respond(
                "<b>⚠️ ᴇʀʀᴏʀ:</b>\n"
                "ᴛɪᴅᴀᴋ ᴅᴀᴘᴀᴛ ᴍᴇɴɢɢᴜɴᴀᴋᴀɴ ᴍᴇɴᴜ ʙᴜᴛᴛᴏɴ ᴅɪ ᴅᴀʟᴀᴍ ᴅᴍ ʙᴏᴛ.\n"
                "sɪʟᴀᴋᴀɴ ɢᴜɴᴀᴋᴀɴ ᴅɪ <b>sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs</b> ᴀᴛᴀᴜ <b>ɢʀᴜᴘ</b>.",
                parse_mode='html'
            )
            return

        # Kirim Menu Help via Bot Client
        text, buttons = get_page_data(0)
        try:
            # Gunakan bot client untuk kirim ke chat tempat user mengetik
            await bot.send_message(
                event.chat_id,
                text,
                buttons=buttons,
                parse_mode='html'
            )
        except errors.rpcerrorlist.ChatWriteForbiddenError:
            await event.respond("❌ Bot tidak memiliki izin menulis di sini.")
        except Exception as e:
            # Fallback jika bot tidak bisa mengirim (misal belum start bot)
            await event.respond(
                f"<b>✘ ᴇʀʀᴏʀ:</b> {str(e)}\n\n"
                "<b>sᴏʟᴜsɪ:</b>\n"
                "1. ᴘᴀsᴛɪᴋᴀɴ ʙᴏᴛ ᴛᴏᴋᴇɴ ʙᴇɴᴀʀ.\n"
                "2. ᴄᴏʙᴀ sᴛᴀʀᴛ ʙᴏᴛ ᴀɴᴅᴀ ᴅᴜʟᴜ (@username_bot).\n"
                "3. ᴊᴀɴɢᴀɴ ᴛᴇs ᴅɪ ᴅᴍ ʙᴏᴛ ʟᴀɪɴ.",
                parse_mode='html'
            )

    # ---------- BOT CALLBACK ----------
    @bot.on(events.CallbackQuery(pattern=b'help_.*'))
    async def help_callback(event):
        # Decode data
        data = event.data.decode('utf-8')
        
        # Validasi Owner (agar orang lain gabisa klik)
        if event.sender_id != OWNER_ID:
            await event.answer("✘ ᴍᴇɴᴜ ɪɴɪ ʜᴀɴʏᴀ ᴜɴᴛᴜᴋ ᴏᴡɴᴇʀ!", alert=True)
            return
            
        if data == "help_close":
            await event.delete()
            return
            
        if data == "help_noop":
            await event.answer("⛧ ᴀʟғʀᴇᴀᴅ ᴜsᴇʀʙᴏᴛ")
            return
            
        if data.startswith("help_goto_"):
            try:
                # Ambil index halaman
                index = int(data.split("_")[-1])
                
                # Update halaman
                text, buttons = get_page_data(index)
                await event.edit(text, buttons=buttons, parse_mode='html')
            except Exception as e:
                print(f"Error callback: {e}")
