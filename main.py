import telebot
import yt_dlp
import os
import random
from telebot import types
from flask import Flask, request, jsonify, render_template
from threading import Thread

# --- 1. إعداد السيرفر (Flask Web App) ---
# template_folder='templates' بيعرفه مكان ملف الـ HTML
app = Flask('', template_folder='templates')

@app.route('/')
def home():
    # دي الصفحة اللي هتفتح لما تدوس على الزرار
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def receive_link():
    data = request.json
    url = data.get('url')
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'status': 'error', 'msg': 'User ID missing'})

    # فحص الصيانة قبل ما يبدأ
    if ("youtube.com" in url or "youtu.be" in url) and MAINTENANCE_STATUS['youtube']:
        return jsonify({'status': 'maintenance', 'msg': 'يوتيوب في الصيانة حالياً ⚠️'})

    # تشغيل التحميل في الخلفية (عشان الموقع ميهنجش)
    Thread(target=process_download, args=(user_id, url)).start()
    
    return jsonify({'status': 'ok'})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعدادات البوت ---
BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
# 🔗 رابط موقعك على ريندر (اللي أنت بعته)
APP_URL = "https://kareem-video-bot.onrender.com"

MAINTENANCE_STATUS = {
    'youtube': True,
    'facebook': False,
    'instagram': False,
    'tiktok': False
}

if not BOT_TOKEN:
    print("Error: TOKEN is missing.")

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"
channel_file = "force_sub.txt"

BLOCKED_KEYWORDS = [
    "xnxx", "pornhub", "xvideos", "sex", "xxx", "nude", "pussy", 
    "dick", "cock", "boobs", "hentai", "milf", "sharmota", "neek", 
    "nik", "sks", "film sex", "سكس", "نيك", "اباحي", "شرموطة", 
    "toz", "kuss"
]

SUCCESS_MSGS = [
    "🚀 عاش! الرابط وصل...",
    "📦 جاري تجهيز طلبك...",
    "🔥 ثواني ويكون عندك...",
    "😎 انت تؤمر.. جاري التحميل..."
]

# --- 3. دوال المعالجة والتحميل ---

def is_safe_content(text):
    text = text.lower()
    for word in BLOCKED_KEYWORDS:
        if word in text: return False
    return True

def save_and_notify_admin(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    username = message.from_user.username or "No User"
    
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    if user_id not in users:
        with open(users_file, "a") as f:
            f.write(user_id + "\n")
        if ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"🚀 **مستخدم جديد:**\n{first_name} (@{username})")
            except: pass

def check_sub(user_id):
    if not os.path.exists(channel_file): return True
    with open(channel_file, "r") as f: ch_user = f.read().strip()
    if not ch_user: return True
    try:
        member = bot.get_chat_member(ch_user, user_id)
        if member.status in ['creator', 'administrator', 'member']: return True
    except: return True
    return False

# 🔥 دالة التحميل الخلفية (بتشتغل لما الويب يبعت رابط)
def process_download(chat_id, url):
    if not is_safe_content(url):
        bot.send_message(chat_id, "🚫 **الرابط يحتوي على محتوى محظور!**")
        return

    # رسالة "جاري التحميل" في الشات
    msg = bot.send_message(chat_id, f"🔎 **وصلني الرابط:**\n{url}\n\n⏳ جاري المعالجة...")

    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'quiet': True,
            'max_filesize': 50*1024*1024,
            'nocheckcertificate': True,
            'format': 'best[ext=mp4]/best' # تحميل أفضل جودة متاحة تلقائياً
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            caption = f"✅ @kareemcv"

            # إرسال الملف
            with open(filename, 'rb') as f:
                # لو صورة
                if filename.lower().endswith(('.jpg', '.png', '.webp')):
                    bot.send_photo(chat_id, f, caption=caption)
                # لو فيديو
                else:
                    bot.send_video(chat_id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)
            bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ فشل التحميل: {str(e)}", chat_id=chat_id, message_id=msg.message_id)


# --- 4. أوامر البوت (والزرار السحري) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_and_notify_admin(message)
    
    welcome_text = (
        f"أهلاً بك يا {message.from_user.first_name}! 👋\n\n"
        "🚀 **لتحميل الفيديوهات بشكل أسرع وأشيك:**\n"
        "اضغط على الزر بالأسفل لفتح نافذة التحميل 👇"
    )

    # هنا بنعمل زرار الـ Web App اللي بيفتح الموقع بتاعك
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo(APP_URL) # ده رابط ريندر اللي حطيناه فوق
    
    # الزرار اللي زي "بدء اللعبة"
    markup.add(types.InlineKeyboardButton(text="📱 اضغط للتحميل (Web App)", web_app=web_app_info))
    
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


# استقبال الروابط العادية (للي لسه عايز يبعت في الشات)
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # نفس الكود القديم عشان لو حد بعت الرابط في الشات مباشرة يشتغل برضه
    if "http" in message.text:
        Thread(target=process_download, args=(message.chat.id, message.text)).start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
