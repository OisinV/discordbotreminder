import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import logging
from typing import Optional, Union

from storage import (
    add_reminder,
    load_data,
    get_user_reminders,
    remove_reminder,
    get_all_reminders,
    set_guild_default_delivery,
    is_reminder_admin,
    is_user_manager,
    TIMEZONE
)

data = load_data()
logger = logging.getLogger("bot")

class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Permission checks ---
    def check_admin_permission(self, user: discord.User, guild_id: int):
        return is_reminder_admin(data, guild_id, user)

    def check_user_manager_permission(self, user: discord.User, guild_id: int):
        return is_reminder_admin(data, guild_id, user) or is_user_manager(data, guild_id, user)

    # --- Guild Default Delivery ---
    @app_commands.command(
        name="setdefaultdelivery",
        description="Set default reminder delivery for the guild (toggleable for User Managers)"
    )
    @app_commands.choices(
        delivery=[
            app_commands.Choice(name="DM only", value="dm"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="DM + Channel", value="both"),
        ]
    )
    async def setdefaultdelivery(self, interaction: discord.Interaction, delivery: app_commands.Choice[str]):
        if not self.check_user_manager_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        set_guild_default_delivery(data, interaction.guild_id, delivery.value)
        await interaction.response.send_message(f"✅ Default delivery set to **{delivery.name}** for this guild.")

    # --- List Admins/User Managers ---
    @app_commands.command(name="listadmins", description="List all Admins and Admin roles")
    async def listadmins(self, interaction: discord.Interaction):
        guild_data = data.get("guilds", {}).get(str(interaction.guild_id), {})
        users = guild_data.get("admins", [])
        roles = guild_data.get("admin_roles", [])

        user_mentions = [interaction.guild.get_member(int(u)).mention for u in users if interaction.guild.get_member(int(u))]
        role_mentions = [interaction.guild.get_role(int(r)).mention for r in roles if interaction.guild.get_role(int(r))]

        await interaction.response.send_message(
            f"Admins: {', '.join(user_mentions) if user_mentions else 'None'}\n"
            f"Roles: {', '.join(role_mentions) if role_mentions else 'None'}"
        )

    @app_commands.command(name="listusermanagers", description="List all User Managers and roles")
    async def listusermanagers(self, interaction: discord.Interaction):
        guild_data = data.get("guilds", {}).get(str(interaction.guild_id), {})
        users = guild_data.get("user_managers", [])
        roles = guild_data.get("user_manager_roles", [])

        user_mentions = [interaction.guild.get_member(int(u)).mention for u in users if interaction.guild.get_member(int(u))]
        role_mentions = [interaction.guild.get_role(int(r)).mention for r in roles if interaction.guild.get_role(int(r))]

        await interaction.response.send_message(
            f"User Managers: {', '.join(user_mentions) if user_mentions else 'None'}\n"
            f"Roles: {', '.join(role_mentions) if role_mentions else 'None'}"
        )

    # --- Manage reminders for other users ---
    @app_commands.command(
        name="addreminder",
        description="Create a reminder for any user, role, or everyone"
    )
    @app_commands.describe(
        minutes="Minutes until the reminder",
        message="Reminder text",
        delivery="Delivery mode: dm / channel / forum / both",
        target="User mention, role mention, or 'everyone'"
    )
    @app_commands.choices(
        delivery=[
            app_commands.Choice(name="DM only", value="dm"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="DM + Channel", value="both"),
        ]
    )
    async def addreminder(self, interaction: discord.Interaction, minutes: int, message: str, delivery: app_commands.Choice[str], target: str):
        if not self.check_user_manager_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return

        guild_id = interaction.guild_id
        mention_text = target

        # Try resolving to user
        member = interaction.guild.get_member_named(target)
        if member:
            mention_text = member.mention
        else:
            # Try role
            role = discord.utils.get(interaction.guild.roles, name=target)
            if role:
                mention_text = role.mention
            elif target.lower() in ["everyone", "here"]:
                mention_text = f"@{target.lower()}"

        when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        channel_id = interaction.channel_id if delivery.value in ("channel", "forum", "both") else None

        reminder_obj = add_reminder(data, interaction.user.id, guild_id, message, when)
        reminder_obj["delivery"] = delivery.value
        reminder_obj["target_mention"] = mention_text
        if channel_id:
            reminder_obj["channel_id"] = channel_id

        logger.info(
            f"[GUILD {interaction.guild.name} ({guild_id})] "
            f"{interaction.user} set reminder '{message}' for '{mention_text}' "
            f"(⏰ {when.strftime('%Y-%m-%d %H:%M:%S %Z')}, delivery={delivery.value}, channel_id={channel_id})"
        )

        await interaction.response.send_message(
            f"✅ Reminder created for {mention_text} at {when.strftime('%Y-%m-%d %H:%M:%S %Z')} "
            f"(Delivery: {delivery.value})"
        )

    @app_commands.command(name="listreminders", description="List all reminders in the guild (Admin/User Manager)")
    async def listreminders(self, interaction: discord.Interaction):
        if not self.check_user_manager_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild_id = interaction.guild_id
        reminders = get_all_reminders(data, guild_id)
        if not reminders:
            await interaction.response.send_message("📭 No active reminders in this guild.")
            return

        lines = []
        for idx, r in enumerate(reminders, 1):
            lines.append(f"{idx}. {r['message']} (User ID: {r['user_id']}, Target: {r.get('target_mention', 'N/A')}, Delivery: {r.get('delivery', 'dm')}, ⏰ {r['time']})")

        await interaction.response.send_message("📋 Guild reminders:\n" + "\n".join(lines[:20]))

    @app_commands.command(name="cancelreminder", description="Cancel a reminder by index")
    async def cancelreminder(self, interaction: discord.Interaction, index: int):
        if not self.check_user_manager_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild_id = interaction.guild_id
        reminders = get_all_reminders(data, guild_id)
        if not reminders:
            await interaction.response.send_message("❌ No active reminders.")
            return
        if index < 1 or index > len(reminders):
            await interaction.response.send_message("❌ Invalid index.")
            return
        remove_reminder(data, reminders[index-1])
        await interaction.response.send_message(f"✅ Removed reminder: {reminders[index-1]['message']}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
