# database.py
import aiosqlite
import asyncio
import traceback
from config import DB_FILE

async def initialize_database():
    """Initialize database with required tables"""
    async with aiosqlite.connect(DB_FILE) as db:
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
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_channels (
                channel_id INTEGER PRIMARY KEY,
                channel_username TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        print("Database initialized.")

async def add_or_update_user(user_id, username=None, first_name=None):
    """Add or update user in database"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
                exists = await cursor.fetchone()

            if exists:
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
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, ui_lang, selected_ai_model, last_seen)
                    VALUES (?, ?, ?, 'fa', 'gpt4', CURRENT_TIMESTAMP)
                """, (user_id, username, first_name))

            await db.commit()
    except Exception as e:
        print(f"DB Error in add_or_update_user for {user_id}: {e}")
        traceback.print_exc()

async def get_user_data(user_id):
    """Get user data from database"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'ui_lang': row[3],
                        'selected_ai_model': row[4]
                    }
                return None
    except Exception as e:
        print(f"DB Error fetching user data for {user_id}: {e}")
        return None

async def update_user_field(user_id, field, value):
    """Update specific field for user"""
    allowed_fields = ['ui_lang', 'selected_ai_model']
    if field not in allowed_fields:
        print(f"Attempted to update disallowed field: {field}")
        return
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(f"UPDATE users SET {field} = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?", (value, user_id))
            await db.commit()
    except Exception as e:
        print(f"DB Error updating field {field} for user {user_id}: {e}")

async def get_all_user_ids():
    """Get all user IDs from database"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        print(f"Database error in get_all_user_ids: {e}")
        return []

async def is_admin(user_id):
    """Check if user is admin"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

async def add_admin(user_id):
    """Add user to admin list"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
            await db.commit()
        return True
    except Exception as e:
        print(f"Error adding admin: {e}")
        return False

async def remove_admin(user_id):
    """Remove user from admin list"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            await db.commit()
        return True
    except Exception as e:
        print(f"Error removing admin: {e}")
        return False

async def get_all_admins():
    """Get all admin IDs"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT user_id FROM admins") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        print(f"Error getting admins: {e}")
        return []

async def get_setting(key, default=None):
    """Get setting value"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return default

async def set_setting(key, value):
    """Set setting value"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            await db.commit()
        return True
    except Exception as e:
        print(f"Error setting setting {key}: {e}")
        return False

async def get_mandatory_channels():
    """Get all mandatory channels"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT channel_id, channel_username FROM mandatory_channels") as cursor:
                rows = await cursor.fetchall()
                return [{'id': row[0], 'username': row[1]} for row in rows]
    except Exception as e:
        print(f"Error getting mandatory channels: {e}")
        return []

async def add_mandatory_channel(channel_id, channel_username):
    """Add mandatory channel"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT OR REPLACE INTO mandatory_channels (channel_id, channel_username) VALUES (?, ?)",
                (channel_id, channel_username)
            )
            await db.commit()
        return True
    except Exception as e:
        print(f"Error adding mandatory channel: {e}")
        return False

async def remove_mandatory_channel(channel_id):
    """Remove mandatory channel"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM mandatory_channels WHERE channel_id = ?", (channel_id,))
            await db.commit()
        return True
    except Exception as e:
        print(f"Error removing mandatory channel: {e}")
        return False
