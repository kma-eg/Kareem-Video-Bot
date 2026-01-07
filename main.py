import telebot
import os
import yt_dlp
from keep_alive import keep_alive

TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not TOKEN or not ADMIN_ID:
    print("Error: TOKEN or ADMIN_ID not found in Environment Variables!")

bot = telebot.TeleBot(TOKEN)
MAX_SIZE = 50 * 1024 * 1024
USERS_FILE = "users.txt"

def save_user(chat_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    
    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(chat_id) not in users:
            f.write(f"{chat_id}\n")

def get_all_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return f.read().splitlines()

def human_readable(num):
    if num is None: return "0"
    num = float(num)
    if num < 1000: return str(int(num))
    if num < 1000000: return f"{num/1000:.1f}K"
    return f"{num/1000000:.1f}M"

keep_alive()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    
    user_name = message.from_user.first_name
    if not user_name and message.from_user.username:
        user_name = f"@{message.from_user.username}"
    if not user_name:
         user_name = "يا صديقي"

    welcome_text = (
        f"👋 **أهلاً بك {user_name}!** ❤️\n\n"
        "🤖 **أنا بوت التحميل الشامل**\n"
        "أقدر أساعدك تحمل فيديوهات من أغلب المنصات بجودة عالية:\n\n"
        "✅ يوتيوب (Youtube)\n"
        "✅ تيك توك (TikTok) - بدون علامة مائية\n"
        "✅ إنستجرام (Reels & Posts)\n"
        "✅ فيسبوك (Facebook)\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "فقط أرسل لي الرابط وسأبدأ التحميل فوراً! 🚀\n\n"
        "〰〰〰〰〰〰〰〰\n"
        "👨‍💻 **تطوير وبرمجة:**\n"
        "🌟 **المطور : (كريم محمد)**\n"
        "للتواصل : (@kareemcv)\n"
        "〰〰〰〰〰〰〰〰"
    )
    
    try:
        with open('start_image.jpg', 'rb') as photo:
             bot.send_photo(message.chat.id, photo, caption=welcome_text, parse_mode='Markdown')
    except FileNotFoundError:
         bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['cast'])
def broadcast_message(message):
    if str(message.chat.id) != str(ADMIN_ID):
        bot.reply_to(message, "⛔ هذا الأمر للمطور فقط.")
        return

    msg_text = message.text.replace("/cast", "").strip()
    if not msg_text:
        bot.reply_to(message, "⚠️ يرجى كتابة الرسالة بعد الأمر.\nمثال: `/cast تحديث جديد!`")
        return

    users = get_all_users()
    sent_count = 0
    fail_count = 0

    status_msg = bot.reply_to(message, f"⏳ جاري إرسال الإذاعة لـ {len(users)} مستخدم...")

    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 **إعلان هام من المطور:**\n\n{msg_text}", parse_mode='Markdown')
            sent_count += 1
        except Exception:
            fail_count += 1
            
    bot.edit_message_text(f"✅ **تمت الإذاعة بنجاح!**\n\nتم الإرسال لـ: {sent_count}\nفشل الإرسال لـ: {fail_count}", message.chat.id, status_msg.message_id, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
         bot.reply_to(message, "⚠️ يرجى إرسال رابط صحيح يبدأ بـ http أو https")
         return

    status_msg = bot.reply_to(message, "⏳ **جاري الفحص والتجهيز...**", parse_mode='Markdown')
    filename = None

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'video_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'max_filesize': MAX_SIZE,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                raise Exception(f"فشل في استخراج معلومات الرابط: {str(e)}")

            fsize = info.get('filesize') or info.get('filesize_approx')
            if fsize and fsize > MAX_SIZE:
                bot.edit_message_text(f"❌ **عذراً، الفيديو كبير جداً!**\n\nحجم الفيديو يتخطى 50 ميجا.\nالحجم المقدر: {round(fsize/(1024*1024), 2)} MB", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                return
            
            title = info.get('title', 'فيديو بدون عنوان')
            uploader = info.get('uploader', 'غير معروف')
            views = human_readable(info.get('view_count'))
            likes = human_readable(info.get('like_count'))

            caption_text = (
                f"✅ {views} views · {likes} reactions | {title} | {uploader}\n"
                f"👤 **By : Kareem Mohamed**\n"
                f"🤖 @{bot.get_me().username}"
            )
            
            bot.edit_message_text(f"⬇️ **جاري التحميل للسيرفر:**\n{title}", message.chat.id, status_msg.message_id)
            
            ydl.download([url])
            filename = ydl.prepare_filename(info)

        bot.edit_message_text("🚀 **جاري الرفع إليك...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        if os.path.getsize(filename) > MAX_SIZE:
             bot.edit_message_text("❌ **خطأ غير متوقع:** الملف المحمل أكبر من 50 ميجا بعد التحميل.", message.chat.id, status_msg.message_id)
             os.remove(filename)
             return

        with open(filename, 'rb') as video:
            bot.send_video(
                message.chat.id, 
                video, 
                caption=caption_text,
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

        if os.path.exists(filename):
            os.remove(filename)
        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        error_message = str(e)
        bot.edit_message_text("❌ **حدث خطأ أثناء المحاولة!**\n\n- قد يكون الرابط غير مدعوم.\n- أو الفيديو خاص/محذوف.\n- أو حدثت مشكلة في السيرفر.\n\n**تم إبلاغ المطور بالمشكلة.**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        if filename and os.path.exists(filename):
            os.remove(filename)

        if ADMIN_ID and str(ADMIN_ID) == "6318333901":
            try:
                bot.send_message(ADMIN_ID, f"⚠️ **تقرير خطأ جديد!**\n\n👤 المستخدم: {message.from_user.first_name} (ID: {message.chat.id})\n🔗 الرابط: {url}\n\n📄 الخطأ:\n`{error_message}`", parse_mode='Markdown')
            except:
                print("Failed to send error report to admin")

print("Bot is running on Render...")
bot.infinity_polling()

