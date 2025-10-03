import json
from datetime import datetime
import pytz
import os

TIMEZONE = pytz.timezone("Europe/Amsterdam")
DATA_FILE = "data.json"

# Initialize data file
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"reminders": [], "guilds": {}}, f, indent=4)

# --- Data Load/Save ---
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

# --- Reminders ---
def add_reminder(data, user_id, guild_id, message, time):
    reminder = {
        "user_id": user_id,
        "guild_id": guild_id,
        "message": message,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    data["reminders"].append(reminder)
    save_data(data)
    return reminder

def remove_reminder(data, reminder):
    if reminder in data["reminders"]:
        data["reminders"].remove(reminder)
        save_data(data)

def get_all_reminders(data, guild_id):
    return [r for r in data["reminders"] if r["guild_id"] == guild_id]

def get_user_reminders(data, user_id, guild_id):
    return [r for r in data["reminders"] if r["guild_id"] == guild_id and r["user_id"] == user_id]

def get_due_reminders(data):
    now = datetime.now(TIMEZONE)
    due = []
    for r in data["reminders"]:
        r_time = datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S")
        r_time = TIMEZONE.localize(r_time)
        if r_time <= now:
            due.append(r)
    return due

def get_guild_default_delivery(data, guild_id):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    return guild.get("default_delivery", None)

# --- Admin/User Manager Helpers ---
def add_admin(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        admin_roles = guild.setdefault("admin_roles", [])
        if str(user_or_role_id) not in admin_roles:
            admin_roles.append(str(user_or_role_id))
    else:
        admins = guild.setdefault("admins", [])
        if str(user_or_role_id) not in admins:
            admins.append(str(user_or_role_id))
    save_data(data)

def remove_admin(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        admin_roles = guild.setdefault("admin_roles", [])
        if str(user_or_role_id) in admin_roles:
            admin_roles.remove(str(user_or_role_id))
    else:
        admins = guild.setdefault("admins", [])
        if str(user_or_role_id) in admins:
            admins.remove(str(user_or_role_id))
    save_data(data)

def add_user_manager(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        manager_roles = guild.setdefault("user_manager_roles", [])
        if str(user_or_role_id) not in manager_roles:
            manager_roles.append(str(user_or_role_id))
    else:
        managers = guild.setdefault("user_managers", [])
        if str(user_or_role_id) not in managers:
            managers.append(str(user_or_role_id))
    save_data(data)

def remove_user_manager(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        manager_roles = guild.setdefault("user_manager_roles", [])
        if str(user_or_role_id) in manager_roles:
            manager_roles.remove(str(user_or_role_id))
    else:
        managers = guild.setdefault("user_managers", [])
        if str(user_or_role_id) in managers:
            managers.remove(str(user_or_role_id))
    save_data(data)

def is_reminder_admin(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    admins = guild.get("admins", [])
    return str(user.id) in admins

def is_user_manager(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    managers = guild.get("user_managers", [])
    return str(user.id) in managers

def set_guild_default_delivery(data, guild_id, delivery):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    guild["default_delivery"] = delivery
    save_data(data)
