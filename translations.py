# translations.py
translations = {
    'fa': {
        'start_welcome': "🌟 **سلام! خوش اومدی دوست عزیز 😊**\n\n🗣️ زبان پیش‌فرض: **فارسی** 🇮🇷\n\n⚙️ برای تغییر زبان یا تنظیمات دیگه، از دکمه‌ی 'Settings ⚙️' استفاده کن!\n\n✨ با آرزوی تجربه‌ای دلچسب و هوشمند ✨",
        'welcome': "👋 **سلام! چطوری می‌تونم کمکت کنم؟** 😊\n\n🤖 **مدل فعال**: `{ai_model_name}`\n\n📚 **لطفاً راهنما را برای جزئیات بیشتر مطالعه کن.** ✨",
        'mandatory_join': "⚠️ **برای استفاده از ربات، ابتدا باید در کانال‌های زیر عضو شوید:**\n\n{channels}\n\nپس از عضویت، دکمه ✅ **عضو شدم** را بزنید.",
        'joined_button': "✅ عضو شدم",
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
        'admin_user_entry': "👤 `ID: {user_id}`\n   _Username:_ @{username}\n   _Name:_ {name}\n--------------------",
        'admin_no_users': "**هنوز هیچ کاربری در دیتابیس ثبت نشده است.**",
        'admin_not_allowed': "**شما اجازه دسترسی به این بخش را ندارید.**",
        'error_generic': "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
        'admin_panel_button': "⚙️ پنل مدیریت",
        'back_button': "🔙 بازگشت",
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
**❗️ نکته مهم:**\nبرای تجربه‌ای بهتر و پاسخ‌های دقیق‌تر، از مدل‌های قدرتمند مثل:\n🔹 `DeepSeek`\n🔹 `Gemini`\n🔹 `GPT`\nاستفاده کنید. 🚀

❗️ **توجه**: ربات در حالت کدنویسی فقط درخواست‌های مرتبط با برنامه‌نویسی را پردازش می‌کند.

💡 لذت ببرید!
        """,
        'start_coding_button': "🏁 شروع کدنویسی!",
        'start_chat_prompt': "✅ بسیار خب! حالا می‌تونی با مدل {ai_model_name} چت کنی. پیامت رو بفرست.",
        'stop_chat_button': "⏹️ پایان چت (منوی اصلی)",
    },
    'en': {
        'start_welcome': "**Hello! Welcome.**\nThe default language is English. Use the 'Settings' button to change the language or other configurations.",
        'welcome': "👋 **Hello! How can I assist you today?** 😊\n\n🤖 *Active Model*: `{ai_model_name}`\n\n📚 *Please read the guide for more details.* ✨",
        'mandatory_join': "⚠️ **To use the bot, you must first join these channels:**\n\n{channels}\n\nAfter joining, press the ✅ **I've Joined** button.",
        'joined_button': "✅ I've Joined",
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
    }
}

def get_translation(key, lang_code='fa', **kwargs):
    """Gets the translated string, defaulting to English."""
    return translations.get(lang_code, translations['fa']).get(key, f"[{key}]").format(**kwargs)
