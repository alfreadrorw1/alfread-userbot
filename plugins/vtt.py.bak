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

# Cek apakah whisper tersedia
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper tidak terinstall. Install dengan: pip install openai-whisper")

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
        'en': 'English',
        'id': 'Indonesian',
        'ar': 'Arabic',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'hi': 'Hindi',
        'it': 'Italian',
        'tr': 'Turkish',
        'nl': 'Dutch',
        'pl': 'Polish',
        'vi': 'Vietnamese',
        'th': 'Thai',
        'fa': 'Persian',
        'ur': 'Urdu',
        'he': 'Hebrew',
        'bn': 'Bengali',
        'ms': 'Malay',
        'fil': 'Filipino',
        'sw': 'Swahili',
        'am': 'Amharic',
        'ta': 'Tamil',
        'te': 'Telugu',
        'mr': 'Marathi',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'or': 'Odia',
        'pa': 'Punjabi',
        'as': 'Assamese',
        'mai': 'Maithili',
        'sa': 'Sanskrit',
        'ne': 'Nepali',
        'si': 'Sinhala',
        'my': 'Burmese',
        'km': 'Khmer',
        'lo': 'Lao',
        'bo': 'Tibetan',
        'ug': 'Uyghur',
        'mn': 'Mongolian',
        'dz': 'Dzongkha',
        'ps': 'Pashto',
        'ku': 'Kurdish',
        'ckb': 'Sorani',
        'sd': 'Sindhi',
        'bal': 'Balochi',
        'brx': 'Bodo',
        'sat': 'Santali',
        'ks': 'Kashmiri',
        'kok': 'Konkani',
        'mni': 'Manipuri',
        'doi': 'Dogri',
        'lus': 'Mizo',
        'npi': 'Nepali',
    }
    return language_names.get(code, f"Unknown ({code})")

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
            print(f"FFmpeg error: {result.stderr}")
            return False
        
        # Verify output file exists and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        return False
        
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return False

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    if not WHISPER_AVAILABLE:
        raise ImportError("Whisper library tidak tersedia")
    
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
        print(f"Transcription error: {e}")
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
                "<blockquote>✘ ᴇʀʀᴏʀ: ʏᴏᴜ ᴍᴜsᴛ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴠᴏɪᴄᴇ/ᴀᴜᴅɪᴏ ᴍᴇssᴀɢᴇ\n"
                "✓ ᴜsᴀɢᴇ: ʀᴇᴘʟʏ ᴛᴏ ᴠᴏɪᴄᴇ → .ᴠᴛᴛ</blockquote>",
                parse_mode='html'
            )
            return
        
        try:
            # Get replied message
            replied_msg = await event.get_reply_message()
            
            # Check if replied message has voice/audio
            if not (replied_msg.voice or replied_msg.audio):
                await event.reply(
                    "<blockquote>✘ ᴇʀʀᴏʀ: ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪs ɴᴏᴛ ᴀ ᴠᴏɪᴄᴇ/ᴀᴜᴅɪᴏ\n"
                    "✓ ᴏɴʟʏ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇs ᴄᴀɴ ʙᴇ ᴛʀᴀɴsᴄʀɪʙᴇᴅ</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Check if Whisper is available
            if not WHISPER_AVAILABLE:
                await event.reply(
                    "<blockquote>✘ ᴇʀʀᴏʀ: ᴡʜɪsᴘᴇʀ ʟɪʙʀᴀʀʏ ɴᴏᴛ ɪɴsᴛᴀʟʟᴇᴅ\n"
                    "✓ ɪɴsᴛᴀʟʟ ᴡɪᴛʜ: ᴘɪᴘ ɪɴsᴛᴀʟʟ ᴏᴘᴇɴᴀɪ-ᴡʜɪsᴘᴇʀ</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Send processing message
            processing_msg = await event.reply(
                "<blockquote>⛧ ᴘʀᴏᴄᴇssɪɴɢ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇ...\n"
                "✓ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀᴜᴅɪᴏ...</blockquote>",
                parse_mode='html'
            )
            
            # Gunakan directory yang lebih aman untuk Termux/VPS
            # Coba beberapa lokasi yang umum
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
            unique_dir = os.path.join(temp_dir, f"vtt_{timestamp}_{os.getpid()}")
            os.makedirs(unique_dir, exist_ok=True)
            
            original_path = os.path.join(unique_dir, "original.ogg")
            converted_path = os.path.join(unique_dir, "converted.wav")
            
            try:
                # Download audio file
                await processing_msg.edit(
                    "<blockquote>⛧ ᴘʀᴏᴄᴇssɪɴɢ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇ...\n"
                    "✓ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀᴜᴅɪᴏ...</blockquote>",
                    parse_mode='html'
                )
                
                # Download the file dengan progress
                download_path = await replied_msg.download_media(file=original_path)
                
                if not download_path or not os.path.exists(download_path):
                    await processing_msg.edit(
                        "<blockquote>✘ ᴇʀʀᴏʀ: ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴀᴜᴅɪᴏ\n"
                        "✓ ᴄʜᴇᴄᴋ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ</blockquote>",
                        parse_mode='html'
                    )
                    return
                
                # Check file size (minimum 2KB)
                file_size = os.path.getsize(download_path)
                if file_size < 2048:
                    await processing_msg.edit(
                        f"<blockquote>✘ ᴇʀʀᴏʀ: ᴀᴜᴅɪᴏ ғɪʟᴇ ɪs ᴛᴏᴏ sᴍᴀʟʟ ({file_size} ʙʏᴛᴇs)\n"
                        "✓ ᴍɪɴɪᴍᴜᴍ sɪᴢᴇ: 2ᴋʙ</blockquote>",
                        parse_mode='html'
                    )
                    return
                
                # Convert audio
                await processing_msg.edit(
                    "<blockquote>⛧ ᴘʀᴏᴄᴇssɪɴɢ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇ...\n"
                    "✓ ᴄᴏɴᴠᴇʀᴛɪɴɢ ᴀᴜᴅɪᴏ ғᴏʀᴍᴀᴛ...</blockquote>",
                    parse_mode='html'
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
                        await processing_msg.edit(
                            "<blockquote>✘ ᴇʀʀᴏʀ: ғᴀɪʟᴇᴅ ᴛᴏ ᴄᴏɴᴠᴇʀᴛ ᴀᴜᴅɪᴏ\n"
                            "✓ ᴍᴀᴋᴇ sᴜʀᴇ ғғᴍᴘᴇɢ ɪs ɪɴsᴛᴀʟʟᴇᴅ</blockquote>",
                            parse_mode='html'
                        )
                        return
                
                # Transcribe audio
                await processing_msg.edit(
                    "<blockquote>⛧ ᴘʀᴏᴄᴇssɪɴɢ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇ...\n"
                    "✓ ᴛʀᴀɴsᴄʀɪʙɪɴɢ ᴡɪᴛʜ ᴡʜɪsᴘᴇʀ...</blockquote>",
                    parse_mode='html'
                )
                
                transcription = transcribe_audio(converted_path)
                
                # Check if transcription is empty
                if not transcription['text'] or len(transcription['text'].strip()) < 2:
                    await processing_msg.edit(
                        "<blockquote>✘ ᴇʀʀᴏʀ: ɴᴏ ᴛᴇxᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ ɪɴ ᴀᴜᴅɪᴏ\n"
                        "✓ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴍᴀʏ ʙᴇ ᴛᴏᴏ sʜᴏʀᴛ, sɪʟᴇɴᴛ, ᴏʀ ɴᴏɪsʏ</blockquote>",
                        parse_mode='html'
                    )
                    return
                
                # Get user info
                sender = replied_msg.sender
                user_name = getattr(sender, 'first_name', '') or 'User'
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
                    transcript_text = transcript_text[:3000] + "...\n[ᴛʀᴜɴᴄᴀᴛᴇᴅ - ᴛᴇxᴛ ᴛᴏᴏ ʟᴏɴɢ]"
                
                output = (
                    f"<blockquote>✞ ᴠᴏɪᴄᴇ ᴛᴏ ᴛᴇxᴛ\n"
                    f"⛧ ғʀᴏᴍ: {user_link}\n"
                    f"✓ ʟᴀɴɢ: {language_name}\n\n"
                    f"✘ ᴛʀᴀɴsᴄʀɪᴘᴛɪᴏɴ:\n"
                    f"{transcript_text}</blockquote>"
                )
                
                await processing_msg.edit(output, parse_mode='html')
                
            except Exception as e:
                error_msg = str(e)[:200]
                await processing_msg.edit(
                    f"<blockquote>✘ ᴇʀʀᴏʀ: {error_msg}\n"
                    f"✓ ᴛʀʏ ᴀɢᴀɪɴ ᴏʀ ᴜsᴇ sʜᴏʀᴛᴇʀ ᴀᴜᴅɪᴏ</blockquote>",
                    parse_mode='html'
                )
                print(f"VTT Error: {traceback.format_exc()}")
            
            finally:
                # Cleanup temp files
                try:
                    import shutil
                    if os.path.exists(unique_dir):
                        shutil.rmtree(unique_dir, ignore_errors=True)
                except:
                    pass
                
        except Exception as e:
            error_msg = str(e)[:200]
            await event.reply(
                f"<blockquote>✘ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ: {error_msg}\n"
                f"✓ ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ</blockquote>",
                parse_mode='html'
            )
            print(f"VTT Main Error: {traceback.format_exc()}")

# Perbaikan: Tambahkan import time yang hilang
import time