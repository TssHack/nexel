# -*- coding: utf-8 -*-
from telethon import TelegramClient, events, Button
import aiosqlite
import json
import requests
import asyncio
import os

# --- Configuration ---
api_id = 18377832
api_hash = "ed8556c450c6d0fd68912423325dd09c"
session_name = "my_ai_multilang"
admin_id = 6856915102 # <<< حتماً آیدی عددی ادمین را اینجا قرار دهید
db_file = "users_data.db" # نام فایل دیتابیس یکپارچه

# --- Bot State ---
client = TelegramClient(session_name, api_id, api_hash)
bot_active = True
user_states = {} # State for coding language selection {user_id: coding_language}
admin_states = {} # State for admin actions {admin_id: action}
user_interface_language = {} # Stores selected UI language {user_id: lang_code}

# --- Bot Data ---
coding_languages = [
    "Laravel", "Python", "Java", "JavaScript", "C#", "C++", "C",
    "Swift", "Golang", "Rust", "Kotlin", "TypeScript", "PhP"
]

ext_map = {
    "Python": "py", "Java": "java", "JavaScript": "js", "C#": "cs", "C++": "cpp", "C": "c",
    "Swift": "swift", "Golang": "go", "Rust": "rs", "Kotlin": "kt", "TypeScript": "ts",
    "PhP": "php", "Laravel": "php"
}

# --- Multilingual Text ---
translations = {
    'fa': {
        'start_choose_lang': "لطفاً زبان مورد نظر خود را انتخاب کنید:",
        'welcome': "**سلام، چطوری میتونم کمکت کنم؟**",
        'coding_button': "🧬 کد نویسی",
        'help_button': "📚 راهنما",
        'developer_button': "🧑‍💻 ارتباط با توسعه دهنده",
        'main_menu_button': "🔙 برگشت به منوی اصلی",
        'choose_coding_lang': "**لطفاً یکی از زبان‌های برنامه‌نویسی را انتخاب کنید:**",
        'coding_lang_selected': "زبان برنامه‌نویسی انتخاب‌شده: {lang}\n\n**سوالت رو بپرس برات کدشو بنویسم.**",
        'back_to_lang_menu': "بازگشت به منوی زبان‌ها",
        'processing': "**در حال پردازش کدت هستم... لطفاً صبر کن.**",
        'code_ready': "کدت آماده‌ست (زبان: {lang})",
        'code_too_long': "کدت آماده‌ست و به صورت فایل ارسال شد (زبان: {lang})",
        'api_error': "خطا در پاسخ‌گویی: {e}",
        'invalid_request': "**پیامت مربوط به برنامه‌نویسی نیست یا نمی‌تونم براش کدی بنویسم.**",
        'help_title': "**🌟 راهنمای استفاده از ربات 🌟**",
        'help_text': """
برای استفاده از ربات، مراحل زیر را دنبال کنید:

1️⃣ **انتخاب زبان برنامه‌نویسی**: ابتدا روی دکمه '{coding_button}' کلیک کرده و یک زبان را انتخاب کنید.
2️⃣ **ارسال سوال**: سوال برنامه‌نویسی خود را بنویسید.
3️⃣ **دریافت کد**: ربات سعی می‌کند بهترین کد ممکن را برای شما بنویسد.

⬅️ **بازگشت به منوها**: از دکمه‌های بازگشت برای جابجایی بین منوها استفاده کنید.

❗️ **توجه**: ربات فقط درخواست‌های مرتبط با برنامه‌نویسی را پردازش می‌کند.

💡 از این ربات لذت ببرید!
        """,
        'start_coding_button': "🏁 شروع کدنویسی!",
        'admin_panel_title': "**⚙️ پنل مدیریت ربات ⚙️**",
        'admin_panel_desc': "لطفاً یک گزینه را انتخاب کنید:",
        'admin_on': "✅ روشن کردن ربات",
        'admin_off': "❌ خاموش کردن ربات",
        'admin_broadcast': "📢 ارسال پیام همگانی",
        'admin_list_users': "👥 لیست کاربران",
        'admin_bot_on_msg': "✅ ربات برای کاربران فعال شد.",
        'admin_bot_off_msg': "❌ ربات برای کاربران غیرفعال شد.",
        'admin_ask_broadcast': "لطفاً پیام همگانی خود را ارسال کنید:",
        'admin_broadcast_sending': "⏳ در حال ارسال پیام به {count} کاربر...",
        'admin_broadcast_sent': "✅ پیام همگانی با موفقیت ارسال شد.",
        'admin_broadcast_failed': "⚠️ ارسال پیام به برخی کاربران با خطا مواجه شد.",
        'admin_list_users_title': "**👥 لیست کاربران ربات ({count} نفر):**\n\n",
        'admin_no_users': "**هنوز هیچ کاربری در دیتابیس ثبت نشده است.**",
        'admin_not_allowed': "**شما اجازه دسترسی به این بخش را ندارید.**",
        'error_generic': "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
         'admin_panel_button': "⚙️ پنل مدیریت" # Button text to open admin panel
    },
    'en': {
        'start_choose_lang': "Please choose your language:",
        'welcome': "**Hello, how can I help you?**",
        'coding_button': "🧬 Coding",
        'help_button': "📚 Help",
        'developer_button': "🧑‍💻 Contact Developer",
        'main_menu_button': "🔙 Back to Main Menu",
        'choose_coding_lang': "**Please choose a programming language:**",
        'coding_lang_selected': "Selected language: {lang}\n\n**Ask your question, and I'll write the code.**",
        'back_to_lang_menu': "Back to Language Menu",
        'processing': "**Processing your code... Please wait.**",
        'code_ready': "Your code is ready (Language: {lang})",
        'code_too_long': "Your code is ready and sent as a file (Language: {lang})",
        'api_error': "Error getting response: {e}",
        'invalid_request': "**Your message isn't related to programming, or I can't write code for it.**",
        'help_title': "**🌟 Bot Usage Guide 🌟**",
        'help_text': """
Follow these steps to use the bot:

1️⃣ **Select Programming Language**: First, click the '{coding_button}' button and choose a language.
2️⃣ **Send Question**: Write your programming question.
3️⃣ **Receive Code**: The bot will try to write the best possible code for you.

⬅️ **Navigate Menus**: Use the back buttons to move between menus.

❗️ **Note**: The bot only processes programming-related requests.

💡 Enjoy using the bot!
        """,
        'start_coding_button': "🏁 Start Coding!",
        'admin_panel_title': "**⚙️ Bot Admin Panel ⚙️**",
        'admin_panel_desc': "Please choose an option:",
        'admin_on': "✅ Turn Bot ON",
        'admin_off': "❌ Turn Bot OFF",
        'admin_broadcast': "📢 Broadcast Message",
        'admin_list_users': "👥 List Users",
        'admin_bot_on_msg': "✅ Bot turned ON for users.",
        'admin_bot_off_msg': "❌ Bot turned OFF for users.",
        'admin_ask_broadcast': "Please send the broadcast message:",
        'admin_broadcast_sending': "⏳ Sending message to {count} users...",
        'admin_broadcast_sent': "✅ Broadcast message sent successfully.",
        'admin_broadcast_failed': "⚠️ Failed to send message to some users.",
        'admin_list_users_title': "**👥 Bot Users List ({count} total):**\n\n",
        'admin_no_users': "**No users found in the database yet.**",
        'admin_not_allowed': "**You do not have permission to access this section.**",
        'error_generic': "An error occurred. Please try again.",
        'admin_panel_button': "⚙️ Admin Panel"
    },
    'ru': {
        'start_choose_lang': "Пожалуйста, выберите ваш язык:",
        'welcome': "**Здравствуйте, чем я могу вам помочь?**",
        'coding_button': "🧬 Кодинг",
        'help_button': "📚 Помощь",
        'developer_button': "🧑‍💻 Связаться с разработчиком",
        'main_menu_button': "🔙 Назад в главное меню",
        'choose_coding_lang': "**Пожалуйста, выберите язык программирования:**",
        'coding_lang_selected': "Выбранный язык: {lang}\n\n**Задайте свой вопрос, и я напишу код.**",
        'back_to_lang_menu': "Назад к меню языков",
        'processing': "**Обрабатываю ваш код... Пожалуйста, подождите.**",
        'code_ready': "Ваш код готов (Язык: {lang})",
        'code_too_long': "Ваш код готов и отправлен в виде файла (Язык: {lang})",
        'api_error': "Ошибка при получении ответа: {e}",
        'invalid_request': "**Ваше сообщение не связано с программированием, или я не могу написать для него код.**",
        'help_title': "**🌟 Руководство по использованию бота 🌟**",
        'help_text': """
Чтобы использовать бота, выполните следующие действия:

1️⃣ **Выберите язык программирования**: Сначала нажмите кнопку '{coding_button}' и выберите язык.
2️⃣ **Отправьте вопрос**: Напишите свой вопрос по программированию.
3️⃣ **Получите код**: Бот постарается написать для вас наилучший код.

⬅️ **Навигация по меню**: Используйте кнопки возврата для перемещения между меню.

❗️ **Примечание**: Бот обрабатывает только запросы, связанные с программированием.

💡 Приятного использования бота!
        """,
        'start_coding_button': "🏁 Начать кодинг!",
        'admin_panel_title': "**⚙️ Панель администратора бота ⚙️**",
        'admin_panel_desc': "Пожалуйста, выберите опцию:",
        'admin_on': "✅ Включить бота",
        'admin_off': "❌ Выключить бота",
        'admin_broadcast': "📢 Рассылка сообщения",
        'admin_list_users': "👥 Список пользователей",
        'admin_bot_on_msg': "✅ Бот включен для пользователей.",
        'admin_bot_off_msg': "❌ Бот выключен для пользователей.",
        'admin_ask_broadcast': "Пожалуйста, отправьте сообщение для рассылки:",
        'admin_broadcast_sending': "⏳ Отправка сообщения {count} пользователям...",
        'admin_broadcast_sent': "✅ Сообщение для рассылки успешно отправлено.",
        'admin_broadcast_failed': "⚠️ Не удалось отправить сообщение некоторым пользователям.",
        'admin_list_users_title': "**👥 Список пользователей бота (всего {count}):**\n\n",
        'admin_no_users': "**Пользователи в базе данных пока не найдены.**",
        'admin_not_allowed': "**У вас нет разрешения на доступ к этому разделу.**",
        'error_generic': "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
        'admin_panel_button': "⚙️ Панель админа"
    },
    'tr': {
        'start_choose_lang': "Lütfen dilinizi seçin:",
        'welcome': "**Merhaba, size nasıl yardımcı olabilirim?**",
        'coding_button': "🧬 Kodlama",
        'help_button': "📚 Yardım",
        'developer_button': "🧑‍💻 Geliştiriciyle İletişime Geç",
        'main_menu_button': "🔙 Ana Menüye Dön",
        'choose_coding_lang': "**Lütfen bir programlama dili seçin:**",
        'coding_lang_selected': "Seçilen dil: {lang}\n\n**Sorunuzu sorun, kodunu yazayım.**",
        'back_to_lang_menu': "Dil Menüsüne Geri Dön",
        'processing': "**Kodunuz işleniyor... Lütfen bekleyin.**",
        'code_ready': "Kodunuz hazır (Dil: {lang})",
        'code_too_long': "Kodunuz hazır ve dosya olarak gönderildi (Dil: {lang})",
        'api_error': "Yanıt alınırken hata oluştu: {e}",
        'invalid_request': "**Mesajınız programlamayla ilgili değil veya bunun için kod yazamıyorum.**",
        'help_title': "**🌟 Bot Kullanım Kılavuzu 🌟**",
        'help_text': """
Botu kullanmak için şu adımları izleyin:

1️⃣ **Programlama Dilini Seçin**: Önce '{coding_button}' düğmesine tıklayın ve bir dil seçin.
2️⃣ **Soru Gönderin**: Programlama sorunuzu yazın.
3️⃣ **Kodu Alın**: Bot sizin için mümkün olan en iyi kodu yazmaya çalışacaktır.

⬅️ **Menülerde Gezinme**: Menüler arasında geçiş yapmak için geri düğmelerini kullanın.

❗️ **Not**: Bot yalnızca programlamayla ilgili istekleri işler.

💡 Botu kullanmanın tadını çıkarın!
        """,
        'start_coding_button': "🏁 Kodlamaya Başla!",
        'admin_panel_title': "**⚙️ Bot Yönetim Paneli ⚙️**",
        'admin_panel_desc': "Lütfen bir seçenek seçin:",
        'admin_on': "✅ Botu AÇ",
        'admin_off': "❌ Botu KAPAT",
        'admin_broadcast': "📢 Toplu Mesaj Gönder",
        'admin_list_users': "👥 Kullanıcıları Listele",
        'admin_bot_on_msg': "✅ Bot kullanıcılar için etkinleştirildi.",
        'admin_bot_off_msg': "❌ Bot kullanıcılar için devre dışı bırakıldı.",
        'admin_ask_broadcast': "Lütfen toplu mesajınızı gönderin:",
        'admin_broadcast_sending': "⏳ Mesaj {count} kullanıcıya gönderiliyor...",
        'admin_broadcast_sent': "✅ Toplu mesaj başarıyla gönderildi.",
        'admin_broadcast_failed': "⚠️ Bazı kullanıcılara mesaj gönderilemedi.",
        'admin_list_users_title': "**👥 Bot Kullanıcı Listesi (toplam {count}):**\n\n",
        'admin_no_users': "**Veritabanında henüz kullanıcı bulunamadı.**",
        'admin_not_allowed': "**Bu bölüme erişim izniniz yok.**",
        'error_generic': "Bir hata oluştu. Lütfen tekrar deneyin.",
        'admin_panel_button': "⚙️ Yönetim Paneli"
    }
}

# --- Helper Functions ---
def get_translation(key, lang_code='fa', **kwargs):
    """Gets the translated string for a given key and language code."""
    lang_code = lang_code or 'fa' # Default to Persian if lang_code is None
    return translations.get(lang_code, translations['fa']).get(key, f"[{key}]").format(**kwargs)

async def get_user_lang(user_id):
    """Gets the user's preferred UI language, defaulting to Persian."""
    return user_interface_language.get(user_id, 'fa')

async def add_user_to_db(user_id):
    """Adds a user ID to the SQLite database if it doesn't exist."""
    try:
        async with aiosqlite.connect(db_file) as db:
            # Ensure table exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Insert or ignore if user already exists
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            # Update last seen time
            await db.execute("UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
            await db.commit()
    except Exception as e:
        print(f"Database error in add_user_to_db: {e}")


async def update_user_details(user_id):
    """Updates user details like username and first name in the DB."""
    try:
        user = await client.get_entity(user_id)
        async with aiosqlite.connect(db_file) as db:
            await db.execute("""
                UPDATE users
                SET username = ?, first_name = ?, last_seen = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user.username, user.first_name, user_id))
            await db.commit()
    except Exception as e:
        # Handle cases where user might not be accessible, etc.
        print(f"Could not update details for user {user_id}: {e}")

async def get_all_user_ids_from_db():
    """Retrieves all user IDs from the database."""
    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        print(f"Database error in get_all_user_ids_from_db: {e}")
        return []

async def call_api(query, user_id):
    """Calls the external API to get code."""
    try:
        url = "https://api.binjie.fun/api/generateStream"
        headers = {
            "authority": "api.binjie.fun",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9", # Keep consistent or vary if needed
            "origin": "https://chat18.aichatos.xyz",
            "referer": "https://chat18.aichatos.xyz/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36", # Updated UA
            "Content-Type": "application/json"
        }
        # Ensure userId is a string as observed in some APIs
        data = {
            "prompt": query,
            "userId": f"#/{str(user_id)}", # Format might be important
            "network": True,
            "system": "", # Add system prompt if beneficial
            "withoutContext": False, # Maintain context if useful
            "stream": False # Get full response at once
        }
        # Increased timeout
        async with requests.Session() as session:
             # Use async context for requests if using an async library like httpx
             # For standard requests, run in executor
             loop = asyncio.get_event_loop()
             res = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=data, timeout=30))
             res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
             res.encoding = 'utf-8' # Ensure correct encoding
             return res.text.strip()
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        lang_code = await get_user_lang(user_id)
        return get_translation('api_error', lang_code, e=e)
    except Exception as e:
        print(f"API Call General Error: {e}")
        lang_code = await get_user_lang(user_id)
        return get_translation('api_error', lang_code, e=e)


async def is_code_related(text, event):
    """Checks if the user's text is a valid request for code generation."""
    lang_code = await get_user_lang(event.sender_id)
    async with client.action(event.chat_id, "typing"):
        # Note: The validation prompt might need adjustment based on the API's behavior
        # Consider providing examples of valid/invalid requests in the prompt.
        check_prompt = f'Analyze the user request: "{text}". Is this a request to generate programming code or explain a programming concept? Answer ONLY with "yes" or "no".'
        try:
            # Use a generic ID for validation to avoid mixing contexts
            reply = await call_api(check_prompt, "validator-check-001")
            # Make the check more robust
            reply_lower = reply.lower().strip().translate(str.maketrans('', '', '.,!?\'"')) # Clean up the reply
            return reply_lower == "yes"
        except Exception as e:
            print(f"Error during code related check: {e}")
            await event.respond(get_translation('error_generic', lang_code))
            return False # Default to false on error

# --- Event Handlers ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id

    # Add user to DB immediately
    await add_user_to_db(user_id)
    # Try to update details (runs in background, doesn't block)
    asyncio.create_task(update_user_details(user_id))

    # Reset any previous state
    if user_id in user_states: del user_states[user_id]
    if user_id in admin_states: del admin_states[user_id] # Clear admin state too

    # Ask for language selection
    await event.respond(
        get_translation('start_choose_lang', 'fa'), # Initial prompt in Persian
        buttons=[
            [Button.inline("🇮🇷 فارسی", b"set_lang_fa"), Button.inline("🇬🇧 English", b"set_lang_en")],
            [Button.inline("🇷🇺 Русский", b"set_lang_ru"), Button.inline("🇹🇷 Türkçe", b"set_lang_tr")]
        ]
    )

@client.on(events.CallbackQuery(pattern=b"set_lang_(.*)"))
async def set_language(event):
    user_id = event.sender_id
    lang_code = event.pattern_match.group(1).decode('utf-8')

    if lang_code not in translations:
        lang_code = 'fa' # Default to Persian if invalid code

    user_interface_language[user_id] = lang_code

    # Show main menu in the selected language
    await show_main_menu(event, edit=True)


async def show_main_menu(event, edit=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_lang(user_id)

    buttons = [
        [Button.inline(get_translation('coding_button', lang_code), b"coding")],
        [Button.inline(get_translation('help_button', lang_code), b"help")],
        [Button.url(get_translation('developer_button', lang_code), "https://t.me/n6xel")]
    ]
     # Add admin panel button only for the admin
    if user_id == admin_id:
        buttons.append([Button.inline(get_translation('admin_panel_button', lang_code), b"admin_panel")])

    text = get_translation('welcome', lang_code)

    if edit:
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"main_menu"))
async def return_to_main_menu(event):
    # Reset coding state if returning to main menu
    if event.sender_id in user_states:
        del user_states[event.sender_id]
    await show_main_menu(event, edit=True)

@client.on(events.CallbackQuery(data=b'coding'))
async def choose_coding_language(event):
    if not bot_active and event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_lang(event.sender_id)

    rows = []
    # Create two buttons per row
    for i in range(0, len(coding_languages), 2):
        row = [Button.inline(coding_languages[i], f"select_code_{coding_languages[i]}".encode())]
        if i + 1 < len(coding_languages):
            row.append(Button.inline(coding_languages[i + 1], f"select_code_{coding_languages[i+1]}".encode()))
        rows.append(row)

    # Add back button
    rows.append([Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")])

    await event.edit(
        get_translation('choose_coding_lang', lang_code),
        buttons=rows
    )

@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def handle_coding_language_selection(event):
    if not bot_active and event.sender_id != admin_id:
        await event.answer()
        return

    selected_lang = event.pattern_match.group(1).decode('utf-8')
    user_id = event.sender_id
    lang_code = await get_user_lang(user_id) # UI language

    if selected_lang in coding_languages:
        user_states[user_id] = selected_lang # Store the *coding* language state
        await event.edit(
            get_translation('coding_lang_selected', lang_code, lang=selected_lang),
            buttons=[
                Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
                Button.inline(get_translation('main_menu_button', lang_code), b"main_menu") # Added main menu return
                ]
        )
    else:
         # Should not happen with buttons, but handle defensively
        await event.answer("Invalid language selected.", alert=True)


@client.on(events.CallbackQuery(data=b"help"))
async def show_help(event):
    await event.answer() # Acknowledge callback
    user_id = event.sender_id
    lang_code = await get_user_lang(user_id)

    # Format the help text with the dynamic button name
    help_message = get_translation('help_title', lang_code) + "\n\n" + \
                   get_translation('help_text', lang_code, coding_button=get_translation('coding_button', lang_code))

    await event.edit(
        help_message,
        buttons=[
            [Button.inline(get_translation('start_coding_button', lang_code), b"coding")],
            [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
        ]
    )

# --- Admin Panel ---

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    """Handles the /admin command to show the panel."""
    if event.sender_id == admin_id:
        await show_admin_panel(event)
    else:
        lang_code = await get_user_lang(event.sender_id)
        await event.respond(get_translation('admin_not_allowed', lang_code))


@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    """Handles the callback button to show the panel."""
    if event.sender_id == admin_id:
        await show_admin_panel(event, edit=True)
    else:
        # Ignore silently or show 'not allowed' message
        await event.answer()


async def show_admin_panel(event, edit=False):
    """Displays the admin panel with buttons."""
    lang_code = await get_user_lang(admin_id) # Admin panel uses admin's language pref
    text = f"**{get_translation('admin_panel_title', lang_code)}**\n\n{get_translation('admin_panel_desc', lang_code)}"

    buttons = [
        [
            Button.inline(get_translation('admin_on', lang_code), b"admin_set_on"),
            Button.inline(get_translation('admin_off', lang_code), b"admin_set_off")
        ],
        [
            Button.inline(get_translation('admin_broadcast', lang_code), b"admin_broadcast"),
            Button.inline(get_translation('admin_list_users', lang_code), b"admin_list_users")
        ],
        [ Button.inline(get_translation('main_menu_button', lang_code), b"main_menu") ] # Back to main menu
    ]

    if edit:
        try:
            await event.edit(text, buttons=buttons)
        except Exception as e:
            print(f"Error editing message for admin panel: {e}")
            # Fallback to sending a new message if edit fails
            await event.respond(text, buttons=buttons)
    else:
         await event.respond(text, buttons=buttons)


@client.on(events.CallbackQuery(data=b"admin_set_on"))
async def admin_turn_on(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = True
        lang_code = await get_user_lang(admin_id)
        await event.answer(get_translation('admin_bot_on_msg', lang_code), alert=True)
        # Optionally update the panel message or buttons if needed
        # await show_admin_panel(event, edit=True)
    else:
        await event.answer() # Ignore for non-admins


@client.on(events.CallbackQuery(data=b"admin_set_off"))
async def admin_turn_off(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = False
        lang_code = await get_user_lang(admin_id)
        await event.answer(get_translation('admin_bot_off_msg', lang_code), alert=True)
        # await show_admin_panel(event, edit=True)
    else:
        await event.answer()


@client.on(events.CallbackQuery(data=b"admin_list_users"))
async def admin_list_users(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_lang(admin_id)
    await event.answer("⏳ Fetching users...") # Give feedback

    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT user_id, username, first_name, last_seen FROM users ORDER BY last_seen DESC") as cursor:
                users = await cursor.fetchall()

        if not users:
            await event.edit(get_translation('admin_no_users', lang_code), buttons=[ Button.inline("🔙 Back", b"admin_panel") ])
            return

        user_list_text = get_translation('admin_list_users_title', lang_code, count=len(users))
        for user_id, username, first_name, last_seen in users:
            display_name = first_name if first_name else f"User_{user_id}"
            user_list_text += f"👤 `{user_id}` - @{username if username else 'N/A'} ({display_name}) - Seen: {last_seen.split('.')[0]}\n" # Nicer formatting

        # Handle potential message too long error for large user lists
        if len(user_list_text) > 4000:
             user_list_text = user_list_text[:4000] + "\n... (list truncated)"

        await event.edit(user_list_text, buttons=[ Button.inline("🔙 Back", b"admin_panel") ], parse_mode='md')

    except Exception as e:
        print(f"Error listing users: {e}")
        await event.edit(f"Error fetching users: {e}", buttons=[ Button.inline("🔙 Back", b"admin_panel") ])


@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_ask_broadcast(event):
    if event.sender_id == admin_id:
        lang_code = await get_user_lang(admin_id)
        admin_states[admin_id] = 'awaiting_broadcast_message' # Set admin state
        await event.edit(
            get_translation('admin_ask_broadcast', lang_code),
            buttons=[ Button.inline("🔙 Cancel", b"admin_panel") ] # Allow cancellation
        )
    else:
        await event.answer()


# --- Main Message Handler ---

@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    user_input = event.text.strip()

    # 1. Handle Admin Broadcast Input
    if user_id == admin_id and admin_states.get(user_id) == 'awaiting_broadcast_message':
        lang_code = await get_user_lang(admin_id)
        broadcast_text = user_input
        del admin_states[user_id] # Clear state

        user_ids = await get_all_user_ids_from_db()
        if not user_ids:
            await event.respond("No users in the database to broadcast to.")
            await show_admin_panel(event) # Show admin panel again
            return

        count = len(user_ids)
        sent_count = 0
        failed_count = 0
        status_message = await event.respond(get_translation('admin_broadcast_sending', lang_code, count=count))

        for target_user_id in user_ids:
            try:
                # Add small delay to avoid flood limits
                await asyncio.sleep(0.1)
                await client.send_message(target_user_id, broadcast_text)
                sent_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send broadcast to {target_user_id}: {e}")
                # Optional: Remove user from DB if blocked/deactivated?
                # async with aiosqlite.connect(db_file) as db:
                #     await db.execute("DELETE FROM users WHERE user_id = ?", (target_user_id,))
                #     await db.commit()

        result_message = get_translation('admin_broadcast_sent', lang_code)
        if failed_count > 0:
            result_message += f"\n{get_translation('admin_broadcast_failed', lang_code)} ({failed_count} failures)"

        await status_message.edit(result_message)
        await asyncio.sleep(2) # Show result briefly
        await show_admin_panel(event) # Go back to admin panel
        return # Stop further processing

    # 2. Ignore messages if bot is off (except for admin)
    if not bot_active and user_id != admin_id:
        return

    # 3. Ignore commands, callbacks handled elsewhere
    if user_input.startswith('/'):
        # Allow /start even if bot is off for language selection
        if user_input == '/start':
             await start(event) # Re-run start logic if needed
        return

    # 4. Handle Coding Requests
    if user_id in user_states:
        coding_lang = user_states[user_id]
        lang_code = await get_user_lang(user_id) # UI Language

        async with client.action(chat_id, "typing"):
            # Validate if the message is code-related *before* calling the main API
            is_valid = await is_code_related(user_input, event)
            if not is_valid:
                await event.respond(get_translation('invalid_request', lang_code))
                # Keep the user in the selected language state? Or clear it?
                # del user_states[user_id] # Optional: clear state if invalid
                return

            # Construct prompt for the API
            # Consider adding more context or structure to the prompt if needed
            prompt = f"Generate {coding_lang} code for the following request:\n\n{user_input}\n\nProvide only the code block as the output."

            processing_msg = await event.respond(get_translation('processing', lang_code))

            response = await call_api(prompt, user_id) # Pass user_id for API context if needed

            # Try cleaning potential markdown issues or unwanted text from API
            if "```" in response:
                # Extract code block if possible
                code_blocks = response.split("```")
                if len(code_blocks) >= 2:
                    # Take the content of the first code block
                    potential_code = code_blocks[1]
                    # Remove language hint if present at the start
                    lines = potential_code.split('\n')
                    if lines[0].strip().lower() in [l.lower() for l in coding_languages + [ext_map.get(coding_lang, '')]]:
                        response = '\n'.join(lines[1:]).strip()
                    else:
                        response = potential_code.strip()
                else:
                    # Fallback if splitting doesn't work as expected
                     response = response.replace("```", "").strip()

            else:
                # If no backticks, just strip whitespace
                response = response.strip()


            # Check if the response is empty or contains only error message
            if not response or response.startswith("Error getting response:") or response.startswith("خطا در"):
                 await processing_msg.edit(response if response else get_translation('error_generic', lang_code))
                 # Clear state on error?
                 # del user_states[user_id]
                 return


            # Handle response length
            if len(response) > 3900: # Telegram message limit is 4096
                ext = ext_map.get(coding_lang, "txt")
                filename = f"code_{coding_lang.lower()}_{user_id}.{ext}"
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(response)
                    await client.send_file(
                        event.chat_id,
                        filename,
                        caption=get_translation('code_too_long', lang_code, lang=coding_lang),
                        reply_to=event.message.id
                        )
                    await processing_msg.delete() # Delete "processing" message
                except Exception as e:
                    print(f"Error sending file: {e}")
                    await processing_msg.edit(f"Error sending code as file: {e}")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename) # Clean up the file
            else:
                # Format as code block for shorter messages
                formatted_response = f"```\n{response}\n```"
                await processing_msg.edit(
                    f"{get_translation('code_ready', lang_code, lang=coding_lang)}\n{formatted_response}",
                     buttons=[
                         Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
                         Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
                     ],
                    parse_mode='md' # Ensure markdown is parsed
                 )

            # Clear the coding state after successfully providing code
            # Keep it if you want the user to ask follow-up questions in the same language
            # del user_states[user_id] # Uncomment this to require language re-selection after each code generation


# --- Bot Startup ---
async def main():
    """Connects the client and runs indefinitely."""
    # Initialize database schema on startup
    async with aiosqlite.connect(db_file) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        print("Database initialized.")

    # Start the client
    await client.start()
    me = await client.get_me()
    print(f"Bot '{me.first_name}' started...")
    print(f"Admin ID: {admin_id}")
    print(f"Bot active: {bot_active}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

