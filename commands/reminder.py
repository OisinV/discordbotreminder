import discord
from discord import app_commands
from discord.ext import commands, tasks
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

    # --- Set Reminder ---
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

    # --- Reminder List ---
    @app_commands.command(
        name="reminderlist",
        description="List reminders in this guild"
    )
    async def reminderlist(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user = interaction.user

        # Determine visibility
        if is_reminder_admin(data, guild_id, user):
            reminders = get_all_reminders(data, guild_id)
        elif is_user_manager(data, guild_id, user):
            reminders = get_all_reminders(data, guild_id)
        else:
            reminders = get_user_reminders(data, user.id, guild_id)

        if not reminders:
            await interaction.response.send_message("No reminders found.")
            return

        # Pagination embed
        embeds = []
        for i in range(0, len(reminders), 10):
            chunk = reminders[i:i + 10]
            description = ""
            for r in chunk:
                creator = f"<@{r['user_id']}>"
                delivery = r.get("delivery", "dm")
                channel = f"<#{r['channel_id']}>" if "channel_id" in r else "N/A"
                due_time = r["time"]
                description += f"**{creator}** | {due_time} | Delivery: {delivery} | Channel: {channel}\nMessage: {r['message']}\n\n"
            embed = discord.Embed(
                title=f"Reminders {i + 1}-{i + len(chunk)}",
                description=description,
                color=discord.Color.blue()
            )
            embeds.append(embed)

        # Send first page
        msg = await interaction.response.send_message(embed=embeds[0])
        # Add pagination if multiple embeds
        if len(embeds) > 1:
            msg = await interaction.original_response()
            await msg.add_reaction("◀️")
            await msg.add_reaction("▶️")

            current = 0

            def check(reaction, user_react):
                return user_react == interaction.user and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == msg.id

            while True:
                try:
                    reaction, user_react = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    if str(reaction.emoji) == "▶️" and current < len(embeds) - 1:
                        current += 1
                        await msg.edit(embed=embeds[current])
                    elif str(reaction.emoji) == "◀️" and current > 0:
                        current -= 1
                        await msg.edit(embed=embeds[current])
                    await msg.remove_reaction(reaction, user_react)
                except asyncio.TimeoutError:
                    break

    # --- Reminder Edit ---
    @app_commands.command(
        name="reminderedit",
        description="Edit an existing reminder"
    )
    @app_commands.describe(
        index="Index of the reminder to edit (from /reminderlist page)",
        message="New message (optional)",
        minutes="New minutes until reminder (optional)",
        delivery="New delivery mode (optional)"
    )
    @app_commands.choices(
        delivery=[
            app_commands.Choice(name="DM only", value="dm"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="DM + Channel", value="both"),
        ]
    )
    async def reminderedit(
        self,
        interaction: discord.Interaction,
        index: int,
        message: Optional[str] = None,
        minutes: Optional[int] = None,
        delivery: Optional[app_commands.Choice[str]] = None
    ):
        guild_id = interaction.guild_id
        user = interaction.user

        # Get reminders visible to user
        if is_reminder_admin(data, guild_id, user) or is_user_manager(data, guild_id, user):
            reminders = get_all_reminders(data, guild_id)
        else:
            reminders = get_user_reminders(data, user.id, guild_id)

        if index < 1 or index > len(reminders):
            await interaction.response.send_message("❌ Invalid reminder index.")
            return

        r = reminders[index - 1]
        if message:
            r["message"] = message
        if minutes is not None:
            new_time = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
            r["time"] = new_time.strftime("%Y-%m-%d %H:%M:%S")
        if delivery:
            r["delivery"] = delivery.value

        from storage import save_data
        save_data(data)
        await interaction.response.send_message(f"✅ Reminder updated successfully.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
