import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import logging

from storage import (
    add_reminder,
    load_data,
    get_user_reminders,
    remove_reminder,
    get_all_reminders,
    TIMEZONE,
    is_reminder_admin
)

data = load_data()
logger = logging.getLogger("bot")


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reminder", description="Set a reminder in X minutes")
    async def reminder(self, interaction: discord.Interaction, minutes: int, message: str):
        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        add_reminder(data, interaction.user.id, interaction.guild_id, message, when)

        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} ({interaction.user.id}) set reminder '{message}' "
            f"for {when.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )

        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )

    @app_commands.command(name="reminderlist", description="List your reminders (admins see all)")
    async def reminderl
