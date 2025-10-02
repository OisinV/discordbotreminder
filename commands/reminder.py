import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

from storage import add_reminder, load_data, get_user_reminders, remove_reminder, get_all_reminders, TIMEZONE

data = load_data()


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reminder", description="Set a reminder in X minutes")
    async def reminder(self, interaction: discord.Interaction, minutes: int, message: str):
        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        add_reminder(data, interaction.user.id, interaction.guild_id, message, when)
        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )

    @app_commands.command(name="reminderlist", description="List your reminders (admins see all)")
    async def reminderlist(self, interaction: discord.Interaction):
        user = interaction.user
        guild_id = interaction.guild_id

        if user.guild_permissions.manage_messages:  # Admin/Mod
            reminders = get_all_reminders(data, guild_id)
            if not reminders:
                await interaction.response.send_message("📭 No active reminders in this server.")
                return
            text = "\n".join(
                f"[{i}] <@{r['user_id']}> — {r['message']} (⏰ {r['time']})"
                for i, r in enumerate(reminders, start=1)
            )
            await interaction.response.send_message(f"📋 All reminders in this server:\n{text}")
        else:  # Regular user
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

        if user.guild_permissions.manage_messages:  # Admin/Mod
            reminders = get_all_reminders(data, guild_id)
        else:  # User
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
