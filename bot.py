from telethon import TelegramClient, events, Button
import aiosqlite
import requests
import asyncio
import os

# مشخصات API تلگرام
api_id = 18377832  # جایگزین شود
api_hash = "ed8556c450c6d0fd68912423325dd09c"  # جایگزین شود
session_name = "my_ai"
admin_id = 7094106651

client = TelegramClient(session_name, api_id, api_hash)
bot_active = True

languages = [
    "Laravel", "Python", "Java", "JavaScript", "C#", "C++", "C",
    "Swift", "Golang", "Rust", "Kotlin", "TypeScript", "PhP"
]

ext_map = {
    "Python": "py", "Java": "java", "JavaScript": "js", "C#": "cs", "C++": "cpp", "C": "c",
    "Swift": "swift", "Golang": "go", "Rust": "rs", "Kotlin": "kt", "TypeScript": "ts",
    "PhP": "php", "Laravel": "php"
}

user_states = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not bot_active and event.sender_id != admin_id:
        return
    await add_user(event.sender_id)
    await event.respond("**سلام، چطوری میتونم کمکت کنم؟**", buttons=[
        [Button.inline("کد نویسی", b"coding")]
    ])

@client.on(events.CallbackQuery(data=b'coding'))
async def choose_language(event):
    if not bot_active and event.sender_id != admin_id:
        return

    # ساخت دکمه‌ها به صورت ردیف‌های دوتایی
    rows = []
    for i in range(0, len(languages), 2):
        row = [Button.inline(languages[i], languages[i].encode())]
        if i + 1 < len(languages):
            row.append(Button.inline(languages[i + 1], languages[i + 1].encode()))
        rows.append(row)

    await event.edit("**یکی از زبان‌ها رو انتخاب کن:**", buttons=rows)


@client.on(events.CallbackQuery)
async def handle_language(event):
    if not bot_active and event.sender_id != admin_id:
        return

    lang = event.data.decode()
    
    # اطمینان از اینکه فقط زبان‌ها پردازش بشن
    if lang in languages:
        user_states[event.sender_id] = lang
        await event.edit(f"زبان انتخاب‌شده: {lang}\n\n**سوالت رو بپرس برات کدشو بنویسم.**", buttons=[
                 Button.inline("بازگشت به منوی زبان‌ها", b"coding")])

@client.on(events.NewMessage)
async def handle_message(event):
    if not bot_active and event.sender_id != admin_id:
        return

    chat_id = event.chat_id

    async with client.action(chat_id, "typing"):  # وضعیت تایپ را نشان می‌دهیم
        if event.sender_id in user_states:
            lang = user_states[event.sender_id]
            user_input = event.text.strip()

            # بررسی معتبر بودن درخواست
            is_valid = await is_code_related(user_input)
            if not is_valid:
                await event.respond("**پیامت مربوط به برنامه‌نویسی نیست یا نمی‌تونم براش کدی بنویسم.**")
                del user_states[event.sender_id]
                return

            prompt = f"{lang}: {user_input}. فقط کد خروجی بده."

            # پیام در حال پردازش
            processing = await event.respond("**در حال پردازش کدت هستم... لطفاً صبر کن.**")

            # درخواست به API برای دریافت کد
            response = await call_api(prompt, event.sender_id)

            if len(response) > 3900:
                # اگر کد طولانی است، آن را در فایل ذخیره می‌کنیم
                ext = ext_map.get(lang, "txt")
                filename = f"code_{lang.lower()}.{ext}"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response)
                await client.send_file(event.chat_id, filename, caption=f"کدت آماده‌ست (زبان: {lang})")
                os.remove(filename)
            else:
                # در غیر این صورت پاسخ را ارسال کرده و دکمه‌ها را اضافه می‌کنیم
                await processing.edit(response, buttons=[
                    [Button.inline("کد جدید از زبان کنونی", b"same_lang"),
                     Button.inline("بازگشت به منوی زبان‌ها", b"coding")]
                ])

            # پاک کردن وضعیت کاربر پس از ارسال پاسخ
            del user_states[event.sender_id]

@client.on(events.NewMessage(pattern='/admin'))
async def admin_panel(event):
    if event.sender_id != admin_id:
        return
    msg = "**پنل مدیریت فعال است:**\n/on - روشن کردن ربات\n/off - خاموش کردن ربات\n/broadcast [پیام]"
    await event.respond(msg)

@client.on(events.NewMessage(pattern='/on'))
async def turn_on(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = True
        await event.respond("ربات روشن شد.")

@client.on(events.NewMessage(pattern='/off'))
async def turn_off(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = False
        await event.respond("ربات خاموش شد.")

@client.on(events.CallbackQuery(data=b'same_lang'))
async def handle_language(event):
    if not bot_active and event.sender_id != admin_id:
        return

    lang = event.data.decode()
    
    if lang in languages:
        user_states[event.sender_id] = lang
        await event.edit(f"زبان ‌فعلی: {lang}\n\n**سوالت رو بپرس برات کدشو بنویسم.**", buttons=[
                 Button.inline("بازگشت به منوی زبان‌ها", b"coding")])
        
@client.on(events.NewMessage(pattern='/broadcast (.+)'))
async def broadcast(event):
    if event.sender_id != admin_id:
        return
    text = event.pattern_match.group(1)
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            async for row in cursor:
                try:
                    await client.send_message(row[0], text)
                except:
                    pass
    await event.respond("پیام برای همه ارسال شد.")


async def call_api(query, user_id):
    try:
        url = "https://api.binjie.fun/api/generateStream"
        headers = {
            "authority": "api.binjie.fun",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://chat18.aichatos.xyz",
            "referer": "https://chat18.aichatos.xyz/",
            "user-agent": "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": query,
            "userId": str(user_id),
            "network": True,
            "system": "",
            "withoutContext": False,
            "stream": False
        }
        res = requests.post(url, headers=headers, json=data, timeout=10)
        res.encoding = 'utf-8'
        return res.text.strip()
    except Exception as e:
        return f"خطا در پاسخ‌گویی: {e}"

async def is_code_related(text):
    check_prompt = f'کاربر این پیام را فرستاده:\n"{text}"\n\nآیا این یک درخواست معتبر برای تولید کد برنامه‌نویسی هست؟ فقط با "yes" یا "no" جواب بده.'
    reply = await call_api(check_prompt, "validator-check")
    return "yes" in reply.lower()

async def add_user(user_id):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

client.start()
print("ربات روشنه...")
client.run_until_disconnected()
