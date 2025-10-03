import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import logging

from storage import (
    add_reminder,
    load_data,
    get_guild_default_delivery,
    TIMEZONE
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
        delivery="Delivery: dm / channel / forum / both",
        target="Optional: user, role, or 'everyone'"
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
        delivery: app_commands.Choice[str] = None,
        target: str = None
    ):
        guild_id = interaction.guild_id
        user = interaction.user

        # Determine delivery
        delivery_mode = delivery.value if delivery else get_guild_default_delivery(data, guild_id)
        if not delivery_mode:
            await interaction.response.send_message("❌ Please specify a delivery mode or set a guild default.")
            return

        # Determine target mention
        mention_text = ""
        if not target or target.lower() == "self":
            mention_text = user.mention
        else:
            # Everyone / here ping
            if target.lower() in ["everyone", "here"]:
                mention_text = f"@{target.lower()}"
            else:
                # Try user
                member = interaction.guild.get_member_named(target)
                if member:
                    mention_text = member.mention
                else:
                    # Try role
                    role = discord.utils.get(interaction.guild.roles, name=target)
                    if role:
                        mention_text = role.mention
                    else:
                        await interaction.response.send_message(f"❌ Target `{target}` not found as user or role.")
                        return

        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        channel_id = interaction.channel_id if delivery_mode in ("channel", "forum", "both") else None

        reminder_obj = add_reminder(data, user.id, guild_id, message, when)
        reminder_obj["delivery"] = delivery_mode
        reminder_obj["target_mention"] = mention_text
        if channel_id:
            reminder_obj["channel_id"] = channel_id

        logger.info(
            f"[GUILD {interaction.guild.name} ({guild_id})] "
            f"{user} set reminder '{message}' for '{mention_text}' "
            f"(⏰ {when.strftime('%Y-%m-%d %H:%M:%S %Z')}, delivery={delivery_mode}, channel_id={channel_id})"
        )

        await interaction.response.send_message(
            f"⏰ Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S %Z')} "
            f"(Delivery: {delivery_mode}, Target: {mention_text})"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
    
