import re
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

from storage import (
    add_reminder, load_data, get_user_reminders, remove_reminder,
    get_all_reminders, is_admin, TIMEZONE
)

data = load_data()


def parse_duration(text: str) -> timedelta:
    """
    Parse strings like '1h30m', '2d5h10m', '45m' into timedelta.
    Default unit = minutes if only number is given.
    """
    pattern = re.compile(r"((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?")
    match = pattern.fullmatch(text.strip().lower())
    if not match:
        raise ValueError("Invalid time format. Use like: 10m, 2h30m, 1d2h")
    parts = {name: int(val) for name, val in match.groupdict(default=0).items()}
    return timedelta(days=parts["days"], hours=parts["hours"], minutes=parts["minutes"])


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reminder", description="Set a reminder with time like 10m, 2h, 1d2h30m")
    async def reminder(self, interaction: discord.Interaction, duration: str, message: str):
        try:
            delta = parse_duration(duration)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        when = datetime.now(TIMEZONE) + delta
        add_reminder(data, interaction.user.id, interaction.guild_id, message, when)
        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )

    @app_commands.command(name="reminderlist", description="List reminders (admins see all)")
    async def reminderlist(self, interaction: discord.Interaction):
        user = interaction.user
        guild_id = interaction.guild_id

        if is_admin(data, guild_id, user):
            reminders = get_all_reminders(data, guild_id)
            if not reminders:
                await interaction.response.send_message("📭 No active reminders in this server.")
                return
            text = "\n".join(
                f"[{i}] <@{r['user_id']}> — {r['message']} (⏰ {r['time']})"
                for i, r in enumerate(reminders, start=1)
            )
            await interaction.response.send_message(f"📋 All reminders in this server:\n{text}")
        else:
            reminders = get_user_reminders(data, user.id, guild_id)
            if not reminders:
                await interaction.response.send_message("📭 You don’t have any active reminders.")
                return
            text = "\n".join(
                f"[{i}] {r['message']} (⏰ {r['time']})"
                for i, r in enumerate(reminders, start=1)
            )
            await interaction.response.send_message(f"📋 Your reminders:\n{text}")

    @app_commands.command(name="remindercancel", description="Cancel a reminder (admins can cancel any)")
    async def remindercancel(self, interaction: discord.Interaction, index: int):
        user = interaction.user
        guild_id = interaction.guild_id

        if is_admin(data, guild_id, user):
            reminders = get_all_reminders(data, guild_id)
        else:
            reminders = get_user_reminders(data, user.id, guild_id)

        if not reminders:
            await interaction.response.send_message("❌ No reminders found.")
            return

        if index < 1 or index > len(reminders):
            await interaction.response.send_message("⚠️ Invalid reminder index.")
            return

        reminder = reminders[index - 1]
        remove_reminder(data, reminder)

        await interaction.response.send_message(
            f"✅ Reminder cancelled: {reminder['message']} (⏰ {reminder['time']})"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
