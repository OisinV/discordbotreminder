import json
from datetime import datetime
import pytz
import os
import logging

# ------------------- Constants -------------------
TIMEZONE = pytz.timezone("Europe/Amsterdam")
DATA_FILE = "data.json"
SETTINGS_FILE = "settings.json"
LOG_FILE = "actions.log"

# ------------------- Logging Setup -------------------
logger = logging.getLogger("actions")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def log_action(action: str):
    logger.info(action)

# ------------------- Initialize Data Files -------------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"reminders": [], "guilds": {}}, f, indent=4)

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"backend_guild": None}, f, indent=4)

# ------------------- Data Load/Save -------------------
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

def load_settings():
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ------------------- Reminders -------------------
def add_reminder(data, user_id, guild_id, message, time: datetime, delivery=None, target_mention=None, channel_id=None):
    reminder = {
        "user_id": user_id,
        "guild_id": guild_id,
        "message": message,
        "time": time.isoformat(),
        "delivery": delivery,
        "target_mention": target_mention,
        "channel_id": channel_id
    }
    data.setdefault("reminders", []).append(reminder)
    save_data(data)
    log_action(f"[GUILD {guild_id}] User {user_id} added reminder: '{message}' for {reminder['time']}")
    return reminder

def remove_reminder(data, reminder):
    if reminder in data.get("reminders", []):
        data["reminders"].remove(reminder)
        save_data(data)
        log_action(f"[GUILD {reminder['guild_id']}] Removed reminder for user {reminder['user_id']}: '{reminder['message']}'")

def get_all_reminders(data, guild_id):
    return [r for r in data.get("reminders", []) if r["guild_id"] == guild_id]

def get_user_reminders(data, guild_id, user_id=None):
    if user_id:
        return [r for r in data.get("reminders", []) if r["guild_id"] == guild_id and r["user_id"] == user_id]
    return [r for r in data.get("reminders", []) if r["guild_id"] == guild_id]

def get_due_reminders(data):
    now = datetime.now(TIMEZONE)
    due = []
    for r in data.get("reminders", []):
        try:
            r_time = datetime.fromisoformat(r["time"])
            if r_time.tzinfo is None:
                r_time = TIMEZONE.localize(r_time)
            if r_time <= now:
                due.append(r)
        except Exception as e:
            log_action(f"[ERROR] Failed to parse reminder time: {r['time']} ({e})")
    return due

# ------------------- Guild Defaults -------------------
def get_guild_default_delivery(data, guild_id):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    return guild.get("default_delivery")

def set_guild_default_delivery(data, guild_id, delivery):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    guild["default_delivery"] = delivery
    save_data(data)
    log_action(f"[GUILD {guild_id}] Default delivery set to {delivery}")

# ------------------- Admin / User Manager -------------------
def add_admin(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    key = "admin_roles" if is_role else "admins"
    items = guild.setdefault(key, [])
    if str(user_or_role_id) not in items:
        items.append(str(user_or_role_id))
        save_data(data)
        log_action(f"[GUILD {guild_id}] Added {'role' if is_role else 'user'} {user_or_role_id} as Admin")

def remove_admin(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    key = "admin_roles" if is_role else "admins"
    items = guild.setdefault(key, [])
    if str(user_or_role_id) in items:
        items.remove(str(user_or_role_id))
        save_data(data)
        log_action(f"[GUILD {guild_id}] Removed {'role' if is_role else 'user'} {user_or_role_id} from Admins")

def add_user_manager(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    key = "user_manager_roles" if is_role else "user_managers"
    items = guild.setdefault(key, [])
    if str(user_or_role_id) not in items:
        items.append(str(user_or_role_id))
        save_data(data)
        log_action(f"[GUILD {guild_id}] Added {'role' if is_role else 'user'} {user_or_role_id} as User Manager")

def remove_user_manager(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    key = "user_manager_roles" if is_role else "user_managers"
    items = guild.setdefault(key, [])
    if str(user_or_role_id) in items:
        items.remove(str(user_or_role_id))
        save_data(data)
        log_action(f"[GUILD {guild_id}] Removed {'role' if is_role else 'user'} {user_or_role_id} from User Managers")

def is_reminder_admin(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    admins = guild.get("admins", [])
    admin_roles = guild.get("admin_roles", [])
    if str(user.id) in admins:
        return True
    if any(str(role.id) in admin_roles for role in getattr(user, "roles", [])):
        return True
    return False

def is_user_manager(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    managers = guild.get("user_managers", [])
    manager_roles = guild.get("user_manager_roles", [])
    if str(user.id) in managers:
        return True
    if any(str(role.id) in manager_roles for role in getattr(user, "roles", [])):
        return True
    return False

# ------------------- Update Channels -------------------
def add_update_channel(data, guild_id, channel_id):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    channels = guild.setdefault("update_channels", [])
    if str(channel_id) not in channels:
        channels.append(str(channel_id))
        save_data(data)
        log_action(f"[GUILD {guild_id}] Added update channel {channel_id}")

def remove_update_channel(data, guild_id, channel_id):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    channels = guild.setdefault("update_channels", [])
    if str(channel_id) in channels:
        channels.remove(str(channel_id))
        save_data(data)
        log_action(f"[GUILD {guild_id}] Removed update channel {channel_id}")

def get_all_update_channels(data):
    channels = []
    for gid, gdata in data.get("guilds", {}).items():
        for ch in gdata.get("update_channels", []):
            channels.append((gid, ch))
    return channels
