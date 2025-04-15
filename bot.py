# -*- coding: utf-8 -*-
from telethon import TelegramClient, events, Button
import aiosqlite
import json
import requests # Note: Using aiohttp for async requests now
import asyncio
import aiohttp
import os
import traceback # For better error logging

# --- Configuration ---
api_id = 18377832
api_hash = "ed8556c450c6d0fd68912423325dd09c"
session_name = "my_ai_multilang_v2"
admin_id = 7094106651 # <<< حتماً آیدی عددی ادمین را اینجا قرار دهید
db_file = "users_data_v2.db" # نام فایل دیتابیس جدید

# --- API Endpoints ---
GPT4_API_URL = "https://api.binjie.fun/api/generateStream"
LAMA_API_URL = "https://lama-ehsan.vercel.app/chat" # model in query param
GEMINI_API_URL = "https://gem-ehsan.vercel.app/gemini/chat" # model in query param

# --- Bot State ---
client = TelegramClient(session_name, api_id, api_hash)
bot_active = True
user_data = {} # Stores user-specific data: {user_id: {'ui_lang': 'fa', 'coding_lang': None, 'ai_model': 'gpt4', 'is_chatting': False, 'last_prompt': None}}
admin_states = {} # State for admin actions {admin_id: action}

# --- Bot Data ---
coding_languages = [
    "Laravel", "Python", "Java", "JavaScript", "C#", "C++", "C",
    "Swift", "Golang", "Rust", "Kotlin", "TypeScript", "PhP"
]

# Model Identifier: Display Name
available_ai_models = {
    "gpt4": "GPT-4 (Default)",
    "llama4-maverick": "Llama4 Maverick",
    "llama4-scout": "Llama4 Scout",
    "llama3-70b": "Llama3 70b",
    "llama3-8b": "Llama3 8b",
    "llama3-free": "Llama3 Free",
    "mixtral": "Mixtral",
    "gemma": "Gemma",
    "deepseek": "Deepseek",
    "gemini": "Gemini Pro" # Gemini API model identifier (can be 1 or 2 usually, let's assume 2 for this setup)
}
DEFAULT_AI_MODEL = "gpt4"

ext_map = {
    "Python": "py", "Java": "java", "JavaScript": "js", "C#": "cs", "C++": "cpp", "C": "c",
    "Swift": "swift", "Golang": "go", "Rust": "rs", "Kotlin": "kt", "TypeScript": "ts",
    "PhP": "php", "Laravel": "php"
}

# --- Multilingual Text (Updated) ---
translations = {
    'fa': {
        'start_welcome': 'start_welcome': "🌟 **سلام! خوش اومدی دوست عزیز 😊**\n\n🗣️ زبان پیش‌فرض: **فارسی** 🇮🇷\n\n⚙️ برای تغییر زبان یا تنظیمات دیگه، از دکمه‌ی 'Settings ⚙️' استفاده کن!\n\n✨ با آرزوی تجربه‌ای دلچسب و هوشمند ✨", # Welcome on first start
        'welcome': 'chat_welcome': "👋 **سلام، چطوری می‌تونم کمکت کنم؟** 😊\n🤖 مدل فعال: `{ai_model_name}`",
        'settings_button': "⚙️ تنظیمات",
        'coding_button': "🧬 کد نویسی",
        'chat_button': "💬 چت با AI",
        'help_button': "📚 راهنما",
        'developer_button': "🧑‍💻 ارتباط با توسعه دهنده",
        'main_menu_button': "🔙 برگشت به منوی اصلی",
        'settings_title': "⚙️ **تنظیمات ربات**",
        'settings_choose_lang': "زبان رابط کاربری را انتخاب کنید:",
        'settings_choose_model': "مدل هوش مصنوعی را برای کدنویسی و چت انتخاب کنید:",
        'settings_lang_button': "🌐 تغییر زبان",
        'settings_model_button': "🧠 انتخاب مدل AI",
        'settings_lang_selected': "✅ زبان به فارسی تغییر کرد.",
        'settings_model_selected': "✅ مدل AI به {model_name} تغییر کرد.",
        'choose_coding_lang': "💻 **لطفاً یکی از زبان‌های برنامه‌نویسی را انتخاب کن:** 🧠👇",
        'coding_lang_selected': "✅ زبان برنامه‌نویسی انتخاب‌شده: `{lang}`\n🤖 مدل هوش مصنوعی فعال: `{ai_model_name}`\n\n🧑‍💻 **حالا سوالت رو بپرس تا برات کدش رو بنویسم!** 🚀",
        'back_to_lang_menu': "زبان‌های دیگر",
        'back_to_settings': "🔙 بازگشت به تنظیمات",
        'processing': "⏳ **در حال پردازش... لطفاً چند لحظه صبر کن.**",
        'code_ready': "✅ **کدت آماده‌ست!**\n🧑‍💻 زبان: `{lang}` | 🤖 مدل: `{ai_model_name}`",
        'code_too_long': "📄 **کدت خیلی طولانی بود، به‌صورت فایل برات فرستادم.**\n🧑‍💻 زبان: `{lang}` | 🤖 مدل: `{ai_model_name}`",
        'new_question_button': "❓ سوال جدید ({lang})",
        'api_error': "خطا در ارتباط با API: {e}",
        'api_error_specific': "خطا در پردازش توسط مدل {model_name}: {e}",
        'empty_response_error': "مدل {model_name} پاسخی برنگرداند.",
        'invalid_request': "⚠️ **پیامت مربوط به برنامه‌نویسی نیست یا نمی‌تونم براش کدی بنویسم.**",
        'invalid_request_help': "📝 **راهنمایی:** لطفاً درخواستت رو واضح و مرتبط با تولید کد در زبان `{lang}` بنویس.\n\nمثال:\n`یک تابع پایتون بنویس که دو عدد رو با هم جمع کنه.`",
        'retry_button': "🔄 تلاش مجدد",
        'help_title': "**🌟 راهنمای استفاده از ربات 🌟**",
        'help_text': """
1️⃣ **انتخاب زبان برنامه‌نویسی**: روی دکمه '{coding_button}' کلیک کرده و یک زبان را انتخاب کنید.
2️⃣ **ارسال سوال**: سوال برنامه‌نویسی خود را بنویسید.
3️⃣ **دریافت کد**: ربات با استفاده از مدل AI انتخاب شده ({ai_model_name}) سعی می‌کند کد را بنویسد.
4️⃣ **چت با AI**: روی '{chat_button}' کلیک کنید و با مدل AI انتخاب شده صحبت کنید.
5️⃣ **تنظیمات**: از منوی '{settings_button}' زبان ربات و مدل AI را تغییر دهید.

⬅️ **بازگشت**: از دکمه‌های بازگشت استفاده کنید.

❗️ **توجه**: ربات در حالت کدنویسی فقط درخواست‌های مرتبط با برنامه‌نویسی را پردازش می‌کند.

💡 لذت ببرید!
        """,
        'start_coding_button': "🏁 شروع کدنویسی!",
        'start_chat_prompt': "✅ بسیار خب! حالا می‌تونی با مدل {ai_model_name} چت کنی. پیامت رو بفرست.",
        'stop_chat_button': "⏹️ پایان چت (منوی اصلی)",
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
        'admin_list_users_title': "**👥 لیست کاربران ربات ({count} نفر):**\n{user_list}", # Placeholder for list
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Username:_ @{username}\n   _Name:_ {name}\n--------------------", # User entry format
        'admin_no_users': "**هنوز هیچ کاربری در دیتابیس ثبت نشده است.**",
        'admin_not_allowed': "**شما اجازه دسترسی به این بخش را ندارید.**",
        'error_generic': "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
        'admin_panel_button': "⚙️ پنل مدیریت",
        'back_button': "🔙 بازگشت"
    },
    'en'
        'start_welcome': "**Hello! Welcome.**\nThe default language is English. Use the 'Settings' button to change the language or other configurations.",
        'welcome': "**Hello, how can I help you?**\nActive Model: {ai_model_name}",
        'settings_button': "⚙️ Settings",
        'coding_button': "🧬 Coding",
        'chat_button': "💬 Chat with AI",
        'help_button': "📚 Help",
        'developer_button': "🧑‍💻 Contact Developer",
        'main_menu_button': "🔙 Back to Main Menu",
        'settings_title': "⚙️ **Bot Settings**",
        'settings_choose_lang': "Select Interface Language:",
        'settings_choose_model': "Select AI Model for Coding & Chat:",
        'settings_lang_button': "🌐 Change Language",
        'settings_model_button': "🧠 Select AI Model",
        'settings_lang_selected': "✅ Language changed to English.",
        'settings_model_selected': "✅ AI Model changed to {model_name}.",
        'choose_coding_lang': "**Please choose a programming language:**",
        'coding_lang_selected': "Language: {lang}\nAI Model: {ai_model_name}\n\n**Ask your question, and I'll write the code.**",
        'back_to_lang_menu': "Other Languages",
        'back_to_settings': "🔙 Back to Settings",
        'processing': "**Processing... Please wait.**",
        'code_ready': "Your code is ready (Language: {lang}, Model: {ai_model_name})",
        'code_too_long': "Your code is ready and sent as a file (Language: {lang}, Model: {ai_model_name})",
        'new_question_button': "❓ New Question ({lang})",
        'api_error': "Error connecting to API: {e}",
        'api_error_specific': "Error processing with model {model_name}: {e}",
        'empty_response_error': "Model {model_name} returned an empty response.",
        'invalid_request': "**Your message isn't related to programming, or I can't write code for it.**",
        'invalid_request_help': "**Tip:** Please state your request clearly and related to code generation in '{lang}'. For example:\n`Write a Python function that sums two numbers.`",
        'retry_button': "🔄 Retry",
        'help_title': "**🌟 Bot Usage Guide 🌟**",
        'help_text': """
1️⃣ **Select Programming Language**: Click '{coding_button}' and choose a language.
2️⃣ **Send Question**: Write your programming question.
3️⃣ **Receive Code**: The bot will try to write code using the selected AI model ({ai_model_name}).
4️⃣ **Chat with AI**: Click '{chat_button}' to talk with the selected AI model.
5️⃣ **Settings**: Use the '{settings_button}' menu to change the bot language and AI model.

⬅️ **Navigate**: Use the back buttons.

❗️ **Note**: In coding mode, the bot only processes programming-related requests.

💡 Enjoy!
        """,
        'start_coding_button': "🏁 Start Coding!",
        'start_chat_prompt': "✅ Alright! You can now chat with {ai_model_name}. Send your message.",
        'stop_chat_button': "⏹️ Stop Chat (Main Menu)",
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
        'admin_list_users_title': "**👥 Bot Users List ({count} total):**\n{user_list}", # Placeholder for list
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Username:_ @{username}\n   _Name:_ {name}\n--------------------", # User entry format
        'admin_no_users': "**No users found in the database yet.**",
        'admin_not_allowed': "**You do not have permission to access this section.**",
        'error_generic': "An error occurred. Please try again.",
        'admin_panel_button': "⚙️ Admin Panel",
        'back_button': "🔙 Back"

    },
    # Add 'ru' and 'tr' translations similarly, adding the new keys
    'ru': {
        # ... (previous translations) ...
        'start_welcome': "**Здравствуйте! Добро пожаловать.**\nЯзык по умолчанию - английский. Используйте кнопку 'Настройки', чтобы изменить язык или другие параметры.",
        'welcome': "**Здравствуйте, чем я могу вам помочь?**\nАктивная модель: {ai_model_name}",
        'settings_button': "⚙️ Настройки",
        'coding_button': "🧬 Кодинг",
        'chat_button': "💬 Чат с ИИ",
        'settings_title': "⚙️ **Настройки бота**",
        'settings_choose_lang': "Выберите язык интерфейса:",
        'settings_choose_model': "Выберите модель ИИ для кодинга и чата:",
        'settings_lang_button': "🌐 Сменить язык",
        'settings_model_button': "🧠 Выбрать модель ИИ",
        'settings_lang_selected': "✅ Язык изменен на Русский.",
        'settings_model_selected': "✅ Модель ИИ изменена на {model_name}.",
        'coding_lang_selected': "Язык: {lang}\nМодель ИИ: {ai_model_name}\n\n**Задайте свой вопрос, и я напишу код.**",
        'back_to_settings': "🔙 Назад к настройкам",
        'code_ready': "Ваш код готов (Язык: {lang}, Модель: {ai_model_name})",
        'code_too_long': "Ваш код готов и отправлен в виде файла (Язык: {lang}, Модель: {ai_model_name})",
        'new_question_button': "❓ Новый вопрос ({lang})",
        'api_error_specific': "Ошибка при обработке моделью {model_name}: {e}",
        'empty_response_error': "Модель {model_name} вернула пустой ответ.",
        'invalid_request_help': "**Подсказка:** Пожалуйста, сформулируйте ваш запрос четко и по теме генерации кода на '{lang}'. Например:\n`Напиши функцию на Python, которая суммирует два числа.`",
        'retry_button': "🔄 Попробовать снова",
        'help_text': """
1️⃣ **Выберите язык программирования**: Нажмите '{coding_button}' и выберите язык.
2️⃣ **Отправьте вопрос**: Напишите ваш вопрос по программированию.
3️⃣ **Получите код**: Бот попытается написать код, используя выбранную модель ИИ ({ai_model_name}).
4️⃣ **Чат с ИИ**: Нажмите '{chat_button}', чтобы поговорить с выбранной моделью ИИ.
5️⃣ **Настройки**: Используйте меню '{settings_button}', чтобы изменить язык бота и модель ИИ.

⬅️ **Навигация**: Используйте кнопки возврата.

❗️ **Примечание**: В режиме кодинга бот обрабатывает только запросы, связанные с программированием.

💡 Удачи!
        """,
        'start_chat_prompt': "✅ Хорошо! Теперь вы можете общаться с {ai_model_name}. Отправьте свое сообщение.",
        'stop_chat_button': "⏹️ Закончить чат (Главное меню)",
        'admin_list_users_title': "**👥 Список пользователей бота ({count} всего):**\n{user_list}",
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Имя пользователя:_ @{username}\n   _Имя:_ {name}\n   _Замечен:_ {last_seen}\n--------------------",
        'back_button': "🔙 Назад"
        # ... (Add other new/modified keys for ru)
    },
    'tr': {
         # ... (previous translations) ...
        'start_welcome': "**Merhaba! Hoş geldiniz.**\nVarsayılan dil İngilizce'dir. Dili veya diğer ayarları değiştirmek için 'Ayarlar' düğmesini kullanın.",
        'welcome': "**Merhaba, size nasıl yardımcı olabilirim?**\nAktif Model: {ai_model_name}",
        'settings_button': "⚙️ Ayarlar",
        'coding_button': "🧬 Kodlama",
        'chat_button': "💬 AI ile Sohbet",
        'settings_title': "⚙️ **Bot Ayarları**",
        'settings_choose_lang': "Arayüz Dilini Seçin:",
        'settings_choose_model': "Kodlama ve Sohbet için AI Modelini Seçin:",
        'settings_lang_button': "🌐 Dili Değiştir",
        'settings_model_button': "🧠 AI Modeli Seç",
        'settings_lang_selected': "✅ Dil Türkçe olarak değiştirildi.",
        'settings_model_selected': "✅ AI Modeli {model_name} olarak değiştirildi.",
        'coding_lang_selected': "Dil: {lang}\nAI Modeli: {ai_model_name}\n\n**Sorunuzu sorun, kodunu yazayım.**",
        'back_to_settings': "🔙 Ayarlara Geri Dön",
        'code_ready': "Kodunuz hazır (Dil: {lang}, Model: {ai_model_name})",
        'code_too_long': "Kodunuz hazır ve dosya olarak gönderildi (Dil: {lang}, Model: {ai_model_name})",
        'new_question_button': "❓ Yeni Soru ({lang})",
        'api_error_specific': "{model_name} modeli ile işlenirken hata oluştu: {e}",
        'empty_response_error': "{model_name} modeli boş yanıt döndürdü.",
        'invalid_request_help': "**İpucu:** Lütfen isteğinizi '{lang}' dilinde kod üretimiyle ilgili açıkça belirtin. Örneğin:\n`İki sayıyı toplayan bir Python fonksiyonu yaz.`",
        'retry_button': "🔄 Tekrar Dene",
        'help_text': """
1️⃣ **Programlama Dilini Seçin**: '{coding_button}' düğmesine tıklayın ve bir dil seçin.
2️⃣ **Soru Gönderin**: Programlama sorunuzu yazın.
3️⃣ **Kodu Alın**: Bot, seçilen AI modelini ({ai_model_name}) kullanarak kod yazmaya çalışacaktır.
4️⃣ **AI ile Sohbet**: Seçilen AI modeliyle konuşmak için '{chat_button}' düğmesine tıklayın.
5️⃣ **Ayarlar**: Bot dilini ve AI modelini değiştirmek için '{settings_button}' menüsünü kullanın.

⬅️ **Gezinme**: Geri düğmelerini kullanın.

❗️ **Not**: Kodlama modunda, bot yalnızca programlamayla ilgili istekleri işler.

💡 Keyfini çıkarın!
        """,
        'start_chat_prompt': "✅ Tamam! Şimdi {ai_model_name} ile sohbet edebilirsiniz. Mesajınızı gönderin.",
        'stop_chat_button': "⏹️ Sohbeti Durdur (Ana Menü)",
        'admin_list_users_title': "**👥 Bot Kullanıcı Listesi (toplam {count}):**\n{user_list}",
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Kullanıcı Adı:_ @{username}\n   _İsim:_ {name}\n   _Görülme:_ {last_seen}\n--------------------",
        'back_button': "🔙 Geri"
        # ... (Add other new/modified keys for tr)
    }
}

# --- Database Functions ---
async def initialize_database():
    """Initializes the database and table schema."""
    async with aiosqlite.connect(db_file) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                ui_lang TEXT DEFAULT 'fa',
                selected_ai_model TEXT DEFAULT 'gpt4',
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        print("Database initialized.")

async def fetch_user_data_from_db(user_id):
    """Fetches user data from DB. Returns None if not found."""
    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT ui_lang, selected_ai_model FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {'ui_lang': row[0], 'selected_ai_model': row[1]}
                return None
    except Exception as e:
        print(f"DB Error fetching user data for {user_id}: {e}")
        return None

async def add_or_update_user_in_db(user_id, username=None, first_name=None):
    """Adds a new user or updates existing user's details and last_seen."""
    current_time = asyncio.get_event_loop().time() # Use event loop time for consistency
    try:
        async with aiosqlite.connect(db_file) as db:
            # Insert or ignore if user doesn't exist, setting defaults
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, ui_lang, selected_ai_model, last_seen)
                VALUES (?, ?, ?, 'fa', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO NOTHING;
            """, (user_id, username, first_name, DEFAULT_AI_MODEL))

            # Always update username, first_name (if provided) and last_seen for existing users
            update_query = "UPDATE users SET last_seen = CURRENT_TIMESTAMP"
            params = []
            if username is not None:
                update_query += ", username = ?"
                params.append(username)
            if first_name is not None:
                update_query += ", first_name = ?"
                params.append(first_name)
            update_query += " WHERE user_id = ?"
            params.append(user_id)

            await db.execute(update_query, tuple(params))
            await db.commit()
    except Exception as e:
        print(f"DB Error in add_or_update_user_in_db for {user_id}: {e}")
        traceback.print_exc()


async def update_user_db_field(user_id, field, value):
    """Updates a specific field for a user in the database."""
    allowed_fields = ['ui_lang', 'selected_ai_model'] # Prevent SQL injection
    if field not in allowed_fields:
        print(f"Attempted to update disallowed field: {field}")
        return
    try:
        async with aiosqlite.connect(db_file) as db:
            await db.execute(f"UPDATE users SET {field} = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?", (value, user_id))
            await db.commit()
    except Exception as e:
        print(f"DB Error updating field {field} for user {user_id}: {e}")

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


# --- Helper Functions ---
def get_translation(key, lang_code='fa', **kwargs):
    """Gets the translated string, defaulting to English."""
    return translations.get(lang_code, translations['fa']).get(key, f"[{key}]").format(**kwargs)

async def get_user_pref(user_id, key, default_value=None):
    """Gets a specific preference for a user, fetching from DB if not in memory."""
    if user_id not in user_data:
        db_data = await fetch_user_data_from_db(user_id)
        if db_data:
            user_data[user_id] = {
                'ui_lang': db_data['ui_lang'],
                'coding_lang': None, # Runtime state
                'ai_model': db_data['selected_ai_model'],
                'is_chatting': False, # Runtime state
                'last_prompt': None # Runtime state
            }
        else:
            # User not in DB yet, use defaults (will be added by add_or_update_user_in_db)
            user_data[user_id] = {
                'ui_lang': 'fa',
                'coding_lang': None,
                'ai_model': DEFAULT_AI_MODEL,
                'is_chatting': False,
                'last_prompt': None
            }
            # Attempt to add them now
            await add_or_update_user_in_db(user_id)


    return user_data.get(user_id, {}).get(key, default_value)

async def set_user_pref(user_id, key, value):
    """Sets a user preference in memory and updates the DB if applicable."""
    if user_id not in user_data:
        await get_user_pref(user_id, 'ui_lang') # Ensure user_data[user_id] exists

    user_data[user_id][key] = value

    # Persist relevant preferences to DB
    if key in ['ui_lang', 'selected_ai_model']:
        await update_user_db_field(user_id, key, value)

# --- API Calling Functions ---

async def call_gpt4_api(prompt, user_id_str):
    """Calls the original GPT-4 API."""
    headers = {
        "authority": "api.binjie.fun", "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9", "origin": "https://chat18.aichatos.xyz",
        "referer": "https://chat18.aichatos.xyz/", "user-agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }
    code_prompt = "فقط کد رو بده تاکید می کنم فقط کد"
    ehsan_prompt = code_prompt + prompt
    data = {
        "prompt": ehsan_prompt, "userId": f"#/{user_id_str}", "network": True,
        "system": "", "withoutContext": False, "stream": False
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GPT4_API_URL, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=45)) as response:
                response.raise_for_status() # Raise error for bad responses (4xx or 5xx)
                text = await response.text()
                return text.strip()
    except aiohttp.ClientResponseError as e:
        print(f"GPT4 API HTTP Error: {e.status} - {e.message}")
        return f"API_ERROR: HTTP {e.status}"
    except asyncio.TimeoutError:
        print("GPT4 API Timeout")
        return "API_ERROR: Timeout"
    except Exception as e:
        print(f"GPT4 API Error: {e}")
        traceback.print_exc()
        return f"API_ERROR: {e}"

async def call_lama_api(prompt, model_id):
    """Calls the Llama API correctly with POST and JSON body."""
    
    code_prompt = "فقط کد رو بده تاکید می کنم فقط کد"
    ehsan_prompt = code_prompt + prompt

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model_id,
                "prompt": ehsan_prompt
            }
            async with session.post(
                LAMA_API_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=45)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get('response', '').strip()
    except aiohttp.ClientResponseError as e:
        print(f"Llama API ({model_id}) HTTP Error: {e.status} - {e.message}")
        return f"API_ERROR: HTTP {e.status}"
    except asyncio.TimeoutError:
        print(f"Llama API ({model_id}) Timeout")
        return "API_ERROR: Timeout"
    except Exception as e:
        print(f"Llama API ({model_id}) Error: {e}")
        traceback.print_exc()
        return f"API_ERROR: {e}"

async def call_gemini_api(prompt, model_param="2"):  # Default model
    """Calls the Gemini API."""
    code_prompt = "فقط کد رو بده تاکید می کنم فقط کد"
    ehsan_prompt = code_prompt + prompt
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_API_URL,
                json={'prompt': ehsan_prompt, 'model': model_param},
                timeout=aiohttp.ClientTimeout(total=45)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get('result', '').strip()  # یا response یا result، بسته به پاسخ سرور
    except aiohttp.ClientResponseError as e:
        print(f"Gemini API HTTP Error: {e.status} - {e.message}")
        return f"API_ERROR: HTTP {e.status}"
    except asyncio.TimeoutError:
        print("Gemini API Timeout")
        return "API_ERROR: Timeout"
    except Exception as e:
        print(f"Gemini API Error: {e}")
        traceback.print_exc()
        return f"API_ERROR: {e}"


async def call_selected_api(prompt, user_id, is_coding_request=False):
    """Calls the appropriate API based on user's selection."""
    model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    model_name = available_ai_models.get(model_id, "Unknown Model")
    user_id_str = str(user_id) # For GPT-4 API

    print(f"User {user_id} calling API. Model: {model_id}, Coding: {is_coding_request}")

    if model_id == "gpt4":
        # Refine prompt slightly for GPT-4 coding
        if is_coding_request:
             coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
             api_prompt = f"Please generate ONLY the {coding_lang} code based on the following request. Do not include explanations, greetings, or markdown formatting like ``` unless it's part of the code itself.\n\nRequest:\n{prompt}"
        else:
             api_prompt = prompt # General chat prompt
        response = await call_gpt4_api(api_prompt, user_id_str)

    elif model_id.startswith("llama") or model_id in ["mixtral", "gemma", "deepseek"]:
        # Lama API - model ID is passed as a parameter
        # Assume these models understand direct prompts well for both chat & code
        api_prompt = prompt
        if is_coding_request:
            coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
            # You might want to add context for coding here if needed
            # api_prompt = f"Generate {coding_lang} code for: {prompt}"
        response = await call_lama_api(api_prompt, model_id)

    elif model_id == "gemini":
        # Gemini API - model param might be fixed (e.g., "2") or dynamic
        api_prompt = prompt
        if is_coding_request:
            coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
            # api_prompt = f"Generate {coding_lang} code for: {prompt}"
        response = await call_gemini_api(api_prompt, model_param="2") # Using fixed model param "2"

    else:
        print(f"Unknown model selected: {model_id}")
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        return get_translation('error_generic', lang_code) + f" (Unknown Model: {model_id})"

    # --- Process API Response ---
    if isinstance(response, str) and response.startswith("API_ERROR:"):
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        error_detail = response.split(":", 1)[1].strip()
        return get_translation('api_error_specific', lang_code, model_name=model_name, e=error_detail)
    elif not response: # Empty response
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        return get_translation('empty_response_error', lang_code, model_name=model_name)
    else:
        # Basic cleaning (can be enhanced)
        cleaned_response = response
        # Remove markdown code blocks if they wrap the entire response (common issue)
        if cleaned_response.startswith("```") and cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[3:-3].strip()
            # Remove potential language hint line (e.g., ```python)
            lines = cleaned_response.split('\n', 1)
            if len(lines) > 1 and lines[0].strip().lower() in [l.lower() for l in coding_languages + list(ext_map.values())]:
                cleaned_response = lines[1].strip()

        return cleaned_response


async def is_code_related(text, event, coding_lang):
    """Checks if the user prompt seems like a valid coding request."""
    user_id = event.sender_id
    # Use the user's selected AI model for validation for consistency
    # Using a simple internal prompt for validation
    check_prompt = f'Analyze the following user request for "{coding_lang}" programming:\n"{text}"\n\nIs this a request to write or explain code? Answer ONLY with "yes" or "no".'

    try:
        async with client.action(event.chat_id, "typing"):
            # Use the selected API for the check
            reply = await call_selected_api(check_prompt, user_id, is_coding_request=False) # Treat check as non-coding request

            if isinstance(reply, str) and reply.startswith("API_ERROR:") or not reply :
                 print(f"Validation API Error or empty response: {reply}")
                 # Fallback: Assume it *might* be code related if API fails validation
                 return True # Default to attempting code generation on validation failure

            print(f"Validation check for '{text}' -> API Reply: '{reply}'")
            return "yes" in reply.lower()
    except Exception as e:
        print(f"Error during code-related check: {e}")
        traceback.print_exc()
        # Fallback on unexpected error during validation
        return True # Let it proceed if validation check itself errors out

# --- Event Handlers ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name

    # Add/Update user in DB and ensure local cache is populated
    await add_or_update_user_in_db(user_id, username, first_name)
    await get_user_pref(user_id, 'ui_lang') # Load/initialize data in user_data dict

    # Reset runtime states
    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'is_chatting', False)
    await set_user_pref(user_id, 'last_prompt', None)
    if user_id in admin_states: del admin_states[user_id]

    # Show main menu (defaults to English initially as per DB default)
    await show_main_menu(event, edit=False, first_start=True)


async def show_main_menu(event, edit=False, first_start=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    buttons = [
        [Button.inline(get_translation('settings_button', lang_code), b"settings"),
         Button.inline(get_translation('coding_button', lang_code), b"coding")],
        [Button.inline(get_translation('help_button', lang_code), b"help")],
        [Button.url(get_translation('developer_button', lang_code), "https://t.me/n6xel")]
    ]
    if user_id == admin_id:
        buttons.append([Button.inline(get_translation('admin_panel_button', lang_code), b"admin_panel")])

    if first_start:
        text = get_translation('start_welcome', lang_code) # Special welcome on first /start
    else:
        text = get_translation('welcome', lang_code, ai_model_name=ai_model_name)

    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing main menu ({'edit' if edit else 'respond'}): {e}")
        if edit: # If edit fails, try responding
             await event.respond(text, buttons=buttons)


@client.on(events.CallbackQuery(data=b"main_menu"))
async def return_to_main_menu(event):
    user_id = event.sender_id
    # Reset potentially active states when returning to main menu
    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'is_chatting', False)
    await set_user_pref(user_id, 'last_prompt', None)
    await show_main_menu(event, edit=True)

# --- Settings Menu ---

@client.on(events.CallbackQuery(data=b"settings"))
async def show_settings_menu(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    buttons = [
        [Button.inline(get_translation('settings_lang_button', lang_code), b"change_ui_lang")],
        [Button.inline(get_translation('settings_model_button', lang_code), b"select_ai_model")],
        [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
    ]
    text = get_translation('settings_title', lang_code)
    await event.edit(text, buttons=buttons)


@client.on(events.CallbackQuery(data=b"change_ui_lang"))
async def show_ui_language_options(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    buttons = [
        # Add flags for visual appeal
        [Button.inline("🇬🇧 English", b"set_lang_en")],
        [utton.inline("🇮🇷 فارسی", b"set_lang_fa")],
        [Button.inline(get_translation('back_to_settings', lang_code), b"settings")]
    ]
    text = get_translation('settings_choose_lang', lang_code)
    await event.edit(text, buttons=buttons)


@client.on(events.CallbackQuery(pattern=b"set_lang_(.*)"))
async def set_ui_language(event):
    user_id = event.sender_id
    new_lang_code = event.pattern_match.group(1).decode('utf-8')

    if new_lang_code in translations:
        await set_user_pref(user_id, 'ui_lang', new_lang_code)
        await event.answer(get_translation('settings_lang_selected', new_lang_code), alert=True)
        # Go back to settings menu after selection
        await show_settings_menu(event) # Will use the new language now
    else:
        await event.answer("Invalid language code.", alert=True)


@client.on(events.CallbackQuery(data=b"select_ai_model"))
async def show_ai_model_options(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    current_model = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)

    buttons = []
    temp_row = []
    for model_id, display_name in available_ai_models.items():
        prefix = "➡️ " if model_id == current_model else ""
        temp_row.append(Button.inline(f"{prefix}{display_name}", f"set_model_{model_id}".encode()))
        if len(temp_row) == 2: # Two models per row
            buttons.append(temp_row)
            temp_row = []
    if temp_row: # Add remaining button if odd number
        buttons.append(temp_row)

    buttons.append([Button.inline(get_translation('back_to_settings', lang_code), b"settings")])
    text = get_translation('settings_choose_model', lang_code)
    await event.edit(text, buttons=buttons)


@client.on(events.CallbackQuery(pattern=b"set_model_(.*)"))
async def set_ai_model(event):
    user_id = event.sender_id
    model_id = event.pattern_match.group(1).decode('utf-8')

    if model_id in available_ai_models:
        await set_user_pref(user_id, 'selected_ai_model', model_id)
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        model_name = available_ai_models[model_id]
        await event.answer(get_translation('settings_model_selected', lang_code, model_name=model_name), alert=True)
        # Go back to settings menu
        await show_settings_menu(event)
    else:
        await event.answer("Invalid AI model selected.", alert=True)


# --- Coding Flow ---

@client.on(events.CallbackQuery(data=b'coding'))
async def choose_coding_language(event):
    if not bot_active and event.sender_id != admin_id:
        await event.answer("Bot is currently inactive.", alert=True)
        return

    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    rows = []
    temp_row = []
    for lang in coding_languages:
        temp_row.append(Button.inline(lang, f"select_code_{lang}".encode()))
        if len(temp_row) == 2: # Two languages per row
            rows.append(temp_row)
            temp_row = []
    if temp_row:
        rows.append(temp_row)

    rows.append([Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")])

    await event.edit(
        get_translation('choose_coding_lang', lang_code),
        buttons=rows
    )
    # Ensure user is not in chat mode when entering coding selection
    await set_user_pref(user_id, 'is_chatting', False)
    # Clear any previous coding language selection here? No, wait for selection.


@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def handle_coding_language_selection(event):
    user_id = event.sender_id
    if not bot_active and user_id != admin_id:
        await event.answer("Bot is currently inactive.", alert=True)
        return

    selected_lang = event.pattern_match.group(1).decode('utf-8')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa') # UI language
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")


    if selected_lang in coding_languages:
        await set_user_pref(user_id, 'coding_lang', selected_lang) # Store the *coding* language state
        await set_user_pref(user_id, 'is_chatting', False) # Ensure not in chat mode
        await set_user_pref(user_id, 'last_prompt', None) # Clear last prompt on new selection

        await event.edit(
            get_translation('coding_lang_selected', lang_code, lang=selected_lang, ai_model_name=ai_model_name),
            buttons=[
                Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
                Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
                ]
        )
    else:
         await event.answer("Invalid language selected.", alert=True)


# --- Chat Flow ---

@client.on(events.CallbackQuery(data=b"start_chat"))
async def start_chatting(event):
    user_id = event.sender_id
    if not bot_active and user_id != admin_id:
        await event.answer("Bot is currently inactive.", alert=True)
        return

    await event.answer()
    await set_user_pref(user_id, 'is_chatting', True)
    await set_user_pref(user_id, 'coding_lang', None) # Exit coding mode
    await set_user_pref(user_id, 'last_prompt', None)

    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    await event.edit(
        get_translation('start_chat_prompt', lang_code, ai_model_name=ai_model_name),
        buttons=[Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")] # Only show stop button
    )


@client.on(events.CallbackQuery(data=b"stop_chat"))
async def stop_chatting(event):
    user_id = event.sender_id
    await event.answer()
    await set_user_pref(user_id, 'is_chatting', False)
    # Go back to main menu
    await show_main_menu(event, edit=True)


# --- Help ---

@client.on(events.CallbackQuery(data=b"help"))
async def show_help(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    # Format help text with dynamic button names and model name
    help_message = get_translation('help_title', lang_code) + "\n\n" + \
                   get_translation('help_text', lang_code,
                                   coding_button=get_translation('coding_button', lang_code),
                                   chat_button=get_translation('chat_button', lang_code),
                                   settings_button=get_translation('settings_button', lang_code),
                                   ai_model_name=ai_model_name)

    await event.edit(
        help_message,
        buttons=[
            [Button.inline(get_translation('start_coding_button', lang_code), b"coding")],
             #Button.inline(get_translation('chat_button', lang_code), b"start_chat")],
            [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
        ]
    )

# --- Admin Panel ---

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if event.sender_id == admin_id:
        # Ensure admin user data is loaded/initialized
        await get_user_pref(admin_id, 'ui_lang')
        await show_admin_panel(event)
    else:
        lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'fa')
        await event.respond(get_translation('admin_not_allowed', lang_code))

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if event.sender_id == admin_id:
        await show_admin_panel(event, edit=True)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_pref(event.sender_id, 'ui_lang', 'fa')), alert=True)


async def show_admin_panel(event, edit=False):
    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa') # Admin panel uses admin's language pref
    text = f"**{get_translation('admin_panel_title', lang_code)}**\n\n{get_translation('admin_panel_desc', lang_code)}"
    bot_status = get_translation('admin_off', lang_code) if not bot_active else get_translation('admin_on', lang_code)

    buttons = [
        [ # Show current status and action to toggle
             Button.inline(f"{'✅ Turn ON' if not bot_active else '❌ Turn OFF'} ({'Currently OFF' if not bot_active else 'Currently ON'})",
                           b"admin_toggle_status")
        ],
        [
            Button.inline(get_translation('admin_broadcast', lang_code), b"admin_broadcast"),
            Button.inline(get_translation('admin_list_users', lang_code), b"admin_list_users")
        ],
        [ Button.inline(get_translation('main_menu_button', lang_code), b"main_menu") ]
    ]

    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing admin panel ({'edit' if edit else 'respond'}): {e}")
        if edit: await event.respond(text, buttons=buttons) # Fallback if edit fails


@client.on(events.CallbackQuery(data=b"admin_toggle_status"))
async def admin_toggle_bot_status(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = not bot_active
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        status_msg = get_translation('admin_bot_on_msg', lang_code) if bot_active else get_translation('admin_bot_off_msg', lang_code)
        await event.answer(status_msg, alert=True)
        # Update the panel to reflect the new status
        await show_admin_panel(event, edit=True)
    else:
        await event.answer()


@client.on(events.CallbackQuery(data=b"admin_list_users"))
async def admin_list_users(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    await event.answer("⏳ Fetching users...")

    try:
        async with aiosqlite.connect(db_file) as db:
            # Fetch more details for a richer list
            async with db.execute("SELECT user_id, username, first_name, ui_lang, selected_ai_model, last_seen FROM users ORDER BY last_seen DESC") as cursor:
                users = await cursor.fetchall()

        if not users:
            await event.edit(get_translation('admin_no_users', lang_code), buttons=[ Button.inline(get_translation('back_button', lang_code), b"admin_panel") ])
            return

        user_list_parts = []
        for user_id, username, first_name, uilang, model, last_seen_ts in users:
            # Format user details cleanly
            display_name = first_name if first_name else "N/A"
            username_str = username if username else "N/A"
            # Format timestamp nicely
            try:
                 # Assuming timestamp is stored like 'YYYY-MM-DD HH:MM:SS.ffffff' or similar
                 last_seen_str = last_seen_ts.split('.')[0] if isinstance(last_seen_ts, str) else str(last_seen_ts) # Basic format
            except:
                 last_seen_str = "N/A"

            model_name = available_ai_models.get(model, model) # Show ID if name not found

            user_entry = get_translation('admin_user_entry', lang_code,
                                         user_id=user_id,
                                         username=username_str,
                                         name=display_name,
                                         last_seen=last_seen_str)
            # Optionally add lang and model:
            # user_entry += f"   Lang: {uilang}, Model: {model_name}\n--------------------"
            user_list_parts.append(user_entry)


        full_user_list = "\n".join(user_list_parts)
        title = get_translation('admin_list_users_title', lang_code, count=len(users), user_list="") # Get title format
        final_text = title + "\n" + full_user_list

        # Handle message length limits
        if len(final_text) > 4000:
             # Truncate smartly, ensuring we don't cut mid-user-entry
             truncated_list = "\n".join(user_list_parts[:len(users)//2]) # Example: show first half
             final_text = title + "\n" + truncated_list + "\n\n... (list truncated due to length)"

        await event.edit(final_text, buttons=[ Button.inline(get_translation('back_button', lang_code), b"admin_panel") ], parse_mode='markdown') # Use Markdown for formatting

    except Exception as e:
        print(f"Error listing users: {e}")
        traceback.print_exc()
        await event.edit(f"Error fetching users: {e}", buttons=[ Button.inline(get_translation('back_button', lang_code), b"admin_panel") ])


@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_ask_broadcast(event):
    if event.sender_id == admin_id:
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        admin_states[admin_id] = 'awaiting_broadcast_message'
        await event.edit(
            get_translation('admin_ask_broadcast', lang_code),
            buttons=[ Button.inline(f"🔙 {get_translation('back_button', lang_code)}", b"admin_panel") ]
        )
    else:
        await event.answer()

# --- Retry Logic ---
@client.on(events.CallbackQuery(data=b"retry_last_prompt"))
async def retry_last_prompt_handler(event):
    user_id = event.sender_id
    last_prompt = await get_user_pref(user_id, 'last_prompt')
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    if not last_prompt or not coding_lang:
        await event.answer("No prompt to retry or coding language not set.", alert=True)
        return

    await event.answer("🔄 Retrying...")
    # Simulate receiving the message again to trigger the main handler's coding logic
    # We need to pass a mock 'event' or directly call the processing logic
    # For simplicity, let's reuse parts of the handle_message logic here

    processing_msg = await event.respond(get_translation('processing', lang_code))
    await process_coding_request(event, last_prompt, processing_msg) # Pass event for context (chat_id etc)


# --- Main Message Processing Logic ---

async def process_coding_request(event, user_input, processing_msg):
    """Handles the logic for processing a coding request after validation."""
    user_id = event.sender_id
    chat_id = event.chat_id
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    async with client.action(chat_id, "typing"):
        response = await call_selected_api(user_input, user_id, is_coding_request=True)

        # --- Send the result (file or message) ---
        buttons_after_code = [
            Button.inline(get_translation('new_question_button', lang_code, lang=coding_lang), f"select_code_{coding_lang}".encode()),
            Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
            Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
        ]

        if isinstance(response, str) and (response.startswith("API_ERROR:") or response.startswith(get_translation('api_error_specific', lang_code, model_name='', e='').split(':')[0])):
             await processing_msg.edit(response, buttons=[ # Show error with retry/menu buttons
                Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt"),
                Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
             ])
             await set_user_pref(user_id, 'last_prompt', user_input) # Save prompt for retry on error
             return

        if len(response) > 3900: # Send as file
            ext = ext_map.get(coding_lang, "txt")
            safe_lang = ''.join(c for c in coding_lang if c.isalnum())
            filename = f"code_{safe_lang}_{user_id}.{ext}"
            try:
                with open(filename, "w", encoding="utf-8") as f: f.write(response)
                caption = get_translation('code_too_long', lang_code, lang=coding_lang, ai_model_name=ai_model_name)
                # Send file and delete processing message
                await client.send_file(chat_id, filename, caption=caption, buttons=buttons_after_code, reply_to=event.message.id if hasattr(event, 'message') else None)
                await processing_msg.delete()
            except Exception as e:
                print(f"Error sending file: {e}")
                traceback.print_exc()
                await processing_msg.edit(f"{get_translation('error_generic', lang_code)}\nError sending file: {e}")
            finally:
                if os.path.exists(filename):
                    try: os.remove(filename)
                    except OSError as e: print(f"Error removing temporary file {filename}: {e}")
        else: # Send as message
            # Prepare message content
            formatted_response = f"```\n{response}\n```" # Basic markdown formatting
            final_message = f"{get_translation('code_ready', lang_code, lang=coding_lang, ai_model_name=ai_model_name)}\n{formatted_response}"

            try:
                 await processing_msg.edit(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
            except Exception as e:
                 print(f"Error editing final code message: {e}")
                 # Fallback: Send new message if edit fails (e.g., message too old)
                 await event.respond(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
                 try: await processing_msg.delete() # Clean up original processing message
                 except: pass # Ignore delete error

        # Clear last prompt after successful processing
        await set_user_pref(user_id, 'last_prompt', None)


async def process_chat_request(event, user_input, processing_msg):
    """Handles the logic for processing a chat request."""
    user_id = event.sender_id
    chat_id = event.chat_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    async with client.action(chat_id, "typing"):
        response = await call_selected_api(user_input, user_id, is_coding_request=False)

        buttons_after_chat = [
             Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")
        ]

        if isinstance(response, str) and (response.startswith("API_ERROR:") or response.startswith(get_translation('api_error_specific', lang_code, model_name='', e='').split(':')[0])):
             # Show error, but keep the chat context (stop button)
             await processing_msg.edit(response, buttons=buttons_after_chat)
             return

        # Send chat response
        try:
            # Edit the "Processing..." message with the actual response
             await processing_msg.edit(response, buttons=buttons_after_chat, link_preview=False)
        except Exception as e:
             print(f"Error editing chat response message: {e}")
             # Fallback: Send new message if edit fails
             await event.respond(response, buttons=buttons_after_chat, link_preview=False)
             try: await processing_msg.delete()
             except: pass

# --- Main Message Handler ---

@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    user_input = event.raw_text # Use raw_text to avoid issues with markdown/entities

    if not user_input or event.via_bot or event.edit_date: # Ignore empty, via bots, edited messages
        return

    user_input = user_input.strip()

    # 0. Get sender details and Add/Update user in DB
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name
    await add_or_update_user_in_db(user_id, username, first_name)
    # Ensure user data is loaded into memory cache
    await get_user_pref(user_id, 'ui_lang') # Loads defaults if not present

    # 1. Handle Admin Broadcast Input FIRST
    if user_id == admin_id and admin_states.get(user_id) == 'awaiting_broadcast_message':
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        broadcast_text = user_input
        del admin_states[user_id] # Clear state

        user_ids = await get_all_user_ids_from_db()
        if not user_ids:
            await event.respond("No users in the database to broadcast to.")
            await show_admin_panel(event)
            return

        count = len(user_ids)
        sent_count = 0
        failed_count = 0
        status_message = await event.respond(get_translation('admin_broadcast_sending', lang_code, count=count))

        tasks = []
        for target_user_id in user_ids:
            # Use a separate function scope for closure
            async def send_to_user(uid, text):
                try:
                    # Avoid sending to self if admin is in user list
                    if uid == admin_id:
                       return True # Skip self
                    await client.send_message(uid, text)
                    await asyncio.sleep(0.1) # Small delay between sends
                    return True
                except Exception as e:
                    print(f"Failed to send broadcast to {uid}: {e}")
                    return False
            tasks.append(send_to_user(target_user_id, broadcast_text))

        results = await asyncio.gather(*tasks)
        sent_count = sum(1 for r in results if r)
        failed_count = count - sent_count - (1 if admin_id in user_ids else 0) # Adjust count if admin skipped

        result_message = get_translation('admin_broadcast_sent', lang_code) + f" ({sent_count} successful)"
        if failed_count > 0:
            result_message += f"\n{get_translation('admin_broadcast_failed', lang_code)} ({failed_count} failures)"

        try:
            await status_message.edit(result_message)
        except Exception: # Handle potential edit errors
            await event.respond(result_message)

        await asyncio.sleep(2)
        await show_admin_panel(event) # Show admin panel again
        return # Stop further processing

    # 2. Ignore messages if bot is off (except for admin)
    if not bot_active and user_id != admin_id:
        return

    # 3. Ignore Commands (handled by specific decorators like /start, /admin)
    if user_input.startswith('/'):
        # Allow /start and /admin to be re-processed if needed by their handlers
        if user_input.split()[0] not in ['/start', '/admin']:
           print(f"Ignoring unknown command: {user_input}")
           return
        # Let specific handlers for /start, /admin catch these

    # --- Get User State ---
    is_chatting = await get_user_pref(user_id, 'is_chatting', False)
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    # 4. Handle Chatting State
    if is_chatting:
        # User is in dedicated chat mode
        processing_msg = await event.respond(get_translation('processing', lang_code))
        await process_chat_request(event, user_input, processing_msg)
        return # Don't process further

    # 5. Handle Coding State
    if coding_lang:
        # User has selected a coding language
        processing_msg = await event.respond(get_translation('processing', lang_code))
        async with client.action(chat_id, "typing"):
             is_valid = await is_code_related(user_input, event, coding_lang)
             if is_valid:
                 await process_coding_request(event, user_input, processing_msg)
             else:
                 # Invalid coding request - show help and retry button
                 help_text = get_translation('invalid_request_help', lang_code, lang=coding_lang)
                 await processing_msg.edit(
                     f"{get_translation('invalid_request', lang_code)}\n\n{help_text}",
                     buttons=[
                         Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt"),
                         Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
                     ]
                 )
                 # Store the invalid prompt for potential retry
                 await set_user_pref(user_id, 'last_prompt', user_input)
        return # Don't process further

    # 6. Handle Idle State (No command, not chatting, no coding language selected)
    # User sent random text in the main menu area
    # Gently guide them back to using buttons
    await event.delete() # Optionally delete the user's random message
    await show_main_menu(event, edit=False) # Show the main menu again


# --- Bot Startup ---
async def main():
    """Connects the client, initializes DB, and runs indefinitely."""
    await initialize_database()

    # Start the client
    print("Starting bot...")
    await client.start()
    me = await client.get_me()
    print(f"Bot '{me.first_name}' started successfully.")
    print(f"Admin ID: {admin_id}")
    print(f"Default AI Model: {DEFAULT_AI_MODEL}")
    print(f"Bot active on start: {bot_active}")
    print("Bot is running...")
    await client.run_until_disconnected()
    print("Bot stopped.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopping...")
