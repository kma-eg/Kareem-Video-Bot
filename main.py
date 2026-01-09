import telebot
import yt_dlp
import os
from telebot import types

# ------------------- Bot Configuration -------------------
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.environ.get('OWNER_ID')) 

bot = telebot.TeleBot(BOT_TOKEN)

users_file = "users.txt"

# --- Function: Save User ID ---
def save_user(user_id):
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(users_file, "a") as f:
            f.write(str(user_id) + "\n")

# --- Function: Get User Count ---
def get_users_count():
    if not os.path.exists(users_file): return 0
    with open(users_file, "r") as f:
        return len(f.read().splitlines())

# ------------------- 1. Admin Panel (لوحة الأدمن) -------------------
@bot.message_handler(commands=['admin', 'لوحة'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        # Buttons in Arabic
        btn1 = types.InlineKeyboardButton(f"📊 المشتركين: {get_users_count()}", callback_data="stats")
        btn2 = types.InlineKeyboardButton("📢 إذاعة للكل", callback_data="broadcast")
        markup.add(btn1, btn2)
        bot.reply_to(message, "👮‍♂️ **أهلاً بك في لوحة التحكم يا مدير!**", reply_markup=markup, parse_mode="Markdown")
    else:
        # Message for non-admins
        bot.reply_to(message, "⛔ هذا الأمر للمدير فقط.")

# ------------------- 2. Start Command (رسالة الترحيب) -------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id) 
    bot.reply_to(message, f"👋 أهلاً بك يا {message.from_user.first_name}!\n\n🚀 **أرسل رابط فيديو (يوتيوب، فيسبوك، انستا) للتحميل.**")

# ------------------- 3. Link Handler (استقبال الروابط) -------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "http" in url:
        markup = types.InlineKeyboardMarkup(row_width=2)
        # Download Buttons in Arabic
        btn_vid = types.InlineKeyboardButton("🎥 فيديو", callback_data="vid") 
        btn_aud = types.InlineKeyboardButton("🎵 ملف صوتي", callback_data="aud")
        markup.add(btn_vid, btn_aud)
        
        bot.reply_to(message, "⬇️ **اختر صيغة التحميل:**", reply_markup=markup)
    else:
        bot.reply_to(message, "⚠️ من فضلك أرسل رابطاً صحيحاً.")

# ------------------- 4. Callback Buttons (الضغط على الأزرار) -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Show stats
    if call.data == "stats":
        bot.answer_callback_query(call.id, f"عدد الأعضاء الحالي: {get_users_count()}")
        
    # Start Broadcast
    elif call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 **أرسل الرسالة التي تريد إذاعتها للأعضاء الآن:**")
        bot.register_next_step_handler(msg, send_broadcast)

    # Handle Download (Video/Audio)
    elif call.data == "vid" or call.data == "aud":
        try:
            original_url = call.message.reply_to_message.text
            download_type = "video" if call.data == "vid" else "audio"
            
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="⏳ **جاري التحميل... انتظر قليلاً**")
            download_and_send(call.message.chat.id, original_url, download_type)
        except AttributeError:
            bot.send_message(call.message.chat.id, "❌ حدث خطأ: لا يمكن العثور على الرابط.")

# ------------------- Broadcast Logic (تنفيذ الإذاعة) -------------------
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
            pass 
    bot.reply_to(message, f"✅ **تمت الإذاعة لـ {count} عضو بنجاح!**")

# ------------------- Download Logic (كود التحميل) -------------------
def download_and_send(chat_id, url, type_dl):
    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt', 
            'quiet': True,
        }
        
        if type_dl == "audio":
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown')
            
            # Caption with your Rights
            caption = f"🎥 **{title}**\n\n👤 By: Kareem Mohamed\n🤖 @kma_tbot"

            with open(filename, 'rb') as f:
                if type_dl == "audio":
                    bot.send_audio(chat_id, f, caption=caption)
                else:
                    bot.send_video(chat_id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename):
                os.remove(filename) 
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}\n\n(تأكد أن الملف أقل من 50 ميجا)")

bot.infinity_polling()
