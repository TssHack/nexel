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
from panel import show_admin_panel, admin_manage_mandatory_channels, admin_add_mandatory_channel
from panel import admin_remove_mandatory_channel, admin_add_admin, admin_remove_admin, admin_list_users, admin_broadcast
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

# Helper Functions
async def show_main_menu(event, user_data, edit=False, first_start=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_data, user_id, 'selected_ai_model', 'gpt4')
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

async def show_settings_menu(event, user_data):
    """Display settings menu"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')

    buttons = [
        [Button.inline(get_translation('settings_lang_button', lang_code), b"change_ui_lang")],
        [Button.inline(get_translation('settings_model_button', lang_code), b"select_ai_model")],
        [Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")]
    ]
    text = get_translation('settings_title', lang_code)
    await event.edit(text, buttons=buttons)
    logger.info(f"Settings menu shown to user {user_id}")

async def show_ui_language_options(event, user_data):
    """Show language selection options"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')

    buttons = [
        [Button.inline("🇬🇧 English", b"set_lang_en")],
        [Button.inline("🇮🇷 فارسی", b"set_lang_fa")],
        [Button.inline(get_translation('back_to_settings', lang_code), b"settings")]
    ]
    text = get_translation('settings_choose_lang', lang_code)
    await event.edit(text, buttons=buttons)
    logger.info(f"Language options shown to user {user_id}")

async def show_ai_model_options(event, user_data):
    """Show AI model selection options"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    current_model = await get_user_pref(user_data, user_id, 'selected_ai_model', 'gpt4')

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

async def choose_coding_language(event, user_data):
    """Show coding language selection"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')

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
    await set_user_pref(user_data, user_id, 'is_chatting', False)
    logger.info(f"Coding language selection shown to user {user_id}")

async def show_help(event, user_data):
    """Show help information"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_data, user_id, 'selected_ai_model', 'gpt4')
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

# Event Handlers
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name

    logger.info(f"User {user_id} ({username}) started the bot")

    # Add/Update user in DB
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

    # Check mandatory channels
    mandatory_channels = await get_mandatory_channels()
    if mandatory_channels:
        channel_list = "\n".join([f"- @{ch['username']}" for ch in mandatory_channels])
        lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
        
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

    # Show main menu
    await show_main_menu(event, user_data, edit=False, first_start=True)

@client.on(events.CallbackQuery(data=b"check_membership"))
async def check_membership(event):
    user_id = event.sender_id
    mandatory_channels = await get_mandatory_channels()
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
    all_joined = True
    for channel in mandatory_channels:
        try:
            await client.get_permissions(channel['id'], user_id)
        except:
            all_joined = False
            break
    
    if all_joined:
        await event.answer("✅ Verified! You can now use the bot.", alert=True)
        await show_main_menu(event, user_data, edit=True)
        logger.info(f"User {user_id} verified membership")
    else:
        await event.answer("❌ You haven't joined all channels yet!", alert=True)
        logger.warning(f"User {user_id} hasn't joined all channels")

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} accessed admin panel")
        await show_admin_panel(event, bot_active, user_data)
    else:
        lang_code = await get_user_pref(user_data, event.sender_id, 'ui_lang', 'fa')
        await event.respond(get_translation('admin_not_allowed', lang_code))
        logger.warning(f"Unauthorized admin access attempt by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} accessed admin panel via callback")
        await show_admin_panel(event, bot_active, user_data, edit=True)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_pref(user_data, event.sender_id, 'ui_lang', 'fa')), alert=True)
        logger.warning(f"Unauthorized admin panel callback by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_mandatory_channels"))
async def admin_mandatory_channels(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} managing mandatory channels")
        await admin_manage_mandatory_channels(event, user_data, admin_states)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized mandatory channels access by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_add_mandatory_channel"))
async def admin_add_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} adding mandatory channel")
        await admin_add_mandatory_channel(event, user_data, admin_states)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized add mandatory channel by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_remove_mandatory_channel"))
async def admin_remove_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} removing mandatory channel")
        await admin_remove_mandatory_channel(event, user_data, client)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized remove mandatory channel by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_add_admin"))
async def admin_add_admin_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} adding new admin")
        await admin_add_admin(event, user_data, admin_states)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized add admin by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_remove_admin"))
async def admin_remove_admin_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} removing admin")
        await admin_remove_admin(event, user_data, client)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized remove admin by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_list_users"))
async def admin_list_users_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} listing users")
        await admin_list_users(event, user_data)
    else:
        await event.answer("Access denied!", alert=True)
        logger.warning(f"Unauthorized list users by {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_broadcast_callback(event):
    if await is_admin(event.sender_id):
        logger.info(f"Admin {event.sender_id} starting broadcast")
        await admin_broadcast(event, user_data, admin_states)
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
        await admin_manage_mandatory_channels(event, user_data, admin_states)
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
        await admin_remove_admin(event, user_data, client)
        logger.info(f"Admin {event.sender_id} removed admin {admin_id}")
    else:
        await event.answer("Failed to remove admin!", alert=True)
        logger.error(f"Failed to remove admin {admin_id} by admin {event.sender_id}")

@client.on(events.CallbackQuery(data=b"admin_toggle_status"))
async def admin_toggle_bot_status(event):
    global bot_active
    if await is_admin(event.sender_id):
        bot_active = not bot_active
        lang_code = await get_user_pref(user_data, event.sender_id, 'ui_lang', 'fa')
        status_msg = get_translation('admin_bot_on_msg', lang_code) if bot_active else get_translation('admin_bot_off_msg', lang_code)
        await event.answer(status_msg, alert=True)
        await show_admin_panel(event, bot_active, user_data, edit=True)
        logger.info(f"Admin {event.sender_id} toggled bot status to {bot_active}")
    else:
        await event.answer()
        logger.warning(f"Unauthorized toggle bot status by {event.sender_id}")

# Main Menu Buttons
@client.on(events.CallbackQuery(data=b"settings"))
async def settings_callback(event):
    logger.info(f"User {event.sender_id} accessed settings")
    await show_settings_menu(event, user_data)

@client.on(events.CallbackQuery(data=b"coding"))
async def coding_callback(event):
    logger.info(f"User {event.sender_id} accessed coding")
    await choose_coding_language(event, user_data)

@client.on(events.CallbackQuery(data=b"start_chat"))
async def start_chat_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_data, user_id, 'is_chatting', True)
    await set_user_pref(user_data, user_id, 'coding_lang', None)
    
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_data, user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

    await event.edit(
        get_translation('start_chat_prompt', lang_code, ai_model_name=ai_model_name),
        buttons=[Button.inline(get_translation('stop_chat_button', lang_code), b"stop_chat")]
    )
    logger.info(f"User {user_id} started chat mode")

@client.on(events.CallbackQuery(data=b"help"))
async def help_callback(event):
    logger.info(f"User {event.sender_id} accessed help")
    await show_help(event, user_data)

@client.on(events.CallbackQuery(data=b"main_menu"))
async def main_menu_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_data, user_id, 'coding_lang', None)
    await set_user_pref(user_data, user_id, 'is_chatting', False)
    await set_user_pref(user_data, user_id, 'last_prompt', None)
    await show_main_menu(event, user_data, edit=True)
    logger.info(f"User {user_id} returned to main menu")

# Settings Buttons
@client.on(events.CallbackQuery(data=b"change_ui_lang"))
async def change_ui_lang_callback(event):
    logger.info(f"User {event.sender_id} changing language")
    await show_ui_language_options(event, user_data)

@client.on(events.CallbackQuery(data=b"select_ai_model"))
async def select_ai_model_callback(event):
    logger.info(f"User {event.sender_id} selecting AI model")
    await show_ai_model_options(event, user_data)

@client.on(events.CallbackQuery(pattern=b"set_lang_(.*)"))
async def set_lang_callback(event):
    user_id = event.sender_id
    new_lang_code = event.pattern_match.group(1).decode('utf-8')

    if new_lang_code in ['fa', 'en']:
        await set_user_pref(user_data, user_id, 'ui_lang', new_lang_code)
        await update_user_field(user_id, 'ui_lang', new_lang_code)
        await event.answer(get_translation('settings_lang_selected', new_lang_code), alert=True)
        await show_settings_menu(event, user_data)
        logger.info(f"User {user_id} changed language to {new_lang_code}")
    else:
        await event.answer("Invalid language code.", alert=True)
        logger.warning(f"Invalid language code {new_lang_code} by user {user_id}")

@client.on(events.CallbackQuery(pattern=b"set_model_(.*)"))
async def set_model_callback(event):
    user_id = event.sender_id
    model_id = event.pattern_match.group(1).decode('utf-8')

    if model_id in AVAILABLE_AI_MODELS:
        await set_user_pref(user_data, user_id, 'selected_ai_model', model_id)
        await update_user_field(user_id, 'selected_ai_model', model_id)
        lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
        model_name = AVAILABLE_AI_MODELS[model_id]
        await event.answer(get_translation('settings_model_selected', lang_code, model_name=model_name), alert=True)
        await show_settings_menu(event, user_data)
        logger.info(f"User {user_id} changed AI model to {model_id}")
    else:
        await event.answer("Invalid AI model selected.", alert=True)
        logger.warning(f"Invalid AI model {model_id} by user {user_id}")

# Coding Buttons
@client.on(events.CallbackQuery(pattern=b"select_code_(.*)"))
async def select_code_callback(event):
    user_id = event.sender_id
    selected_lang = event.pattern_match.group(1).decode('utf-8')
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_data, user_id, 'selected_ai_model', 'gpt4')
    ai_model_name = AVAILABLE_AI_MODELS.get(ai_model_id, "Unknown")

    if selected_lang in CODING_LANGUAGES:
        await set_user_pref(user_data, user_id, 'coding_lang', selected_lang)
        await set_user_pref(user_data, user_id, 'is_chatting', False)
        await set_user_pref(user_data, user_id, 'last_prompt', None)

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

# Chat Buttons
@client.on(events.CallbackQuery(data=b"stop_chat"))
async def stop_chat_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_data, user_id, 'is_chatting', False)
    await show_main_menu(event, user_data, edit=True)
    logger.info(f"User {user_id} stopped chat mode")

# Retry Button
@client.on(events.CallbackQuery(data=b"retry_last_prompt"))
async def retry_last_prompt_callback(event):
    user_id = event.sender_id
    last_prompt = await get_user_pref(user_data, user_id, 'last_prompt')
    coding_lang = await get_user_pref(user_data, user_id, 'coding_lang')
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')

    if not last_prompt or not coding_lang:
        await event.answer("No prompt to retry or coding language not set.", alert=True)
        logger.warning(f"Retry attempt by user {user_id} without valid prompt or language")
        return

    await event.answer("🔄 Retrying...")
    logger.info(f"User {user_id} retrying prompt: {last_prompt}")
    # Here you would normally process the prompt again
    await event.respond(f"Retrying: {last_prompt}\nLanguage: {coding_lang}")

# Handle admin states
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
                        await admin_manage_mandatory_channels(event, user_data, admin_states)
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
                    await show_admin_panel(event, bot_active, user_data)
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
                await show_admin_panel(event, bot_active, user_data)
                return

            count = len(user_ids)
            status_message = await event.respond(f"⏳ Sending message to {count} users...")
            logger.info(f"Broadcast started to {count} users by admin {user_id}")

            sent_count = 0
            failed_count = 0

            for uid in user_ids:
                try:
                    if uid == user_id:  # Skip the admin themselves
                        continue
                    await client.send_message(uid, user_input)
                    sent_count += 1
                    await asyncio.sleep(0.1)  # Small delay to avoid flood limits
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send broadcast to {uid}: {e}")

            result_message = f"✅ Broadcast sent successfully!\n\nSent: {sent_count}\nFailed: {failed_count}"
            await status_message.edit(result_message)
            del admin_states[user_id]
            logger.info(f"Broadcast completed by admin {user_id}: {sent_count} sent, {failed_count} failed")
            await asyncio.sleep(2)
            await show_admin_panel(event, bot_active, user_data)
            return
    
    # Handle chat mode
    is_chatting = await get_user_pref(user_data, user_id, 'is_chatting', False)
    if is_chatting:
        lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
        processing_msg = await event.respond(get_translation('processing', lang_code))
        logger.info(f"Chat message from user {user_id}: {user_input[:50]}...")
        
        # Here you would normally process the chat message
        await processing_msg.edit(f"Chat response: {user_input}")
        return
    
    # Handle coding mode
    coding_lang = await get_user_pref(user_data, user_id, 'coding_lang')
    if coding_lang:
        lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
        processing_msg = await event.respond(get_translation('processing', lang_code))
        
        # Save the prompt for retry
        await set_user_pref(user_data, user_id, 'last_prompt', user_input)
        logger.info(f"Coding request from user {user_id} in {coding_lang}: {user_input[:50]}...")
        
        # Here you would normally process the coding request
        await processing_msg.edit(
            f"Code generated for {coding_lang}:\n```python\n# Your code here\nprint('{user_input}')\n```",
            buttons=[
                Button.inline(get_translation('new_question_button', lang_code, lang=coding_lang), f"select_code_{coding_lang}".encode()),
                Button.inline(get_translation('back_to_lang_menu', lang_code), b"coding"),
                Button.inline(get_translation('main_menu_button', lang_code), b"main_menu")
            ],
            parse_mode='md'
        )
        return
    
    # If we get here, the user sent a message without being in a specific mode
    logger.info(f"Idle message from user {user_id}: {user_input[:50]}...")
    await show_main_menu(event, user_data, edit=False)

# Main function
async def main():
    await initialize_database()
    
    # Add default admin if not exists
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
