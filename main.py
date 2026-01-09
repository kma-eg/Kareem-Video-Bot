import telebot
import yt_dlp
import os
from telebot import types

# ------------------- Bot Configuration -------------------
# Get variables from Environment
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# Ensure OWNER_ID is an integer
ADMIN_ID = int(os.environ.get('OWNER_ID')) 

bot = telebot.TeleBot(BOT_TOKEN)

# File to store user IDs for broadcasting
users_file = "users.txt"

# Function to save user ID
def save_user(user_id):
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(users_file, "a") as f:
            f.write(str(user_id) + "\n")

# Function to get total user count
def get_users_count():
    if not os.path.exists(users_file): return 0
    with open(users_file, "r") as f:
        return len(f.read().splitlines())

# ------------------- 1. Admin Panel Command -------------------
@bot.message_handler(commands=['admin', 'panel'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(f"📊 Users: {get_users_count()}", callback_data="stats")
        btn2 = types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")
        markup.add(btn1, btn2)
        bot.reply_to(message, "👮‍♂️ **Welcome to the Admin Panel!**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⛔ This command is for the Admin only.")

# ------------------- 2. Start Command -------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id) # Save user ID
    bot.reply_to(message, f"👋 Hello {message.from_user.first_name}!\n\n🚀 **Send a video link (YouTube, Facebook, Instagram) to download.**")

# ------------------- 3. Link Handler -------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "http" in url:
        # Create Inline Buttons
        markup = types.InlineKeyboardMarkup(row_width=2)
        # Shorten URL in callback_data to avoid limits
        btn_vid = types.InlineKeyboardButton("🎥 Video", callback_data=f"vid") 
        btn_aud = types.InlineKeyboardButton("🎵 Audio", callback_data=f"aud")
        markup.add(btn_vid, btn_aud)
        
        # Reply with buttons
        bot.reply_to(message, "⬇️ **Choose download format:**", reply_markup=markup)
    else:
        bot.reply_to(message, "⚠️ Please send a valid link.")

# ------------------- 4. Callback Query Handler -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "stats":
        bot.answer_callback_query(call.id, f"Total Users: {get_users_count()}")
        
    elif call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 **Send the message you want to broadcast now:**")
        bot.register_next_step_handler(msg, send_broadcast)

    elif call.data == "vid" or call.data == "aud":
        # Get the original link from the message the bot replied to
        try:
            original_url = call.message.reply_to_message.text
            download_type = "video" if call.data == "vid" else "audio"
            
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="⏳ **Processing... Please wait.**")
            download_and_send(call.message.chat.id, original_url, download_type)
        except AttributeError:
            bot.send_message(call.message.chat.id, "❌ Error: Could not find the original link.")

# ------------------- Broadcast Function -------------------
def send_broadcast(message):
    if not os.path.exists(users_file): return
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    
    count = 0
    for user_id in users:
        try:
            bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except:
            pass # User blocked the bot
    bot.reply_to(message, f"✅ **Broadcast sent to {count} users successfully!**")

# ------------------- Download & Send Function -------------------
def download_and_send(chat_id, url, type_dl):
    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt', # Important for YouTube
            'quiet': True,
        }
        
        if type_dl == "audio":
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'best[ext=mp4]/best' # Force MP4 for video

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown')
            
            # Caption with credits
            caption = f"🎥 **{title}**\n\n👤 By: Kareem Mohamed\n🤖 @YourBotName"

            with open(filename, 'rb') as f:
                if type_dl == "audio":
                    bot.send_audio(chat_id, f, caption=caption)
                else:
                    bot.send_video(chat_id, f, caption=caption, supports_streaming=True)
            
            # Remove file after sending to save space
            if os.path.exists(filename):
                os.remove(filename) 
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}\n\n(Note: File size must be under 50MB)")

# Start Polling
bot.infinity_polling()
