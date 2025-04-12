from telethon import TelegramClient, events, Button
import aiosqlite
import json
import requests
import asyncio
import os


api_id = 18377832  
api_hash = "ed8556c450c6d0fd68912423325dd09c"  
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

json_file = 'users.json'

# بارگذاری کاربران از فایل JSON
def load_users():
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# ذخیره کاربران به فایل JSON
def save_users(users):
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(users, file, ensure_ascii=False, indent=4)

# ذخیره کاربر در فایل JSON هنگام استارت ربات
def save_started_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# دریافت لیست کاربران استارت کرده از فایل JSON
def get_started_users():
    return load_users()

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not bot_active and event.sender_id != admin_id:
        return

    user_id = event.sender_id
    await add_user(event.sender_id)
    save_started_user(user_id)
    await event.respond(
    "**سلام، چطوری میتونم کمکت کنم؟**", 
    buttons=[
        [Button.inline("🧬 کد نویسی", b"coding")],
        [Button.inline("📚 راهنما", b"help")],
        [Button.url("🧑‍💻 ارتباط با توسعه دهنده", "https://t.me/n6xel")]
    ]
)

@client.on(events.CallbackQuery(data=b"main_menu"))
async def return_to_main_menu(event):
    await event.edit(
        "**سلام، چطوری میتونم کمکت کنم؟**", 
        buttons=[
            [Button.inline("🧬 کد نویسی", b"coding")],
            [Button.inline("📚 راهنما", b"help")],
            [Button.url("🧑‍💻 ارتباط با توسعه دهنده", "https://t.me/n6xel")],
            [Button.inline("🔙 برگشت به منوی اصلی", b"main_menu")]  # دکمه برگشت به منو
        ]
    )


@client.on(events.CallbackQuery(data=b'coding'))
async def choose_language(event):
    if not bot_active and event.sender_id != admin_id:
        return

    
    rows = []
    for i in range(0, len(languages), 2):
        row = [Button.inline(languages[i], languages[i].encode())]
        if i + 1 < len(languages):
            row.append(Button.inline(languages[i + 1], languages[i + 1].encode()))
        rows.append(row)

    await event.edit(
        help_message, 
        buttons=[
            [Button.inline("🏁 شروع کنید!", b"coding")],
            [Button.inline("🔙 برگشت به منوی اصلی", b"main_menu")]  # دکمه برگشت به منو اصلی
        ]
    )


@client.on(events.CallbackQuery)
async def handle_language(event):
    if not bot_active and event.sender_id != admin_id:
        return

    lang = event.data.decode()

    
    if lang in languages:
        user_states[event.sender_id] = lang
        await event.edit(f"زبان انتخاب‌شده: {lang}\n\n**سوالت رو بپرس برات کدشو بنویسم.**", buttons=[
                 Button.inline("بازگشت به منوی زبان‌ها", b"coding")])

@client.on(events.NewMessage)
async def handle_message(event):
    if not bot_active and event.sender_id != admin_id:
        return

    chat_id = event.chat_id
    user_input = event.text.strip()

    # اضافه کردن تایپینگ
    async with client.action(chat_id, "typing"):
        if event.sender_id in user_states:
            lang = user_states[event.sender_id]
            
            # بررسی معتبر بودن درخواست
            is_valid = await is_code_related(user_input, event)  # اضافه کردن event
            if not is_valid:
                await event.respond("**پیامت مربوط به برنامه‌نویسی نیست یا نمی‌تونم براش کدی بنویسم.**")
                del user_states[event.sender_id]
                return

            prompt = f"{lang}: {user_input}. فقط کد خروجی بده."

            processing = await event.respond("**در حال پردازش کدت هستم... لطفاً صبر کن.**")

            response = await call_api(prompt, event.sender_id)

            if len(response) > 3900:
                ext = ext_map.get(lang, "txt")
                filename = f"code_{lang.lower()}.{ext}"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response)
                await client.send_file(event.chat_id, filename, caption=f"کدت آماده‌ست (زبان: {lang})")
                os.remove(filename)
            else:
                await processing.edit(response, buttons=[
                 Button.inline("بازگشت به منوی زبان‌ها", b"coding")])

            
            del user_states[event.sender_id]

@client.on(events.NewMessage(pattern='/admin'))
async def admin_panel(event):
    if event.sender_id != admin_id:
        return
    msg = "**پنل مدیریت فعال است:**\n/on - روشن کردن ربات\n/off - خاموش کردن ربات\n/broadcast [پیام]"
    await event.respond(msg)

@client.on(events.NewMessage(pattern="/list_started"))
async def list_started_users(event):
    admin_id = 7094106651  # اید‌ی تلگرام ادمین را وارد کنید
    
    if event.sender_id == admin_id:  # فقط ادمین مجاز به دیدن لیست است
        users = get_started_users()
        user_list = ""
        for user_id in users:
            user = await client.get_entity(user_id)
            user_list += f"@{user.username if user.username else 'Unknown'}\n"
        
        if not user_list:
            user_list = "**هیچ کاربری ربات را استارت نکرده است.**"
        
        # ارسال لیست به ادمین
        await event.respond(f"**لیست کاربرانی که ربات را استارت کرده‌اند:**\n\n{user_list}")
    else:
        await event.respond("**شما اجازه مشاهده این اطلاعات را ندارید.**")

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

@client.on(events.CallbackQuery(data=b"help"))
async def show_help(event):
    await event.answer()  

    help_message = """
    **🌟 راهنمای استفاده از ربات 🌟**

    برای استفاده از ربات، مراحل زیر را دنبال کنید:
    
    1️⃣ **انتخاب زبان**: ابتدا یک زبان برنامه‌نویسی انتخاب کنید.
    2️⃣ **ارسال سوال**: سوال خود را به زبان انتخابی بنویسید.
    3️⃣ **دریافت کد**: ربات سعی می‌کند بهترین کد ممکن را برای شما بنویسد.
    
    🔄 **کد جدید**: اگر می‌خواهید کد جدیدی از همان زبان دریافت کنید، دکمه "کد جدید از زبان کنونی" را فشار دهید.
    
    ⬅️ **بازگشت به زبان‌ها**: برای بازگشت به منوی انتخاب زبان‌ها، دکمه "بازگشت به منوی زبان‌ها" را بزنید.

    ❗️ **توجه**: ربات فقط درخواست‌های مرتبط با برنامه‌نویسی را پردازش می‌کند. اگر پیامی غیرمرتبط ارسال کنید، پردازش نخواهد شد.
    
    🔄 برای دریافت راهنمای بیشتر، همین دکمه را دوباره فشار دهید.

    💡 از این ربات لذت ببرید و سوالات خود را به راحتی بپرسید!
    """

    await event.edit(
        help_message, 
        buttons=[
            [Button.inline("🏁 شروع کنید!", b"coding")],
            [Button.inline("🔙 برگشت به منوی اصلی", b"main_menu")]  # دکمه برگشت به منو اصلی
        ]
    )

        
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

async def is_code_related(text, event):
    # نشان دادن تایپینگ
    async with client.action(event.chat_id, "typing"):
        check_prompt = f'کاربر این پیام را فرستاده:\n"{text}"\n\nآیا این یک درخواست معتبر برای تولید کد برنامه‌نویسی هست؟ فقط با "yes" یا "no" جواب بده.'
        reply = await call_api(check_prompt, "validator-check")
        return "yes" in reply.lower()

async def add_user(user_id):
    async with aiosqlite.connect("users.db", check_same_thread=False) as db:
        await db.execute("PRAGMA busy_timeout = 3000")
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

client.start()
print("ربات روشنه...")
client.run_until_disconnected()
