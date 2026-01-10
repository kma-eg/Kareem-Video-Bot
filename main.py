import telebot
import yt_dlp
import os
from telebot import types
from flask import Flask
from threading import Thread

# ------------------- Web Server -------------------
app = Flask('')

@app.route('/')
def home():
    return "<b>Bot is running... 🚀</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------- Bot Configuration -------------------
BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN:
    print("Error: TOKEN is missing.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"

# ------------------- User Management -------------------
def save_user(user_id):
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(users_file, "a") as f:
            f.write(str(user_id) + "\n")

def get_users_count():
    if not os.path.exists(users_file): return 0
    with open(users_file, "r") as f:
        return len(f.read().splitlines())

# ------------------- Start Command -------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id)
    
    # Removed ** stars as requested
    welcome_text = (
        f"👋 أهلاً بك يا {message.from_user.first_name}! \n\n"
        "✨ أنا بوت التحميل الشامل (النسخة المطورة) 🤖\n\n"
        "🌟 مميزات البوت:\n"
        "✅ اختيار الجودة (144p - 360p - 720p)\n"
        "✅ تحميل صوت (MP3) بأعلى نقاء 🎵\n"
        "✅ دعم يوتيوب، فيسبوك، تيك توك، إنستجرام\n\n"
        "💡 كيف أعمل؟\n"
        "1️⃣ أرسل الرابط مباشرة لاختيار الجودة.\n"
        "2️⃣ أرسل اسم الفيديو للبحث عنه.\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "👨‍💻 المطور: @kareemcv"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))
    
    current_user = str(message.from_user.id).strip()
    admin_clean = str(ADMIN_ID).strip() if ADMIN_ID else ""

    if admin_clean and current_user == admin_clean:
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم (Admin)", callback_data="admin_home"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ------------------- Message Handler -------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    
    # If Link -> Show Thumbnail + Buttons
    if "http" in text:
        status_msg = bot.reply_to(message, "🔎 جاري جلب بيانات الفيديو...")
        
        try:
            ydl_opts = {'quiet': True, 'cookiefile': 'cookies.txt', 'ignoreerrors': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
                
            title = info.get('title', 'Video')
            thumbnail = info.get('thumbnail')
            
            # Create Quality Buttons
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_144 = types.InlineKeyboardButton("📱 144p", callback_data="q|144")
            btn_360 = types.InlineKeyboardButton("📺 360p", callback_data="q|360")
            btn_720 = types.InlineKeyboardButton("💿 720p", callback_data="q|720")
            btn_audio = types.InlineKeyboardButton("🎵 MP3", callback_data="q|audio")
            
            markup.add(btn_144, btn_360)
            markup.add(btn_720, btn_audio)
            
            # Send Photo with Buttons (Reply to original link)
            if thumbnail:
                bot.send_photo(message.chat.id, thumbnail, caption=f"🎬 {title}\n\n⬇️ اختر الجودة:", reply_to_message_id=message.message_id, reply_markup=markup)
            else:
                bot.reply_to(message, f"🎬 {title}\n\n⬇️ اختر الجودة:", reply_markup=markup)
            
            # Delete "Searching" message
            bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: لم أتمكن من جلب البيانات. \n{str(e)}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        
    # If Text -> Search
    else:
        msg = bot.reply_to(message, f"🔍 جاري البحث عن: {text}...")
        try:
            ydl_opts = {
                'quiet': True, 'default_search': 'ytsearch8', 'extract_flat': True, 'ignoreerrors': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    title = entry.get('title')
                    vid_id = entry.get('id')
                    if title and vid_id:
                        markup.add(types.InlineKeyboardButton(f"🎬 {title}", callback_data=f"sel|{vid_id}"))
                bot.edit_message_text(f"✅ نتائج البحث عن: {text}", chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ لم يتم العثور على نتائج.", chat_id=message.chat.id, message_id=msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

# ------------------- Callback Handler -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    # Selection from Search
    if data.startswith("sel|"):
        vid_id = data.split("|")[1]
        link = f"https://youtu.be/{vid_id}"
        # Trigger the link handler logic manually
        call.message.text = link
        handle_message(call.message)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    # Quality Selection
    elif data.startswith("q|"):
        quality = data.split("|")[1]
        try:
            # Important: Get the link from the message the PHOTO replied to
            if call.message.reply_to_message:
                original_link = call.message.reply_to_message.text
                start_download_quality(call.message, original_link, quality)
            else:
                bot.answer_callback_query(call.id, "❌ الرابط الأصلي مفقود.")
        except:
            bot.answer_callback_query(call.id, "❌ حدث خطأ، حاول مجدداً.")

    # Admin Logic
    elif data == "admin_home":
        if str(call.from_user.id).strip() == str(ADMIN_ID).strip():
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton(f"👥 المشتركين: {get_users_count()}", callback_data="stats"),
                       types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"))
            markup.add(types.InlineKeyboardButton("❌ إغلاق", callback_data="close_admin"))
            bot.edit_message_caption("👮‍♂️ لوحة التحكم:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
             bot.answer_callback_query(call.id, "⛔ أنت لست المدير!", show_alert=True)

    elif data == "close_admin":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif data == "stats":
        bot.answer_callback_query(call.id, f"عدد المشتركين: {get_users_count()}", show_alert=True)
    elif data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل الرسالة للإذاعة الآن:")
        bot.register_next_step_handler(msg, broadcast_msg)

# ------------------- Download Logic -------------------
def start_download_quality(message, link, quality):
    bot.edit_message_caption(caption=f"⏳ جاري التحميل ({quality})...", chat_id=message.chat.id, message_id=message.message_id)
    
    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt', 
            'quiet': True,
            'max_filesize': 50*1024*1024
        }

        if quality == "audio":
            ydl_opts['format'] = 'bestaudio/best'
        elif quality == "144":
            ydl_opts['format'] = 'bestvideo[height<=144]+bestaudio/best[height<=144]'
        elif quality == "360":
            ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
        elif quality == "720":
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        else:
             ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown')
            caption = f"🎬 {title}\n💿 الجودة: {quality}\n\n👤 By: @kareemcv"

            with open(filename, 'rb') as f:
                if quality == "audio": 
                    bot.send_audio(message.chat.id, f, caption=caption)
                else: 
                    bot.send_video(message.chat.id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        err_msg = str(e)
        if "File is larger than" in err_msg:
             bot.send_message(message.chat.id, "❌ الملف أكبر من 50 ميجا! حاول اختيار جودة أقل.")
        else:
             bot.send_message(message.chat.id, "❌ فشل التحميل.")

# ------------------- Broadcast Logic -------------------
def broadcast_msg(message):
    if not os.path.exists(users_file): return
    with open(users_file, "r") as f: users = f.read().splitlines()
    count = 0
    loading = bot.reply_to(message, "🚀 جاري الإرسال...")
    for uid in users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except: pass
    bot.edit_message_text(f"✅ تمت الإذاعة لـ {count} مشترك.", chat_id=message.chat.id, message_id=loading.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
