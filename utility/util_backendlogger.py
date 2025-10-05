# utility/util_backendlogger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger():
    """Sets up a rotating logger for the bot and returns it."""
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "bot.log")

    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger  # Prevent double initialization

    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.info("Logger initialized successfully.")
    return logger


def log_command_attempt(interaction, command_name: str, permission_required: str, success: bool, reason: str = ""):
    """
    Centralized command audit logger.
    Logs who used a command, when, success/fail, and permission result.
    """
    logger = logging.getLogger("bot")

    user = f"{interaction.user} ({interaction.user.id})"
    guild = interaction.guild.name if interaction.guild else "DM"
    guild_id = interaction.guild.id if interaction.guild else "None"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    status = "✅ SUCCESS" if success else "❌ FAILED"
    reason_text = f"Reason: {reason}" if reason else ""

    log_entry = (
        f"[{timestamp}] [{status}] Command: /{command_name} | "
        f"User: {user} | Guild: {guild} ({guild_id}) | "
        f"Permission: {permission_required} | {reason_text}"
    )

    if success:
        logger.info(log_entry)
    else:
        logger.warning(log_entry)
