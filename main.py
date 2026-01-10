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
OWNER_ID = os.environ.get('OWNER_ID')

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

# ------------------- Start Command (القائمة + زر الأدمن الذكي) -------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id)
    
    caption_text = (
        f"❤️ أهلاً بك {message.from_user.first_name}! 👋\n\n"
        "🤖 **أنا بوت التحميل الشامل**\n"
        "أقدر أساعدك تحمل فيديوهات من أغلب المنصات:\n\n"
        "✅ يوتيوب - تيك توك - إنستجرام - فيسبوك\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "1️⃣ أرسل **الرابط** للتحميل المباشر 🚀\n"
        "2️⃣ أرسل **اسم الفيديو** للبحث عنه 🔍\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "👨‍💻 المطور: (كريم محمد)"
    )

    # إعداد الأزرار
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # 🌟 هنا السحر: لو أنت الأدمن، هيظهرلك زرار التحكم
    if str(message.from_user.id) == str(OWNER_ID):
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم (للأدمن فقط)", callback_data="admin_home"))
    
    # زرار قناة المطور (اختياري)
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/kareemcv"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, caption_text, reply_markup=markup)

# -------------------
