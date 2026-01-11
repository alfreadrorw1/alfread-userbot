# vtt.py - Voice To Text untuk Termux
import os
import json
import speech_recognition as sr
from telethon import events
from telethon.tl.types import DocumentAttributeAudio
import tempfile
import subprocess
from config import OWNER_ID

def is_voice_or_audio(message):
    """Check if message is voice/audio"""
    if not message.media:
        return False
    
    if hasattr(message.media, 'document'):
        # Cek voice message
        for attr in message.media.document.attributes:
            if isinstance(attr, DocumentAttributeAudio):
                if attr.voice:
                    return True
        
        # Cek audio file
        mime_type = getattr(message.media.document, 'mime_type', '')
        if mime_type and mime_type.startswith('audio/'):
            return True
    
    return False

def convert_audio_to_flac(input_path, output_path):
    """Convert audio to FLAC format for speech recognition"""
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ac', '1',           # Mono channel
            '-ar', '16000',       # 16kHz sample rate
            '-acodec', 'flac',    # FLAC codec
            '-compression_level', '5',  # Medium compression
            '-y',                 # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            # Fallback: try WAV format
            wav_path = output_path.replace('.flac', '.wav')
            cmd_wav = [
                'ffmpeg',
                '-i', input_path,
                '-ac', '1',
                '-ar', '16000',
                '-acodec', 'pcm_s16le',
                '-y',
                wav_path
            ]
            
            result_wav = subprocess.run(cmd_wav, capture_output=True, text=True, timeout=30)
            if result_wav.returncode == 0:
                return wav_path
            else:
                raise Exception(f"FFmpeg error: {result.stderr[:200]}")
        
        return output_path
    except subprocess.TimeoutExpired:
        raise Exception("Audio conversion timeout")
    except Exception as e:
        raise Exception(f"Conversion error: {str(e)}")

def recognize_speech_multilingual(audio_path):
    """Recognize speech from audio file in multiple languages automatically"""
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Record the audio
            audio_data = recognizer.record(source)
            
            # Try English first (most common)
            try:
                text = recognizer.recognize_google(
                    audio_data, 
                    language='en-US',
                    show_all=False
                )
                detected_lang = "English"
                return text.strip(), detected_lang
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Try Indonesian
            try:
                text = recognizer.recognize_google(
                    audio_data, 
                    language='id-ID',
                    show_all=False
                )
                detected_lang = "Indonesia"
                return text.strip(), detected_lang
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Try Japanese
            try:
                text = recognizer.recognize_google(
                    audio_data, 
                    language='ja-JP',
                    show_all=False
                )
                detected_lang = "Japanese"
                return text.strip(), detected_lang
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Try Korean
            try:
                text = recognizer.recognize_google(
                    audio_data, 
                    language='ko-KR',
                    show_all=False
                )
                detected_lang = "Korean"
                return text.strip(), detected_lang
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Try Arabic
            try:
                text = recognizer.recognize_google(
                    audio_data, 
                    language='ar-SA',
                    show_all=False
                )
                detected_lang = "Arabic"
                return text.strip(), detected_lang
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Fallback: try without language (auto-detect)
            try:
                text = recognizer.recognize_google(
                    audio_data,
                    show_all=False
                )
                detected_lang = "Auto-detected 🌐"
                return text.strip(), detected_lang
            except sr.UnknownValueError:
                return None, None
            except sr.RequestError as e:
                raise Exception(f"Google Speech API error: {str(e)}")
                
    except Exception as e:
        raise Exception(f"Recognition error: {str(e)}")

def setup(bot, user):
    
    # ========== VTT REPLY HANDLER ==========
    @user.on(events.NewMessage(pattern=r'^vtt$'))
    async def vtt_reply_handler(event):
        """Handle vtt command when replying to voice/audio"""
        if event.sender_id != OWNER_ID:
            return
        
        # Cek apakah ini reply
        if not event.is_reply:
            await event.reply(
                "<blockquote>✘ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴠᴏɪᴄᴇ/ᴀᴜᴅɪᴏ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ 'ᴠᴛᴛ'</blockquote>",
                parse_mode='html'
            )
            return
        
        processing_msg = None
        
        try:
            # Ambil pesan yang di-reply
            replied_msg = await event.get_reply_message()
            
            # Cek apakah itu voice/audio
            if not is_voice_or_audio(replied_msg):
                await event.reply(
                    "<blockquote>✘ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪs ɴᴏᴛ ᴀ ᴠᴏɪᴄᴇ ᴏʀ ᴀᴜᴅɪᴏ ғɪʟᴇ</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Kirim status processing
            processing_msg = await event.reply(
                "<blockquote>⛧ ᴄᴏɴᴠᴇʀᴛɪɴɢ ᴠᴏɪᴄᴇ ᴛᴏ ᴛᴇxᴛ...\n✘ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</blockquote>",
                parse_mode='html'
            )
            
            # Buat temporary directory
            temp_dir = tempfile.mkdtemp(dir='/data/data/com.termux/files/usr/tmp')
            
            # Download audio
            audio_path = os.path.join(temp_dir, 'audio.ogg')
            await event.client.download_media(replied_msg, audio_path)
            
            # Convert to FLAC
            flac_path = os.path.join(temp_dir, 'audio.flac')
            converted_path = convert_audio_to_flac(audio_path, flac_path)
            
            # Convert speech to text with auto language detection
            text, detected_lang = recognize_speech_multilingual(converted_path)
            
            # Cleanup temporary files
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                if os.path.exists(converted_path):
                    os.remove(converted_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
            
            if not text:
                await processing_msg.edit(
                    "<blockquote>✘ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴜɴᴅᴇʀsᴛᴀɴᴅ ᴛʜᴇ ᴀᴜᴅɪᴏ\n⛧ ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜᴇ ᴀᴜᴅɪᴏ ɪs ᴄʟᴇᴀʀ</blockquote>",
                    parse_mode='html'
                )
                return
            
            # Get sender info
            sender = await replied_msg.get_sender()
            user_name = "Unknown"
            if sender:
                first_name = getattr(sender, 'first_name', '') or ''
                last_name = getattr(sender, 'last_name', '') or ''
                user_name = f"{first_name} {last_name}".strip()
                if not user_name:
                    user_name = getattr(sender, 'username', 'Unknown')
            
            # Format hasil dengan HTML quote block
            result = (
                f"<blockquote>✞ <b>ᴠᴏɪᴄᴇ ᴛᴏ ᴛᴇxᴛ</b>\n"
                f"⛧ ғʀᴏᴍ: {user_name}\n"
                f"✓ ʟᴀɴɢ: {detected_lang}\n\n"
                f"✘ ᴛʀᴀɴsᴄʀɪᴘᴛɪᴏɴ:\n<b>{text}</b></blockquote>"
            )
            
            await processing_msg.edit(result, parse_mode='html')
            
            # Hapus pesan "vtt" user
            try:
                await event.delete()
            except:
                pass
            
        except Exception as e:
            error_msg = f"<blockquote>✘ ᴇʀʀᴏʀ: {str(e)[:150]}</blockquote>"
            if processing_msg:
                try:
                    await processing_msg.edit(error_msg, parse_mode='html')
                except:
                    await event.reply(error_msg, parse_mode='html')
            else:
                await event.reply(error_msg, parse_mode='html')
    
    # ========== VTT INFO COMMAND ==========
    @user.on(events.NewMessage(pattern=r'^\.vttinfo$'))
    async def vtt_info_handler(event):
        """Show vtt info"""
        if event.sender_id != OWNER_ID:
            return
        
        # Check if ffmpeg is available
        try:
            ffmpeg_result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            ffmpeg_ok = ffmpeg_result.returncode == 0
        except:
            ffmpeg_ok = False
        
        info_text = (
            f"<blockquote>⛧ <b>ᴠᴏɪᴄᴇ ᴛᴏ ᴛᴇxᴛ ɪɴғᴏ</b>\n\n"
            f"✘ <b>ᴍᴏᴅᴇ:</b> ᴀᴜᴛᴏ-ᴅᴇᴛᴇᴄᴛ 🌐\n"
            f"✞ <b>sᴜᴘᴘᴏʀᴛᴇᴅ ʟᴀɴɢᴜᴀɢᴇs:</b>\n"
            f"  • English 🇺🇸\n"
            f"  • Bahasa Indonesia 🇮🇩\n"
            f"  • Japanese 🇯🇵\n"
            f"  • Korean 🇰🇷\n"
            f"  • Arabic 🇸🇦\n\n"
            f"✓ <b>ᴅᴇᴘᴇɴᴅᴇɴᴄɪᴇs:</b>\n"
            f"  • FFmpeg: {'✓ Available' if ffmpeg_ok else '✘ Not Found'}\n"
            f"  • SpeechRecognition: ✓ Available\n\n"
            f"✘ <b>ᴜsᴀɢᴇ:</b> Reply to voice/audio with <code>vtt</code>\n"
            f"⛧ <b>ɴᴏᴛᴇ:</b> ᴛʜᴇ sʏsᴛᴇᴍ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇᴛᴇᴄᴛ ᴛʜᴇ ʟᴀɴɢᴜᴀɢᴇ!</blockquote>"
        )
        
        await event.reply(info_text, parse_mode='html')