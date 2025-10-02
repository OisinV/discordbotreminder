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
