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
        # ... other translations
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
        # ... other translations
    }
}

def get_translation(key, lang_code='fa', **kwargs):
    """Gets the translated string, defaulting to English."""
    return translations.get(lang_code, translations['fa']).get(key, f"[{key}]").format(**kwargs)
