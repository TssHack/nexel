# main.py
import asyncio
import os
import traceback
from telethon import TelegramClient, events, Button
import aiosqlite
import aiohttp
from config import API_ID, API_HASH, SESSION_NAME, DB_FILE
from database import initialize_database, add_or_update_user, get_user_data, update_user_field
from database import get_all_user_ids, is_admin, add_admin, remove_admin, get_all_admins
from database import get_mandatory_channels, add_mandatory_channel, remove_mandatory_channel
from panel import show_admin_panel, admin_manage_mandatory_channels, admin_add_mandatory_channel
from panel import admin_remove_mandatory_channel, admin_add_admin, admin_remove_admin
from translations import get_translation

# Bot State
bot_active = True
user_data = {}
admin_states = {}

# AI Models
available_ai_models = {
    "gpt4": "GPT-4",
    "qwen2.5": "Qwen2.5 Coder",
    "arcee-ai": "Arcee Ai",
    # ... other models
}

# Initialize client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Helper Functions
async def get_user_pref(user_id, key, default_value=None):
    """Gets a specific preference for a user, fetching from DB if not in memory."""
    if user_id not in user_data:
        db_data = await get_user_data(user_id)
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
                'ai_model': 'gpt4',
                'is_chatting': False,
                'last_prompt': None
            }
    
    return user_data.get(user_id, {}).get(key, default_value)

async def set_user_pref(user_id, key, value):
    """Sets a user preference in memory and updates the DB if applicable."""
    if user_id not in user_data:
        await get_user_pref(user_id, 'ui_lang')  # Ensure user_data[user_id] exists

    user_data[user_id][key] = value

    # Persist relevant preferences to DB
    if key in ['ui_lang', 'selected_ai_model']:
        await update_user_field(user_id, key, value)

async def show_main_menu(event, edit=False, first_start=False):
    """Displays the main menu."""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    ai_model_id = await get_user_pref(user_id, 'ai_model', 'gpt4')
    ai_model_name = available_ai_models.get(ai_model_id, "Unknown")

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
        lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
        
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
    await show_main_menu(event, edit=False, first_start=True)

@client.on(events.CallbackQuery(data=b"check_membership"))
async def check_membership(event):
    user_id = event.sender_id
    mandatory_channels = await get_mandatory_channels()
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
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
        await show_main_menu(event, edit=True)
    else:
        await event.answer("❌ You haven't joined all channels yet!", alert=True)

@client.on(events.NewMessage(pattern='/admin'))
async def admin_command(event):
    if await is_admin(event.sender_id):
        await show_admin_panel(event)
    else:
        lang_code = await get_user_pref(event.sender_id, 'ui_lang', 'fa')
        await event.respond(get_translation('admin_not_allowed', lang_code))

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if await is_admin(event.sender_id):
        await show_admin_panel(event, edit=True)
    else:
        await event.answer(get_translation('admin_not_allowed', await get_user_pref(event.sender_id, 'ui_lang', 'fa')), alert=True)

@client.on(events.CallbackQuery(data=b"admin_mandatory_channels"))
async def admin_mandatory_channels(event):
    if await is_admin(event.sender_id):
        await admin_manage_mandatory_channels(event)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_add_mandatory_channel"))
async def admin_add_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        await admin_add_mandatory_channel(event)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_remove_mandatory_channel"))
async def admin_remove_mandatory_channel_callback(event):
    if await is_admin(event.sender_id):
        await admin_remove_mandatory_channel(event)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_add_admin"))
async def admin_add_admin_callback(event):
    if await is_admin(event.sender_id):
        await admin_add_admin(event)
    else:
        await event.answer("Access denied!", alert=True)

@client.on(events.CallbackQuery(data=b"admin_remove_admin"))
async def admin_remove_admin_callback(event):
    if await is_admin(event.sender_id):
        await admin_remove_admin(event)
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
        await admin_manage_mandatory_channels(event)
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
        await admin_remove_admin(event)
    else:
        await event.answer("Failed to remove admin!", alert=True)

# Handle mandatory channel input
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
                        await admin_manage_mandatory_channels(event)
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
                    await show_admin_panel(event)
                else:
                    await event.respond("❌ Failed to add admin!")
            except Exception as e:
                await event.respond(f"❌ Error: {str(e)}")
            return
    
    # ... rest of the message handling logic ...

# Main function
async def main():
    await initialize_database()
    
    # Add default admin if not exists
    default_admin_id = 7094106651
    if not await is_admin(default_admin_id):
        await add_admin(default_admin_id)
    
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
