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
    TIMEZONE,
    get_guild_default_delivery
)

data = load_data()
logger = logging.getLogger("bot")

class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- /reminder ---
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

        # Determine delivery mode
        delivery_mode = delivery.value if delivery else get_guild_default_delivery(data, guild_id)
        if not delivery_mode:
            await interaction.response.send_message(
                "❌ Please specify a delivery mode or set a guild default."
            )
            return

        # Determine target mention
        mention_text = user.mention
        if target and target.lower() != "self":
            # Everyone / here ping
            if target.lower() in ["everyone", "here"]:
                if not interaction.user.guild_permissions.mention_everyone:
                    await interaction.response.send_message(
                        "❌ You do not have permission to mention everyone/here."
                    )
                    return
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
                        await interaction.response.send_message(
                            f"❌ Target `{target}` not found as user or role."
                        )
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

    # --- /reminderlist ---
    @app_commands.command(
        name="reminderlist",
        description="List your active reminders"
    )
    async def reminderlist(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user = interaction.user
        reminders = get_user_reminders(data, user.id, guild_id)

        if not reminders:
            await interaction.response.send_message("📭 You have no active reminders.")
            return

        lines = []
        for idx, r in enumerate(reminders, 1):
            lines.append(
                f"{idx}. {r['message']} (⏰ {r['time']}, Delivery: {r.get('delivery', 'dm')}, Target: {r.get('target_mention', user.mention)})"
            )

        chunk_size = 2000
        text = "\n".join(lines)
        if len(text) <= chunk_size:
            await interaction.response.send_message(f"📋 Your reminders:\n{text}")
        else:
            # Split into multiple messages if too long
            for i in range(0, len(lines), 20):
                await interaction.user.send("📋 Your reminders:\n" + "\n".join(lines[i:i+20]))
            await interaction.response.send_message("✅ Your reminders list was sent via DM (too long for chat).")

    # --- /remindercancel ---
    @app_commands.command(
        name="remindercancel",
        description="Cancel one of your active reminders"
    )
    @app_commands.describe(
        index="Index of the reminder from /reminderlist to cancel"
    )
    async def remindercancel(self, interaction: discord.Interaction, index: int):
        guild_id = interaction.guild_id
        user = interaction.user
        reminders = get_user_reminders(data, user.id, guild_id)

        if not reminders:
            await interaction.response.send_message("📭 You have no active reminders.")
            return

        if index < 1 or index > len(reminders):
            await interaction.response.send_message("❌ Invalid reminder index.")
            return

        reminder_to_remove = reminders[index - 1]
        remove_reminder(data, reminder_to_remove)
        await interaction.response.send_message(
            f"✅ Reminder cancelled: {reminder_to_remove['message']}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
