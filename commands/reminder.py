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
    is_reminder_admin,
    is_user_manager,
    get_guild_default_delivery
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

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
