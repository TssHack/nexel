# -*- coding: utf-8 -*-
from telethon import TelegramClient, events, Button
import aiosqlite
import json
import requests # Using requests synchronously within asyncio via run_in_executor
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
            # Update last seen time upon interaction
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
    lang_code = await get_user_lang(user_id) # Get language for potential error messages
    try:
        url = "[https://api.binjie.fun/api/generateStream](https://api.binjie.fun/api/generateStream)"
        headers = {
            "authority": "api.binjie.fun",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9", # Keep consistent or vary if needed
            "origin": "[https://chat18.aichatos.xyz](https://chat18.aichatos.xyz)",
            "referer": "[https://chat18.aichatos.xyz/](https://chat18.aichatos.xyz/)",
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
        # Use run_in_executor to run the synchronous requests call in a separate thread
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None, # Use default executor
            lambda: requests.post(url, headers=headers, json=data, timeout=30) # Timeout set to 30 seconds
        )
        res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        res.encoding = 'utf-8' # Ensure correct encoding
        return res.text.strip()
    except requests.exceptions.Timeout:
        print(f"API Request Timeout for user {user_id}")
        return get_translation('api_error', lang_code, e="Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"API Request Error for user {user_id}: {e}")
        return get_translation('api_error', lang_code, e=e)
    except Exception as e:
        print(f"API Call General Error for user {user_id}: {e}")
        return get_translation('api_error', lang_code, e=e)

# --- START: Replaced Function ---
async def is_code_related(text, event):
    """Checks if the user's text is a valid request for code generation using the Persian prompt."""
    lang_code = await get_user_lang(event.sender_id)
    async with client.action(event.chat_id, "typing"):
        # Using the Persian prompt as requested
        check_prompt = f'کاربر این پیام را فرستاده:\n"{text}"\n\nآیا این یک درخواست معتبر برای تولید کد برنامه‌نویسی هست؟ فقط با "yes" یا "no" جواب بده.'
        try:
            # Using a distinct ID for validation calls as requested
            reply = await call_api(check_prompt, "validator-check")
            # Simple check if "yes" (case-insensitive) is in the reply
            return "yes" in reply.lower()
        except Exception as e:
            print(f"Error during code related check: {e}")
            # Notify the user about the error during the check
            await event.respond(get_translation('error_generic', lang_code))
            return False # Default to false on error during check
# --- END: Replaced Function ---

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
    # Reset language preference, force re-selection on /start
    if user_id in user_interface_language: del user_interface_language[user_id]

    # Ask for language selection
    await event.respond(
        get_translation('start_choose_lang', 'fa'), # Initial prompt always shows language options
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
    await event.answer() # Acknowledge the button press

    # Show main menu in the selected language
    await show_main_menu(event, edit=True)


async def show_main_menu(event, edit=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_lang(user_id)

    buttons = [
        [Button.inline(get_translation('coding_button', lang_code), b"coding")],
        [Button.inline(get_translation('help_button', lang_code), b"help")],
        # خط اصلاح شده 👇
        [Button.url(get_translation('developer_button', lang_code), "https://t.me/n6xel")]
    ]
     # Add admin panel button only for the admin
    if user_id == admin_id:
        buttons.append([Button.inline(get_translation('admin_panel_button', lang_code), b"admin_panel")])

    text = get_translation('welcome', lang_code)

    try:
        if edit:
            # اطمینان حاصل کنید که دکمه‌ها قبل از ارسال به تابع edit معتبر هستند
            await event.edit(text, buttons=buttons)
        else:
            # اطمینان حاصل کنید که دکمه‌ها قبل از ارسال به تابع respond معتبر هستند
            await event.respond(text, buttons=buttons)
    except telethon.errors.rpcerrorlist.ButtonUrlInvalidError as e:
         print(f"Button URL Invalid Error showing main menu (edit={edit}): {e}")
         # می‌توانید اینجا یک پیام خطا به کاربر نشان دهید یا لاگ کنید
         # یا با دکمه‌های پیش‌فرض (بدون URL مشکل‌دار) مجدد تلاش کنید
         # Fallback if editing fails (e.g., message too old)
         await event.respond(text) # ارسال بدون دکمه یا با دکمه‌های امن
    except Exception as e:
        print(f"General Error showing main menu (edit={edit}): {e}")
        # Fallback if editing fails
        if edit:
             try:
                 await event.respond(text, buttons=buttons)
             except Exception as resp_e:
                 print(f"Error responding after edit failed: {resp_e}")
                 await event.respond(text) # نهایی‌ترین fallback بدون دکمه



@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def handle_coding_language_selection(event):
    user_id = event.sender_id
    if not bot_active and user_id != admin_id:
        await event.answer("Bot is currently disabled.", alert=True)
        return

    selected_lang = event.pattern_match.group(1).decode('utf-8')
    lang_code = await get_user_lang(user_id) # UI language

    if selected_lang in coding_languages:
        user_states[user_id] = selected_lang # Store the *coding* language state
        await event.answer(f"{selected_lang} selected!") # Quick feedback
        try:
            await event.edit(
                get_translation('coding_lang_selected', lang_code, lang=selected_lang),
                buttons=[
                    Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
                    Button.inline(get_translation('main_menu_button', lang_code), b"main_menu") # Added main menu return
                    ]
            )
        except Exception as e:
             print(f"Error editing after language selection: {e}")
             # Don't resend message here, answer is enough feedback
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

    try:
        await event.edit(
            help_message,
            buttons=[
                [Button.inline(get_translation('start_coding_button', lang_code), b"coding")],
                [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
            ]
        )
    except Exception as e:
        print(f"Error editing help message: {e}")
        await event.respond(help_message, buttons=[[Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]]) # Fallback

# --- Admin Panel ---

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    """Handles the /admin command to show the panel."""
    if event.sender_id == admin_id:
        # Reset admin state when explicitly calling /admin
        if admin_id in admin_states:
            del admin_states[admin_id]
        await show_admin_panel(event)
    else:
        lang_code = await get_user_lang(event.sender_id)
        await event.respond(get_translation('admin_not_allowed', lang_code))


@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    """Handles the callback button to show the panel."""
    if event.sender_id == admin_id:
         # Reset admin state when returning to panel via button
        if admin_id in admin_states:
            del admin_states[admin_id]
        await show_admin_panel(event, edit=True)
    else:
        # Ignore silently or show 'not allowed' message
        await event.answer(get_translation('admin_not_allowed', await get_user_lang(event.sender_id)), alert=True)


async def show_admin_panel(event, edit=False):
    """Displays the admin panel with buttons."""
    lang_code = await get_user_lang(admin_id) # Admin panel uses admin's language pref
    text = f"**{get_translation('admin_panel_title', lang_code)}**\n\n{get_translation('admin_panel_desc', lang_code)}\n`Bot Status: {'ON' if bot_active else 'OFF'}`"

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

    try:
        if edit:
            await event.edit(text, buttons=buttons, parse_mode='md')
        else:
             await event.respond(text, buttons=buttons, parse_mode='md')
    except Exception as e:
        print(f"Error showing admin panel (edit={edit}): {e}")
        # Fallback to sending a new message if edit fails
        if edit:
            await event.respond(text, buttons=buttons, parse_mode='md')


@client.on(events.CallbackQuery(data=b"admin_set_on"))
async def admin_turn_on(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = True
        lang_code = await get_user_lang(admin_id)
        await event.answer(get_translation('admin_bot_on_msg', lang_code), alert=True)
        # Update the panel message to reflect the new status
        await show_admin_panel(event, edit=True)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_lang(event.sender_id)), alert=True)


@client.on(events.CallbackQuery(data=b"admin_set_off"))
async def admin_turn_off(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = False
        lang_code = await get_user_lang(admin_id)
        await event.answer(get_translation('admin_bot_off_msg', lang_code), alert=True)
        # Update the panel message to reflect the new status
        await show_admin_panel(event, edit=True)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_lang(event.sender_id)), alert=True)


@client.on(events.CallbackQuery(data=b"admin_list_users"))
async def admin_list_users(event):
    if event.sender_id != admin_id:
        await event.answer(get_translation('admin_not_allowed', await get_user_lang(event.sender_id)), alert=True)
        return

    lang_code = await get_user_lang(admin_id)
    await event.answer("⏳ Fetching users...") # Give feedback

    back_button = [ Button.inline("🔙 Back to Admin Panel", b"admin_panel") ]

    try:
        async with aiosqlite.connect(db_file) as db:
            # Fetch users ordered by last seen, newest first
            async with db.execute("SELECT user_id, username, first_name, strftime('%Y-%m-%d %H:%M:%S', last_seen) FROM users ORDER BY last_seen DESC") as cursor:
                users = await cursor.fetchall()

        if not users:
            await event.edit(get_translation('admin_no_users', lang_code), buttons=[ back_button ])
            return

        user_list_text = get_translation('admin_list_users_title', lang_code, count=len(users))
        max_users_to_display = 50 # Limit display to avoid message length issues initially
        displayed_count = 0
        for user_id, username, first_name, last_seen in users:
            if displayed_count >= max_users_to_display:
                user_list_text += f"\n... (and {len(users) - displayed_count} more users)"
                break

            display_name = first_name if first_name else f"User_{user_id}"
            user_list_text += f"👤 `{user_id}` - @{username if username else 'N/A'} ({display_name}) - Seen: {last_seen}\n"
            displayed_count += 1

        # Handle potential message too long error (though limited display helps)
        if len(user_list_text) > 4000:
             user_list_text = user_list_text[:4000] + "\n... (list truncated due to length)"

        await event.edit(user_list_text, buttons=[ back_button ], parse_mode='md')

    except Exception as e:
        print(f"Error listing users: {e}")
        await event.edit(f"Error fetching users: {e}", buttons=[ back_button ])


@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_ask_broadcast(event):
    if event.sender_id == admin_id:
        lang_code = await get_user_lang(admin_id)
        admin_states[admin_id] = 'awaiting_broadcast_message' # Set admin state
        try:
            await event.edit(
                get_translation('admin_ask_broadcast', lang_code),
                buttons=[ Button.inline("🔙 Cancel", b"admin_panel") ] # Allow cancellation
            )
        except Exception as e:
            print(f"Error editing for broadcast prompt: {e}")
            await event.respond(get_translation('admin_ask_broadcast', lang_code), buttons=[ Button.inline("🔙 Cancel", b"admin_panel") ])
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_lang(event.sender_id)), alert=True)


# --- Main Message Handler ---

@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    user_input = event.text

    # Ignore empty messages or potential NoneType
    if not user_input:
        return

    user_input = user_input.strip()

    # 0. Ensure user is in DB and update last seen/details (Important for users interacting without /start first)
    # Note: This might run slightly redundantly if /start was just called, but it's harmless and ensures DB presence.
    await add_user_to_db(user_id)
    asyncio.create_task(update_user_details(user_id)) # Update details in background

    # 1. Handle Admin Broadcast Input FIRST
    if user_id == admin_id and admin_states.get(user_id) == 'awaiting_broadcast_message':
        lang_code = await get_user_lang(admin_id)
        broadcast_text = user_input # The message sent by admin is the broadcast content
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

        # ... (rest of broadcast logic remains the same) ...
        tasks = []
        for target_user_id in user_ids:
            async def send_to_user(uid, text):
                nonlocal sent_count, failed_count
                try:
                    await client.send_message(uid, text)
                    return True
                except Exception as e:
                    print(f"Failed to send broadcast to {uid}: {e}")
                    return False

            tasks.append(send_to_user(target_user_id, broadcast_text))
            if len(tasks) % 20 == 0:
                await asyncio.sleep(1)

        results = await asyncio.gather(*tasks)
        sent_count = sum(1 for r in results if r)
        failed_count = count - sent_count
        result_message = get_translation('admin_broadcast_sent', lang_code) + f" ({sent_count} successful)"
        if failed_count > 0:
            result_message += f"\n{get_translation('admin_broadcast_failed', lang_code)} ({failed_count} failures)"
        try:
            await status_message.edit(result_message)
        except Exception as e:
            print(f"Error editing broadcast status message: {e}")
            await event.respond(result_message)
        await asyncio.sleep(3)
        await show_admin_panel(event)
        return # Stop further processing


    # 2. Ignore messages if bot is off (except for admin)
    if not bot_active and user_id != admin_id:
        return

    # 3. Ignore ALL commands here (they should be handled by specific handlers like @client.on(events.NewMessage(pattern='/start')))
    # This prevents processing commands like /start or /admin in this general handler.
    if user_input.startswith('/'):
        return # Exit if it's any command, let specific handlers deal with them.


    # --- Now, handle regular text messages ---

    # 4. Handle cases where the user hasn't selected a language yet
    # This check should now ONLY run for non-command messages if the language isn't set.
    if user_id not in user_interface_language:
         await event.respond(
             get_translation('start_choose_lang', 'fa'), # Ask again
             buttons=[
                 [Button.inline("🇮🇷 فارسی", b"set_lang_fa"), Button.inline("🇬🇧 English", b"set_lang_en")],
                 [Button.inline("🇷🇺 Русский", b"set_lang_ru"), Button.inline("🇹🇷 Türkçe", b"set_lang_tr")]
             ]
         )
         return


    # 5. Handle Coding Requests (if user is in a coding state)
    if user_id in user_states:
        coding_lang = user_states[user_id]
        lang_code = await get_user_lang(user_id) # UI Language

        async with client.action(chat_id, "typing"):
            # --- Step 1: Validate if the message is code-related ---
            is_valid = await is_code_related(user_input, event)
            if not is_valid:
                if "validator-check" not in str(user_id):
                   await event.respond(get_translation('invalid_request', lang_code))
                return

            # --- Step 2: Construct prompt and call the main API ---
            prompt = f"Please generate ONLY the {coding_lang} code based on the following request. Do not include explanations, greetings, or markdown formatting like ``` unless it's part of the code itself.\n\nRequest:\n{user_input}"
            processing_msg = await event.respond(get_translation('processing', lang_code))
            response = await call_api(prompt, user_id)

            # --- Step 3: Process and Clean the Response ---
            cleaned_response = response
            if cleaned_response.startswith("Error getting response:") or cleaned_response.startswith("خطا در"):
                 await processing_msg.edit(cleaned_response)
                 return
            if cleaned_response.startswith("```") and cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[3:-3].strip()
                lines = cleaned_response.split('\n', 1)
                if len(lines) > 1 and lines[0].strip().lower() in [l.lower() for l in coding_languages + list(ext_map.values())]:
                    cleaned_response = lines[1].strip()
            if not cleaned_response:
                 await processing_msg.edit(get_translation('api_error', lang_code, e="API returned an empty response."))
                 return

            # --- Step 4: Send the result (file or message) ---
            # ... (rest of file/message sending logic remains the same) ...
            final_caption_or_message = ""
            buttons_after_code = [
                 Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
                 Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
            ]
            if len(cleaned_response) > 3900:
                ext = ext_map.get(coding_lang, "txt")
                safe_lang = ''.join(c for c in coding_lang if c.isalnum())
                filename = f"code_{safe_lang}_{user_id}.{ext}"
                try:
                    with open(filename, "w", encoding="utf-8") as f: f.write(cleaned_response)
                    final_caption_or_message = get_translation('code_too_long', lang_code, lang=coding_lang)
                    await client.send_file(event.chat_id, filename, caption=final_caption_or_message, buttons=buttons_after_code, reply_to=event.message.id)
                    await processing_msg.delete()
                except Exception as e:
                    print(f"Error sending file: {e}")
                    await processing_msg.edit(f"{get_translation('error_generic', lang_code)}\nError sending code as file: {e}")
                finally:
                    if os.path.exists(filename):
                        try: os.remove(filename)
                        except OSError as e: print(f"Error removing temporary file {filename}: {e}")
            else:
                formatted_response = f"```\n{cleaned_response}\n```"
                final_caption_or_message = f"{get_translation('code_ready', lang_code, lang=coding_lang)}\n{formatted_response}"
                try:
                    await processing_msg.edit(final_caption_or_message, buttons=buttons_after_code, parse_mode='md')
                except Exception as e:
                     print(f"Error editing final code message: {e}")
                     await event.respond(final_caption_or_message, buttons=buttons_after_code, parse_mode='md')
                     await processing_msg.delete()


    # 6. If message wasn't a command, wasn't broadcast input, language IS set, but user is NOT in a coding state:
    # This means the user sent random text after selecting a language but before selecting a coding language.
    elif user_id not in user_states: # Check if NOT in coding state
         lang_code = await get_user_lang(user_id)
         # Gently guide them to the coding section or main menu
         await event.respond(
             f"{get_translation('welcome', lang_code)}\n\nلطفاً از دکمه '{get_translation('coding_button', lang_code)}' برای شروع کدنویسی استفاده کنید یا به منوی اصلی بازگردید.",
             buttons=[
                 [Button.inline(get_translation('coding_button', lang_code), b"coding")],
                 [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
             ]
         )




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
        # Optional: Add indexes for faster lookups if needed
        # await db.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id);")
        # await db.execute("CREATE INDEX IF NOT EXISTS idx_last_seen ON users(last_seen);")
        await db.commit()
        print("Database initialized.")

    # Start the client
    await client.start()
    me = await client.get_me()
    print(f"Bot '{me.first_name}' started...")
    print(f"Admin ID: {admin_id}")
    print(f"Bot active: {bot_active}")
    print("Bot is running...")
    await client.run_until_disconnected()
    print("Bot stopped.")

if __name__ == '__main__':
    # Ensure necessary directories exist (if session file needs one)
    session_dir = os.path.dirname(session_name)
    if session_dir and not os.path.exists(session_dir):
        os.makedirs(session_dir)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopping via KeyboardInterrupt...")

