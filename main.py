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

# ------------------- Bot Setup -------------------
BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN:
    print("Error: TOKEN is missing.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"

# ------------------- Functions -------------------
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
        f"👋 أهلاً بك يا {message.from_user.first_name}! \n\n"
        "🤖 **أنا بوت التحميل الشامل**\n"
        "✅ يوتيوب - فيسبوك - تيك توك - إنستجرام\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "1️⃣ أرسل **الرابط** وسيظهر لك زر التحميل فوراً.\n"
        "2️⃣ أرسل **اسم الفيديو** للبحث عنه.\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "🤖 **بوت:** @kma_tbot\n"
        "👨‍💻 **المطور:** @kareemcv"
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
    
    # --- Link Handler ---
    if "http" in text:
        status_msg = bot.reply_to(message, "🔎 جاري جلب الفيديو...")
        
        try:
            # تمويه المتصفح
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
            
            if not info:
                bot.edit_message_text("❌ الرابط غير صالح أو محظور.", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
                return

            title = info.get('title', 'فيديو')
            thumbnail = info.get('thumbnail')
            
            # أزرار مبسطة لضمان العمل على Render
            markup = types.InlineKeyboardMarkup(row_width=2)
            # زر "تحميل فيديو" ده بيجيب ملف واحد جاهز (صوت وصورة) عشان ميفشلش
            markup.add(types.InlineKeyboardButton("🎬 تحميل فيديو", callback_data="dl_video"))
            markup.add(types.InlineKeyboardButton("🎵 تحميل صوت", callback_data="dl_audio"))
            
            if thumbnail:
                bot.send_photo(message.chat.id, thumbnail, caption=f"🎬 {title}\n\n⬇️ اختر نوع التحميل:", reply_to_message_id=message.message_id, reply_markup=markup)
            else:
                bot.reply_to(message, f"🎬 {title}\n\n⬇️ اختر نوع التحميل:", reply_markup=markup)
            
            bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        
    # --- Search Handler ---
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
    
    # اختيار من البحث
    if data.startswith("sel|"):
        vid_id = data.split("|")[1]
        link = f"https://youtu.be/{vid_id}"
        # نبعت الرابط عشان يتعامل معاه كأنه لينك جديد
        call.message.text = link
        handle_message(call.message)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    # بدء التحميل (فيديو أو صوت)
    elif data == "dl_video" or data == "dl_audio":
        try:
            if call.message.reply_to_message:
                original_link = call.message.reply_to_message.text
                start_download_final(call.message, original_link, data)
            else:
                bot.answer_callback_query(call.id, "❌ الرابط الأصلي مفقود.")
        except:
            bot.answer_callback_query(call.id, "❌ حدث خطأ.")

    # لوحة التحكم
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

# ------------------- Download Logic (بدون FFmpeg) -------------------
def start_download_final(message, link, type):
    bot.edit_message_caption(caption="⏳ جاري التحميل... يرجى الانتظار", chat_id=message.chat.id, message_id=message.message_id)
    
    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'quiet': True,
            'max_filesize': 50*1024*1024,
            'nocheckcertificate': True
        }

        if type == "dl_audio":
            ydl_opts['format'] = 'bestaudio/best'
        else:
            # هنا التعديل السحري: بنقوله هات أفضل ملف MP4 جاهز (فيه صوت وصورة)
            # عشان منتطرش نعمل دمج ويفشل التحميل
            ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown')
            # تم تعديل التوقيع لاسم البوت
            caption = f"🎬 {title}\n\n🤖 Bot: @kma_tbot\n👨‍💻 Dev: @kareemcv"

            with open(filename, 'rb') as f:
                if type == "dl_audio": 
                    bot.send_audio(message.chat.id, f, caption=caption)
                else: 
                    bot.send_video(message.chat.id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل التحميل.\nالسبب: السيرفر لا يدعم هذا الفيديو حالياً.")

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
