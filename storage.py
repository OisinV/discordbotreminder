import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = Path("data.json")
TIMEZONE = ZoneInfo("Europe/Amsterdam")

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"reminders": [], "settings": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_reminder(data, user_id: int, message: str, when: datetime):
    reminder = {
        "user_id": user_id,
        "message": message,
        "time": when.astimezone(TIMEZONE).isoformat()
    }
    data["reminders"].append(reminder)
    save_data(data)

def remove_reminder(data, reminder):
    data["reminders"].remove(reminder)
    save_data(data)

def get_due_reminders(data):
    now = datetime.now(TIMEZONE)
    due = [r for r in data["reminders"] if datetime.fromisoformat(r["time"]) <= now]
    return due
