import telebot
import yt_dlp
import os
from telebot import types
from flask import Flask
from threading import Thread
import time

# ------------------- Web Server (عشان البوت ميفصلش) -------------------
app = Flask('')

@app.route('/')
def home():
    return "<b>Bot is running... 🚀</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------- Bot Setup -------------------
# قراءة التوكن والأيدي من إعدادات الموقع
BOT_TOKEN = os.environ.get('TOKEN')
OWNER_ID = os.environ.get('OWNER_ID')

# تأمين: لو البيانات ناقصة
if not BOT_TOKEN:
    print("❌ Error: TOKEN is missing.")
    # بنحط توكن وهمي عشان الكود ميضربش لو نسيته، بس مش هيشتغل
    BOT_TOKEN = "0000:dummy" 

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"

# --- دوال مساعدة ---
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
    
    welcome_text = (
        f"❤️ أهلاً بك {message.from_user.first_name}! 👋\n\n"
        "🤖 **أنا بوت التحميل الشامل**\n"
        "✅ يوتيوب - تيك توك - فيسبوك - إنستجرام\n\n"
        "💡 **كيف تعمل؟**\n"
        "1️⃣ أرسل **الرابط** للتحميل المباشر.\n"
        "2️⃣ أرسل **اسم الفيديو** للبحث عنه.\n\n"
        "👨‍💻 المطور: @kareemcv"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    # زر لوحة التحكم يظهر للمطور فقط
    if OWNER_ID and str(message.from_user.id) == str(OWNER_ID):
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم", callback_data="admin_home"))
    
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/kareemcv"))

    # محاولة إرسال الصورة لو موجودة
    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ------------------- Logic Handler (رابط ولا بحث؟) -------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    
    # 1. لو رابط (Link)
    if "http" in text:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_vid = types.InlineKeyboardButton("🎥 فيديو", callback_data="direct|vid")
        btn_aud = types.InlineKeyboardButton("🎵 صوت", callback_data="direct|aud")
        markup.add(btn_vid, btn_aud)
        bot.reply_to(message, "⬇️ **اختر صيغة التحميل:**", reply_markup=markup)
        
    # 2. لو بحث (Search)
    else:
        msg = bot.reply_to(message, f"🔍 **جاري البحث عن: {text}...**")
        try:
            # إعدادات البحث (بدون كوكيز عشان ميعملش خطأ)
            ydl_opts = {
                'quiet': True,
                'default_search': 'ytsearch8',
                'extract_flat': True,
                'ignoreerrors': True
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
                
                bot.edit_message_text(f"✅ **نتائج البحث عن: {text}**", chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ لم يتم العثور على نتائج.", chat_id=message.chat.id, message_id=msg.message_id)
        except Exception as e:
            bot.edit_message_text("❌ حدث خطأ في البحث.", chat_id=message.chat.id, message_id=msg.message_id)

# ------------------- Callback Handler (الأزرار) -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    # اختيار من البحث
    if data.startswith("sel|"):
        vid_id = data.split("|")[1]
        link = f"https://youtu.be/{vid_id}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🎥 فيديو", callback_data=f"dl|vid|{vid_id}"),
                   types.InlineKeyboardButton("🎵 صوت", callback_data=f"dl|aud|{vid_id}"))
        bot.edit_message_text(f"🔗 {link}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    # بدء التحميل
    elif data.startswith("dl|") or data.startswith("direct|"):
        try:
            if data.startswith("dl|"):
                _, type_dl, vid_id = data.split("|")
                link = f"https://youtu.be/{vid_id}"
            else: # direct link
                link = call.message.reply_to_message.text
                type_dl = data.split("|")[1]

            start_download(call.message, link, type_dl)
        except:
            bot.answer_callback_query(call.id, "❌ حدث خطأ، حاول مجدداً.")

    # لوحة التحكم
    elif data == "admin_home":
        if str(call.from_user.id) == str(OWNER_ID):
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton(f"👥 المشتركين: {get_users_count()}", callback_data="stats"),
                       types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"))
            bot.edit_message_caption("👮‍♂️ **لوحة التحكم:**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    
    elif data == "stats":
        bot.answer_callback_query(call.id, f"المشتركين: {get_users_count()}", show_alert=True)
    
    elif data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 **أرسل الرسالة للإذاعة الآن:**")
        bot.register_next_step_handler(msg, broadcast_msg)

# ------------------- Download Function -------------------
def start_download(message, link, type_dl):
    bot.edit_message_text("⏳ **جاري التحميل...**", chat_id=message.chat.id, message_id=message.message_id)
    try:
        # هنا بنستخدم الكوكيز للتحميل
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'max_filesize': 50*1024*1024
        }
        if type_dl == "aud": ydl_opts['format'] = 'bestaudio/best'
        else: ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            caption = f"🎬 **{info.get('title')}**\n👤 By: @kareemcv"

            with open(filename, 'rb') as f:
                if type_dl == "aud": bot.send_audio(message.chat.id, f, caption=caption)
                else: bot.send_video(message.chat.id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)
    except Exception as e:
        bot.send_message(message.chat.id, "❌ فشل التحميل (قد يكون الملف كبيراً).")

# ------------------- Broadcast Function -------------------
def broadcast_msg(message):
    if not os.path.exists(users_file): return
    with open(users_file, "r") as f: users = f.read().splitlines()
    count = 0
    for uid in users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except: pass
    bot.reply_to(message, f"✅ تم للإذاعة لـ {count}")

# تشغيل السيرفر والبوت
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
