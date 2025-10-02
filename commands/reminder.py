import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

from storage import add_reminder, load_data, TIMEZONE

data = load_data()


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reminder", description="Set a reminder in X minutes")
    async def reminder(self, interaction: discord.Interaction, minutes: int, message: str):
        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        add_reminder(data, interaction.user.id, message, when)
        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
