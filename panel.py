# panel.py
from telethon import Button
from database import get_all_user_ids, get_mandatory_channels, add_mandatory_channel, remove_mandatory_channels
from database import is_admin, get_all_admins, add_admin, remove_admin, get_setting, set_setting
from translations import get_translation

async def show_admin_panel(event, edit=False):
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
    
    action = event.edit if edit else event.respond
    try:
        await action(text, buttons=buttons)
    except Exception as e:
        print(f"Error showing admin panel: {e}")
        if edit:
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

async def admin_add_mandatory_channel(event):
    """Add mandatory channel"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_mandatory_channel'
    await event.edit(
        "Send the channel username (e.g., @channel_name):",
        buttons=[Button.inline("🔙 Back", b"admin_mandatory_channels")]
    )

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

async def admin_add_admin(event):
    """Add new admin"""
    user_id = event.sender_id
    lang_code = await get_user_pref(user_id, 'ui_lang', 'fa')
    
    admin_states[user_id] = 'awaiting_new_admin'
    await event.edit(
        "Send the user ID or username of the new admin:",
        buttons=[Button.inline("🔙 Back", b"admin_panel")]
    )

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
