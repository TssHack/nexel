# -*- coding: utf-8 -*-
from telethon import TelegramClient, events, Button
import aiosqlite
import json
# import requests # Note: Using aiohttp for async requests now (Keep comment for history)
import asyncio
import aiohttp
import os
import traceback # For better error logging

# --- Configuration ---
api_id = 18377832
api_hash = "ed8556c450c6d0fd68912423325dd09c"
session_name = "my_ai_multilang"
admin_id = 7094106651 # <<< حتماً آیدی عددی ادمین را اینجا قرار دهید
db_file = "users_data.db" # نام فایل دیتابیس جدید

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
# --- Updated available_ai_models ---
available_ai_models = {
    "gpt4": "GPT-4",
    "llama4-maverick": "Llama4 Maverick",
    "llama4-scout": "Llama4 Scout",
    "llama3-70b": "Llama3 70b",
    "llama3-8b": "Llama3 8b",
    "llama3-free": "Llama3 Free",
    "mixtral": "Mixtral",
    "gemma": "Gemma",
    "deepseek": "Deepseek",
    # --- New Gemini Models ---
    "gemini-1.0-pro": "Gemini 1.0 Pro",
    "gemini-1.5-flash-latest": "Gemini 1.5 Flash",
    "gemini-1.5-pro-latest": "Gemini 1.5 Pro",
    # "gemini-2.5-pro-exp-03-25": "Gemini 2.5 Pro (Exp)", # Uncomment if you want to test experimental
    "gemini-pro-vision": "Gemini Pro Vision" # Note: Vision model might require different handling (e.g., image input)
}
# --- Default model can remain or be changed ---
DEFAULT_AI_MODEL = "gpt4" # Or set to e.g., "gemini-1.0-pro"

ext_map = {
    "Python": "py", "Java": "java", "JavaScript": "js", "C#": "cs", "C++": "cpp", "C": "c",
    "Swift": "swift", "Golang": "go", "Rust": "rs", "Kotlin": "kt", "TypeScript": "ts",
    "PhP": "php", "Laravel": "php"
}

# --- Multilingual Text (Updated) ---
# No changes needed in translations for this update, but ensure keys match if you modify text later
translations = {
    'fa': {
        'start_welcome': "🌟 **سلام! خوش اومدی دوست عزیز 😊**\n\n🗣️ زبان پیش‌فرض: **فارسی** 🇮🇷\n\n⚙️ برای تغییر زبان یا تنظیمات دیگه، از دکمه‌ی 'Settings ⚙️' استفاده کن!\n\n✨ با آرزوی تجربه‌ای دلچسب و هوشمند ✨", # Welcome on first start
        'welcome': "👋 **سلام! چطوری می‌تونم کمکت کنم؟** 😊\n\n🤖 **مدل فعال**: `{ai_model_name}`\n\n📚 **لطفاً راهنما را برای جزئیات بیشتر مطالعه کن.** ✨",
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
4️⃣ **تنظیمات**: از منوی '{settings_button}' زبان ربات و مدل AI را تغییر دهید.
⬅️ **بازگشت**: از دکمه‌های بازگشت استفاده کنید.
**❗️ نکته مهم:**\nبرای تجربه‌ای بهتر و پاسخ‌های دقیق‌تر، از مدل‌های قدرتمند مثل:\n🔹 `DeepSeek`\n🔹 `Gemini`\n🔹 `GPT`\nاستفاده کنید. 🚀",

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
    'en': {
        'start_welcome': "**Hello! Welcome.**\nThe default language is English. Use the 'Settings' button to change the language or other configurations.",
        'welcome': "👋 **Hello! How can I assist you today?** 😊\n\n🤖 *Active Model*: `{ai_model_name}`\n\n📚 *Please read the guide for more details.* ✨",
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
4️⃣ **Settings**: Use the '{settings_button}' menu to change the bot language and AI model.
⬅️ **Navigate**: Use the back buttons.
📌 **Important Note:**\nFor a better experience and more accurate responses, use powerful models like:\n🔹 `DeepSeek`\n🔹 `Gemini`\n🔹 `GPT`\nEnjoy the best results! 🚀
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

    }
}

# --- Database Functions ---
async def initialize_database():
    """Initializes the database and table schema."""
    async with aiosqlite.connect(db_file) as db:
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                ui_lang TEXT DEFAULT 'fa',
                selected_ai_model TEXT DEFAULT '{DEFAULT_AI_MODEL}',
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )
       """)
        # Add migration step if default model changes and DB exists
        # Example: await db.execute("UPDATE users SET selected_ai_model = ? WHERE selected_ai_model = 'old_default'", (DEFAULT_AI_MODEL,))
        await db.commit()
        print("Database initialized.")

async def fetch_user_data_from_db(user_id):
    """Fetches user data from DB. Returns None if not found."""
    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT ui_lang, selected_ai_model FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Ensure the selected model is still valid, otherwise fallback to default
                    selected_model = row[1]
                    if selected_model not in available_ai_models:
                        print(f"User {user_id} had invalid model '{selected_model}', resetting to default.")
                        selected_model = DEFAULT_AI_MODEL
                        # Optionally update the DB immediately
                        # await update_user_db_field(user_id, 'selected_ai_model', selected_model)
                    return {'ui_lang': row[0], 'selected_ai_model': selected_model}
                return None
    except Exception as e:
        print(f"DB Error fetching user data for {user_id}: {e}")
        return None

async def add_or_update_user_in_db(user_id, username=None, first_name=None):
    """Adds a new user or updates existing user's details and last_seen."""
    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
                exists = await cursor.fetchone()

            if exists:
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
            else:
                # Insert new user with the current default AI model
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, ui_lang, selected_ai_model, last_seen)
                    VALUES (?, ?, ?, 'fa', ?, CURRENT_TIMESTAMP)
                """, (user_id, username, first_name, DEFAULT_AI_MODEL))
            await db.commit()
    except Exception as e:
        print(f"DB Error in add_or_update_user_in_db for {user_id}: {e}")
        traceback.print_exc()


async def update_user_db_field(user_id, field, value):
    """Updates a specific field for a user in the database."""
    allowed_fields = ['ui_lang', 'selected_ai_model']
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
    # Use 'fa' as the ultimate fallback if lang_code doesn't exist
    return translations.get(lang_code, translations['fa']).get(key, f"[{key}]").format(**kwargs)

async def get_user_pref(user_id, key, default_value=None):
    """Gets a specific preference for a user, fetching from DB if not in memory."""
    if user_id not in user_data:
        db_data = await fetch_user_data_from_db(user_id)
        if db_data:
            # Ensure the model from DB is still valid
            selected_model = db_data['selected_ai_model']
            if selected_model not in available_ai_models:
                print(f"User {user_id} data had invalid model '{selected_model}' in cache load, resetting to default.")
                selected_model = DEFAULT_AI_MODEL
                # Update DB field if fetch logic didn't already
                # await update_user_db_field(user_id, 'selected_ai_model', selected_model)

            user_data[user_id] = {
                'ui_lang': db_data['ui_lang'],
                'coding_lang': None, # Runtime state
                'ai_model': selected_model, # Use validated or default model
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
            # Attempt to add them now if they interact
            # await add_or_update_user_in_db(user_id) # This happens in message handler anyway

    # Provide default if key doesn't exist for the user
    return user_data.get(user_id, {}).get(key, default_value if default_value is not None else (DEFAULT_AI_MODEL if key == 'ai_model' else None))

async def set_user_pref(user_id, key, value):
    """Sets a user preference in memory and updates the DB if applicable."""
    if user_id not in user_data:
        await get_user_pref(user_id, 'ui_lang') # Ensure user_data[user_id] exists

    user_data[user_id][key] = value

    # Persist relevant preferences to DB
    if key in ['ui_lang', 'selected_ai_model']:
        # Ensure the selected model is valid before saving
        if key == 'selected_ai_model' and value not in available_ai_models:
            print(f"Attempted to set invalid model '{value}' for user {user_id}. Keeping previous or default.")
            # Revert to previous valid value or default if necessary
            # This logic might need refinement based on desired behavior
            user_data[user_id][key] = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL) # Get validated pref
            return # Don't save the invalid value
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
    # Prompt refinement is now handled in call_selected_api
    # code_prompt = "فقط کد رو بده تاکید می کنم فقط کد"
    # ehsan_prompt = code_prompt + prompt
    data = {
        "prompt": prompt, # Use the prompt passed from call_selected_api
        "userId": f"#/{user_id_str}", "network": True,
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
    # Prompt refinement is now handled in call_selected_api
    # code_prompt = "فقط کد رو بده تاکید می کنم فقط کد"
    # ehsan_prompt = code_prompt + prompt
    print(f"Calling Lama API with model: {model_id}") # Add logging
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model_id,
                "prompt": prompt # Use the prompt passed from call_selected_api
            }
            async with session.post(
                LAMA_API_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=45)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                # Check common response keys
                if 'response' in data:
                     return data['response'].strip()
                elif 'result' in data: # Some APIs might use 'result'
                     return data['result'].strip()
                else:
                     print(f"Llama API ({model_id}) response format unknown: {data}")
                     return "API_ERROR: Unknown response format"
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

# --- Modified call_gemini_api ---
async def call_gemini_api(prompt, model_id):
    """Calls the Gemini API with the specified model ID."""
    # Consider if this prefix is always needed, might interfere with chat
    # code_prompt = "فقط کد رو بده تاکید می کنم فقط کد"
    # ehsan_prompt = code_prompt + prompt
    ehsan_prompt = prompt # Use the prompt passed from call_selected_api
    print(f"Calling Gemini API with model: {model_id}") # Add logging
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_API_URL,
                json={'prompt': ehsan_prompt, 'model': model_id}, # Use the provided model_id
                timeout=aiohttp.ClientTimeout(total=60) # Increased timeout slightly for potentially larger models
            ) as response:
                response.raise_for_status()
                data = await response.json()
                # Check common response keys based on observed API behavior
                if 'result' in data:
                     return data['result'].strip()
                elif 'response' in data: # Adjust if the actual key is different
                     return data['response'].strip()
                elif 'text' in data: # Another common key
                     return data['text'].strip()
                else:
                     print(f"Gemini API ({model_id}) response format unknown: {data}")
                     return "API_ERROR: Unknown response format"
    except aiohttp.ClientResponseError as e:
        print(f"Gemini API ({model_id}) HTTP Error: {e.status} - {e.message} - Response: {await e.text()}") # Log response text on error
        return f"API_ERROR: HTTP {e.status}"
    except asyncio.TimeoutError:
        print(f"Gemini API ({model_id}) Timeout")
        return "API_ERROR: Timeout"
    except Exception as e:
        print(f"Gemini API ({model_id}) Error: {e}")
        traceback.print_exc()
        return f"API_ERROR: {e}"

# --- Modified call_selected_api ---
async def call_selected_api(prompt, user_id, is_coding_request=False):
    """Calls the appropriate API based on user's selection."""
    model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    # Use model_id as fallback name if display name not found
    model_name = available_ai_models.get(model_id, model_id)
    user_id_str = str(user_id) # For GPT-4 API

    print(f"User {user_id} calling API. Model ID: {model_id}, Coding: {is_coding_request}, Prompt: '{prompt[:100]}...'") # Log prompt start

    response = None
    api_prompt = prompt # Default prompt

    # --- Determine API call and refine prompt based on model_id and request type ---
    if model_id == "gpt4":
        if is_coding_request:
             coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
             # Specific instructions for GPT-4 coding
             api_prompt = f"Please generate ONLY the {coding_lang} code based on the following request. Do not include explanations, greetings, or markdown formatting like ``` unless it's part of the code itself.\n\nRequest:\n{prompt}"
        # else: api_prompt remains the original prompt for chat
        response = await call_gpt4_api(api_prompt, user_id_str)

    elif model_id.startswith("llama") or model_id in ["mixtral", "gemma", "deepseek"]:
        if is_coding_request:
            coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
            # Add context and instruction for coding (adjust as needed per model behavior)
            api_prompt = f"Generate {coding_lang} code for the following request. Only output the raw code, without any introduction, explanation, or markdown ``` formatting:\n\n{prompt}"
        # else: api_prompt remains the original prompt for chat
        response = await call_lama_api(api_prompt, model_id)

    elif model_id.startswith("gemini-"): # Check if it's any of the Gemini models
        # Specific Gemini Vision handling might be needed here if user provides images
        if model_id == "gemini-pro-vision" and not is_coding_request:
             print("Warning: Using Gemini Vision model for text-only chat.")
             # No specific prompt change here, but keep in mind its primary function

        if is_coding_request:
            coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
            # Instruct Gemini for code generation (adjust based on testing)
            api_prompt = f"Generate {coding_lang} code for the following request. Provide only the code itself, without explanations or markdown code fences (```):\n\n{prompt}"
        # else: api_prompt remains the original prompt for chat
        response = await call_gemini_api(api_prompt, model_id) # Pass the actual model_id

    else:
        print(f"Unknown or unsupported model selected: {model_id}")
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        return get_translation('error_generic', lang_code) + f" (Unknown Model ID: {model_id})"

    # --- Process API Response ---
    if response is None:
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        # This case should ideally not be reached if the else handles unknown models
        print(f"Error: API call did not return a response for model {model_id}")
        return get_translation('error_generic', lang_code) + " (Internal logic error: No response)"

    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa') # Get lang code for potential error messages

    if isinstance(response, str) and response.startswith("API_ERROR:"):
        error_detail = response.split(":", 1)[1].strip() if ":" in response else response
        # Use the potentially more specific model_name here
        return get_translation('api_error_specific', lang_code, model_name=model_name, e=error_detail)
    elif not response: # Empty response
        return get_translation('empty_response_error', lang_code, model_name=model_name)
    else:
        # Basic cleaning (can be enhanced)
        cleaned_response = response
        # Remove markdown code blocks if they wrap the entire response (common issue)
        # Be careful not to remove intentional markdown within the response
        if cleaned_response.startswith("```") and cleaned_response.endswith("```"):
            # Attempt to strip outer fences and potential language hint
            temp_response = cleaned_response[3:-3].strip()
            first_line, newline, rest = temp_response.partition('\n')
            # Check if the first line looks like a language hint (case-insensitive)
            possible_hints = [l.lower() for l in coding_languages + list(ext_map.values())]
            if newline and first_line.strip().lower() in possible_hints:
                 cleaned_response = rest.strip() # Use the rest
            else:
                 cleaned_response = temp_response # Keep if first line wasn't a hint

        # Further cleaning specific to model outputs might be needed here
        # e.g., removing introductory sentences if the prompt failed to suppress them.

        return cleaned_response


async def is_code_related(text, event, coding_lang):
    """Checks if the user prompt seems like a valid coding request."""
    user_id = event.sender_id
    # Using a simple internal prompt for validation
    # Consider using a cheaper/faster model for this check if possible, or simplifying the check
    check_prompt = f'Analyze the following user request regarding "{coding_lang}" programming:\n"{text}"\n\nIs this primarily a request to write, explain, debug, or modify code? Answer ONLY with "yes" or "no".'

    try:
        async with client.action(event.chat_id, "typing"):
            # Use the user's selected API for the check for consistency, but treat as non-coding
            reply = await call_selected_api(check_prompt, user_id, is_coding_request=False)

            if isinstance(reply, str) and reply.startswith("API_ERROR:") or not reply :
                 print(f"Validation API Error or empty response: {reply}")
                 # Fallback: Assume it *might* be code related if API fails validation
                 return True # Default to attempting code generation on validation failure

            print(f"Validation check for '{text[:50]}...' -> API Reply: '{reply}'")
            # Make the check more robust (case-insensitive, check for variations)
            reply_lower = reply.lower().strip().strip('.').strip()
            return reply_lower == "yes"
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
    # Load/initialize data in user_data dict, ensuring model is valid
    await get_user_pref(user_id, 'ui_lang') # This now includes model validation

    # Reset runtime states
    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'is_chatting', False)
    await set_user_pref(user_id, 'last_prompt', None)
    if user_id in admin_states: del admin_states[user_id]

    # Show main menu
    await show_main_menu(event, edit=False, first_start=True)


async def show_main_menu(event, edit=False, first_start=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, ai_model_id) # Show ID if name missing

    buttons = [
        [Button.inline(get_translation('settings_button', lang_code), b"settings"),
         Button.inline(get_translation('coding_button', lang_code), b"coding")],
        # Add Chat button back if desired
        [Button.inline(get_translation('chat_button', lang_code), b"start_chat"),
         Button.inline(get_translation('help_button', lang_code), b"help")],
        [Button.url(get_translation('developer_button', lang_code), "(https://t.me/n6xel)")]
    ]
    if user_id == admin_id:
        buttons.append([Button.inline(get_translation('admin_panel_button', lang_code), b"admin_panel")])

    if first_start:
        text = get_translation('start_welcome', lang_code) # Special welcome on first /start
    else:
        text = get_translation('welcome', lang_code, ai_model_name=ai_model_name)

    action = event.edit if edit else event.respond
    try:
        # Make sure message content is not identical if editing to avoid flood waits
        current_text = getattr(event.message, 'text', '') if edit else ''
        if edit and text == current_text:
            await event.answer() # Just acknowledge if content is the same
        else:
            await action(text, buttons=buttons, parse_mode='markdown') # Use markdown for welcome message
    except Exception as e:
        print(f"Error showing main menu ({'edit' if edit else 'respond'}): {e}")
        # Fallback if edit fails or other issues
        if edit and "Message not modified" not in str(e):
             try:
                 await event.respond(text, buttons=buttons, parse_mode='markdown')
             except Exception as e2:
                 print(f"Error responding after edit failed: {e2}")
        elif not edit:
             print(f"Error responding to show main menu: {e}")



@client.on(events.CallbackQuery(data=b"main_menu"))
async def return_to_main_menu(event):
    user_id = event.sender_id
    # Reset potentially active states when returning to main menu
    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'is_chatting', False)
    await set_user_pref(user_id, 'last_prompt', None)
    if user_id in admin_states: del admin_states[user_id] # Clear admin state too
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
    try:
        await event.edit(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing settings menu: {e}")


@client.on(events.CallbackQuery(data=b"change_ui_lang"))
async def show_ui_language_options(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    buttons = [
        [Button.inline("🇬🇧 English", b"set_lang_en")],
        [Button.inline("🇮🇷 فارسی", b"set_lang_fa")],
        [Button.inline(get_translation('back_to_settings', lang_code), b"settings")]
    ]
    text = get_translation('settings_choose_lang', lang_code)
    try:
        await event.edit(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing UI lang options: {e}")


@client.on(events.CallbackQuery(pattern=b"set_lang_(.*)"))
async def set_ui_language(event):
    user_id = event.sender_id
    new_lang_code = event.pattern_match.group(1).decode('utf-8')

    if new_lang_code in translations:
        await set_user_pref(user_id, 'ui_lang', new_lang_code)
        # Get translation in the *new* language for the confirmation message
        await event.answer(get_translation('settings_lang_selected', new_lang_code), alert=True)
        # Go back to settings menu after selection (will now use the new language)
        await show_settings_menu(event)
    else:
        # Use existing language for the error message
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        await event.answer(get_translation('error_generic', lang_code) + " (Invalid Lang)", alert=True)


@client.on(events.CallbackQuery(data=b"select_ai_model"))
async def show_ai_model_options(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    current_model = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)

    buttons = []
    temp_row = []
    # Sort models for consistent display, perhaps prioritizing certain types
    # sorted_models = sorted(available_ai_models.items(), key=lambda item: item[0]) # Sort by ID
    sorted_models = available_ai_models.items() # Keep original order for now

    for model_id, display_name in sorted_models:
        prefix = "✅ " if model_id == current_model else ""
        # Ensure button data doesn't exceed Telegram limits if model_id is very long
        button_data = f"set_model_{model_id}".encode()
        if len(button_data) > 60: # Telegram callback_data limit is 64 bytes
             print(f"Warning: Model ID '{model_id}' might be too long for callback data.")
             # Consider using a shorter alias or different mechanism if this occurs
             continue # Skip models with excessively long IDs for safety

        temp_row.append(Button.inline(f"{prefix}{display_name}", button_data))
        if len(temp_row) == 2: # Two models per row
            buttons.append(temp_row)
            temp_row = []
    if temp_row: # Add remaining button if odd number
        buttons.append(temp_row)

    buttons.append([Button.inline(get_translation('back_to_settings', lang_code), b"settings")])
    text = get_translation('settings_choose_model', lang_code)
    try:
        await event.edit(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing AI model options: {e}")


@client.on(events.CallbackQuery(pattern=b"set_model_(.*)"))
async def set_ai_model(event):
    user_id = event.sender_id
    # Decode carefully, pattern might capture unexpected bytes
    try:
        model_id = event.pattern_match.group(1).decode('utf-8', 'ignore')
    except Exception as e:
        print(f"Error decoding model ID from callback: {e}")
        await event.answer("Error processing selection.", alert=True)
        return

    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa') # Get current lang for messages

    if model_id in available_ai_models:
        await set_user_pref(user_id, 'selected_ai_model', model_id)
        model_name = available_ai_models[model_id]
        await event.answer(get_translation('settings_model_selected', lang_code, model_name=model_name), alert=True)
        # Go back to settings menu
        await show_settings_menu(event)
    else:
        print(f"Invalid AI model selected via callback: {model_id}")
        await event.answer(get_translation('error_generic', lang_code) + f" (Invalid Model: {model_id})", alert=True)


# --- Coding Flow ---

@client.on(events.CallbackQuery(data=b'coding'))
async def choose_coding_language(event):
    user_id = event.sender_id # Moved user_id fetch earlier
    # Check bot status *before* trying to get language preference
    if not bot_active and user_id != admin_id:
        # Need a way to answer without knowing user's language pref yet
        # Default to English for this specific alert, or try fetching lang first
        try: lang_code_alert = await get_user_pref(user_id, 'ui_lang', 'en') # Default to 'en' for alert
        except: lang_code_alert = 'en'
        await event.answer(get_translation('admin_bot_off_msg', lang_code_alert).replace("❌ ","").replace(" for users.",""), alert=True)
        return

    await event.answer() # Answer callback query early
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

    # Ensure user is not in chat mode when entering coding selection
    await set_user_pref(user_id, 'is_chatting', False)
    # Clear any previous coding language selection? No, wait for selection.
    # await set_user_pref(user_id, 'coding_lang', None) # Don't clear yet

    try:
        await event.edit(
            get_translation('choose_coding_lang', lang_code),
            buttons=rows
        )
    except Exception as e:
        print(f"Error showing coding language choice: {e}")


@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def handle_coding_language_selection(event):
    user_id = event.sender_id
    if not bot_active and user_id != admin_id:
        try: lang_code_alert = await get_user_pref(user_id, 'ui_lang', 'en')
        except: lang_code_alert = 'en'
        await event.answer(get_translation('admin_bot_off_msg', lang_code_alert).replace("❌ ","").replace(" for users.",""), alert=True)
        return

    try:
        selected_lang = event.pattern_match.group(1).decode('utf-8')
    except Exception as e:
        print(f"Error decoding language from callback: {e}")
        await event.answer("Error processing selection.", alert=True)
        return

    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa') # UI language
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, ai_model_id)

    if selected_lang in coding_languages:
        await set_user_pref(user_id, 'coding_lang', selected_lang) # Store the *coding* language state
        await set_user_pref(user_id, 'is_chatting', False) # Ensure not in chat mode
        await set_user_pref(user_id, 'last_prompt', None) # Clear last prompt on new selection

        await event.answer(f"{selected_lang} selected.") # Simple confirmation

        try:
            await event.edit(
                get_translation('coding_lang_selected', lang_code, lang=selected_lang, ai_model_name=ai_model_name),
                buttons=[
                    # Keep the "New Question ({lang})" button concept for retrying? No, let user type.
                    # Button.inline(get_translation('new_question_button', lang_code, lang=selected_lang), f"select_code_{selected_lang}".encode()), # Re-select same lang? Maybe not needed.
                    Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"), # Go back to language list
                    Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
                    ]
            )
        except Exception as e:
             print(f"Error editing message after lang selection: {e}")
    else:
         await event.answer(f"Invalid language selected: {selected_lang}", alert=True)


# --- Chat Flow ---

@client.on(events.CallbackQuery(data=b"start_chat"))
async def start_chatting(event):
    user_id = event.sender_id
    if not bot_active and user_id != admin_id:
        try: lang_code_alert = await get_user_pref(user_id, 'ui_lang', 'en')
        except: lang_code_alert = 'en'
        await event.answer(get_translation('admin_bot_off_msg', lang_code_alert).replace("❌ ","").replace(" for users.",""), alert=True)
        return

    await event.answer()
    await set_user_pref(user_id, 'is_chatting', True)
    await set_user_pref(user_id, 'coding_lang', None) # Exit coding mode
    await set_user_pref(user_id, 'last_prompt', None)

    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, ai_model_id)

    try:
        await event.edit(
            get_translation('start_chat_prompt', lang_code, ai_model_name=ai_model_name),
            buttons=[Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")] # Only show stop button
        )
    except Exception as e:
        print(f"Error editing message for start_chat: {e}")


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
    ai_model_name = available_ai_models.get(ai_model_id, ai_model_id)

    # Format help text with dynamic button names and model name
    help_message = get_translation('help_title', lang_code) + "\n\n" + \
                   get_translation('help_text', lang_code,
                                   coding_button=get_translation('coding_button', lang_code),
                                   chat_button=get_translation('chat_button', lang_code),
                                   settings_button=get_translation('settings_button', lang_code),
                                   ai_model_name=ai_model_name)

    try:
        await event.edit(
            help_message,
            buttons=[
                [Button.inline(get_translation('start_coding_button', lang_code), b"coding")],
                [Button.inline(get_translation('chat_button', lang_code), b"start_chat")], # Add chat button here too
                [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
            ],
            parse_mode='markdown', # Ensure markdown is enabled for help text
            link_preview=False
        )
    except Exception as e:
        print(f"Error showing help: {e}")


# --- Admin Panel ---

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if event.sender_id == admin_id:
        # Ensure admin user data is loaded/initialized
        await get_user_pref(admin_id, 'ui_lang')
        await show_admin_panel(event)
    else:
        # Try to get user's language for the "not allowed" message
        try: lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'en')
        except: lang_code = 'en' # Fallback to English if user data fails
        await event.respond(get_translation('admin_not_allowed', lang_code))

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if event.sender_id == admin_id:
        # Clear potential leftover admin state
        if admin_id in admin_states: del admin_states[admin_id]
        await show_admin_panel(event, edit=True)
    else:
        try: lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'en')
        except: lang_code = 'en'
        await event.answer(get_translation('admin_not_allowed', lang_code), alert=True)


async def show_admin_panel(event, edit=False):
    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa') # Admin panel uses admin's language pref
    text = f"**{get_translation('admin_panel_title', lang_code)}**\n\n{get_translation('admin_panel_desc', lang_code)}"
    # More descriptive toggle button text
    toggle_text = f"{'✅ Turn Bot ON' if not bot_active else '❌ Turn Bot OFF'}"
    status_text = f"{'(Currently OFF)' if not bot_active else '(Currently ON)'}"

    buttons = [
        [ Button.inline(f"{toggle_text} {status_text}", b"admin_toggle_status") ],
        [
            Button.inline(get_translation('admin_broadcast', lang_code), b"admin_broadcast"),
            Button.inline(get_translation('admin_list_users', lang_code), b"admin_list_users")
        ],
        [ Button.inline(get_translation('main_menu_button', lang_code), b"main_menu") ]
    ]

    action = event.edit if edit else event.respond
    try:
        # Avoid editing if message content is identical
        current_text = getattr(event.message, 'text', '') if edit else ''
        if edit and text == current_text:
             await event.answer() # Just acknowledge
        else:
             await action(text, buttons=buttons, parse_mode='markdown') # Use markdown
    except Exception as e:
        print(f"Error showing admin panel ({'edit' if edit else 'respond'}): {e}")
        if edit and "Message not modified" not in str(e):
            try:
                await event.respond(text, buttons=buttons, parse_mode='markdown') # Fallback if edit fails
            except Exception as e2:
                print(f"Error responding after admin panel edit failed: {e2}")
        elif not edit:
             print(f"Error responding to show admin panel: {e}")

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
        await event.answer() # Ignore silently for non-admins


@client.on(events.CallbackQuery(data=b"admin_list_users"))
async def admin_list_users(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    await event.answer("⏳ Fetching users...")

    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT user_id, username, first_name, ui_lang, selected_ai_model, last_seen FROM users ORDER BY last_seen DESC") as cursor:
                users = await cursor.fetchall()

        back_button = [ Button.inline(get_translation('back_button', lang_code), b"admin_panel") ]

        if not users:
            await event.edit(get_translation('admin_no_users', lang_code), buttons=back_button)
            return

        user_list_parts = []
        count = len(users)
        for user_id, username, first_name, uilang, model, last_seen_ts in users:
            display_name = first_name.replace('`','').replace('_','').replace('*','') if first_name else "N/A" # Basic sanitization
            username_str = username.replace('`','').replace('_','').replace('*','') if username else "N/A"
            try:
                 last_seen_str = str(last_seen_ts).split('.')[0] if last_seen_ts else "N/A"
            except:
                 last_seen_str = "N/A"

            model_display = available_ai_models.get(model, model) # Show display name or ID

            user_entry = get_translation('admin_user_entry', lang_code,
                                         user_id=user_id,
                                         username=username_str,
                                         name=display_name)
            # Add extra details below the main entry
            user_entry += f"   *Lang:* `{uilang}` | *Model:* `{model_display}`\n   *Seen:* `{last_seen_str}`\n--------------------"
            user_list_parts.append(user_entry)


        full_user_list = "\n".join(user_list_parts)
        title = get_translation('admin_list_users_title', lang_code, count=count, user_list="") # Get title format
        final_text = title + "\n" + full_user_list

        # Handle message length limits by sending as a file if too long
        if len(final_text) > 4000: # Telegram message limit is 4096
             filename = f"user_list_{count}.txt"
             try:
                 with open(filename, "w", encoding="utf-8") as f: f.write(title + "\n" + full_user_list) # Write non-markdown version to file
                 await event.delete() # Delete the "Fetching..." message
                 await client.send_file(
                     admin_id,
                     filename,
                     caption=f"{title}\n(Full list sent as file due to length)",
                     buttons=back_button
                 )
                 os.remove(filename)
             except Exception as e_file:
                 print(f"Error sending user list as file: {e_file}")
                 await event.edit(f"Error creating user list file: {e_file}", buttons=back_button)
        else:
             # Ensure message is not identical before editing
             current_text = getattr(event.message, 'text', '')
             if final_text == current_text:
                  await event.answer("User list already displayed.")
             else:
                  await event.edit(final_text, buttons=back_button, parse_mode='markdown')

    except Exception as e:
        print(f"Error listing users: {e}")
        traceback.print_exc()
        await event.edit(f"Error fetching users: {e}", buttons=[ Button.inline(get_translation('back_button', lang_code), b"admin_panel") ])


@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_ask_broadcast(event):
    if event.sender_id == admin_id:
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        admin_states[admin_id] = 'awaiting_broadcast_message'
        try:
            await event.edit(
                get_translation('admin_ask_broadcast', lang_code),
                buttons=[ Button.inline(f"🔙 {get_translation('back_button', lang_code)}", b"admin_panel") ]
            )
        except Exception as e:
            print(f"Error editing for broadcast prompt: {e}")
    else:
        await event.answer()

# --- Retry Logic ---
@client.on(events.CallbackQuery(data=b"retry_last_prompt"))
async def retry_last_prompt_handler(event):
    user_id = event.sender_id
    last_prompt = await get_user_pref(user_id, 'last_prompt')
    coding_lang = await get_user_pref(user_id, 'coding_lang') # Check if still in coding mode
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    if not last_prompt:
        await event.answer("No prompt found to retry.", alert=True)
        return

    # Decide if it's a coding or chat retry based on current state
    is_coding_retry = bool(coding_lang)

    if is_coding_retry:
         await event.answer(f"🔄 Retrying for {coding_lang}...")
         # Edit the previous error message to show processing again
         processing_msg = await event.edit(get_translation('processing', lang_code))
         await process_coding_request(event, last_prompt, processing_msg)
    else:
         # Assume it was a chat prompt if not in coding mode
         # Check if user is currently in chat mode for consistency?
         is_chatting_now = await get_user_pref(user_id, 'is_chatting', False)
         if not is_chatting_now:
              await event.answer("Cannot retry chat prompt, not in chat mode.", alert=True)
              return # Or potentially switch to chat mode? Risky.

         await event.answer("🔄 Retrying chat prompt...")
         processing_msg = await event.edit(get_translation('processing', lang_code))
         await process_chat_request(event, last_prompt, processing_msg) # Needs process_chat_request


# --- Main Message Processing Logic ---

async def process_coding_request(event, user_input, processing_msg):
    """Handles the logic for processing a coding request after validation."""
    user_id = event.sender_id
    chat_id = event.chat_id
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, ai_model_id)

    if not coding_lang: # Should not happen if called correctly, but check anyway
        await processing_msg.edit(get_translation('error_generic', lang_code) + " (Coding lang not set)")
        return

    # Reply to the original user message if possible
    reply_to_msg_id = event.message.id if hasattr(event, 'message') and hasattr(event.message, 'id') else None

    async with client.action(chat_id, "typing"):
        response = await call_selected_api(user_input, user_id, is_coding_request=True)

        # --- Buttons for after code ---
        buttons_after_code = [
            # Button to go back to language list is more useful than re-selecting same lang
            # Button.inline(get_translation('new_question_button', lang_code, lang=coding_lang), f"select_code_{coding_lang}".encode()),
            Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
            Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
        ]

        # --- Handle API Errors ---
        if isinstance(response, str) and (response.startswith("API_ERROR:") or response.startswith(get_translation('api_error_specific', lang_code, model_name='', e='').split(':')[0]) or response.startswith(get_translation('empty_response_error', lang_code, model_name='').split(' ')[0])):
             retry_button = Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt")
             menu_button = Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
             try:
                 await processing_msg.edit(response, buttons=[retry_button, menu_button])
             except Exception as e_edit:
                 print(f"Error editing processing message with API error: {e_edit}")
                 await event.respond(response, buttons=[retry_button, menu_button], reply_to=reply_to_msg_id)
             await set_user_pref(user_id, 'last_prompt', user_input) # Save prompt for retry on error
             return # Stop processing here

        # --- Send the result (file or message) ---
        try:
            if len(response) > 3900: # Send as file
                ext = ext_map.get(coding_lang, "txt")
                safe_lang = ''.join(c for c in coding_lang if c.isalnum())
                # Include timestamp or random element to avoid filename clashes if simultaneous requests occur
                filename = f"code_{safe_lang}_{user_id}_{event.id}.{ext}"
                try:
                    with open(filename, "w", encoding="utf-8") as f: f.write(response)
                    caption = get_translation('code_too_long', lang_code, lang=coding_lang, ai_model_name=ai_model_name)
                    # Send file and delete processing message
                    await client.send_file(chat_id, filename, caption=caption, buttons=buttons_after_code, reply_to=reply_to_msg_id)
                    await processing_msg.delete()
                except Exception as e_file:
                    print(f"Error sending file: {e_file}")
                    traceback.print_exc()
                    await processing_msg.edit(f"{get_translation('error_generic', lang_code)}\nError sending file: {e_file}")
                finally:
                    if os.path.exists(filename):
                        try: os.remove(filename)
                        except OSError as e_rem: print(f"Error removing temporary file {filename}: {e_rem}")
            else: # Send as message
                # Try formatting as markdown code block
                formatted_response = f"```{ext_map.get(coding_lang, '')}\n{response}\n```"
                final_message = f"{get_translation('code_ready', lang_code, lang=coding_lang, ai_model_name=ai_model_name)}\n{formatted_response}"

                try:
                     await processing_msg.edit(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
                except Exception as e_edit:
                     print(f"Error editing final code message (Markdown): {e_edit}")
                     # Fallback 1: Send without markdown if markdown fails
                     try:
                         final_message_plain = f"{get_translation('code_ready', lang_code, lang=coding_lang, ai_model_name=ai_model_name)}\n{response}"
                         await processing_msg.edit(final_message_plain, buttons=buttons_after_code, link_preview=False)
                     except Exception as e_edit_plain:
                         print(f"Error editing final code message (Plain): {e_edit_plain}")
                         # Fallback 2: Send new message if edit fails completely
                         await event.respond(final_message_plain, buttons=buttons_after_code, reply_to=reply_to_msg_id, link_preview=False)
                         try: await processing_msg.delete() # Clean up original processing message
                         except: pass # Ignore delete error

            # Clear last prompt after successful processing
            await set_user_pref(user_id, 'last_prompt', None)

        except Exception as e_outer:
             print(f"Outer error during code processing/sending: {e_outer}")
             traceback.print_exc()
             try:
                 await processing_msg.edit(f"{get_translation('error_generic', lang_code)} (Processing Error)")
             except: pass # Ignore if editing fails here


async def process_chat_request(event, user_input, processing_msg):
    """Handles the logic for processing a chat request."""
    user_id = event.sender_id
    chat_id = event.chat_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, ai_model_id)

    reply_to_msg_id = event.message.id if hasattr(event, 'message') and hasattr(event.message, 'id') else None

    async with client.action(chat_id, "typing"):
        response = await call_selected_api(user_input, user_id, is_coding_request=False)

        # --- Buttons for after chat ---
        buttons_after_chat = [
             Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")
             # Maybe add a retry button for chat too?
             # Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt")
        ]
        buttons_on_error = [
            Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt"),
            Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")
        ]

        # --- Handle API Errors ---
        if isinstance(response, str) and (response.startswith("API_ERROR:") or response.startswith(get_translation('api_error_specific', lang_code, model_name='', e='').split(':')[0]) or response.startswith(get_translation('empty_response_error', lang_code, model_name='').split(' ')[0])):
             try:
                 await processing_msg.edit(response, buttons=buttons_on_error)
             except Exception as e_edit:
                 print(f"Error editing processing message with chat API error: {e_edit}")
                 await event.respond(response, buttons=buttons_on_error, reply_to=reply_to_msg_id)
             await set_user_pref(user_id, 'last_prompt', user_input) # Save prompt for retry on error
             return # Stop processing here

        # --- Send chat response ---
        try:
            # Edit the "Processing..." message with the actual response
            # Check message length for chat too, although less common to hit limits
            if len(response) > 4000:
                response = response[:4000] + "... (message truncated)"

            await processing_msg.edit(response, buttons=buttons_after_chat, link_preview=False)
            # Clear last prompt after successful chat response
            await set_user_pref(user_id, 'last_prompt', None)
        except Exception as e:
             print(f"Error editing chat response message: {e}")
             # Fallback: Send new message if edit fails
             try:
                 await event.respond(response, buttons=buttons_after_chat, reply_to=reply_to_msg_id, link_preview=False)
                 await processing_msg.delete() # Clean up original processing message
                 # Clear last prompt after successful chat response (fallback)
                 await set_user_pref(user_id, 'last_prompt', None)
             except Exception as e_resp:
                 print(f"Error sending fallback chat response: {e_resp}")
                 # If fallback also fails, at least inform the user
                 try: await processing_msg.edit(get_translation('error_generic', lang_code) + " (Send Error)")
                 except: pass


# --- Main Message Handler ---
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    chat_id = event.chat_id

    # Ignore messages from bots, channels, edited messages, service messages etc.
    if not event.is_private or event.via_bot or event.edit_date or not event.raw_text or event.sticker or event.photo or event.document:
        # Allow documents/photos if using vision model? Requires more logic.
        # For now, ignore non-text messages.
        # print(f"Ignoring message from {user_id}: Not private text or edited/via_bot.")
        return

    user_input = event.raw_text.strip()
    if not user_input: # Ignore empty messages after stripping
        return

    # --- Handle Commands FIRST ---
    if user_input.startswith('/'):
        command = user_input.split()[0]
        if command == '/start':
            # Let the dedicated /start handler manage this
            return
        elif command == '/admin' and user_id == admin_id:
            # Let the dedicated /admin handler manage this
            return
        elif command == '/cancel': # Example: command to exit current state
             await set_user_pref(user_id, 'coding_lang', None)
             await set_user_pref(user_id, 'is_chatting', False)
             if user_id in admin_states: del admin_states[user_id]
             await event.delete() # Delete the /cancel message
             await show_main_menu(event)
             return
        else:
            # Ignore unknown commands silently or send a help message
            # print(f"Ignoring unknown command: {user_input}")
             lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
             await event.respond(f"Unknown command: `{command}`. Use /start or the buttons.", parse_mode='md')
             return

    # --- Add/Update User in DB and Load Preferences ---
    try:
        sender = await event.get_sender()
        username = sender.username
        first_name = sender.first_name
        await add_or_update_user_in_db(user_id, username, first_name)
        # Load preferences, ensuring model validity
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    except Exception as e:
        print(f"Error getting sender/DB update for {user_id}: {e}")
        # Allow proceeding with defaults if possible, but log the error
        lang_code = 'fa' # Fallback language

    # --- Handle Admin Broadcast Input ---
    if user_id == admin_id and admin_states.get(user_id) == 'awaiting_broadcast_message':
        broadcast_text = user_input
        admin_states.pop(admin_id, None) # Remove state safely

        user_ids = await get_all_user_ids_from_db()
        if not user_ids:
            await event.respond("No users in the database to broadcast to.")
            await show_admin_panel(event)
            return

        count = len(user_ids)
        status_message = await event.respond(get_translation('admin_broadcast_sending', lang_code, count=count))

        success_count = 0
        fail_count = 0
        tasks = []

        async def send_to_user(uid, text):
            # Rate limiting: sleep slightly between sends
            await asyncio.sleep(0.05) # Sleep 50ms between attempts
            try:
                if uid == admin_id: return True # Don't message self
                await client.send_message(uid, text, link_preview=False) # Send message
                return True
            except Exception as e:
                print(f"Failed to send broadcast to {uid}: {e}")
                # Handle specific errors like UserIsBlocked, PeerIdInvalid etc. if needed
                return False

        for uid in user_ids:
             # Use asyncio.create_task for concurrent sending with rate limiting inside the task
             tasks.append(asyncio.create_task(send_to_user(uid, broadcast_text)))

        results = await asyncio.gather(*tasks) # Wait for all tasks to complete

        success_count = sum(1 for r in results if r)
        # Adjust count if admin was in the list and skipped
        admin_was_in_list = admin_id in user_ids
        total_attempted = count - 1 if admin_was_in_list else count
        fail_count = total_attempted - success_count

        result_message = get_translation('admin_broadcast_sent', lang_code) + f" ({success_count} successful)"
        if fail_count > 0:
            result_message += f"\n{get_translation('admin_broadcast_failed', lang_code)} ({fail_count} failures)"

        try:
            await status_message.edit(result_message)
        except Exception: # If editing fails, send new message
            await event.respond(result_message)

        await asyncio.sleep(2) # Pause before showing panel again
        await show_admin_panel(event) # Show admin panel again
        return

    # --- Ignore messages if bot is off (except for admin) ---
    if not bot_active and user_id != admin_id:
        # Maybe send a message? Or just ignore silently.
        # print(f"Bot inactive, ignoring message from {user_id}")
        return

    # --- Get User State ---
    is_chatting = await get_user_pref(user_id, 'is_chatting', False)
    coding_lang = await get_user_pref(user_id, 'coding_lang')

    # --- Handle Chatting State ---
    if is_chatting:
        processing_msg = await event.respond(get_translation('processing', lang_code))
        await process_chat_request(event, user_input, processing_msg)
        return

    # --- Handle Coding State ---
    if coding_lang:
        processing_msg = await event.respond(get_translation('processing', lang_code))
        async with client.action(chat_id, "typing"):
             # Check if the input seems like a request for code
             is_valid = await is_code_related(user_input, event, coding_lang)
             if is_valid:
                 await process_coding_request(event, user_input, processing_msg)
             else:
                 # If not code-related, explain and offer retry/menu
                 help_text = get_translation('invalid_request_help', lang_code, lang=coding_lang)
                 retry_button = Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt")
                 menu_button = Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
                 try:
                     await processing_msg.edit(
                         f"{get_translation('invalid_request', lang_code)}\n\n{help_text}",
                         buttons=[retry_button, menu_button]
                     )
                 except Exception as e_edit:
                      print(f"Error editing invalid request message: {e_edit}")
                      # Fallback respond
                      await event.respond(f"{get_translation('invalid_request', lang_code)}\n\n{help_text}", buttons=[retry_button, menu_button])
                 await set_user_pref(user_id, 'last_prompt', user_input) # Save for potential retry
        return

    # --- Handle Idle State (No command, not chatting, no coding language selected) ---
    # User sent a message when they should have used buttons.
    # Delete the message and show the main menu again.
    try:
        await event.delete()
    except Exception as e:
        print(f"Could not delete idle message from {user_id}: {e}")
    # Show main menu as a new message, not edit, since the original was deleted (or couldn't be)
    await show_main_menu(event, edit=False)


# --- Bot Startup ---
async def main():
    """Connects the client, initializes DB, and runs indefinitely."""
    print("Initializing database...")
    await initialize_database()

    # Start the client using bot token if available, otherwise user account
    print("Starting bot client...")
    # If you have a bot token, use it like this:
    # await client.start(bot_token='YOUR_BOT_TOKEN')
    # Otherwise, it will prompt for phone/code for user account:
    await client.start()

    me = await client.get_me()
    print(f"Bot '{me.first_name}' (ID: {me.id}) started successfully.")
    print(f"Admin ID configured: {admin_id}")
    print(f"Default AI Model: {DEFAULT_AI_MODEL}")
    print(f"Initial Bot Active Status: {bot_active}")
    print("Bot is running... Press Ctrl+C to stop.")
    await client.run_until_disconnected()
    print("Bot disconnected.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCtrl+C received. Stopping bot...")
    finally:
        # Perform any cleanup here if needed
        print("Bot stopped.")

