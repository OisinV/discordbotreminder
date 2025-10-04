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
    get_guild_default_delivery,
    save_data,
    TIMEZONE
)

data = load_data()
logger = logging.getLogger("bot")

class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def resolve_target(self, interaction: discord.Interaction, target: str):
        """Resolve target string to member or role mention."""
        user = interaction.user
        if not target or target.lower() == "self":
            return user.mention

        if target.lower() in ["everyone", "here"]:
            if not user.guild_permissions.mention_everyone:
                return None
            return f"@{target.lower()}"

        member = None
        # Check if mention like <@123456789>
        if target.startswith("<@") and target.endswith(">"):
            try:
                target_id = int(target.replace("<@", "").replace(">", "").replace("!", ""))
                member = interaction.guild.get_member(target_id)
            except Exception:
                member = None
        elif target.isdigit():
            member = interaction.guild.get_member(int(target))
        else:
            member = interaction.guild.get_member_named(target)

        if member:
            return member.mention

        # Check role by name
        role = discord.utils.get(interaction.guild.roles, name=target)
        if role:
            return role.mention

        return None

    @app_commands.command(name="reminder", description="Set a reminder")
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
        try:
            guild_id = interaction.guild_id
            user = interaction.user

            delivery_mode = delivery.value if delivery else get_guild_default_delivery(data, guild_id)
            if not delivery_mode:
                await interaction.response.send_message("❌ Please specify a delivery mode or set a guild default.")
                return

            mention_text = self.resolve_target(interaction, target)
            if not mention_text:
                await interaction.response.send_message(f"❌ Target `{target}` not found or you lack permissions.")
                return

            when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)

            # Thread-aware: store actual channel/thread ID
            if delivery_mode in ("channel", "forum", "both"):
                channel_id = interaction.channel.id
            else:
                channel_id = None

            reminder_obj = add_reminder(data, user.id, guild_id, message, when)
            reminder_obj["delivery"] = delivery_mode
            reminder_obj["target_mention"] = mention_text
            if channel_id:
                reminder_obj["channel_id"] = channel_id

            # Save time as ISO string to avoid datetime issues
            reminder_obj["time"] = when.isoformat()

            save_data(data)

            await interaction.response.send_message(
                f"⏰ Reminder set for {mention_text} at {when.strftime('%Y-%m-%d %H:%M:%S %Z')} (Delivery: {delivery_mode})"
            )
            logger.info(
                f"[GUILD {interaction.guild.name} ({guild_id})] {user} set reminder '{message}' for '{mention_text}' "
                f"(⏰ {when}, delivery={delivery_mode}, channel={channel_id})"
            )
        except Exception as e:
            logger.exception(f"Error in reminder command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while setting the reminder.")

    @app_commands.command(name="cancelreminder", description="Cancel your own reminders")
    async def cancelreminder(self, interaction: discord.Interaction):
        try:
            guild_id = interaction.guild_id
            user_id = interaction.user.id
            reminders = get_user_reminders(data, guild_id, user_id)
            if not reminders:
                await interaction.response.send_message("You have no active reminders.")
                return

            for r in reminders:
                remove_reminder(data, r)
            save_data(data)

            await interaction.response.send_message(f"✅ Canceled {len(reminders)} of your reminders.")
            logger.info(f"[GUILD {interaction.guild.name} ({guild_id})] {interaction.user} canceled {len(reminders)} reminders.")
        except Exception as e:
            logger.exception(f"Error in cancelreminder command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while canceling your reminders.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
