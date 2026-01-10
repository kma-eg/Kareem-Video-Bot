import telebot
import yt_dlp
import os
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "<b>Bot is running successfully!</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

BOT_TOKEN = os.environ.get('TOKEN')
OWNER_ID = os.environ.get('OWNER_ID')

if not BOT_TOKEN:
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id)
    
    welcome_text = (
        f"❤️ أهلاً بك {message.from_user.first_name}! 👋\n\n"
        "🤖 **أنا بوت التحميل الشامل**\n"
        "أقدر أساعدك تحمل فيديوهات من أغلب\n"
        "المنصات بجودة عالية:\n\n"
        "✅ يوتيوب (Youtube)\n"
        "✅ تيك توك (TikTok) - بدون علامة مائية\n"
        "✅ إنستجرام (Reels & Posts)\n"
        "✅ فيسبوك (Facebook)\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "1️⃣ أرسل **الرابط** للتحميل المباشر 🚀\n"
        "2️⃣ أرسل **اسم الفيديو** للبحث عنه في\n"
        "يوتيوب 🔍\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "👨‍💻 **تطوير وبرمجة:**\n"
        "🌟 المطور : (كريم محمد)\n"
        "للتواصل : (@kareemcv)"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))
    
    if OWNER_ID and str(message.from_user.id) == str(OWNER_ID):
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم (Admin)", callback_data="admin_home"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_home")
def admin_panel_callback(call):
    if str(call.from_user.id) != str(OWNER_ID):
        bot.answer_callback_query(call.id, "⛔ هذا الزر للمطور فقط!")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(f"👥 المشتركين: {get_users_count()}", callback_data="stats")
    btn2 = types.InlineKeyboardButton("📢 إذاعة للكل", callback_data="broadcast")
    btn_close = types.InlineKeyboardButton("❌ إغلاق", callback_data="close_admin")
    markup.add(btn1, btn2)
    markup.add(btn_close)
    
    bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption="👮‍♂️ **لوحة التحكم الخاصة بك:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "close_admin")
def close_admin(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    
    if "http" in text:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_vid = types.InlineKeyboardButton("🎥 فيديو", callback_data="direct|vid")
        btn_aud = types.InlineKeyboardButton("🎵 صوت", callback_data="direct|aud")
        markup.add(btn_vid, btn_aud)
        bot.reply_to(message, "⬇️ **تم استلام الرابط.. اختر الصيغة:**", reply_markup=markup)
        
    else:
        msg = bot.reply_to(message, f"🔍 **جاري البحث عن: {text}...**")
        try:
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
            bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    if data.startswith("sel|"):
        vid_id = data.split("|")[1]
        link = f"https://youtu.be/{vid_id}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🎥 تحميل فيديو", callback_data=f"dl|vid|{vid_id}"),
                   types.InlineKeyboardButton("🎵 تحميل صوت", callback_data=f"dl|aud|{vid_id}"))
        bot.edit_message_text(f"⬇️ **ماذا تريد أن تفعل بهذا الفيديو؟**\n🔗 {link}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data.startswith("dl|") or data.startswith("direct|"):
        try:
            if data.startswith("dl|"):
                _, type_dl, vid_id = data.split("|")
                link = f"https://youtu.be/{vid_id}"
            else:
                link = call.message.reply_to_message.text
                type_dl = data.split("|")[1]

            start_download(call.message, link, type_dl)
        except:
            bot.answer_callback_query(call.id, "❌ الرابط انتهى، أرسله مجدداً.")

    elif data == "stats":
        bot.answer_callback_query(call.id, f"عدد المشتركين: {get_users_count()}", show_alert=True)
    
    elif data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 **أرسل الرسالة (نص أو صورة) للإذاعة الآن:**")
        bot.register_next_step_handler(msg, broadcast_msg)

def start_download(message, link, type_dl):
    bot.edit_message_text("⏳ **جاري التحميل...**", chat_id=message.chat.id, message_id=message.message_id)
    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'max_filesize': 50*1024*1024
        }
        
        if type_dl == "aud": 
            ydl_opts['format'] = 'bestaudio/best'
        else: 
            ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown')
            caption = f"🎬 **{title}**\n\n👤 By: @kareemcv"

            with open(filename, 'rb') as f:
                if type_dl == "aud": bot.send_audio(message.chat.id, f, caption=caption)
                else: bot.send_video(message.chat.id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        bot.send_message(message.chat.id, "❌ فشل التحميل (تأكد أن الملف أقل من 50 ميجا).")

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
    bot.edit_message_text(f"✅ **تمت الإذاعة لـ {count} مشترك.**", chat_id=message.chat.id, message_id=loading.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
