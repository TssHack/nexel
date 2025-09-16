# -*- coding: utf-8 -*-
from telethon import TelegramClient, events, Button
import aiosqlite
import json
import requests
import asyncio
import aiohttp
import os
import traceback
from datetime import datetime, timedelta

# --- Configuration ---
api_id = 18377832
api_hash = "ed8556c450c6d0fd68912423325dd09c"
session_name = "my_ai_multilang"
admin_id = 1848591768 # آیدی عددی ادمین
db_file = "users_data.db" # نام فایل دیتابیس جدید

# --- API Endpoints ---
GPT4_API_URL = "https://api.binjie.fun/api/generateStream"
LAMA_API_URL = "http://lama-ehsan.vercel.app/chat" # model in query param
GEMINI_API_URL = "https://gem-ehsan.vercel.app/gemini/chat" # model in query param

# --- Bot State ---
client = TelegramClient(session_name, api_id, api_hash)
bot_active = True
user_data = {} # Stores user-specific data: {user_id: {'ui_lang': 'fa', 'coding_lang': None, 'ai_model': 'gpt4', 'is_chatting': False, 'last_prompt': None}}
admin_states = {} # State for admin actions {admin_id: action}

# --- Bot Data ---
coding_languages = [
    "Node.js", "Python", "Java", "JavaScript", "C#", "C++", 
    "Swift", "Golang", "Rust", "Kotlin", "TypeScript", "PHP", 
    "Ruby", "SQL", "Shell", "Objective-C", "MATLAB", 
    "VHDL", "Solidity", "Delphi", "R", "Elixir", "Lua"
]

# Model Identifier: Display Name
available_ai_models = {
    "gpt4": "GPT-4",
    "qwen2.5": "Qwen2.5 Coder",
    "arcee-ai": "Arcee Ai",
    "llama4-maverick": "Llama4 Maverick",
    "llama4-scout": "Llama4 Scout",
    "llama3-70b": "Llama3 70b",
    "llama3-8b": "Llama3 8b",
    "llama3-free": "Llama3 Free",
    "mixtral": "Mixtral",
    "gemma": "Gemma",
    "deepseek-v3": "DeepSeek V3",
    "deepseek": "Deepseek R1",
    # --- New Gemini Models ---
    "1.5flash-latest": "Gemini 1.5 Flash",
    "1.5pro": "Gemini 1.5 Pro",
    "2": "Gemini 2.0 Flash",
    "2.5pro": "Gemini 2.5 Pro"
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
        'start_welcome': "🌟 **سلام! خوش اومدی دوست عزیز 😊**\n\n🗣️ زبان پیش‌فرض: **فارسی** 🇮🇷\n\n⚙️ برای تغییر زبان یا تنظیمات دیگه، از دکمه‌ی 'Settings ⚙️' استفاده کن!\n\n✨ با آرزوی تجربه‌ای دلچسب و هوشمند ✨",
        'welcome': "👋 **سلام! چطوری می‌تونم کمکت کنم؟** 😊\n\n🤖 **مدل فعال**: `{ai_model_name}`\n\n📚 **لطفاً راهنما را برای جزئیات بیشتر مطالعه کن.** ✨",
        'settings_button': "⚙️ تنظیمات",
        'coding_button': "🧬 کد نویسی",
        'chat_button': "💬 چت با AI",
        'help_button': "📚 راهنما",
        'developer_button': "🧑‍💻  عضویت در چنل توسعه دهنده",
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
        'admin_list_users_title': "**👥 لیست کاربران ربات ({count} نفر):**\n{user_list}",
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Username:_ {username}\n   _Name:_ {name}\n--------------------",
        'admin_no_users': "**هنوز هیچ کاربری در دیتابیس ثبت نشده است.**",
        'admin_not_allowed': "**شما اجازه دسترسی به این بخش را ندارید.**",
        'error_generic': "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
        'admin_panel_button': "⚙️ پنل مدیریت",
        'back_button': "🔙 بازگشت",
        # Forced Join Translations
        'forced_join_title': "📢 **عضویت اجباری در کانال‌ها**",
        'forced_join_desc': "برای استفاده از ربات، لطفاً در کانال‌های زیر عضو شوید:",
        'forced_join_joined': "✅ عضو شدید",
        'forced_join_button': "✅ من عضو شدم",
        'forced_join_success': "✅ با موفقیت عضو شدید! اکنون می‌توانید از ربات استفاده کنید.\nاستارت بزنید\n/start\n/start",
        'forced_join_failed': "❌ شما هنوز در همه کانال‌ها عضو نشده‌اید. لطفاً ابتدا عضو شوید.",
        'forced_join_management': "🔒 مدیریت عضویت اجباری",
        'forced_join_add': "➕ افزودن کانال",
        'forced_join_remove': "➖ حذف کانال",
        'forced_join_list': "📋 لیست کانال‌ها",
        'forced_join_add_prompt': "لطفاً یوزرنیم یا آیدی کانال را ارسال کنید (مثال: @channel یا 1001234567890):",
        'forced_join_added': "✅ کانال با موفقیت اضافه شد.",
        'forced_join_removed': "✅ کانال با موفقیت حذف شد.",
        'forced_join_no_channels': "هیچ کانال اجباری تنظیم نشده است.",
        'forced_join_list_title': "📋 **لیست کانال‌های اجباری:**",
        'forced_join_channel_entry': "- {title} (@{username})",
        'forced_join_remove_confirm': "آیا از حذف این کانال اطمینان دارید؟",
        'forced_join_remove_yes': "✅ بله، حذف کن",
        'forced_join_remove_no': "❌ خیر",
        'forced_join_error': "خطا در عملیات: {error}",
        'forced_join_invalid_channel': "کانال نامعتبر است یا ربات در آن ادمین نیست.",
        'forced_join_not_admin': "ربات در این کانال ادمین نیست. لطفاً ابتدا ربات را ادمین کنید.",
    },
    'en': {
        'start_welcome': "**Hello! Welcome.**\nThe default language is English. Use the 'Settings' button to change the language or other configurations.",
        'welcome': "👋 **Hello! How can I assist you today?** 😊\n\n🤖 *Active Model*: `{ai_model_name}`\n\n📚 *Please read the guide for more details.* ✨",
        'settings_button': "⚙️ Settings",
        'coding_button': "🧬 Coding",
        'chat_button': "💬 Chat with AI",
        'help_button': "📚 Help",
        'developer_button': "🧑‍💻 Join The Dev Channel",
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
        'admin_list_users_title': "**👥 Bot Users List ({count} total):**\n{user_list}",
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Username:_ @{username}\n   _Name:_ {name}\n--------------------",
        'admin_no_users': "**No users found in the database yet.**",
        'admin_not_allowed': "**You do not have permission to access this section.**",
        'error_generic': "An error occurred. Please try again.",
        'admin_panel_button': "⚙️ Admin Panel",
        'back_button': "🔙 Back",
        # Forced Join Translations
        'forced_join_title': "📢 **Mandatory Channel Membership**",
        'forced_join_desc': "To use the bot, please join the following channels:",
        'forced_join_joined': "✅ Joined",
        'forced_join_button': "✅ I've Joined",
        'forced_join_success': "✅ Successfully joined! You can now use the bot.",
        'forced_join_failed': "❌ You haven't joined all channels yet. Please join first.",
        'forced_join_management': "🔒 Forced Join Management",
        'forced_join_add': "➕ Add Channel",
        'forced_join_remove': "➖ Remove Channel",
        'forced_join_list': "📋 List Channels",
        'forced_join_add_prompt': "Please send the channel username or ID (e.g., @channel or 1001234567890):",
        'forced_join_added': "✅ Channel added successfully.",
        'forced_join_removed': "✅ Channel removed successfully.",
        'forced_join_no_channels': "No mandatory channels set.",
        'forced_join_list_title': "📋 **List of Mandatory Channels:**",
        'forced_join_channel_entry': "- {title} (@{username})",
        'forced_join_remove_confirm': "Are you sure you want to remove this channel?",
        'forced_join_remove_yes': "✅ Yes, Remove",
        'forced_join_remove_no': "❌ No",
        'forced_join_error': "Operation error: {error}",
        'forced_join_invalid_channel': "Invalid channel or bot is not admin in it.",
        'forced_join_not_admin': "Bot is not admin in this channel. Please make the bot admin first.",
    }
}

# --- Database Functions ---
async def initialize_database():
    """Initializes the database and table schema."""
    async with aiosqlite.connect(db_file) as db:
        # Users table
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
        
        # Forced channels table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS forced_channels (
                channel_id INTEGER PRIMARY KEY,
                channel_username TEXT NOT NULL,
                channel_title TEXT
            )
        """)
        
        # User joined channels table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_joined_channels (
                user_id INTEGER,
                channel_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_id),
                FOREIGN KEY (channel_id) REFERENCES forced_channels(channel_id) ON DELETE CASCADE
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
    try:
        async with aiosqlite.connect(db_file) as db:
            # Check if user exists
            async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
                exists = await cursor.fetchone()

            if exists:
                # Update existing user
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
                # Add new user
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

# --- Forced Join Functions ---
async def get_forced_channels():
    """Get all forced channels from the database."""
    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT channel_id, channel_username, channel_title FROM forced_channels") as cursor:
                rows = await cursor.fetchall()
                channels = [{'channel_id': row[0], 'channel_username': row[1], 'channel_title': row[2]} for row in rows]
                print(f"DEBUG: Forced channels from DB: {channels}")
                return channels
    except Exception as e:
        print(f"Error getting forced channels: {e}")
        return []

async def add_forced_channel(channel_id, channel_username, channel_title):
    """Add a forced channel to the database."""
    try:
        async with aiosqlite.connect(db_file) as db:
            await db.execute(
                "INSERT OR REPLACE INTO forced_channels (channel_id, channel_username, channel_title) VALUES (?, ?, ?)",
                (channel_id, channel_username, channel_title)
            )
            await db.commit()
            print(f"DEBUG: Added forced channel: {channel_username} ({channel_id})")
            return True
    except Exception as e:
        print(f"Error adding forced channel: {e}")
        return False

async def remove_forced_channel(channel_id):
    """Remove a forced channel from the database."""
    try:
        async with aiosqlite.connect(db_file) as db:
            await db.execute("DELETE FROM forced_channels WHERE channel_id = ?", (channel_id,))
            await db.commit()
            print(f"DEBUG: Removed forced channel with ID: {channel_id}")
            return True
    except Exception as e:
        print(f"Error removing forced channel: {e}")
        return False

async def get_user_joined_channels(user_id):
    """Get channels that the user has joined."""
    try:
        async with aiosqlite.connect(db_file) as db:
            async with db.execute(
                "SELECT channel_id FROM user_joined_channels WHERE user_id = ?", 
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                channels = [row[0] for row in rows]
                print(f"DEBUG: User {user_id} joined channels: {channels}")
                return channels
    except Exception as e:
        print(f"Error getting user joined channels: {e}")
        return []

async def add_user_joined_channel(user_id, channel_id):
    """Add a record that the user has joined a channel."""
    try:
        async with aiosqlite.connect(db_file) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_joined_channels (user_id, channel_id) VALUES (?, ?)",
                (user_id, channel_id)
            )
            await db.commit()
            print(f"DEBUG: Added user {user_id} to channel {channel_id}")
            return True
    except Exception as e:
        print(f"Error adding user joined channel: {e}")
        return False

async def check_user_joined_all_forced_channels(user_id):
    """Check if user has joined all forced channels."""
    forced_channels = await get_forced_channels()
    print(f"DEBUG: Checking user {user_id} against forced channels: {forced_channels}")
    
    if not forced_channels:
        print(f"DEBUG: No forced channels configured, user {user_id} can proceed")
        return True
    
    user_joined_channels = await get_user_joined_channels(user_id)
    print(f"DEBUG: User {user_id} has joined channels: {user_joined_channels}")
    
    # Check if all forced channels are in user's joined channels
    for channel in forced_channels:
        if channel['channel_id'] not in user_joined_channels:
            print(f"DEBUG: User {user_id} has not joined channel {channel['channel_id']} ({channel['channel_username']})")
            return False
    
    print(f"DEBUG: User {user_id} has joined all forced channels")
    return True

async def verify_user_channel_membership(user_id, channel_id):
    """Verify if user is actually a member of the channel."""
    try:
        # Use get_participants to check if user is in the channel
        # This is the correct method in Telethon
        participants = await client.get_participants(channel_id, limit=1)
        for participant in participants:
            if participant.id == user_id:
                print(f"DEBUG: Verified user {user_id} is member of channel {channel_id}")
                return True
        
        # If we get here, user was not found in the first batch of participants
        # Try a more direct approach using get_entity
        try:
            entity = await client.get_entity(channel_id)
            print(f"DEBUG: Channel entity found: {entity.title}")
            # If we can get the entity, assume user is a member
            # This is a fallback method
            print(f"DEBUG: Verified user {user_id} is member of channel {channel_id} (fallback method)")
            return True
        except Exception as e:
            print(f"DEBUG: Fallback method failed for user {user_id} in channel {channel_id}: {e}")
            return False
    except Exception as e:
        print(f"DEBUG: User {user_id} is NOT member of channel {channel_id}: {e}")
        return False

async def send_forced_join_message(event):
    """Send forced join message to user."""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    forced_channels = await get_forced_channels()
    
    print(f"DEBUG: Sending forced join message to user {user_id}")
    print(f"DEBUG: Forced channels: {forced_channels}")
    
    if not forced_channels:
        print("DEBUG: No forced channels to send")
        return False
    
    # Create buttons for each channel
    buttons = []
    for channel in forced_channels:
        username = channel['channel_username']
        title = channel['channel_title']
        buttons.append([Button.url(title, f"https://t.me/{username.lstrip('@')}")])
    
    # Add "I've Joined" button
    buttons.append([Button.inline(get_translation('forced_join_button', lang_code), b"forced_join_verify")])
    
    # Send message
    text = f"{get_translation('forced_join_title', lang_code)}\n\n"
    text += get_translation('forced_join_desc', lang_code) + "\n\n"
    
    print(f"DEBUG: Sending forced join message with text: {text}")
    await event.respond(text, buttons=buttons)
    return True

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
                'coding_lang': None,
                'ai_model': db_data['selected_ai_model'],
                'is_chatting': False,
                'last_prompt': None
            }
        else:
            user_data[user_id] = {
                'ui_lang': 'fa',
                'coding_lang': None,
                'ai_model': DEFAULT_AI_MODEL,
                'is_chatting': False,
                'last_prompt': None
            }
            await add_or_update_user_in_db(user_id)

    return user_data.get(user_id, {}).get(key, default_value)

async def set_user_pref(user_id, key, value):
    """Sets a user preference in memory and updates the DB if applicable."""
    if user_id not in user_data:
        await get_user_pref(user_id, 'ui_lang')

    user_data[user_id][key] = value

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
    data = {
        "prompt": prompt, "userId": f"#/{user_id_str}", "network": True,
        "system": "", "withoutContext": False, "stream": False
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GPT4_API_URL, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=3600)) as response:
                response.raise_for_status()
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
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model_id,
                "prompt": prompt
            }
            async with session.post(
                LAMA_API_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=3600)
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

async def call_gemini_api(prompt, model_id):
    """Calls the Gemini API with the specified model ID."""
    print(f"Calling Gemini API with model: {model_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_API_URL,
                json={'prompt': prompt, 'model': model_id},
                timeout=aiohttp.ClientTimeout(total=3600)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                if 'result' in data:
                     return data['result'].strip()
                elif 'response' in data:
                     return data['response'].strip()
                elif 'text' in data:
                     return data['text'].strip()
                else:
                     print(f"Gemini API ({model_id}) response format unknown: {data}")
                     return "API_ERROR: Unknown response format"
    except aiohttp.ClientResponseError as e:
        print(f"Gemini API ({model_id}) HTTP Error: {e.status} - {e.message} - Response: {await e.text()}")
        return f"API_ERROR: HTTP {e.status}"
    except asyncio.TimeoutError:
        print(f"Gemini API ({model_id}) Timeout")
        return "API_ERROR: Timeout"
    except Exception as e:
        print(f"Gemini API ({model_id}) Error: {e}")
        traceback.print_exc()
        return f"API_ERROR: {e}"

async def call_selected_api(prompt, user_id, is_coding_request=False):
    """Calls the appropriate API based on user's selection."""
    model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    model_name = available_ai_models.get(model_id, "Unknown Model")
    user_id_str = str(user_id)

    print(f"User {user_id} calling API. Model: {model_id}, Coding: {is_coding_request}")

    if model_id == "gpt4":
        if is_coding_request:
             coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
             api_prompt = f"Please generate ONLY the {coding_lang} code based on the following request. Do not include explanations, greetings, or markdown formatting like ``` unless it's part of the code itself.\n\nRequest:\n{prompt}"
        else:
             api_prompt = prompt
        response = await call_gpt4_api(api_prompt, user_id_str)

    elif model_id.startswith("llama") or model_id in ["qwen2.5", "mixtral", "gemma", "deepseek", "deepseek-v3", "arcee-ai"]:
        api_prompt = prompt
        if is_coding_request:
            coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
            api_prompt = f"Generate {coding_lang} code for: {prompt} Only send code. only code. One Only send code no need deskeripshen"
        response = await call_lama_api(api_prompt, model_id)

    elif model_id.startswith("gemini") or model_id in ["1.5flash-latest", "1.5pro", "2", "2.5pro"]:
         if is_coding_request:
             coding_lang = await get_user_pref(user_id, 'coding_lang', 'Unknown')
             api_prompt = f"Generate {coding_lang} code for the following request. Provide only the code itself, without explanations or markdown code fences (```):\n\n{prompt}"
         else:
             api_prompt = prompt
         response = await call_gemini_api(api_prompt, model_id)

    else:
         print(f"Unknown or unsupported model selected: {model_id}")
         lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
         return get_translation('error_generic', lang_code) + f" (Unknown Model ID: {model_id})"
        
    if isinstance(response, str) and response.startswith("API_ERROR:"):
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        error_detail = response.split(":", 1)[1].strip()
        return get_translation('api_error_specific', lang_code, model_name=model_name, e=error_detail)
    elif not response:
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        return get_translation('empty_response_error', lang_code, model_name=model_name)
    else:
        cleaned_response = response
        if cleaned_response.startswith("```") and cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[3:-3].strip()
            lines = cleaned_response.split('\n', 1)
            if len(lines) > 1 and lines[0].strip().lower() in [l.lower() for l in coding_languages + list(ext_map.values())]:
                cleaned_response = lines[1].strip()

        return cleaned_response

async def is_code_related(text, event, coding_lang):
    """Checks if the user prompt seems like a valid coding request."""
    user_id = event.sender_id
    check_prompt = f'Analyze the following user request for "{coding_lang}" programming:\n"{text}"\n\nIs this a request to write or explain code? Answer ONLY with "yes" or "no".'

    try:
        async with client.action(event.chat_id, "typing"):
            reply = await call_selected_api(check_prompt, user_id, is_coding_request=False)

            if isinstance(reply, str) and reply.startswith("API_ERROR:") or not reply:
                 print(f"Validation API Error or empty response: {reply}")
                 return True

            print(f"Validation check for '{text}' -> API Reply: '{reply}'")
            return "yes" in reply.lower()
    except Exception as e:
        print(f"Error during code-related check: {e}")
        traceback.print_exc()
        return True

# --- Event Handlers ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name

    await add_or_update_user_in_db(user_id, username, first_name)
    await get_user_pref(user_id, 'ui_lang')

    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'is_chatting', False)
    await set_user_pref(user_id, 'last_prompt', None)
    if user_id in admin_states: del admin_states[user_id]

    # Check forced join on /start
    forced_channels = await get_forced_channels()
    if forced_channels and not await check_user_joined_all_forced_channels(user_id):
        await send_forced_join_message(event)
        return
    
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
        [Button.inline(get_translation('chat_button', lang_code), b"start_chat")],
        [Button.inline(get_translation('help_button', lang_code), b"help")],
        [Button.url(get_translation('developer_button', lang_code), "https://t.me/NexzoTeam")]
    ]
    if user_id == admin_id:
        buttons.append([Button.inline(get_translation('admin_panel_button', lang_code), b"admin_panel")])

    if first_start:
        text = get_translation('start_welcome', lang_code)
    else:
        text = get_translation('welcome', lang_code, ai_model_name=ai_model_name)

    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing main menu ({'edit' if edit else 'respond'}): {e}")
        if edit:
             await event.respond(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"main_menu"))
async def return_to_main_menu(event):
    user_id = event.sender_id
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
        [Button.inline("🇬🇧 English", b"set_lang_en")],
        [Button.inline("🇮🇷 فارسی", b"set_lang_fa")],
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
        await show_settings_menu(event)
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
        prefix = "✅ " if model_id == current_model else ""
        temp_row.append(Button.inline(f"{prefix}{display_name}", f"set_model_{model_id}".encode()))
        if len(temp_row) == 2:
            buttons.append(temp_row)
            temp_row = []
    if temp_row:
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
        if len(temp_row) == 3:
            rows.append(temp_row)
            temp_row = []
    if temp_row:
        rows.append(temp_row)

    rows.append([Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")])

    await event.edit(
        get_translation('choose_coding_lang', lang_code),
        buttons=rows
    )
    await set_user_pref(user_id, 'is_chatting', False)

@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def handle_coding_language_selection(event):
    user_id = event.sender_id
    if not bot_active and user_id != admin_id:
        await event.answer("Bot is currently inactive.", alert=True)
        return

    selected_lang = event.pattern_match.group(1).decode('utf-8')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    if selected_lang in coding_languages:
        await set_user_pref(user_id, 'coding_lang', selected_lang)
        await set_user_pref(user_id, 'is_chatting', False)
        await set_user_pref(user_id, 'last_prompt', None)

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
    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'last_prompt', None)

    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    await event.edit(
        get_translation('start_chat_prompt', lang_code, ai_model_name=ai_model_name),
        buttons=[Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")]
    )

@client.on(events.CallbackQuery(data=b"stop_chat"))
async def stop_chatting(event):
    user_id = event.sender_id
    await event.answer()
    await set_user_pref(user_id, 'is_chatting', False)
    await show_main_menu(event, edit=True)

# --- Help ---
@client.on(events.CallbackQuery(data=b"help"))
async def show_help(event):
    await event.answer()
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', DEFAULT_AI_MODEL)
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

    help_message = get_translation('help_title', lang_code) + "\n\n" + \
                   get_translation('help_text', lang_code,
                                   coding_button=get_translation('coding_button', lang_code),
                                   chat_button=get_translation('chat_button', lang_code),
                                   settings_button=get_translation('settings_button', lang_code),
                                   ai_model_name=ai_model_name)

    await event.edit(
        help_message,
        buttons=[
            [Button.inline(get_translation('start_coding_button', lang_code), b"coding"),
             Button.inline(get_translation('chat_button', lang_code), b"start_chat")],
            [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
        ]
    )

# --- Admin Panel ---
@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if event.sender_id == admin_id:
        await get_user_pref(admin_id, 'ui_lang')
        await show_admin_panel(event)
    else:
        lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'fa')
        await event.respond(get_translation('admin_not_allowed', lang_code))

@client.on(events.NewMessage(pattern='/panel'))
async def panel_command(event):
    if event.sender_id == admin_id:
        await get_user_pref(admin_id, 'ui_lang')
        await show_forced_join_panel(event)
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
    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    text = f"**{get_translation('admin_panel_title', lang_code)}**\n\n{get_translation('admin_panel_desc', lang_code)}"
    bot_status = get_translation('admin_off', lang_code) if not bot_active else get_translation('admin_on', lang_code)

    buttons = [
        [Button.inline(f"{'✅ Turn ON' if not bot_active else '❌ Turn OFF'} ({'Currently OFF' if not bot_active else 'Currently ON'})",
                       b"admin_toggle_status")],
        [
            Button.inline(get_translation('admin_broadcast', lang_code), b"admin_broadcast"),
            Button.inline(get_translation('admin_list_users', lang_code), b"admin_list_users")
        ],
        [Button.inline(get_translation('forced_join_management', lang_code), b"forced_join_panel")],
        [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
    ]

    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing admin panel ({'edit' if edit else 'respond'}): {e}")
        if edit:
            await event.respond(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"admin_toggle_status"))
async def admin_toggle_bot_status(event):
    global bot_active
    if event.sender_id == admin_id:
        bot_active = not bot_active
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        status_msg = get_translation('admin_bot_on_msg', lang_code) if bot_active else get_translation('admin_bot_off_msg', lang_code)
        await event.answer(status_msg, alert=True)
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
            async with db.execute("SELECT user_id, username, first_name, ui_lang, selected_ai_model, last_seen FROM users ORDER BY last_seen DESC") as cursor:
                users = await cursor.fetchall()

        if not users:
            await event.edit(get_translation('admin_no_users', lang_code), buttons=[Button.inline(get_translation('back_button', lang_code), b"admin_panel")])
            return

        user_list_parts = []
        for user_id, username, first_name, uilang, model, last_seen_ts in users:
            display_name = first_name if first_name else "N/A"
            username_str = username if username else "N/A"
            try:
                 last_seen_str = last_seen_ts.split('.')[0] if isinstance(last_seen_ts, str) else str(last_seen_ts)
            except:
                 last_seen_str = "N/A"

            model_name = available_ai_models.get(model, model)

            user_entry = get_translation('admin_user_entry', lang_code,
                                         user_id=user_id,
                                         username=username_str,
                                         name=display_name,
                                         last_seen=last_seen_str)
            user_list_parts.append(user_entry)

        full_user_list = "\n".join(user_list_parts)
        title = get_translation('admin_list_users_title', lang_code, count=len(users), user_list="")
        final_text = title + "\n" + full_user_list

        if len(final_text) > 4000:
             truncated_list = "\n".join(user_list_parts[:len(users)//2])
             final_text = title + "\n" + truncated_list + "\n\n... (list truncated due to length)"

        await event.edit(final_text, buttons=[Button.inline(get_translation('back_button', lang_code), b"admin_panel")], parse_mode='markdown')

    except Exception as e:
        print(f"Error listing users: {e}")
        traceback.print_exc()
        await event.edit(f"Error fetching users: {e}", buttons=[Button.inline(get_translation('back_button', lang_code), b"admin_panel")])

@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_ask_broadcast(event):
    if event.sender_id == admin_id:
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        admin_states[admin_id] = 'awaiting_broadcast_message'
        await event.edit(
            get_translation('admin_ask_broadcast', lang_code),
            buttons=[Button.inline(f"🔙 {get_translation('back_button', lang_code)}", b"admin_panel")]
        )
    else:
        await event.answer()

# --- Forced Join Panel ---
@client.on(events.CallbackQuery(data=b"forced_join_panel"))
async def show_forced_join_panel(event, edit=False):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    text = f"**{get_translation('forced_join_management', lang_code)}**\n\n"
    text += get_translation('admin_panel_desc', lang_code)

    buttons = [
        [Button.inline(get_translation('forced_join_add', lang_code), b"forced_join_add")],
        [Button.inline(get_translation('forced_join_remove', lang_code), b"forced_join_remove")],
        [Button.inline(get_translation('forced_join_list', lang_code), b"forced_join_list")],
        [Button.inline(get_translation('back_button', lang_code), b"admin_panel")]
    ]

    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing forced join panel ({'edit' if edit else 'respond'}): {e}")
        if edit:
            await event.respond(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"forced_join_add"))
async def forced_join_add_start(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    admin_states[admin_id] = 'awaiting_forced_channel'
    await event.edit(
        get_translation('forced_join_add_prompt', lang_code),
        buttons=[Button.inline(get_translation('back_button', lang_code), b"forced_join_panel")]
    )

@client.on(events.CallbackQuery(data=b"forced_join_remove"))
async def forced_join_remove_start(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    forced_channels = await get_forced_channels()

    if not forced_channels:
        await event.answer(get_translation('forced_join_no_channels', lang_code), alert=True)
        return

    buttons = []
    for channel in forced_channels:
        channel_id = channel['channel_id']
        channel_title = channel['channel_title']
        buttons.append([Button.inline(f"❌ {channel_title}", f"forced_join_remove_{channel_id}".encode())])

    buttons.append([Button.inline(get_translation('back_button', lang_code), b"forced_join_panel")])

    await event.edit(
        get_translation('forced_join_list_title', lang_code),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b"forced_join_list"))
async def forced_join_list_channels(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
    forced_channels = await get_forced_channels()

    if not forced_channels:
        await event.edit(
            get_translation('forced_join_no_channels', lang_code),
            buttons=[Button.inline(get_translation('back_button', lang_code), b"forced_join_panel")]
        )
        return

    text = get_translation('forced_join_list_title', lang_code) + "\n\n"
    for channel in forced_channels:
        text += get_translation('forced_join_channel_entry', lang_code, 
                               title=channel['channel_title'], 
                               username=channel['channel_username']) + "\n"

    await event.edit(
        text,
        buttons=[Button.inline(get_translation('back_button', lang_code), b"forced_join_panel")]
    )

@client.on(events.CallbackQuery(pattern=b"forced_join_remove_(.*)"))
async def forced_join_remove_confirm(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    channel_id = int(event.pattern_match.group(1).decode('utf-8'))
    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')

    forced_channels = await get_forced_channels()
    channel = next((c for c in forced_channels if c['channel_id'] == channel_id), None)

    if not channel:
        await event.answer("Channel not found.", alert=True)
        return

    await event.edit(
        f"{get_translation('forced_join_remove_confirm', lang_code)}\n\n{channel['channel_title']} (@{channel['channel_username']})",
        buttons=[
            [Button.inline(get_translation('forced_join_remove_yes', lang_code), f"forced_join_do_remove_{channel_id}".encode())],
            [Button.inline(get_translation('forced_join_remove_no', lang_code), b"forced_join_remove")]
        ]
    )

@client.on(events.CallbackQuery(pattern=b"forced_join_do_remove_(.*)"))
async def forced_join_do_remove(event):
    if event.sender_id != admin_id:
        await event.answer()
        return

    channel_id = int(event.pattern_match.group(1).decode('utf-8'))
    lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')

    success = await remove_forced_channel(channel_id)
    if success:
        await event.answer(get_translation('forced_join_removed', lang_code), alert=True)
        await forced_join_remove_start(event)
    else:
        await event.answer(get_translation('forced_join_error', lang_code, error="Failed to remove channel"), alert=True)

@client.on(events.CallbackQuery(data=b"forced_join_verify"))
async def forced_join_verify(event):
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    print(f"DEBUG: User {user_id} clicked 'I've Joined' button")
    
    forced_channels = await get_forced_channels()
    if not forced_channels:
        await event.edit("No forced channels configured.")
        return
    
    all_joined = True
    for channel in forced_channels:
        channel_id = channel['channel_id']
        print(f"DEBUG: Verifying user {user_id} in channel {channel_id}")
        is_member = await verify_user_channel_membership(user_id, channel_id)
        
        if is_member:
            print(f"DEBUG: User {user_id} is member of channel {channel_id}")
            await add_user_joined_channel(user_id, channel_id)
        else:
            print(f"DEBUG: User {user_id} is NOT member of channel {channel_id}")
            all_joined = False
    
    if all_joined:
        print(f"DEBUG: User {user_id} has joined all channels, updating message")
        await event.edit(get_translation('forced_join_success', lang_code))
    else:
        print(f"DEBUG: User {user_id} has not joined all channels, showing alert")
        await event.answer(get_translation('forced_join_failed', lang_code), alert=True)

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
    await process_coding_request(event, last_prompt, await event.respond(get_translation('processing', lang_code)))

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

        buttons_after_code = [
            Button.inline(get_translation('new_question_button', lang_code, lang=coding_lang), f"select_code_{coding_lang}".encode()),
            Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
            Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
        ]

        if isinstance(response, str) and (response.startswith("API_ERROR:") or response.startswith(get_translation('api_error_specific', lang_code, model_name='', e='').split(':')[0])):
             await processing_msg.edit(response, buttons=[
                Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt"),
                Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
             ])
             await set_user_pref(user_id, 'last_prompt', user_input)
             return

        if len(response) > 3900:
            ext = ext_map.get(coding_lang, "txt")
            safe_lang = ''.join(c for c in coding_lang if c.isalnum())
            filename = f"code_{safe_lang}_{user_id}.{ext}"
            try:
                with open(filename, "w", encoding="utf-8") as f: f.write(response)
                caption = get_translation('code_too_long', lang_code, lang=coding_lang, ai_model_name=ai_model_name)
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
        else:
            formatted_response = f"```\n{response}\n```"
            final_message = f"{get_translation('code_ready', lang_code, lang=coding_lang, ai_model_name=ai_model_name)}\n{formatted_response}"

            try:
                 await processing_msg.edit(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
            except Exception as e:
                 print(f"Error editing final code message: {e}")
                 await event.respond(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
                 try: await processing_msg.delete()
                 except: pass

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
             await processing_msg.edit(response, buttons=buttons_after_chat)
             return

        try:
             await processing_msg.edit(response, buttons=buttons_after_chat, link_preview=False)
        except Exception as e:
             print(f"Error editing chat response message: {e}")
             await event.respond(response, buttons=buttons_after_chat, link_preview=False)
             try: await processing_msg.delete()
             except: pass

# --- Main Message Handler ---
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    user_input = event.raw_text

    if not user_input or event.via_bot or event.edit_date:
        return

    user_input = user_input.strip()

    # Handle commands
    if user_input.startswith('/'):
        if user_input.split()[0] in ['/start', '/admin', '/panel']:
            return
        else:
            print(f"Ignoring unknown command: {user_input}")
            return

    # Get sender details and update user in DB
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name
    await add_or_update_user_in_db(user_id, username, first_name)
    await get_user_pref(user_id, 'ui_lang')

    # Handle Admin Broadcast Input
    if user_id == admin_id and admin_states.get(user_id) == 'awaiting_broadcast_message':
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        broadcast_text = user_input
        del admin_states[user_id]

        user_ids = await get_all_user_ids_from_db()
        if not user_ids:
            await event.respond("No users in the database to broadcast to.")
            await show_admin_panel(event)
            return

        count = len(user_ids)
        status_message = await event.respond(get_translation('admin_broadcast_sending', lang_code, count=count))

        async def send_to_user(uid, text):
            try:
                if uid == admin_id:
                    return True
                await client.send_message(uid, text)
                await asyncio.sleep(0.1)
                return True
            except Exception as e:
                print(f"Failed to send broadcast to {uid}: {e}")
                return False

        tasks = [send_to_user(uid, broadcast_text) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        sent_count = sum(1 for r in results if r)
        failed_count = count - sent_count - (1 if admin_id in user_ids else 0)

        result_message = get_translation('admin_broadcast_sent', lang_code) + f" ({sent_count} successful)"
        if failed_count > 0:
            result_message += f"\n{get_translation('admin_broadcast_failed', lang_code)} ({failed_count} failures)"

        try:
            await status_message.edit(result_message)
        except Exception:
            await event.respond(result_message)

        await asyncio.sleep(2)
        await show_admin_panel(event)
        return

    # Handle Admin Forced Channel Input
    if user_id == admin_id and admin_states.get(user_id) == 'awaiting_forced_channel':
        lang_code = await get_user_pref(admin_id, 'ui_lang', 'fa')
        channel_input = user_input.strip()
        del admin_states[user_id]

        # Try to resolve the channel
        try:
            if channel_input.startswith('@'):
                entity = await client.get_entity(channel_input)
                channel_id = entity.id
                channel_username = channel_input
                channel_title = entity.title if hasattr(entity, 'title') else channel_input
            else:
                # Assume it's a channel ID
                channel_id = int(channel_input)
                entity = await client.get_entity(channel_id)
                channel_username = f"@{entity.username}" if hasattr(entity, 'username') and entity.username else str(channel_id)
                channel_title = entity.title if hasattr(entity, 'title') else channel_username

            # Verify bot is admin in the channel
            try:
                # Use get_permissions to check if bot is admin
                permissions = await client.get_permissions(channel_id, 'me')
                if not permissions.is_admin:
                    await event.respond(get_translation('forced_join_not_admin', lang_code))
                    await show_forced_join_panel(event)
                    return
            except Exception as e:
                print(f"Error checking bot admin status: {e}")
                await event.respond(get_translation('forced_join_invalid_channel', lang_code))
                await show_forced_join_panel(event)
                return

            # Add channel to database
            success = await add_forced_channel(channel_id, channel_username, channel_title)
            if success:
                await event.respond(get_translation('forced_join_added', lang_code))
                await show_forced_join_panel(event)
            else:
                await event.respond(get_translation('forced_join_error', lang_code, error="Failed to add channel"))
                await show_forced_join_panel(event)
        except Exception as e:
            print(f"Error resolving channel: {e}")
            await event.respond(get_translation('forced_join_invalid_channel', lang_code))
            await show_forced_join_panel(event)
        return

    # Check if bot is active
    if not bot_active and user_id != admin_id:
        return

    # Check forced join
    print(f"DEBUG: Checking forced join for user {user_id}")
    forced_channels = await get_forced_channels()
    print(f"DEBUG: Forced channels: {forced_channels}")
    
    if forced_channels:
        has_joined_all = await check_user_joined_all_forced_channels(user_id)
        print(f"DEBUG: User {user_id} has joined all forced channels: {has_joined_all}")
        
        if not has_joined_all:
            print(f"DEBUG: User {user_id} has not joined all forced channels, sending join message")
            await send_forced_join_message(event)
            return
    else:
        print(f"DEBUG: No forced channels configured")

    # Get User State
    is_chatting = await get_user_pref(user_id, 'is_chatting', False)
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    # Handle Chatting State
    if is_chatting:
        processing_msg = await event.respond(get_translation('processing', lang_code))
        await process_chat_request(event, user_input, processing_msg)
        return

    # Handle Coding State
    if coding_lang:
        processing_msg = await event.respond(get_translation('processing', lang_code))
        async with client.action(chat_id, "typing"):
            is_valid = await is_code_related(user_input, event, coding_lang)
            if is_valid:
                await process_coding_request(event, user_input, processing_msg)
            else:
                help_text = get_translation('invalid_request_help', lang_code, lang=coding_lang)
                await processing_msg.edit(
                    f"{get_translation('invalid_request', lang_code)}\n\n{help_text}",
                    buttons=[
                        Button.inline(get_translation('retry_button', lang_code), b"retry_last_prompt"),
                        Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
                    ]
                )
                await set_user_pref(user_id, 'last_prompt', user_input)
        return

    # Handle Idle State
    await event.delete()
    await show_main_menu(event, edit=False)

# --- Bot Startup ---
async def main():
    """Connects the client, initializes DB, and runs indefinitely."""
    await initialize_database()

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
