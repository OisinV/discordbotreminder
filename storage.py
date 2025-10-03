import json
from datetime import datetime, timezone, timedelta
import os
import pytz

TIMEZONE = pytz.timezone("Europe/Amsterdam")
DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"reminders": [], "guilds": {}}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

# Reminders
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

# Admin/User managers
def is_reminder_admin(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    admins = guild.get("admins", [])
    return str(user.id) in admins

def is_user_manager(data, guild_id, user):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    managers = guild.get("user_managers", [])
    return str(user.id) in managers

# Guild Settings
def set_guild_default_delivery(data, guild_id, delivery):
    if "guilds" not in data:
        data["guilds"] = {}
    if str(guild_id) not in data["guilds"]:
        data["guilds"][str(guild_id)] = {}
    data["guilds"][str(guild_id)]["default_delivery"] = delivery
    save_data(data)

def get_guild_default_delivery(data, guild_id):
    guild = data.get("guilds", {}).get(str(guild_id), {})
    return guild.get("default_delivery", None)
