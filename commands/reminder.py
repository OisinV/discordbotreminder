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

    @app_commands.command(
        name="reminder",
        description="Set a reminder"
    )
    @app_commands.describe(
        minutes="In how many minutes the reminder should fire",
        message="Reminder text",
        delivery="Delivery method: dm / channel / forum / both"
    )
    @app_commands.choices(
        delivery=[
            app_commands.Choice(name="DM only", value="dm"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="DM + Channel", value="both"),
        ]
    )
    async def reminder(
        self,
        interaction: discord.Interaction,
        minutes: int,
        message: str,
        delivery: app_commands.Choice[str] = None
    ):
        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)

        # Determine delivery mode
        delivery_mode = delivery.value if delivery else "dm"
        channel_id = None

        # Automatically assign channel_id if needed
        if delivery_mode in ("channel", "forum", "both"):
            channel_id = interaction.channel_id

        add_reminder(
            data,
            user_id=interaction.user.id,
            guild_id=interaction.guild_id,
            message=message,
            when=when,
        )
        # Save delivery info inside the last added reminder
        data["reminders"][-1]["delivery"] = delivery_mode
        if channel_id:
            data["reminders"][-1]["channel_id"] = channel_id

        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} ({interaction.user.id}) set reminder '{message}' "
            f"for {when.strftime('%Y-%m-%d %H:%M:%S %Z')} "
            f"with delivery='{delivery_mode}' channel_id={channel_id}"
        )

        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')} "
            f"(Delivery: {delivery_mode})"
        )

    @app_commands.command(name="reminderlist", description="List your reminders (admins see all)")
    async def reminderlist(self, interaction: discord.Interaction):
        user = interaction.user
        guild_id = interaction.guild_id

        if is_reminder_admin(data, guild_id, user):  # Admin/Mod
            reminders = get_all_reminders(data, guild_id)
            if not reminders:
                await interaction.response.send_message("📭 No active reminders in this server.")
                return
            text = "\n".join(
                f"[{i}] <@{r['user_id']}> — {r['message']} (⏰ {r['time']}, {r.get('delivery','dm')})"
                for i, r in enumerate(reminders, start=1)
            )

            logger.info(
                f"[GUILD {interaction.guild.name} ({guild_id})] "
                f"{user} ({user.id}) listed ALL reminders ({len(reminders)})"
            )

            await interaction.response.send_message(f"📋 All reminders in this server:\n{text}")
        else:  # Regular user
            reminders = get_user_reminders(data, user.id, guild_id)
            if not reminders:
                await interaction.response.send_message("📭 You don’t have any active reminders.")
                return
            text = "\n".join(
                f"[{i}] {r['message']} (⏰ {r['time']}, {r.get('delivery','dm')})"
                for i, r in enumerate(reminders, start=1)
            )

            logger.info(
                f"[GUILD {interaction.guild.name} ({guild_id})] "
                f"{user} ({user.id}) listed THEIR reminders ({len(reminders)})"
            )

            await interaction.response.send_message(f"📋 Your reminders:\n{text}")

    @app_commands.command(name="remindercancel", description="Cancel a reminder (admins can cancel any)")
    async def remindercancel(self, interaction: discord.Interaction, index: int):
        user = interaction.user
        guild_id = interaction.guild_id

        if is_reminder_admin(data, guild_id, user):  # Admin/Mod
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

        logger.info(
            f"[GUILD {interaction.guild.name} ({guild_id})] "
            f"{user} ({user.id}) cancelled reminder '{reminder['message']}' "
            f"(⏰ {reminder['time']}) from user {reminder['user_id']}"
        )

        await interaction.response.send_message(
            f"✅ Reminder cancelled: {reminder['message']} (⏰ {reminder['time']})"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
