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
    return "<b>Bot is running...</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------- Bot Setup -------------------
BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('OWNER_ID')

if not BOT_TOKEN:
    print("Error: Token not found")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"

# --- Functions ---
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

# ------------------- Start Command (الشكل القديم) -------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id)
    
    # النص المنسق القديم
    caption_text = (
        f"❤️ أهلاً بك {message.from_user.first_name}! 👋\n\n"
        "🤖 **أنا بوت التحميل الشامل**\n"
        "أقدر أساعدك تحمل فيديوهات من أغلب المنصات بجودة عالية:\n\n"
        "✅ يوتيوب (Youtube)\n"
        "✅ تيك توك (TikTok) - بدون علامة مائية\n"
        "✅ إنستجرام (Reels & Posts)\n"
        "✅ فيسبوك (Facebook)\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "1️⃣ أرسل **الرابط** للتحميل المباشر 🚀\n"
        "2️⃣ أرسل **اسم الفيديو** للبحث عنه في يوتيوب 🔍\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "👨‍💻 **تطوير وبرمجة:**\n"
        "🌟 المطور : (كريم محمد)\n"
        "للتواصل : (@kareemcv)"
    )

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption_text)
    except:
        bot.send_message(message.chat.id, caption_text)

# ------------------- Admin Panel -------------------
@bot.message_handler(commands=['admin', 'لوحة'])
def admin_panel(message):
    if not ADMIN_ID: return
    if str(message.from_user.id) == str(ADMIN_ID):
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(f"📊 المشتركين: {get_users_count()}", callback_data="stats")
        btn2 = types.InlineKeyboardButton("📢 إذاعة للكل", callback_data="broadcast")
        markup.add(btn1, btn2)
        bot.reply_to(message, "👮‍♂️ **لوحة التحكم:**", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔ هذا الأمر للمدير فقط.")

# ------------------- Search & Link Handler (التصليح هنا) -------------------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    
    # لو رابط
    if "http" in text:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_vid = types.InlineKeyboardButton("🎥 فيديو", callback_data=f"direct|vid")
        btn_aud = types.InlineKeyboardButton("🎵 صوت", callback_data=f"direct|aud")
        markup.add(btn_vid, btn_aud)
        bot.reply_to(message, "⬇️ **تم استلام الرابط.. اختر الصيغة:**", reply_markup=markup)
        
    # لو بحث
    else:
        msg = bot.reply_to(message, f"🔍 **جاري البحث عن: {text}...**")
        try:
            # هنا التعديل: ضفنا ملف الكوكيز للبحث
            ydl_opts = {
                'quiet': True,
                'default_search': 'ytsearch10',
                'extract_flat': True,
                'cookiefile': 'cookies.txt',  # <-- دي اللي كانت ناقصة
                'ignoreerrors': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    title = entry.get('title')
                    vid_id = entry.get('id')
                    # نتأكد إن النتيجة سليمة وليها عنوان
                    if title and vid_id:
                        btn = types.InlineKeyboardButton(f"🎬 {title}", callback_data=f"sel|{vid_id}")
                        markup.add(btn)
                
                bot.edit_message_text(f"✅ **نتائج البحث عن: {text}**", chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ لم يتم العثور على نتائج (تأكد من الكوكيز).", chat_id=message.chat.id, message_id=msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

# ------------------- Callback Handler -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    if data.startswith("sel|"):
        vid_id = data.split("|")[1]
        link = f"https://youtu.be/{vid_id}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_vid = types.InlineKeyboardButton("🎥 تحميل فيديو", callback_data=f"dl|vid|{vid_id}")
        btn_aud = types.InlineKeyboardButton("🎵 تحميل صوت", callback_data=f"dl|aud|{vid_id}")
        markup.add(btn_vid, btn_aud)
        bot.edit_message_text(f"⬇️ **ماذا تريد أن تفعل بهذا الفيديو؟**\n🔗 {link}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data.startswith("dl|"):
        _, type_dl, vid_id = data.split("|")
        link = f"https://youtu.be/{vid_id}"
        start_download(call.message, link, type_dl)

    elif data.startswith("direct|"):
        try:
            link = call.message.reply_to_message.text
            type_dl = data.split("|")[1]
            start_download(call.message, link, type_dl)
        except:
            bot.answer_callback_query(call.id, "❌ الرابط غير متاح.")

    elif data == "stats":
        bot.answer_callback_query(call.id, f"المشتركين: {get_users_count()}")
    elif data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل رسالة الإذاعة:")
        bot.register_next_step_handler(msg, send_broadcast)

# ------------------- Download Function -------------------
def start_download(message, link, type_dl):
    bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="⏳ **جاري التحميل...**")
    try:
        ydl_opts = {'outtmpl': 'media/%(title)s.%(ext)s', 'cookiefile': 'cookies.txt', 'quiet': True}
        if type_dl == "aud": ydl_opts['format'] = 'bestaudio/best'
        else: ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown')
            caption = f"🎬 **{title}**\n\n👤 By: Kareem Mohamed\n🤖 @kma_tbot"

            with open(filename, 'rb') as f:
                if type_dl == "aud": bot.send_audio(message.chat.id, f, caption=caption)
                else: bot.send_video(message.chat.id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ (تأكد من الحجم < 50MB).")

def send_broadcast(message):
    if not os.path.exists(users_file): return
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    count = 0
    for user_id in users:
        try:
            bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except: pass
    bot.reply_to(message, f"✅ تم للإذاعة لـ {count} عضو.")

keep_alive()
bot.infinity_polling()
