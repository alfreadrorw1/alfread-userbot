# plugins/vtt.py
import os
import tempfile
import asyncio
from datetime import datetime
import json
from telethon import events
import subprocess
from config import OWNER_ID
import traceback
import time
import random  # Untuk membuat unique message

# Cek apakah whisper tersedia
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠ ᴡʜɪsᴘᴇʀ ᴛɪᴅᴀᴋ ᴛᴇʀɪɴsᴛᴀʟʟ. ɪɴsᴛᴀʟʟ ᴅᴇɴɢᴀɴ: ᴘɪᴘ ɪɴsᴛᴀʟʟ ᴏᴘᴇɴᴀɪ-ᴡʜɪsᴘᴇʀ")

def get_prefix():
    """Get current prefix from config"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def get_language_name(code):
    """Convert language code to readable name"""
    language_names = {
        'en': 'ᴇɴɢʟɪsʜ',
        'id': 'ɪɴᴅᴏɴᴇsɪᴀɴ',
        'ar': 'ᴀʀᴀʙɪᴄ',
        'es': 'sᴘᴀɴɪsʜ',
        'fr': 'ғʀᴇɴᴄʜ',
        'de': 'ɢᴇʀᴍᴀɴ',
        'pt': 'ᴘᴏʀᴛᴜɢᴜᴇsᴇ',
        'ru': 'ʀᴜssɪᴀɴ',
        'zh': 'ᴄʜɪɴᴇsᴇ',
        'ja': 'ᴊᴀᴘᴀɴᴇsᴇ',
        'ko': 'ᴋᴏʀᴇᴀɴ',
        'hi': 'ʜɪɴᴅɪ',
        'it': 'ɪᴛᴀʟɪᴀɴ',
        'tr': 'ᴛᴜʀᴋɪsʜ',
        'nl': 'ᴅᴜᴛᴄʜ',
        'pl': 'ᴘᴏʟɪsʜ',
        'vi': 'ᴠɪᴇᴛɴᴀᴍᴇsᴇ',
        'th': 'ᴛʜᴀɪ',
        'fa': 'ᴘᴇʀsɪᴀɴ',
        'ur': 'ᴜʀᴅᴜ',
        'he': 'ʜᴇʙʀᴇᴡ',
        'bn': 'ʙᴇɴɢᴀʟɪ',
        'ms': 'ᴍᴀʟᴀʏ',
        'fil': 'ғɪʟɪᴘɪɴᴏ',
        'sw': 'sᴡᴀʜɪʟɪ',
        'am': 'ᴀᴍʜᴀʀɪᴄ',
        'ta': 'ᴛᴀᴍɪʟ',
        'te': 'ᴛᴇʟᴜɢᴜ',
        'mr': 'ᴍᴀʀᴀᴛʜɪ',
        'gu': 'ɢᴜᴊᴀʀᴀᴛɪ',
        'kn': 'ᴋᴀɴɴᴀᴅᴀ',
        'ml': 'ᴍᴀʟᴀʏᴀʟᴀᴍ',
        'or': 'ᴏᴅɪᴀ',
        'pa': 'ᴘᴜɴᴊᴀʙɪ',
        'as': 'ᴀssᴀᴍᴇsᴇ',
        'mai': 'ᴍᴀɪᴛʜɪʟɪ',
        'sa': 'sᴀɴsᴋʀɪᴛ',
        'ne': 'ɴᴇᴘᴀʟɪ',
        'si': 'sɪɴʜᴀʟᴀ',
        'my': 'ʙᴜʀᴍᴇsᴇ',
        'km': 'ᴋʜᴍᴇʀ',
        'lo': 'ʟᴀᴏ',
        'bo': 'ᴛɪʙᴇᴛᴀɴ',
        'ug': 'ᴜʏɢʜᴜʀ',
        'mn': 'ᴍᴏɴɢᴏʟɪᴀɴ',
        'dz': 'ᴅᴢᴏɴɢᴋʜᴀ',
        'ps': 'ᴘᴀsʜᴛᴏ',
        'ku': 'ᴋᴜʀᴅɪsʜ',
        'ckb': 'sᴏʀᴀɴɪ',
        'sd': 'sɪɴᴅʜɪ',
        'bal': 'ʙᴀʟᴏᴄʜɪ',
        'brx': 'ʙᴏᴅᴏ',
        'sat': 'sᴀɴᴛᴀʟɪ',
        'ks': 'ᴋᴀsʜᴍɪʀɪ',
        'kok': 'ᴋᴏɴᴋᴀɴɪ',
        'mni': 'ᴍᴀɴɪᴘᴜʀɪ',
        'doi': 'ᴅᴏɢʀɪ',
        'lus': 'ᴍɪᴢᴏ',
        'npi': 'ɴᴇᴘᴀʟɪ',
    }
    return language_names.get(code, f"ᴜɴᴋɴᴏᴡɴ ({code})")

def convert_audio(input_path, output_path):
    """Convert audio to WAV format using ffmpeg"""
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ac', '1',  # Mono channel
            '-ar', '16000',  # 16kHz sample rate
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-y',  # Overwrite output
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ғғᴍᴘᴇɢ ᴇʀʀᴏʀ: {result.stderr}")
            return False
        
        # Verify output file exists and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        return False
        
    except Exception as e:
        print(f"ᴀᴜᴅɪᴏ ᴄᴏɴᴠᴇʀsɪᴏɴ ᴇʀʀᴏʀ: {e}")
        return False

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    if not WHISPER_AVAILABLE:
        raise ImportError("ᴡʜɪsᴘᴇʀ ʟɪʙʀᴀʀʏ ᴛɪᴅᴀᴋ ᴛᴇʀsᴇᴅɪᴀ")
    
    try:
        # Load model (gunakan 'base' untuk kecepatan, 'small' untuk akurasi lebih baik)
        model = whisper.load_model("base")
        
        # Transcribe dengan parameter yang dioptimalkan
        result = model.transcribe(
            audio_path,
            task="transcribe",
            language=None,  # Auto-detect
            temperature=0,
            fp16=False,
            verbose=False
        )
        
        return {
            'text': result['text'].strip(),
            'language': result.get('language', 'unknown'),
            'segments': result.get('segments', [])
        }
        
    except Exception as e:
        print(f"ᴛʀᴀɴsᴄʀɪᴘᴛɪᴏɴ ᴇʀʀᴏʀ: {e}")
        raise

async def safe_edit_message(message, new_text):
    """Safely edit a message, avoiding 'content not modified' error"""
    try:
        # Cek apakah teks sudah berbeda
        if hasattr(message, 'message') and message.message == new_text:
            # Tambahkan karakter unik di akhir untuk menghindari error
            unique_char = f" [{random.randint(1000, 9999)}]"
            new_text = new_text.replace("</blockquote>", f"{unique_char}</blockquote>")
        
        await message.edit(new_text, parse_mode='html')
        return True
    except Exception as e:
        if "not modified" in str(e).lower():
            # Jika error karena content sama, abaikan saja
            print(f"ɪɴғᴏ: ᴘᴇsᴀɴ sᴜᴅᴀʜ ᴜᴘᴅᴀᴛᴇ ({e})")
            return True
        else:
            # Jika error lain, lempar exception
            raise

def setup(bot, user):
    
    @user.on(events.NewMessage())
    async def vtt_handler(event):
        """Handle Voice to Text command"""
        if event.sender_id != OWNER_ID:
            return
        
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check for .vtt command
        is_vtt = False
        
        if current_prefix == "no" and message.lower() == "vtt":
            is_vtt = True
        elif current_prefix != "no" and message.startswith(current_prefix):
            cmd_text = message[len(current_prefix):].strip().lower()
            if cmd_text == "vtt":
                is_vtt = True
        
        if not is_vtt:
            return
        
        # Check if replying to a message
        if not event.is_reply:
            await event.reply(
                "<blockquote>⚠ ᴇʀʀᴏʀ: ʜᴀʀᴀᴘ ʀᴇᴘʟʏ ᴘᴇsᴀɴ ʏᴀɴɢ ᴍᴇɴɢᴀɴᴅᴜɴɢ ᴠᴏɪᴄᴇ/ᴀᴜᴅɪᴏ\n"
                "📌 ᴜsᴀɢᴇ: ʀᴇᴘʟʏ ᴠᴏɪᴄᴇ → .ᴠᴛᴛ</blockquote>",
                parse_mode='html'
            )
            return
        
        # Variabel untuk tracking progress
        processing_msg = None
        processing_stages = [
            "⏳ ᴍᴇᴍᴘʀᴏsᴇs ᴠᴏɪᴄᴇ ᴍᴇɴᴊᴀᴅɪ ᴛᴇᴋsᴛ...",
            "📥 ᴍᴇɴɢᴜɴᴅᴜʜ ᴀᴜᴅɪᴏ...",
            "🔄 ᴍᴇɴɢᴏɴᴠᴇʀsɪ ᴀᴜᴅɪᴏ ғᴏʀᴍᴀᴛ...",
            "📝 ᴍᴇɴᴛʀᴀɴsᴋʀɪᴘsɪ ᴅᴇɴɢᴀɴ ᴡʜɪsᴘᴇʀ..."
        ]
        current_stage = 0
        
        try:
            # Get replied message
            replied_msg = await event.get_reply_message()
            
            # Check if replied message has voice/audio
            if not (replied_msg.voice or replied_msg.audio):
                await event.reply(
                    "<blockquote>⚠ ᴇʀʀᴏʀ: ᴘᴇsᴀɴ ʏᴀɴɢ ᴅɪʀᴇᴘʟʏ ʙᴜᴋᴀɴ ᴠᴏɪᴄᴇ/ᴀᴜᴅɪᴏ\n"
                    "📌 ᴘᴀsᴛɪᴋᴀɴ ᴍᴇɴɢʀᴇᴘʟʏ ᴘᴇsᴀɴ ᴠᴏɪᴄᴇ ʏᴀɴɢ ʙᴇɴᴀʀ</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Check if Whisper is available
            if not WHISPER_AVAILABLE:
                await event.reply(
                    "<blockquote>⚠ ᴇʀʀᴏʀ: ᴡʜɪsᴘᴇʀ ᴛɪᴅᴀᴋ ᴛᴇʀɪɴsᴛᴀʟʟ\n"
                    "📌 ɪɴsᴛᴀʟʟ ᴡʜɪsᴘᴇʀ ᴅᴇɴɢᴀɴ: ᴘɪᴘ ɪɴsᴛᴀʟʟ ᴏᴘᴇɴᴀɪ-ᴡʜɪsᴘᴇʀ</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Send initial processing message
            processing_msg = await event.reply(
                f"<blockquote>{processing_stages[current_stage]}</blockquote>",
                parse_mode='html'
            )
            
            # Gunakan directory yang lebih aman untuk Termux/VPS
            temp_dirs = [
                '/tmp',
                '/data/data/com.termux/files/usr/tmp',
                os.path.join(os.path.expanduser('~'), 'tmp'),
                'tmp_vtt'
            ]
            
            temp_dir = None
            for dir_path in temp_dirs:
                try:
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                    # Test write permission
                    test_file = os.path.join(dir_path, 'test_write.tmp')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    temp_dir = dir_path
                    break
                except:
                    continue
            
            if not temp_dir:
                # Buat directory di current working directory
                temp_dir = 'vtt_temp'
                os.makedirs(temp_dir, exist_ok=True)
            
            # Buat unique subdirectory dalam temp_dir
            timestamp = int(time.time())
            unique_dir = os.path.join(temp_dir, f"vtt_{timestamp}_{os.getpid()}_{random.randint(1000, 9999)}")
            os.makedirs(unique_dir, exist_ok=True)
            
            original_path = os.path.join(unique_dir, "original.ogg")
            converted_path = os.path.join(unique_dir, "converted.wav")
            
            try:
                # Stage 1: Download audio file
                current_stage = 1
                await safe_edit_message(
                    processing_msg,
                    f"<blockquote>{processing_stages[current_stage]}</blockquote>"
                )
                
                # Download the file
                download_path = await replied_msg.download_media(file=original_path)
                
                if not download_path or not os.path.exists(download_path):
                    await safe_edit_message(
                        processing_msg,
                        "<blockquote>⚠ ᴇʀʀᴏʀ: ɢᴀɢᴀʟ ᴍᴇɴɢᴜɴᴅᴜʜ ᴀᴜᴅɪᴏ\n"
                        "📌 ᴘᴇʀɪᴋsᴀ ᴋᴇᴍʙᴀʟɪ ᴋᴏɴᴇᴋsɪ ɪɴᴛᴇʀɴᴇᴛ</blockquote>"
                    )
                    return
                
                # Check file size (minimum 2KB)
                file_size = os.path.getsize(download_path)
                if file_size < 2048:
                    await safe_edit_message(
                        processing_msg,
                        f"<blockquote>⚠ ᴇʀʀᴏʀ: ᴀᴜᴅɪᴏ ᴛᴇʀʟᴀʟᴜ ᴘᴇɴᴅᴇᴋ ({file_size} ʙʏᴛᴇs)\n"
                        "📌 ᴍɪɴɪᴍᴀʟ sɪᴢᴇ: 2ᴋʙ</blockquote>"
                    )
                    return
                
                # Stage 2: Convert audio
                current_stage = 2
                await safe_edit_message(
                    processing_msg,
                    f"<blockquote>{processing_stages[current_stage]}</blockquote>"
                )
                
                if not convert_audio(download_path, converted_path):
                    # Coba dengan format lain
                    converted_path = os.path.join(unique_dir, "converted.mp3")
                    cmd_mp3 = [
                        'ffmpeg', '-i', download_path,
                        '-ac', '1',
                        '-ar', '16000',
                        '-y',
                        converted_path
                    ]
                    
                    result_mp3 = subprocess.run(
                        cmd_mp3,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if result_mp3.returncode != 0:
                        await safe_edit_message(
                            processing_msg,
                            "<blockquote>⚠ ᴇʀʀᴏʀ: ɢᴀɢᴀʟ ᴍᴇɴɢᴏɴᴠᴇʀsɪ ᴀᴜᴅɪᴏ\n"
                            "📌 ᴘᴀsᴛɪᴋᴀɴ ғғᴍᴘᴇɢ ᴛᴇʀɪɴsᴛᴀʟʟ ᴅᴀɴ ᴛᴇʀsᴇᴅɪᴀ</blockquote>"
                        )
                        return
                
                # Stage 3: Transcribe audio
                current_stage = 3
                await safe_edit_message(
                    processing_msg,
                    f"<blockquote>{processing_stages[current_stage]}</blockquote>"
                )
                
                transcription = transcribe_audio(converted_path)
                
                # Check if transcription is empty
                if not transcription['text'] or len(transcription['text'].strip()) < 2:
                    await safe_edit_message(
                        processing_msg,
                        "<blockquote>⚠ ᴇʀʀᴏʀ: ᴛɪᴅᴀᴋ ᴅᴀᴘᴀᴛ ᴍᴇɴɢᴇɴᴀʟɪ ᴛᴇᴋsᴛ ᴅᴀʀɪ ᴀᴜᴅɪᴏ\n"
                        "📌 ᴘᴀsᴛɪᴋᴀɴ ᴀᴜᴅɪᴏ ᴊᴇʟᴀs, ᴛɪᴅᴀᴋ ʙɪsᴜ, ᴅᴀɴ ᴛᴇʀᴅᴀᴘᴀᴛ ᴜᴄᴀᴘᴀɴ</blockquote>"
                    )
                    return
                
                # Get user info
                sender = replied_msg.sender
                user_name = getattr(sender, 'first_name', '') or 'ᴜsᴇʀ'
                if hasattr(sender, 'last_name') and sender.last_name:
                    user_name += f" {sender.last_name}"
                
                if hasattr(sender, 'username') and sender.username:
                    user_link = f'<a href="https://t.me/{sender.username}">{user_name}</a>'
                else:
                    user_link = user_name
                
                # Get language name
                lang_code = transcription['language']
                language_name = get_language_name(lang_code)
                
                # Format output
                transcript_text = transcription['text']
                
                # Split long transcripts
                if len(transcript_text) > 3000:
                    transcript_text = transcript_text[:3000] + "...\n[ᴛʀᴜɴᴄᴀᴛᴇᴅ - ᴛᴇᴋsᴛ ᴛᴇʀʟᴀʟᴜ ᴘᴀɴᴊᴀɴɢ]"
                
                output = (
                    f"<blockquote>🎤 ᴠᴏɪᴄᴇ ᴛᴏ ᴛᴇxᴛ\n"
                    f"👤 ᴘᴇɴɢɢᴜɴᴀ: {user_link}\n"
                    f"📌 ʙᴀʜᴀsᴀ: {language_name}\n\n"
                    f"📝 ᴛʀᴀɴsᴋʀɪᴘsɪ:\n"
                    f"{transcript_text}</blockquote>"
                )
                
                await safe_edit_message(processing_msg, output)
                
            except Exception as e:
                error_msg = str(e)[:200]
                await safe_edit_message(
                    processing_msg,
                    f"<blockquote>⚠ ᴇʀʀᴏʀ: {error_msg}\n"
                    f"📌 ᴄᴏʙᴀ ᴜʟᴀɴɢɪ ᴏʀ ᴜsᴇ sʜᴏʀᴛᴇʀ ᴀᴜᴅɪᴏ</blockquote>"
                )
                print(f"ᴠᴛᴛ ᴇʀʀᴏʀ: {traceback.format_exc()}")
            
            finally:
                # Cleanup temp files dengan delay kecil
                await asyncio.sleep(1)
                try:
                    import shutil
                    if os.path.exists(unique_dir):
                        shutil.rmtree(unique_dir, ignore_errors=True)
                except:
                    pass
                
        except Exception as e:
            error_msg = str(e)[:200]
            if processing_msg:
                await safe_edit_message(
                    processing_msg,
                    f"<blockquote>⚠ ᴛᴇʀᴊᴀᴅɪ ᴋᴇsᴀʟᴀʜᴀɴ: {error_msg}\n"
                    f"📌 ᴘᴇʀɪᴋsᴀ ᴋᴇᴍʙᴀʟɪ ᴘᴇʀɪɴᴛᴀʜ</blockquote>"
                )
            else:
                await event.reply(
                    f"<blockquote>⚠ ᴛᴇʀᴊᴀᴅɪ ᴋᴇsᴀʟᴀʜᴀɴ: {error_msg}\n"
                    f"📌 ᴘᴇʀɪᴋsᴀ ᴋᴇᴍʙᴀʟɪ ᴘᴇʀɪɴᴛᴀʜ</blockquote>",
                    parse_mode='html'
                )
            print(f"ᴠᴛᴛ ᴍᴀɪɴ ᴇʀʀᴏʀ: {traceback.format_exc()}")