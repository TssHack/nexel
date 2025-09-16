# panel.py
from telethon import Button
from database import get_all_user_ids, get_mandatory_channels, add_mandatory_channel, remove_mandatory_channel
from database import is_admin, get_all_admins, add_admin, remove_admin
from translations import get_translation
from utils import get_user_pref, set_user_pref
import logging

logger = logging.getLogger(__name__)

async def show_admin_panel(event, bot_active, user_data, edit=False):
    """Display admin panel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
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
    
    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
        logger.info(f"Admin panel shown to admin {user_id}")
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")
        if edit:
            await event.respond(text, buttons=buttons)

async def admin_manage_mandatory_channels(event, user_data, admin_states):
    """Manage mandatory channels"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
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

async def admin_add_mandatory_channel(event, user_data, admin_states):
    """Add mandatory channel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_mandatory_channel'
    await event.edit(
        "Send the channel username (e.g., @channel_name):",
        buttons=[Button.inline("🔙 Back", b"admin_mandatory_channels")]
    )
    logger.info(f"Admin {user_id} adding mandatory channel")

async def admin_remove_mandatory_channel(event, user_data, client):
    """Remove mandatory channel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
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

async def admin_add_admin(event, user_data, admin_states):
    """Add new admin"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_new_admin'
    await event.edit(
        "Send the user ID or username of the new admin:",
        buttons=[Button.inline("🔙 Back", b"admin_panel")]
    )
    logger.info(f"Admin {user_id} adding new admin")

async def admin_remove_admin(event, user_data, client):
    """Remove admin"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
    admins = await get_all_admins()
    if len(admins) <= 1:
        await event.answer("Cannot remove the last admin!", alert=True)
        return
    
    buttons = []
    for admin_id in admins:
        # Get admin username if possible
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

async def admin_list_users(event, user_data):
    """List all users"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
    try:
        from database import aiosqlite
        async with aiosqlite.connect("users_data.db") as db:
            async with db.execute("SELECT user_id, username, first_name, last_seen FROM users ORDER BY last_seen DESC LIMIT 50") as cursor:
                users = await cursor.fetchall()
        
        if not users:
            await event.edit("**No users found in the database.**", 
                           buttons=[Button.inline("🔙 Back", b"admin_panel")])
            return
        
        user_list = "**👥 Bot Users (Last 50):**\n\n"
        for user in users:
            user_id, username, first_name, last_seen = user
            username_str = username if username else "N/A"
            first_name_str = first_name if first_name else "N/A"
            user_list += f"👤 `{user_id}`\n   Name: {first_name_str}\n   Username: @{username_str}\n   Last Seen: {last_seen}\n\n"
        
        # Split into multiple messages if too long
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

async def admin_broadcast(event, user_data, admin_states):
    """Start broadcast message"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_data, user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_broadcast_message'
    await event.edit(
        get_translation('admin_ask_broadcast', lang_code),
        buttons=[Button.inline("🔙 Back", b"admin_panel")]
    )
    logger.info(f"Admin {user_id} starting broadcast")
