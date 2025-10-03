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
    edit_reminder,
    get_reminder_by_index,
    TIMEZONE,
    is_reminder_admin,
    is_user_manager,
    get_guild_default_delivery
)

data = load_data()
logger = logging.getLogger("bot")


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- /reminder command ---
    @app_commands.command(
        name="reminder",
        description="Set a reminder"
    )
    @app_commands.describe(
        minutes="Minutes until the reminder",
        message="Reminder text",
        delivery="Delivery: dm / channel / forum / both"
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
        guild_id = interaction.guild_id
        user = interaction.user

        # Determine delivery
        if delivery:
            delivery_mode = delivery.value
        else:
            default = get_guild_default_delivery(data, guild_id)
            if default:
                delivery_mode = default
            else:
                await interaction.response.send_message(
                    "❌ Please specify a delivery mode or set a guild default."
                )
                return

        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        channel_id = interaction.channel_id if delivery_mode in ("channel", "forum", "both") else None

        reminder_obj = add_reminder(data, user.id, guild_id, message, when)
        reminder_obj["delivery"] = delivery_mode
        if channel_id:
            reminder_obj["channel_id"] = channel_id

        logger.info(
            f"[GUILD {interaction.guild.name} ({guild_id})] "
            f"{user} set reminder '{message}' "
            f"(⏰ {when.strftime('%Y-%m-%d %H:%M:%S %Z')}, delivery={delivery_mode}, channel_id={channel_id})"
        )

        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')} "
            f"(Delivery: {delivery_mode})"
        )

    # --- /reminderlist command ---
    @app_commands.command(
        name="reminderlist",
        description="List reminders for yourself (or others if you have permission)"
    )
    async def reminderlist(self, interaction: discord.Interaction, page: int = 1):
        guild_id = interaction.guild_id
        user = interaction.user

        # Determine which reminders user can see
        if is_reminder_admin(data, guild_id, user) or is_user_manager(data, guild_id, user):
            reminders = get_all_reminders(data, guild_id)
        else:
            reminders = get_user_reminders(data, user.id, guild_id)

        if not reminders:
            await interaction.response.send_message("No reminders found.")
            return

        # Pagination
        per_page = 5
        max_pages = (len(reminders) + per_page - 1) // per_page
        if page < 1 or page > max_pages:
            await interaction.response.send_message(f"Invalid page. Must be 1-{max_pages}.")
            return

        start = (page - 1) * per_page
        end = start + per_page
        text = ""
        for i, r in enumerate(reminders[start:end], start=start + 1):
            text += f"**{i}.** {r['message']} (⏰ {r['time']}, delivery={r.get('delivery','dm')})\n"

        await interaction.response.send_message(f"Reminders (Page {page}/{max_pages}):\n{text}")

    # --- /reminderedit command ---
    @app_commands.command(
        name="reminderedit",
        description="Edit an existing reminder"
    )
    @app_commands.describe(
        index="Reminder index from /reminderlist",
        message="New message (optional)",
        minutes="New minutes until reminder (optional)"
    )
    async def reminderedit(self, interaction: discord.Interaction, index: int, message: str = None, minutes: int = None):
        guild_id = interaction.guild_id
        user = interaction.user

        # Determine which reminders user can edit
        if is_reminder_admin(data, guild_id, user) or is_user_manager(data, guild_id, user):
            reminder_obj = get_reminder_by_index(data, guild_id, index)
        else:
            reminder_obj = get_reminder_by_index(data, guild_id, index, user)

        if not reminder_obj:
            await interaction.response.send_message("❌ Reminder not found or you do not have permission.")
            return

        new_time = datetime.now(TIMEZONE) + timedelta(minutes=minutes) if minutes else None
        edit_reminder(data, reminder_obj, message=message, new_time=new_time)

        await interaction.response.send_message(f"✅ Reminder updated successfully.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
