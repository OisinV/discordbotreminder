import json
from datetime import datetime, timezone, timedelta
import os
import pytz

TIMEZONE = pytz.timezone("Europe/Amsterdam")
DATA_FILE = "data.json"

# --- Initialization ---
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"reminders": [], "guilds": {}}, f)


# --- Data Loading/Saving ---
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


def edit_reminder(data, reminder, message=None, new_time=None, delivery=None, channel_id=None):
    if message:
        reminder["message"] = message
    if new_time:
        reminder["time"] = new_time.strftime("%Y-%m-%d %H:%M:%S")
    if delivery:
        reminder["delivery"] = delivery
    if channel_id is not None:
        reminder["channel_id"] = channel_id
    save_data(data)


def get_reminder_by_index(data, guild_id, index, user=None):
    """
    Returns the reminder at the given 1-based index for the guild.
    If user is provided, only their reminders are considered.
    """
    reminders = get_all_reminders(data, guild_id) if user is None else get_user_reminders(data, user.id, guild_id)
    if 1 <= index <= len(reminders):
        return reminders[index - 1]
    return None


# --- Admin/User Managers ---
def is_reminder_admin(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    admins = guild.get("admins", [])
    admin_roles = guild.get("admin_roles", [])
    if str(user.id) in admins:
        return True
    # Check roles
    if isinstance(user, discord.Member):
        for r in user.roles:
            if str(r.id) in admin_roles:
                return True
    return False


def is_user_manager(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    managers = guild.get("user_managers", [])
    manager_roles = guild.get("user_manager_roles", [])
    if str(user.id) in managers:
        return True
    # Check roles
    if isinstance(user, discord.Member):
        for r in user.roles:
            if str(r.id) in manager_roles:
                return True
    return False


# --- Guild Settings ---
def set_guild_default_delivery(data, guild_id, delivery):
    guild_data = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    guild_data["default_delivery"] = delivery
    save_data(data)


def get_guild_default_delivery(data, guild_id):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    return guild.get("default_delivery", None)
