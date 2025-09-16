# utils.py
import logging

logger = logging.getLogger(__name__)

async def get_user_pref(user_id, key, default_value=None):
    """Gets a specific preference for a user."""
    if user_id not in user_data:
        return default_value
    return user_data.get(user_id, {}).get(key, default_value)

async def set_user_pref(user_id, key, value):
    """Sets a user preference in memory."""
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id][key] = value
    logger.debug(f"Set user {user_id} preference {key} to {value}")
