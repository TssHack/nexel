# main.py
import asyncio
import os
import traceback
import logging
from telethon import TelegramClient, events, Button
import aiosqlite
import aiohttp
from config import API_ID, API_HASH, SESSION_NAME, DEFAULT_ADMIN_ID, AVAILABLE_AI_MODELS, CODING_LANGUAGES, EXT_MAP
from database import initialize_database, add_or_update_user, get_user_data, update_user_field
from database import get_all_user_ids, is_admin, add_admin, remove_admin, get_all_admins
from database import get_mandatory_channels, add_mandatory_channel, remove_mandatory_channel
from translations import get_translation
from utils import get_user_pref, set_user_pref

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot State
bot_active = True
user_data = {}
admin_states = {}

# Initialize client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

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
            async with session.post("https://api.binjie.fun/api/generateStream", json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=3600)) as response:
                response.raise_for_status()
                text = await response.text()
                return text.strip()
    except Exception as e:
        logger.error(f"GPT4 API Error: {e}")
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
                "http://lama-ehsan.vercel.app/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=3600)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get('response', '').strip()
    except Exception as e:
        logger.error(f"Llama API Error: {e}")
        return f"API_ERROR: {e}"

async def call_gemini_api(prompt, model_id):
    """Calls the Gemini API with the specified model ID."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://gem-ehsan.vercel.app/gemini/chat",
                json={'prompt': prompt, 'model': model_id},
                timeout=aiohttp.ClientTimeout(total=3600)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                if 'result' in data:
                     return data['result'].strip()
                elif 'response' in data:
                     return data['response'].strip()
                else:
                     logger.error(f"Gemini API response format unknown: {data}")
                     return "API_ERROR: Unknown response format"
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return f"API_ERROR: {e}"

async def call_selected_api(prompt, user_id, is_coding_request=False):
    """Calls the appropriate API based on user's selection."""
    model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    model_name = AVAILABLE_AI_MODELS.get(model_id, "Unknown Model")
    user_id_str = str(user_id)

    logger.info(f"User {user_id} calling API. Model: {model_id}, Coding: {is_coding_request}")

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
         logger.error(f"Unknown model selected: {model_id}")
         lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
         return get_translation('error_generic', lang_code) + f" (Unknown Model ID: {model_id})"
        
    # Process API Response
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
            if len(lines) > 1 and lines[0].strip().lower() in [l.lower() for l in CODING_LANGUAGES + list(EXT_MAP.values())]:
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
                 logger.error(f"Validation API Error: {reply}")
                 return True
            logger.info(f"Validation check for '{text}' -> API Reply: '{reply}'")
            return "yes" in reply.lower()
    except Exception as e:
        logger.error(f"Error during code-related check: {e}")
        return True

# --- Helper Functions ---
async def show_main_menu(event, edit=False, first_start=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

    buttons = [
        [Button.inline(get_translation('settings_button', lang_code), b"settings"),
         Button.inline(get_translation('coding_button', lang_code), b"coding")],
        [Button.inline(get_translation('chat_button', lang_code), b"start_chat")],
        [Button.inline(get_translation('help_button', lang_code), b"help")],
        [Button.url(get_translation('developer_button', lang_code), "https://t.me/NexzoTeam")]
    ]
    if await is_admin(user_id):
        buttons.append([Button.inline(get_translation('admin_panel_button', lang_code), b"admin_panel")])

    if first_start:
        text = get_translation('start_welcome', lang_code)
    else:
        text = get_translation('welcome', lang_code, ai_model_name=ai_model_name)

    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
        logger.info(f"Main menu shown to user {user_id}")
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        if edit:
            await event.respond(text, buttons=buttons)

async def show_settings_menu(event):
    """Display settings menu"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    buttons = [
        [Button.inline(get_translation('settings_lang_button', lang_code), b"change_ui_lang")],
        [Button.inline(get_translation('settings_model_button', lang_code), b"select_ai_model")],
        [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
    ]
    text = get_translation('settings_title', lang_code)
    await event.edit(text, buttons=buttons)
    logger.info(f"Settings menu shown to user {user_id}")

async def show_ui_language_options(event):
    """Show language selection options"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    buttons = [
        [Button.inline("🇬🇧 English", b"set_lang_en")],
        [Button.inline("🇮🇷 فارسی", b"set_lang_fa")],
        [Button.inline(get_translation('back_to_settings', lang_code), b"settings")]
    ]
    text = get_translation('settings_choose_lang', lang_code)
    await event.edit(text, buttons=buttons)
    logger.info(f"Language options shown to user {user_id}")

async def show_ai_model_options(event):
    """Show AI model selection options"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    current_model = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')

    buttons = []
    temp_row = []
    for model_id, display_name in AVAILABLE_AI_MODELS.items():
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
    logger.info(f"AI model options shown to user {user_id}")

async def choose_coding_language(event):
    """Show coding language selection"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    rows = []
    temp_row = []
    for lang in CODING_LANGUAGES:
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
    logger.info(f"Coding language selection shown to user {user_id}")

async def show_help(event):
    """Show help information"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

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
    logger.info(f"Help shown to user {user_id}")

async def process_coding_request(event, user_input, processing_msg):
    """Handles the logic for processing a coding request after validation."""
    user_id = event.sender_id
    chat_id = event.chat_id
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

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
            ext = EXT_MAP.get(coding_lang, "txt")
            safe_lang = ''.join(c for c in coding_lang if c.isalnum())
            filename = f"code_{safe_lang}_{user_id}.{ext}"
            try:
                with open(filename, "w", encoding="utf-8") as f: f.write(response)
                caption = get_translation('code_too_long', lang_code, lang=coding_lang, ai_model_name=ai_model_name)
                await client.send_file(chat_id, filename, caption=caption, buttons=buttons_after_code, reply_to=event.message.id if hasattr(event, 'message') else None)
                await processing_msg.delete()
            except Exception as e:
                logger.error(f"Error sending file: {e}")
                await processing_msg.edit(f"{get_translation('error_generic', lang_code)}\nError sending file: {e}")
            finally:
                if os.path.exists(filename):
                    try: os.remove(filename)
                    except OSError as e: logger.error(f"Error removing temporary file {filename}: {e}")
        else:
            formatted_response = f"```\n{response}\n```"
            final_message = f"{get_translation('code_ready', lang_code, lang=coding_lang, ai_model_name=ai_model_name)}\n{formatted_response}"

            try:
                 await processing_msg.edit(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
            except Exception as e:
                 logger.error(f"Error editing final code message: {e}")
                 await event.respond(final_message, buttons=buttons_after_code, parse_mode='md', link_preview=False)
                 try: await processing_msg.delete()
                 except: pass

        await set_user_pref(user_id, 'last_prompt', None)

async def process_chat_request(event, user_input, processing_msg):
    """Handles the logic for processing a chat request."""
    user_id = event.sender_id
    chat_id = event.chat_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

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
             logger.error(f"Error editing chat response message: {e}")
             await event.respond(response, buttons=buttons_after_chat, link_preview=False)
             try: await processing_msg.delete()
             except: pass

# --- Event Handlers ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name

    logger.info(f"User {user_id} ({username}) started the bot")

    await add_or_update_user(user_id, username, first_name)
    user_db_data = await get_user_data(user_id)
    
    if user_db_data:
        user_data[user_id] = {
            'ui_lang': user_db_data['ui_lang'],
            'coding_lang': None,
            'ai_model': user_db_data['selected_ai_model'],
            'is_chatting': False,
            'last_prompt': None
        }
    else:
        user_data[user_id] = {
            'ui_lang': 'fa',
            'coding_lang': None,
            'ai_model': 'gpt4',
            'is_chatting': False,
            'last_prompt': None
        }

    mandatory_channels = await get_mandatory_channels()
    if mandatory_channels:
        channel_list = "\n".join([f"- @{ch['username']}" for ch in mandatory_channels])
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        
        buttons = [
            [Button.inline(get_translation('joined_button', lang_code), b"check_membership")],
            [Button.url("📢 Join Channels", f"https://t.me/{mandatory_channels[0]['username']}")]
        ]
        
        await event.respond(
            get_translation('mandatory_join', lang_code, channels=channel_list),
            buttons=buttons
        )
        logger.info(f"Mandatory channels check shown to user {user_id}")
        return

    await show_main_menu(event, edit=False, first_start=True)

@client.on(events.CallbackQuery(data=b"check_membership"))
async def check_membership(event):
    user_id = event.sender_id
    mandatory_channels = await get_mandatory_channels()
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    all_joined = True
    for channel in mandatory_channels:
        try:
            await client.get_permissions(channel['id'], user_id)
        except:
            all_joined = False
            break
    
    if all_joined:
        await event.answer("✅ Verified! You can now use the bot.", alert=True)
        await show_main_menu(event, edit=True)
        logger.info(f"User {user_id} verified membership")
    else:
        await event.answer("❌ You haven't joined all channels yet!", alert=True)
        logger.warning(f"User {user_id} hasn't joined all channels")

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} accessed admin panel")
        await show_admin_panel(event)
    else:
        lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'fa')
        await event.respond(get_translation('admin_not_allowed', lang_code))
        logger.warning(f"Unauthorized admin access attempt by {event.sender_id}")

# --- Admin Panel Functions ---
async def show_admin_panel(event):
    """Display admin panel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    bot_status = "✅ ON" if bot_active else "❌ OFF"
    text = f"**{get_translation('admin_panel_title', lang_code)}**\n\n"
    text += f"Bot Status: {bot_status}\n"
    text += get_translation('admin_panel_desc', lang_code)
    
    buttons = [
        [Button.inline(f"🔘 Toggle Bot ({bot_status})", b"admin_toggle_status")],
        [Button.inline("➕ Add Admin", b"admin_add_admin"),
         Button.inline("➖ Remove Admin", b"admin_remove_admin")],
        [Button.inline("📢 Broadcast", b"admin_broadcast"),
         Button.inline("👥 List Users", b"admin_list_users")],
        [Button.inline("🔒 Mandatory Channels", b"admin_mandatory_channels")],
        [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
    ]
    
    try:
        await event.edit(text, buttons=buttons)
        logger.info(f"Admin panel shown to admin {user_id}")
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")
        await event.respond(text, buttons=buttons)

async def admin_manage_mandatory_channels(event):
    """Manage mandatory channels"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    channels = await get_mandatory_channels()
    
    if not channels:
        text = "No mandatory channels set.\n\nSend a channel username to add:"
        buttons = [
            [Button.inline("🔙 Back", b"admin_panel")]
        ]
        admin_states[user_id] = 'awaiting_mandatory_channel'
    else:
        text = "**Mandatory Channels:**\n\n"
        for channel in channels:
            text += f"- {channel['username']}\n"
        
        text += "\nChoose an action:"
        buttons = [
            [Button.inline("➕ Add Channel", b"admin_add_mandatory_channel")],
            [Button.inline("➖ Remove Channel", b"admin_remove_mandatory_channel")],
            [Button.inline("🔙 Back", b"admin_panel")]
        ]
    
    await event.edit(text, buttons=buttons)
    logger.info(f"Mandatory channels management shown to admin {user_id}")

async def admin_add_mandatory_channel(event):
    """Add mandatory channel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_mandatory_channel'
    await event.edit(
        "Send the channel username (e.g., @channel_name):",
        buttons=[Button.inline("🔙 Back", b"admin_mandatory_channels")]
    )
    logger.info(f"Admin {user_id} adding mandatory channel")

async def admin_remove_mandatory_channel(event):
    """Remove mandatory channel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    channels = await get_mandatory_channels()
    if not channels:
        await event.answer("No channels to remove!", alert=True)
        return
    
    buttons = []
    for channel in channels:
        buttons.append([Button.inline(
            f"❌ {channel['username']}", 
            f"remove_channel_{channel['id']}".encode()
        )])
    
    buttons.append([Button.inline("🔙 Back", b"admin_mandatory_channels")])
    
    await event.edit(
        "Select channel to remove:",
        buttons=buttons
    )
    logger.info(f"Admin {user_id} removing mandatory channel")

async def admin_add_admin(event):
    """Add new admin"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_new_admin'
    await event.edit(
        "Send the user ID or username of the new admin:",
        buttons=[Button.inline("🔙 Back", b"admin_panel")]
    )
    logger.info(f"Admin {user_id} adding new admin")

async def admin_remove_admin(event):
    """Remove admin"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    admins = await get_all_admins()
    if len(admins) <= 1:
        await event.answer("Cannot remove the last admin!", alert=True)
        return
    
    buttons = []
    for admin_id in admins:
        try:
            admin_user = await client.get_entity(admin_id)
            admin_name = admin_user.first_name or admin_user.username or str(admin_id)
        except:
            admin_name = str(admin_id)
        
        buttons.append([Button.inline(
            f"❌ {admin_name}", 
            f"remove_admin_{admin_id}".encode()
        )])
    
    buttons.append([Button.inline("🔙 Back", b"admin_panel")])
    
    await event.edit(
        "Select admin to remove:",
        buttons=buttons
    )
    logger.info(f"Admin {user_id} removing admin")

async def admin_list_users(event):
    """List all users"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    try:
        async with aiosqlite.connect("users_data.db") as db:
            async with db.execute("SELECT user_id, username, first_name, last_seen FROM users ORDER BY last_seen DESC LIMIT 50") as cursor:
                users = await cursor.fetchall()
        
        if not users:
            await event.edit("**No users found in the database.**", 
                           buttons=[Button.inline("🔙 Back", b"admin_panel")])
            return
        
        user_list = "**👥 Bot Users (Last 50):**\n\n"
        for user in users:
            user_id_db, username, first_name, last_seen = user
            username_str = username if username else "N/A"
            first_name_str = first_name if first_name else "N/A"
            user_list += f"👤 `{user_id_db}`\n   Name: {first_name_str}\n   Username: @{username_str}\n   Last Seen: {last_seen}\n\n"
        
        if len(user_list) > 4000:
            parts = [user_list[i:i+4000] for i in range(0, len(user_list), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await event.edit(part, buttons=[Button.inline("🔙 Back", b"admin_panel")])
                else:
                    await event.respond(part)
        else:
            await event.edit(user_list, buttons=[Button.inline("🔙 Back", b"admin_panel")])
        
        logger.info(f"Admin {user_id} listed users")
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await event.edit(f"Error: {str(e)}", buttons=[Button.inline("🔙 Back", b"admin_panel")])

async def admin_broadcast(event):
    """Start broadcast message"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_broadcast_message'
    await event.edit(
        get_translation('admin_ask_broadcast', lang_code),
        buttons=[Button.inline("🔙 Back", b"admin_panel")]
    )
    logger.info(f"Admin {user_id} starting broadcast")

# --- Button Callback Handlers ---
@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} accessed admin panel via callback")
        await show_admin_panel(event)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_pref(event.sender_id, 'ui_lang', 'fa')), alert=True)
        logger.warning(f"Unauthorized admin panel callback by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_mandatory_channels"))
async def admin_mandatory_channels_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} managing mandatory channels")
        await admin_manage_mandatory_channels(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized mandatory channels access by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_add_mandatory_channel"))
async def admin_add_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} adding mandatory channel")
        await admin_add_mandatory_channel(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized add mandatory channel by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_remove_mandatory_channel"))
async def admin_remove_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} removing mandatory channel")
        await admin_remove_mandatory_channel(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized remove mandatory channel by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_add_admin"))
async def admin_add_admin_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} adding new admin")
        await admin_add_admin(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized add admin by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_remove_admin"))
async def admin_remove_admin_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} removing admin")
        await admin_remove_admin(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized remove admin by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_list_users"))
async def admin_list_users_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} listing users")
        await admin_list_users(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized list users by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_broadcast_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} starting broadcast")
        await admin_broadcast(event)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized broadcast by {event.sender_id}")

@client.on(events.CallbackQuery(pattern=b"remove_channel_(.*)"))
async def remove_channel_callback(event):
    if not await is_admin(event.sender_id):
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized remove channel by {event.sender_id}")
        return
    
    channel_id = int(event.pattern_match.group(1).decode('utf-8'))
    if await remove_mandatory_channel(channel_id):
        await event.answer("Channel removed successfully!", alert=True)
        await admin_manage_mandatory_channels(event)
        logger.info(f"Admin {event.sender_id} removed channel {channel_id}")
    else:
        await event.answer("Failed to remove channel!", alert=True)
        logger.error(f"Failed to remove channel {channel_id} by admin {event.sender_id}")

@client.on(events.CallbackQuery(pattern=b"remove_admin_(.*)"))
async def remove_admin_callback(event):
    if not await is_admin(event.sender_id):
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized remove admin by {event.sender_id}")
        return
    
    admin_id = int(event.pattern_match.group(1).decode('utf-8'))
    if await remove_admin(admin_id):
        await event.answer("Admin removed successfully!", alert=True)
        await admin_remove_admin(event)
        logger.info(f"Admin {event.sender_id} removed admin {admin_id}")
    else:
        await event.answer("Failed to remove admin!", alert=True)
        logger.error(f"Failed to remove admin {admin_id} by admin {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_toggle_status"))
async def admin_toggle_bot_status(event):
    global bot_active
    if await is_admin(event.sender_id):
        bot_active = not bot_active
        lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'fa')
        status_msg = get_translation('admin_bot_on_msg', lang_code) if bot_active else get_translation('admin_bot_off_msg', lang_code)
        await event.answer(status_msg, alert=True)
        await show_admin_panel(event)
        logger.info(f"Admin {event.sender_id} toggled bot status to {bot_active}")
    else:
        await event.answer()
        logger.warning(f"Unauthorized toggle bot status by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"settings"))
async def settings_callback(event):
    logger.info(f"User {event.sender_id} accessed settings")
    await show_settings_menu(event)

@client.on(events.CallbackQuery(data=b"coding"))
async def coding_callback(event):
    logger.info(f"User {event.sender_id} accessed coding")
    await choose_coding_language(event)

@client.on(events.CallbackQuery(data=b"start_chat"))
async def start_chat_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_id, 'is_chatting', True)
    await set_user_pref(user_id, 'coding_lang', None)
    
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

    await event.edit(
        get_translation('start_chat_prompt', lang_code, ai_model_name=ai_model_name),
        buttons=[Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")]
    )
    logger.info(f"User {user_id} started chat mode")

@client.on(events.CallbackQuery(data=b"help"))
async def help_callback(event):
    logger.info(f"User {event.sender_id} accessed help")
    await show_help(event)

@client.on(events.CallbackQuery(data=b"main_menu"))
async def main_menu_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_id, 'coding_lang', None)
    await set_user_pref(user_id, 'is_chatting', False)
    await set_user_pref(user_id, 'last_prompt', None)
    await show_main_menu(event, edit=True)
    logger.info(f"User {user_id} returned to main menu")

@client.on(events.CallbackQuery(data=b"change_ui_lang"))
async def change_ui_lang_callback(event):
    logger.info(f"User {event.sender_id} changing language")
    await show_ui_language_options(event)

@client.on(events.CallbackQuery(data=b"select_ai_model"))
async def select_ai_model_callback(event):
    logger.info(f"User {event.sender_id} selecting AI model")
    await show_ai_model_options(event)

@client.on(events.CallbackQuery(pattern=b"set_lang_(.*)"))
async def set_lang_callback(event):
    user_id = event.sender_id
    new_lang_code = event.pattern_match.group(1).decode('utf-8')

    if new_lang_code in ['fa', 'en']:
        await set_user_pref(user_id, 'ui_lang', new_lang_code)
        await update_user_field(user_id, 'ui_lang', new_lang_code)
        await event.answer(get_translation('settings_lang_selected', new_lang_code), alert=True)
        await show_settings_menu(event)
        logger.info(f"User {user_id} changed language to {new_lang_code}")
    else:
        await event.answer("Invalid language code.", alert=True)
        logger.warning(f"Invalid language code {new_lang_code} by user {user_id}")

@client.on(events.CallbackQuery(pattern=b"set_model_(.*)"))
async def set_model_callback(event):
    user_id = event.sender_id
    model_id = event.pattern_match.group(1).decode('utf-8')

    if model_id in AVAILABLE_AI_MODELS:
        await set_user_pref(user_id, 'selected_ai_model', model_id)
        await update_user_field(user_id, 'selected_ai_model', model_id)
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        model_name = AVAILABLE_AI_MODELS[model_id]
        await event.answer(get_translation('settings_model_selected', lang_code, model_name=model_name), alert=True)
        await show_settings_menu(event)
        logger.info(f"User {user_id} changed AI model to {model_id}")
    else:
        await event.answer("Invalid AI model selected.", alert=True)
        logger.warning(f"Invalid AI model {model_id} by user {user_id}")

@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def select_code_callback(event):
    user_id = event.sender_id
    selected_lang = event.pattern_match.group(1).decode('utf-8')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

    if selected_lang in CODING_LANGUAGES:
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
        logger.info(f"User {user_id} selected coding language {selected_lang}")
    else:
        await event.answer("Invalid language selected.", alert=True)
        logger.warning(f"Invalid coding language {selected_lang} by user {user_id}")

@client.on(events.CallbackQuery(data=b"stop_chat"))
async def stop_chat_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_id, 'is_chatting', False)
    await show_main_menu(event, edit=True)
    logger.info(f"User {user_id} stopped chat mode")

@client.on(events.CallbackQuery(data=b"retry_last_prompt"))
async def retry_last_prompt_callback(event):
    user_id = event.sender_id
    last_prompt = await get_user_pref(user_id, 'last_prompt')
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')

    if not last_prompt or not coding_lang:
        await event.answer("No prompt to retry or coding language not set.", alert=True)
        logger.warning(f"Retry attempt by user {user_id} without valid prompt or language")
        return

    await event.answer("🔄 Retrying...")
    logger.info(f"User {user_id} retrying prompt: {last_prompt}")
    processing_msg = await event.respond(get_translation('processing', lang_code))
    await process_coding_request(event, last_prompt, processing_msg)

# --- Message Handler ---
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    user_input = event.raw_text.strip()
    
    # Handle admin states
    if await is_admin(user_id):
        if admin_states.get(user_id) == 'awaiting_mandatory_channel':
            logger.info(f"Admin {user_id} adding mandatory channel: {user_input}")
            if user_input.startswith('@'):
                try:
                    channel_entity = await client.get_entity(user_input)
                    channel_id = channel_entity.id
                    channel_username = user_input
                    
                    if await add_mandatory_channel(channel_id, channel_username):
                        await event.respond(f"✅ Channel {user_input} added successfully!")
                        del admin_states[user_id]
                        await admin_manage_mandatory_channels(event)
                        logger.info(f"Admin {user_id} successfully added channel {user_input}")
                    else:
                        await event.respond("❌ Failed to add channel!")
                        logger.error(f"Admin {user_id} failed to add channel {user_input}")
                except Exception as e:
                    await event.respond(f"❌ Error: {str(e)}")
                    logger.error(f"Error adding channel by admin {user_id}: {e}")
            else:
                await event.respond("Please send a valid channel username (e.g., @channel_name)")
                logger.warning(f"Invalid channel format by admin {user_id}: {user_input}")
            return
        
        elif admin_states.get(user_id) == 'awaiting_new_admin':
            logger.info(f"Admin {user_id} adding new admin: {user_input}")
            try:
                if user_input.startswith('@'):
                    admin_entity = await client.get_entity(user_input)
                    admin_id = admin_entity.id
                else:
                    admin_id = int(user_input)
                
                if await add_admin(admin_id):
                    await event.respond(f"✅ Admin added successfully!")
                    del admin_states[user_id]
                    await show_admin_panel(event)
                    logger.info(f"Admin {user_id} successfully added admin {admin_id}")
                else:
                    await event.respond("❌ Failed to add admin!")
                    logger.error(f"Admin {user_id} failed to add admin {admin_id}")
            except Exception as e:
                await event.respond(f"❌ Error: {str(e)}")
                logger.error(f"Error adding admin by admin {user_id}: {e}")
            return
        
        elif admin_states.get(user_id) == 'awaiting_broadcast_message':
            logger.info(f"Admin {user_id} sending broadcast: {user_input[:50]}...")
            user_ids = await get_all_user_ids()
            if not user_ids:
                await event.respond("No users in the database to broadcast to.")
                await show_admin_panel(event)
                return

            count = len(user_ids)
            status_message = await event.respond(f"⏳ Sending message to {count} users...")
            logger.info(f"Broadcast started to {count} users by admin {user_id}")

            sent_count = 0
            failed_count = 0

            for uid in user_ids:
                try:
                    if uid == user_id:
                        continue
                    await client.send_message(uid, user_input)
                    sent_count += 1
                    await asyncio.sleep(0.1)
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send broadcast to {uid}: {e}")

            result_message = f"✅ Broadcast sent successfully!\n\nSent: {sent_count}\nFailed: {failed_count}"
            await status_message.edit(result_message)
            del admin_states[user_id]
            logger.info(f"Broadcast completed by admin {user_id}: {sent_count} sent, {failed_count} failed")
            await asyncio.sleep(2)
            await show_admin_panel(event)
            return
    
    # Handle chat mode
    is_chatting = await get_user_pref(user_id, 'is_chatting', False)
    if is_chatting:
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        processing_msg = await event.respond(get_translation('processing', lang_code))
        logger.info(f"Chat message from user {user_id}: {user_input[:50]}...")
        await process_chat_request(event, user_input, processing_msg)
        return
    
    # Handle coding mode
    coding_lang = await get_user_pref(user_id, 'coding_lang')
    if coding_lang:
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        processing_msg = await event.respond(get_translation('processing', lang_code))
        
        await set_user_pref(user_id, 'last_prompt', user_input)
        logger.info(f"Coding request from user {user_id} in {coding_lang}: {user_input[:50]}...")
        
        async with client.action(event.chat_id, "typing"):
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
    
    # If we get here, the user sent a message without being in a specific mode
    logger.info(f"Idle message from user {user_id}: {user_input[:50]}...")
    await show_main_menu(event, edit=False)

# --- Main Function ---
async def main():
    await initialize_database()
    
    if not await is_admin(DEFAULT_ADMIN_ID):
        await add_admin(DEFAULT_ADMIN_ID)
        logger.info(f"Added default admin: {DEFAULT_ADMIN_ID}")
    
    logger.info("Starting bot...")
    await client.start()
    me = await client.get_me()
    logger.info(f"Bot '{me.first_name}' started successfully.")
    logger.info("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopping...")
