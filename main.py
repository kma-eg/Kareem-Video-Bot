import telebot
import os
import yt_dlp
from keep_alive import keep_alive

TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not TOKEN or not ADMIN_ID:
    print("Error: TOKEN or ADMIN_ID not found in Environment Variables!")

bot = telebot.TeleBot(TOKEN)
MAX_SIZE = 50 * 1024 * 1024  # 50 MB Limit
USERS_FILE = "users.txt"

# --- دالة حفظ المستخدمين ---
def save_user(chat_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    
    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(chat_id) not in users:
            f.write(f"{chat_id}\n")
            return True # مستخدم جديد
    return False # مستخدم قديم

# --- دالة جلب عدد المستخدمين ---
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

# تشغيل سيرفر الإنعاش
keep_alive()

# --- أمر البداية (Start) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    is_new = save_user(message.chat.id)
    
    # 1. تجهيز اسم المستخدم
    user_name = message.from_user.first_name
    if not user_name:
         user_name = "يا صديقي"

    # 2. رسالة الترحيب
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
    
    # 3. إرسال الصورة والرسالة
    try:
        with open('start_image.jpg', 'rb') as photo:
             bot.send_photo(message.chat.id, photo, caption=welcome_text, parse_mode='Markdown')
    except FileNotFoundError:
         bot.reply_to(message, welcome_text, parse_mode='Markdown')

    # 4. تنبيه الأدمن بدخول عضو جديد (كما طلبت)
    if is_new and str(message.chat.id) != str(ADMIN_ID):
        try:
            users_count = len(get_all_users())
            username_txt = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
            
            alert_msg = (
                f"🚨 **تم دخول شخص جديد للبوت!**\n"
                f"----------------------------\n"
                f"• **معلومات العضو:**\n\n"
                f"• الاسم: {user_name}\n"
                f"• المعرف: {username_txt}\n"
                f"• الآيدي: `{message.chat.id}`\n"
                f"----------------------------\n"
                f"👥 **العدد الكلي للأعضاء: {users_count}**"
            )
            bot.send_message(ADMIN_ID, alert_msg, parse_mode='Markdown')
        except:
            pass # لو فشل الإرسال للأدمن ميعطلش البوت

# --- أمر الإذاعة (Broadcast) ---
@bot.message_handler(commands=['cast'])
def broadcast_message(message):
    if str(message.chat.id) != str(ADMIN_ID):
        return # تجاهل الأمر لو مش الأدمن

    msg_text = message.text.replace("/cast", "").strip()
    if not msg_text:
        bot.reply_to(message, "⚠️ اكتب الرسالة بعد الأمر.\nمثال: `/cast تحديث جديد`")
        return

    users = get_all_users()
    sent_count = 0
    fail_count = 0
    
    status_msg = bot.reply_to(message, f"⏳ يتم الإرسال لـ {len(users)} عضو...")

    for user_id in users:
        try:
            bot.send_message(user_id, msg_text)
            sent_count += 1
        except:
            fail_count += 1
            
    bot.edit_message_text(f"✅ **تم الانتهاء!**\n\nوصلت لـ: {sent_count}\nفشلت لـ: {fail_count}", message.chat.id, status_msg.message_id, parse_mode='Markdown')

# --- تحميل الفيديو ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
         bot.reply_to(message, "⚠️ يرجى إرسال رابط صحيح")
         return

    status_msg = bot.reply_to(message, "⏳ **جاري التحميل...**", parse_mode='Markdown')
    filename = None

    try:
        # إعدادات التحميل (تمت إضافة الكوكيز هنا)
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'video_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'max_filesize': MAX_SIZE,
        }

        # استخدام ملف الكوكيز لو موجود
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                raise Exception("الرابط غير صالح أو الموقع محظور")

            fsize = info.get('filesize') or info.get('filesize_approx')
            if fsize and fsize > MAX_SIZE:
                bot.edit_message_text(f"❌ الفيديو مساحته أكبر من 50 ميجا ({round(fsize/(1024*1024), 2)} MB).", message.chat.id, status_msg.message_id)
                return
            
            title = info.get('title', 'فيديو')
            uploader = info.get('uploader', 'غير معروف')
            views = human_readable(info.get('view_count'))
            likes = human_readable(info.get('like_count'))

            # تم تعديل التنسيق وإزالة المارك داون لتجنب أخطاء فيسبوك
            caption_text = (
                f"{title}\n\n"
                f"👤 {uploader} | 👀 {views} | ❤️ {likes}\n"
                f"----------------------\n"
                f"🌟 By: Kareem Mohamed\n"
                f"🤖 @kma_tbot" 
            )
            
            bot.edit_message_text(f"⬇️ جاري الرفع: {title}", message.chat.id, status_msg.message_id)
            
            ydl.download([url])
            filename = ydl.prepare_filename(info)

        bot.edit_message_text("🚀 جاري الإرسال...", message.chat.id, status_msg.message_id)
        
        with open(filename, 'rb') as video:
            bot.send_video(
                message.chat.id, 
                video, 
                caption=caption_text,
                reply_to_message_id=message.message_id
                # تم حذف parse_mode لحل مشكلة فيسبوك نهائياً
            )

        if os.path.exists(filename):
            os.remove(filename)
        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        # تقرير الخطأ للأدمن
        bot.edit_message_text("❌ حدث خطأ، تأكد من الرابط أو حاول لاحقاً.", message.chat.id, status_msg.message_id)
        
        if filename and os.path.exists(filename):
            os.remove(filename)

        if str(message.chat.id) != str(ADMIN_ID): # منبعتش الخطأ للأدمن لو هو اللي بيجرب
            try:
                bot.send_message(ADMIN_ID, f"⚠️ **خطأ جديد:**\n🔗 {url}\n📄 {str(e)}", parse_mode='Markdown')
            except: pass

print("Bot is running...")
bot.infinity_polling()
