import random
import time
import firebase_admin
from firebase_admin import credentials, firestore
from telethon import events, Button
from telethon.tl.types import MessageEntityMention
import asyncio
import os
from config import OWNER_ID

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Collections
QUESTIONS_COLLECTION = "family100_questions"
SCORES_COLLECTION = "family100_scores"
ACTIVE_GAMES_COLLECTION = "active_games"

# Game state per chat
active_games = {}

def get_prefix():
    """Get current prefix from config"""
    try:
        import json
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except:
        return '.'

def setup(bot, user):
    
    # ========== FAMILY100 COMMAND ==========
    @user.on(events.NewMessage(pattern='/family100'))
    async def family100_handler(event):
        """Start a new Family100 game"""
        chat_id = event.chat_id
        user_id = event.sender_id
        username = event.sender.username or str(user_id)
        
        # Check if game already active in this chat
        if chat_id in active_games:
            await event.reply("⚠️ Masih ada game yang berlangsung di chat ini!")
            return
        
        # Get random question from Firebase
        questions_ref = db.collection(QUESTIONS_COLLECTION)
        questions = questions_ref.stream()
        
        questions_list = []
        for doc in questions:
            questions_list.append(doc.to_dict())
        
        if not questions_list:
            await event.reply("❌ Tidak ada soal tersedia. Gunakan /add untuk menambah soal baru.")
            return
        
        # Select random question
        question_data = random.choice(questions_list)
        question_id = question_data.get('id', '')
        
        # Initialize game state
        game_state = {
            'question_id': question_id,
            'question': question_data['question'],
            'answers': question_data['answers'],
            'answered': [False, False, False, False],
            'answered_by': ['', '', '', ''],
            'answered_users': set(),
            'hint_used': False,
            'start_time': time.time(),
            'creator_id': user_id,
            'creator_username': username
        }
        
        active_games[chat_id] = game_state
        
        # Format question display
        display_text = f"**{question_data['question']}**\n\n"
        for i in range(4):
            if game_state['answered'][i]:
                answer = game_state['answers'][i]
                user_link = game_state['answered_by'][i]
                display_text += f"{i+1}. {answer} (+10) {user_link}\n"
            else:
                display_text += f"{i+1}. ______\n"
        
        display_text += "\n➡️ Jawab dengan mengirim teks biasa"
        display_text += "\n💡 Gunakan /hint untuk bantuan"
        display_text += "\n📊 Gunakan /score untuk cek poin"
        
        await event.reply(display_text, parse_mode='markdown')
        
        # Save to Firebase for persistence
        game_ref = db.collection(ACTIVE_GAMES_COLLECTION).document(str(chat_id))
        game_ref.set({
            'question_id': question_id,
            'question': question_data['question'],
            'answers': question_data['answers'],
            'answered': [False, False, False, False],
            'answered_by': ['', '', '', ''],
            'answered_users': [],
            'hint_used': False,
            'start_time': time.time(),
            'creator_id': user_id,
            'creator_username': username
        })
    
    # ========== HINT COMMAND ==========
    @user.on(events.NewMessage(pattern='/hint'))
    async def hint_handler(event):
        """Show hint for current game"""
        chat_id = event.chat_id
        
        if chat_id not in active_games:
            await event.reply("❌ Tidak ada game yang aktif!")
            return
        
        game_state = active_games[chat_id]
        
        if game_state['hint_used']:
            await event.reply("⚠️ Hint sudah digunakan untuk soal ini!")
            return
        
        # Find first unanswered question
        for i, answered in enumerate(game_state['answered']):
            if not answered:
                answer = game_state['answers'][i]
                # Show first letter or length
                hint_type = random.choice(['first_letter', 'length'])
                
                if hint_type == 'first_letter':
                    hint_text = f"💡 Jawaban ke-{i+1} dimulai dengan huruf: **{answer[0].upper()}**"
                else:
                    hint_text = f"💡 Jawaban ke-{i+1} memiliki **{len(answer)}** huruf"
                
                game_state['hint_used'] = True
                
                # Update Firebase
                game_ref = db.collection(ACTIVE_GAMES_COLLECTION).document(str(chat_id))
                game_ref.update({'hint_used': True})
                
                await event.reply(hint_text, parse_mode='markdown')
                return
        
        await event.reply("🎉 Semua jawaban sudah ditemukan!")
    
    # ========== SCORE COMMAND ==========
    @user.on(events.NewMessage(pattern='/score'))
    async def score_handler(event):
        """Show user score"""
        user_id = event.sender_id
        username = event.sender.username or str(user_id)
        
        # Get score from Firebase
        score_ref = db.collection(SCORES_COLLECTION).document(str(user_id))
        score_doc = score_ref.get()
        
        if score_doc.exists:
            score_data = score_doc.to_dict()
            current_score = score_data.get('score', 0)
        else:
            current_score = 0
            # Initialize user score
            score_ref.set({
                'user_id': user_id,
                'username': username,
                'score': 0
            })
        
        await event.reply(f"🏆 **Score kamu: {current_score}**\n\nTotal poin yang berhasil dikumpulkan!", parse_mode='markdown')
    
    # ========== ADD COMMAND ==========
    @user.on(events.NewMessage(pattern='/add'))
    async def add_handler(event):
        """Show button to admin website"""
        # Create button with link to admin website
        # Replace with your actual Vercel URL
        vercel_url = "https://your-family100-admin.vercel.app"
        
        buttons = [
            [Button.url("➕ Tambah Soal Baru", vercel_url)],
            [Button.url("📝 Edit/Hapus Soal", vercel_url)]
        ]
        
        await event.reply(
            "🔧 **Admin Panel Family100**\n\n"
            "Klik tombol di bawah untuk menambah atau mengedit soal:\n\n"
            "Password: `alfread`",
            buttons=buttons,
            parse_mode='markdown'
        )
    
    # ========== ANSWER HANDLER ==========
    @user.on(events.NewMessage())
    async def answer_handler(event):
        """Handle user answers"""
        # Skip if it's a command
        message_text = event.raw_text.strip()
        if message_text.startswith('/'):
            return
        
        chat_id = event.chat_id
        user_id = event.sender_id
        username = event.sender.username
        
        if chat_id not in active_games:
            return
        
        game_state = active_games[chat_id]
        
        # Check if user already answered in this game
        if user_id in game_state['answered_users']:
            await event.reply("⚠️ Kamu sudah menjawab di game ini!")
            return
        
        user_answer = message_text.lower().strip()
        
        # Check answer
        for i, correct_answer in enumerate(game_state['answers']):
            if game_state['answered'][i]:
                continue
            
            if user_answer == correct_answer.lower():
                # Correct answer!
                game_state['answered'][i] = True
                game_state['answered_users'].add(user_id)
                
                # Create user mention link
                if username:
                    user_link = f"[@{username}](tg://user?id={user_id})"
                else:
                    user_link = f"[User](tg://user?id={user_id})"
                
                game_state['answered_by'][i] = user_link
                
                # Update score in Firebase
                score_ref = db.collection(SCORES_COLLECTION).document(str(user_id))
                score_doc = score_ref.get()
                
                if score_doc.exists:
                    current_score = score_doc.to_dict().get('score', 0)
                    score_ref.update({'score': current_score + 10})
                else:
                    score_ref.set({
                        'user_id': user_id,
                        'username': username or str(user_id),
                        'score': 10
                    })
                
                # Update Firebase game state
                game_ref = db.collection(ACTIVE_GAMES_COLLECTION).document(str(chat_id))
                game_ref.update({
                    f'answered.{i}': True,
                    f'answered_by.{i}': user_link,
                    'answered_users': list(game_state['answered_users'])
                })
                
                # Format updated display
                display_text = f"**{game_state['question']}**\n\n"
                all_answered = True
                
                for j in range(4):
                    if game_state['answered'][j]:
                        answer = game_state['answers'][j]
                        user_link_display = game_state['answered_by'][j]
                        display_text += f"{j+1}. {answer} (+10) {user_link_display}\n"
                    else:
                        display_text += f"{j+1}. ______\n"
                        all_answered = False
                
                if all_answered:
                    display_text += "\n🎉 **Semua jawaban berhasil ditebak!**"
                    
                    # Remove game from active
                    del active_games[chat_id]
                    game_ref = db.collection(ACTIVE_GAMES_COLLECTION).document(str(chat_id))
                    game_ref.delete()
                else:
                    display_text += f"\n✅ **@{username if username else 'User'}** menjawab dengan benar!"
                    display_text += "\n➡️ Lanjutkan menebak jawaban lainnya..."
                
                # Delete the answer message
                try:
                    await event.delete()
                except:
                    pass
                
                # Send updated question
                await event.respond(display_text, parse_mode='markdown')
                return
        
        # If answer is wrong
        await event.reply("❌ Jawaban salah! Coba lagi.")
    
    # ========== RESTORE ACTIVE GAMES ON STARTUP ==========
    async def restore_active_games():
        """Restore active games from Firebase on bot startup"""
        games_ref = db.collection(ACTIVE_GAMES_COLLECTION)
        games = games_ref.stream()
        
        for game_doc in games:
            game_data = game_doc.to_dict()
            chat_id = int(game_doc.id)
            
            # Convert answered_users list back to set
            answered_users_set = set(game_data.get('answered_users', []))
            
            active_games[chat_id] = {
                'question_id': game_data.get('question_id', ''),
                'question': game_data['question'],
                'answers': game_data['answers'],
                'answered': game_data['answered'],
                'answered_by': game_data['answered_by'],
                'answered_users': answered_users_set,
                'hint_used': game_data.get('hint_used', False),
                'start_time': game_data.get('start_time', time.time()),
                'creator_id': game_data.get('creator_id', 0),
                'creator_username': game_data.get('creator_username', '')
            }
        
        print(f"Restored {len(active_games)} active games from Firebase")
    
    # Call restore on setup
    asyncio.create_task(restore_active_games())
    
    # ========== ADMIN COMMANDS ==========
    @user.on(events.NewMessage())
    async def admin_commands(event):
        """Admin commands for managing questions"""
        if event.sender_id != OWNER_ID:
            return
        
        message_text = event.raw_text.strip()
        
        # List all questions
        if message_text == '/listquestions':
            questions_ref = db.collection(QUESTIONS_COLLECTION)
            questions = questions_ref.stream()
            
            response = "📋 **Daftar Soal Family100:**\n\n"
            count = 0
            
            for doc in questions:
                count += 1
                data = doc.to_dict()
                response += f"{count}. {data['question']}\n"
                for i, ans in enumerate(data['answers']):
                    response += f"   {i+1}. {ans}\n"
                response += f"   ID: `{doc.id}`\n\n"
            
            if count == 0:
                response = "❌ Tidak ada soal tersedia."
            
            await event.reply(response, parse_mode='markdown')
        
        # Delete question by ID
        elif message_text.startswith('/delquestion '):
            question_id = message_text.split(' ', 1)[1]
            
            try:
                db.collection(QUESTIONS_COLLECTION).document(question_id).delete()
                await event.reply(f"✅ Soal dengan ID `{question_id}` berhasil dihapus!", parse_mode='markdown')
            except Exception as e:
                await event.reply(f"❌ Gagal menghapus: {str(e)}")