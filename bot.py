from telethon import TelegramClient, events, Button
import aiosqlite
import requests
import asyncio
import os

# مشخصات API تلگرام
api_id = 18377832  # جایگزین شود
api_hash = "ed8556c450c6d0fd68912423325dd09c"  # جایگزین شود
session_name = "my_ai"

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
    await event.respond("سلام، چطوری میتونم کمکت کنم؟", buttons=[
        [Button.inline("کد نویسی", b"coding")]
    ])

@client.on(events.CallbackQuery(data=b'coding'))
async def choose_language(event):
    if not bot_active and event.sender_id != admin_id:
        return
    rows = [[Button.inline(lang, lang.encode())] for lang in languages]
    await event.edit("یکی از زبان‌ها رو انتخاب کن:", buttons=rows)

@client.on(events.CallbackQuery)
async def handle_language(event):
    if not bot_active and event.sender_id != admin_id:
        return

    lang = event.data.decode()
    if lang in languages:
        user_states[event.sender_id] = lang
        await event.respond(f"زبان انتخاب‌شده: {lang}\nپیامت رو بفرست تا کد رو بسازم.")

@client.on(events.NewMessage)
async def handle_message(event):
    if not bot_active and event.sender_id != admin_id:
        return

    if event.sender_id in user_states:
        lang = user_states[event.sender_id]
        prompt = f"{lang}: {event.text.strip()}. فقط کد خروجی بده."

        processing = await event.respond("در حال پردازش کدت هستم... لطفاً صبر کن.")

        response = await call_api(prompt, event.sender_id)

        if len(response) > 3900:
            ext = ext_map.get(lang, "txt")
            filename = f"code_{lang.lower()}.{ext}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response)
            await client.send_file(event.chat_id, filename, caption=f"کدت آماده‌ست (زبان: {lang})")
            os.remove(filename)
        else:
            await processing.edit(response)

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

async def add_user(user_id):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

client.start()
print("ربات روشنه...")
client.run_until_disconnected()
