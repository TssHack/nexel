# main.py
import asyncio
import os
import traceback
from telethon import TelegramClient, events, Button
import aiosqlite
import aiohttp
from config import API_ID, API_HASH, SESSION_NAME, DEFAULT_ADMIN_ID, AVAILABLE_AI_MODELS, CODING_LANGUAGES, EXT_MAP
from database import initialize_database, add_or_update_user, get_user_data, update_user_field
from database import get_all_user_ids, is_admin, add_admin, remove_admin, get_all_admins
from database import get_mandatory_channels, add_mandatory_channel, remove_mandatory_channel
from panel import show_admin_panel, admin_manage_mandatory_channels, admin_add_mandatory_channel
from panel import admin_remove_mandatory_channel, admin_add_admin, admin_remove_admin
from translations import get_translation
from utils import get_user_pref, set_user_pref

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
    ai_model_id = await get_user_pref(user_data, user_id, 'ai_model', 'gpt4')
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
    except Exception as e:
        print(f"Error showing main menu ({'edit' if edit else 'respond'}): {e}")
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

# Event Handlers
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    username = sender.username
    first_name = sender.first_name

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
            # Check if user is member of the channel
            await client.get_permissions(channel['id'], user_id)
        except:
            all_joined = False
            break
    
    if all_joined:
        await event.answer("✅ Verified! You can now use the bot.", alert=True)
        await show_main_menu(event, user_data, edit=True)
    else:
        await event.answer("❌ You haven't joined all channels yet!", alert=True)

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if await is_admin(event.sender_id):
        await show_admin_panel(event, bot_active, user_data)
    else:
        lang_code = await get_user_pref(user_data, event.sender_id, 'ui_lang', 'fa')
        await event.respond(get_translation('admin_not_allowed', lang_code))

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if await is_admin(event.sender_id):
        await show_admin_panel(event, bot_active, user_data, edit=True)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_pref(user_data, event.sender_id, 'ui_lang', 'fa')), alert=True)

@client.on(events.CallbackQuery(data=b"admin_mandatory_channels"))
async def admin_mandatory_channels(event):
    if await is_admin(event.sender_id):
        await admin_manage_mandatory_channels(event, user_data, admin_states)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_add_mandatory_channel"))
async def admin_add_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        await admin_add_mandatory_channel(event, user_data, admin_states)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_remove_mandatory_channel"))
async def admin_remove_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        await admin_remove_mandatory_channel(event, user_data, client)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_add_admin"))
async def admin_add_admin_callback(event):
    if await is_admin(event.sender_id):
        await admin_add_admin(event, user_data, admin_states)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_remove_admin"))
async def admin_remove_admin_callback(event):
    if await is_admin(event.sender_id):
        await admin_remove_admin(event, user_data, client)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(pattern=b"remove_channel_(.*)"))
async def remove_channel_callback(event):
    if not await is_admin(event.sender_id):
        await event.answer("Access denied!", alert=True)
        return
    
    channel_id = int(event.pattern_match.group(1).decode('utf-8'))
    if await remove_mandatory_channel(channel_id):
        await event.answer("Channel removed successfully!", alert=True)
        await admin_manage_mandatory_channels(event, user_data, admin_states)
    else:
        await event.answer("Failed to remove channel!", alert=True)

@client.on(events.CallbackQuery(pattern=b"remove_admin_(.*)"))
async def remove_admin_callback(event):
    if not await is_admin(event.sender_id):
        await event.answer("Access denied!", alert=True)
        return
    
    admin_id = int(event.pattern_match.group(1).decode('utf-8'))
    if await remove_admin(admin_id):
        await event.answer("Admin removed successfully!", alert=True)
        await admin_remove_admin(event, user_data, client)
    else:
        await event.answer("Failed to remove admin!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_toggle_status"))
async def admin_toggle_bot_status(event):
    global bot_active
    if await is_admin(event.sender_id):
        bot_active = not bot_active
        lang_code = await get_user_pref(user_data, event.sender_id, 'ui_lang', 'fa')
        status_msg = get_translation('admin_bot_on_msg', lang_code) if bot_active else get_translation('admin_bot_off_msg', lang_code)
        await event.answer(status_msg, alert=True)
        await show_admin_panel(event, bot_active, user_data, edit=True)
    else:
        await event.answer()

# Main Menu Buttons
@client.on(events.CallbackQuery(data=b"settings"))
async def settings_callback(event):
    await show_settings_menu(event, user_data)

@client.on(events.CallbackQuery(data=b"coding"))
async def coding_callback(event):
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

@client.on(events.CallbackQuery(data=b"help"))
async def help_callback(event):
    await show_help(event, user_data)

@client.on(events.CallbackQuery(data=b"main_menu"))
async def main_menu_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_data, user_id, 'coding_lang', None)
    await set_user_pref(user_data, user_id, 'is_chatting', False)
    await set_user_pref(user_data, user_id, 'last_prompt', None)
    await show_main_menu(event, user_data, edit=True)

# Settings Buttons
@client.on(events.CallbackQuery(data=b"change_ui_lang"))
async def change_ui_lang_callback(event):
    await show_ui_language_options(event, user_data)

@client.on(events.CallbackQuery(data=b"select_ai_model"))
async def select_ai_model_callback(event):
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
    else:
        await event.answer("Invalid language code.", alert=True)

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
    else:
        await event.answer("Invalid AI model selected.", alert=True)

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
    else:
        await event.answer("Invalid language selected.", alert=True)

# Chat Buttons
@client.on(events.CallbackQuery(data=b"stop_chat"))
async def stop_chat_callback(event):
    user_id = event.sender_id
    await set_user_pref(user_data, user_id, 'is_chatting', False)
    await show_main_menu(event, user_data, edit=True)

# Retry Button
@client.on(events.CallbackQuery(data=b"retry_last_prompt"))
async def retry_last_prompt_callback(event):
    user_id = event.sender_id
    last_prompt = await get_user_pref(user_data, user_id, 'last_prompt')
    coding_lang = await get_user_pref(user_data, user_id, 'coding_lang')
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')

    if not last_prompt or not coding_lang:
        await event.answer("No prompt to retry or coding language not set.", alert=True)
        return

    await event.answer("🔄 Retrying...")
    # Here you would normally process the prompt again
    # For now, just show a message
    await event.respond(f"Retrying: {last_prompt}\nLanguage: {coding_lang}")

# Handle admin states
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    user_input = event.raw_text.strip()
    
    # Handle admin states
    if await is_admin(user_id):
        if admin_states.get(user_id) == 'awaiting_mandatory_channel':
            # Add mandatory channel
            if user_input.startswith('@'):
                try:
                    channel_entity = await client.get_entity(user_input)
                    channel_id = channel_entity.id
                    channel_username = user_input
                    
                    if await add_mandatory_channel(channel_id, channel_username):
                        await event.respond(f"✅ Channel {user_input} added successfully!")
                        del admin_states[user_id]
                        await admin_manage_mandatory_channels(event, user_data, admin_states)
                    else:
                        await event.respond("❌ Failed to add channel!")
                except Exception as e:
                    await event.respond(f"❌ Error: {str(e)}")
            else:
                await event.respond("Please send a valid channel username (e.g., @channel_name)")
            return
        
        elif admin_states.get(user_id) == 'awaiting_new_admin':
            # Add new admin
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
                else:
                    await event.respond("❌ Failed to add admin!")
            except Exception as e:
                await event.respond(f"❌ Error: {str(e)}")
            return
    
    # Handle chat mode
    is_chatting = await get_user_pref(user_data, user_id, 'is_chatting', False)
    if is_chatting:
        lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
        processing_msg = await event.respond(get_translation('processing', lang_code))
        
        # Here you would normally process the chat message
        # For now, just show a response
        await processing_msg.edit(f"Chat response: {user_input}")
        return
    
    # Handle coding mode
    coding_lang = await get_user_pref(user_data, user_id, 'coding_lang')
    if coding_lang:
        lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
        processing_msg = await event.respond(get_translation('processing', lang_code))
        
        # Save the prompt for retry
        await set_user_pref(user_data, user_id, 'last_prompt', user_input)
        
        # Here you would normally process the coding request
        # For now, just show a response
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
    # Just show the main menu
    await show_main_menu(event, user_data, edit=False)

# Main function
async def main():
    await initialize_database()
    
    # Add default admin if not exists
    if not await is_admin(DEFAULT_ADMIN_ID):
        await add_admin(DEFAULT_ADMIN_ID)
    
    print("Starting bot...")
    await client.start()
    me = await client.get_me()
    print(f"Bot '{me.first_name}' started successfully.")
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopping...")
