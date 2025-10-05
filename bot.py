import discord
from discord.ext import commands
import asyncio
import logging
import json
import os
import time
from storage import load_data, get_due_reminders, remove_reminder
from utility.util_backendlogger import setup_logger

logger = setup_logger()
logger.info("Bot starting...")

# ============================================================
# ------------------- Logging Setup ------------------------
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# ============================================================
# ------------------- Settings Management ------------------
# ============================================================
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "token": "YOUR_BOT_TOKEN_HERE",
    "test_guild_id": None,
    "backend_guild_id": 1424002405913202700, # this is a default option, if you want your own server please replace this
    "backend_log_channel_id": None,
    "support_invite": "https://discord.gg/YOUR_DEFAULT_INVITE",
    "check_interval_seconds": 60,
    "log_level": "INFO",
    "auto_restart": True
}

_last_settings_mtime = None
_settings_cache = None

def load_settings(force=False):
    """
    Load or create settings.json with defaults.
    Auto-fills missing keys and updates cached settings.
    """
    global _last_settings_mtime, _settings_cache

    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        logging.warning(f"No {SETTINGS_FILE} found. Created default settings. Edit token before running.")
        return DEFAULT_SETTINGS.copy()

    mtime = os.path.getmtime(SETTINGS_FILE)
    if not force and _last_settings_mtime == mtime and _settings_cache:
        return _settings_cache

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)

    # Fill missing keys
    changed = False
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
            changed = True
    if changed:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        logging.info("Updated settings.json with missing default keys.")

    _last_settings_mtime = mtime
    _settings_cache = settings

    # Update log level dynamically
    log_level = getattr(logging, settings.get("log_level", "INFO").upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)

    return settings

settings = load_settings()

# ============================================================
# ------------------- Bot Setup -----------------------------
# ============================================================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
data = load_data()

# ============================================================
# ------------------- Backend Logging -----------------------
# ============================================================
async def backend_log(message: str):
    """Send a message to the backend log channel if configured."""
    backend_channel_id = settings.get("backend_log_channel_id")
    if not backend_channel_id:
        return
    try:
        channel = bot.get_channel(int(backend_channel_id))
        if channel:
            await channel.send(f"🛰️ **Backend Log:** {message}")
        else:
            logging.warning(f"Backend log channel {backend_channel_id} not found.")
    except Exception as e:
        logging.error(f"Failed to send backend log: {e}")

# ============================================================
# ------------------- Reminder Delivery ---------------------
# ============================================================
async def deliver_reminder(r, missed=False):
    """Deliver a single reminder according to its delivery type."""
    try:
        delivery_mode = r.get("delivery", "dm")
        target_mention = r.get("target_mention", f"<@{r['user_id']}>")
        status = "MISSED " if missed else ""

        if delivery_mode in ("dm", "both"):
            user = await bot.fetch_user(r["user_id"])
            if user:
                await user.send(f"⏰ {status}Reminder: {r['message']}")

        if delivery_mode in ("channel", "both") and "channel_id" in r:
            channel = bot.get_channel(r["channel_id"])
            if channel:
                await channel.send(f"⏰ {status}Reminder for {target_mention}: {r['message']}")

        if delivery_mode == "forum" and "channel_id" in r:
            channel = bot.get_channel(r["channel_id"])
            if isinstance(channel, discord.Thread):
                await channel.send(f"{target_mention} ⏰ {status}Reminder: {r['message']}")
            elif isinstance(channel, discord.ForumChannel):
                thread = await channel.create_thread(
                    name=f"{status}Reminder: {r['message'][:50]}",
                    type=discord.ChannelType.public_thread
                )
                await thread.send(f"{target_mention} ⏰ {r['message']}")
    except Exception as e:
        await backend_log(f"⚠️ Failed to deliver reminder: {e}")
        logging.error(f"[GUILD {r.get('guild_id', '?')}] Failed to deliver {status.lower()}reminder: {e}")

# ============================================================
# ------------------- Reminder Loop -------------------------
# ============================================================
async def reminder_loop():
    """Background task to check for due reminders."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            current_settings = load_settings()
            interval = current_settings.get("check_interval_seconds", 60)

            due = get_due_reminders(data)
            for r in due:
                await deliver_reminder(r)
                remove_reminder(data, r)
        except Exception as e:
            await backend_log(f"💥 Reminder loop crashed: {e}")
            logging.exception(f"Error in reminder loop: {e}")
        await asyncio.sleep(interval)

# ============================================================
# ------------------- Settings Watcher ----------------------
# ============================================================
async def settings_watcher():
    """Watch settings.json for changes and reload automatically."""
    await bot.wait_until_ready()
    last_seen = os.path.getmtime(SETTINGS_FILE)
    while not bot.is_closed():
        try:
            mtime = os.path.getmtime(SETTINGS_FILE)
            if mtime != last_seen:
                load_settings(force=True)
                last_seen = mtime
                await backend_log("🔄 Settings file reloaded successfully.")
                logging.info("Settings reloaded from disk.")
        except Exception as e:
            await backend_log(f"⚠️ Settings watcher error: {e}")
            logging.error(f"Settings watcher error: {e}")
        await asyncio.sleep(10)

# ============================================================
# ------------------- Bot Events ----------------------------
# ============================================================
@bot.event
async def on_ready():
    logging.info(f"Bot online as {bot.user}")
    await backend_log(f"✅ Bot online as **{bot.user}**")

    # Deliver missed reminders
    for r in get_due_reminders(data):
        await deliver_reminder(r, missed=True)
        remove_reminder(data, r)

    # Start background loops
    bot.loop.create_task(reminder_loop())
    bot.loop.create_task(settings_watcher())

    # Command syncing
    TEST_GUILD_ID = settings.get("test_guild_id")
    try:
        if TEST_GUILD_ID:
            synced_guild = await bot.tree.sync(guild=discord.Object(id=TEST_GUILD_ID))
            logging.info(f"Synced {len(synced_guild)} commands to test guild ({TEST_GUILD_ID})")
    except Exception as e:
        logging.error(f"Failed to sync test guild commands: {e}")

    try:
        synced_global = await bot.tree.sync()
        logging.info(f"Synced {len(synced_global)} global commands")
    except Exception as e:
        logging.error(f"Failed to sync global commands: {e}")

# ============================================================
# ------------------- Load Extensions -----------------------
# ============================================================
async def load_commands():
    """Load all command cogs."""
    await bot.load_extension("commands.reminder")
    await bot.load_extension("commands.reminderadmin")
    await bot.load_extension("commands.testmsg")
    await bot.load_extension("commands.backendcontrol")

# ============================================================
# ------------------- Main Entry ----------------------------
# ============================================================
async def main():
    async with bot:
        await load_commands()
        token = settings.get("token")
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            logging.error("❌ Discord token missing in settings.json! Please fill it in before running the bot.")
            return
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
