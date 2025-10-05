import json
import subprocess
import time
import os
import threading

LAUNCHER_CONTROL_FILE = "launcher_control.json"
BOT_COMMAND = ["python", "bot.py"]  # adjust if needed

# --- Helper functions ---
def read_launcher_control():
    if not os.path.exists(LAUNCHER_CONTROL_FILE):
        return {}
    try:
        with open(LAUNCHER_CONTROL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def write_launcher_control(data: dict):
    with open(LAUNCHER_CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def set_launcher_flag(key: str, value: bool):
    control = read_launcher_control() or {}
    control[key] = bool(value)
    write_launcher_control(control)

def clear_restart_flag():
    control = read_launcher_control() or {}
    control["restart"] = False
    write_launcher_control(control)

# --- Terminal input thread ---
def terminal_listener():
    while True:
        cmd = input().strip().lower()
        if cmd == "r":
            print("[Launcher] Restart requested via terminal.")
            set_launcher_flag("restart", True)
        elif cmd == "q":
            print("[Launcher] Quit requested via terminal.")
            set_launcher_flag("stop", True)
            break

threading.Thread(target=terminal_listener, daemon=True).start()

# --- Launcher loop ---
while True:
    # Ensure stop/restart flags exist
    control = read_launcher_control()
    if "stop" not in control:
        control["stop"] = False
    if "restart" not in control:
        control["restart"] = False
    write_launcher_control(control)

    # Reset stop to False at launch so it doesn't block normal start
    if control.get("stop"):
        print("[Launcher] Stop flag was True at launch. Clearing to allow start.")
        set_launcher_flag("stop", False)

    print("[Launcher] Starting bot...")
    process = subprocess.Popen(BOT_COMMAND)

    # Wait for bot to exit
    process.wait()

    # Reload control flags
    control = read_launcher_control()
    restart_requested = control.get("restart", False)
    stop_requested = control.get("stop", False)

    # Clear restart immediately to prevent boot loop
    clear_restart_flag()

    if stop_requested:
        print("[Launcher] Stop flag detected after bot exit. Exiting launcher.")
        break

    if restart_requested:
        print("[Launcher] Restarting bot as requested...")
        time.sleep(1)  # small delay before restart
        continue

    print("[Launcher] Bot exited normally. Launcher stopping.")
    break
