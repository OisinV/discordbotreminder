import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = Path("data.json")
TIMEZONE = ZoneInfo("Europe/Amsterdam")


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"reminders": [], "settings": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------- Reminders ---------------- #

def add_reminder(data, user_id: int, guild_id: int, message: str, when: datetime):
    reminder = {
        "user_id": user_id,
        "guild_id": guild_id,
        "message": message,
        "time": when.astimezone(TIMEZONE).isoformat()
    }
    data["reminders"].append(reminder)
    save_data(data)


def remove_reminder(data, reminder):
    if reminder in data["reminders"]:
        data["reminders"].remove(reminder)
        save_data(data)


def get_due_reminders(data):
    now = datetime.now(TIMEZONE)
    due = []
    for r in data["reminders"]:
        try:
            rt = datetime.fromisoformat(r["time"])
        except Exception:
            continue
        if rt <= now:
            due.append(r)
    return due


def get_user_reminders(data, user_id: int, guild_id: int):
    return [r for r in data["reminders"] if r["user_id"] == user_id and r["guild_id"] == guild_id]


def get_all_reminders(data, guild_id: int):
    return [r for r in data["reminders"] if r["guild_id"] == guild_id]


# ---------------- Admins ---------------- #

def _ensure_guild_settings(data, guild_id: int):
    if str(guild_id) not in data["settings"]:
        data["settings"][str(guild_id)] = {"admins": {"users": [], "roles": []}}


def add_admin(data, guild_id: int, target_id: int, kind: str):
    """kind = 'user' or 'role'"""
    _ensure_guild_settings(data, guild_id)
    admins = data["settings"][str(guild_id)]["admins"][f"{kind}s"]
    if target_id not in admins:
        admins.append(target_id)
        save_data(data)


def remove_admin(data, guild_id: int, target_id: int, kind: str):
    _ensure_guild_settings(data, guild_id)
    admins = data["settings"][str(guild_id)]["admins"][f"{kind}s"]
    if target_id in admins:
        admins.remove(target_id)
        save_data(data)


def list_admins(data, guild_id: int):
    _ensure_guild_settings(data, guild_id)
    return data["settings"][str(guild_id)]["admins"]


def is_reminder_admin(data, guild_id: int, member) -> bool:
    """Check if a member is a reminder admin (by user or role)."""
    _ensure_guild_settings(data, guild_id)
    guild_admins = data["settings"][str(guild_id)]["admins"]

    # User match
    if member.id in guild_admins["users"]:
        return True

    # Role match
    if any(role.id in guild_admins["roles"] for role in member.roles):
        return True

    return False
