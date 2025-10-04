import discord
from discord import app_commands
from discord.ext import commands
from typing import Union
from datetime import datetime, timedelta
import logging

from storage import (
    load_data,
    save_data,
    is_reminder_admin,
    is_user_manager,
    set_guild_default_delivery,
    add_reminder,
    get_user_reminders,
    remove_reminder,
    get_guild_default_delivery,
    TIMEZONE
)

data = load_data()
logger = logging.getLogger("bot")  # Central logger, set up in main bot file

class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Helpers ---
    def check_admin_permission(self, member: discord.Member, guild_id: int):
        if member.id == member.guild.owner_id:
            return True
        if is_reminder_admin(data, guild_id, member) or is_user_manager(data, guild_id, member):
            return True
        return any(role.permissions.administrator or role.permissions.manage_guild for role in member.roles)

    def check_user_manager_permission(self, member: discord.Member, guild_id: int):
        return self.check_admin_permission(member, guild_id)

    def resolve_target(self, interaction: discord.Interaction, target: str):
        """Resolve target string to member or role mention."""
        if not target or target.lower() == "self":
            return interaction.user.mention
        if target.lower() in ["everyone", "here"]:
            if not interaction.user.guild_permissions.mention_everyone:
                return None
            return f"@{target.lower()}"

        # Check if mention ID
        if target.startswith("<@") and target.endswith(">"):
            try:
                target_id = int(target.replace("<@", "").replace(">", "").replace("!", ""))
                member = interaction.guild.get_member(target_id)
                if member:
                    return member.mention
            except Exception:
                return None

        # Check numeric ID
        if target.isdigit():
            member = interaction.guild.get_member(int(target))
            if member:
                return member.mention

        # Username#discriminator
        member = interaction.guild.get_member_named(target)
        if member:
            return member.mention

        # Role by name
        role = discord.utils.get(interaction.guild.roles, name=target)
        if role:
            return role.mention

        return None

    def get_delivery_channel(self, interaction: discord.Interaction, delivery_mode: str):
        """Determine which channel or thread the reminder should go to."""
        if delivery_mode in ("channel", "forum", "both"):
            if isinstance(interaction.channel, discord.Thread):
                return interaction.channel.id
            return interaction.channel_id
        return None

    # --- Guild Join DM ---
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        message_template = (
            "Hello {user_name},\n\n"
            "Thanks for adding me to **{guild_name}**!\n\n"
            "To set up the bot, please:\n"
            "1. Set default reminder delivery with `/setdefaultdelivery`.\n"
            "2. Add Admins with `/addadmin` and User Managers with `/addusermanager`.\n"
            "3. Use `/reminderfor` to set reminders for others.\n\n"
            "For help, go to the support discord server.\n"
            "Support server: https://discord.gg/5W7tU6A49P"
        )

        try:
            if guild.owner:
                await guild.owner.send(message_template.format(user_name=guild.owner.name, guild_name=guild.name))
        except Exception:
            logger.warning(f"Could not DM guild owner {guild.owner} of {guild.name}")

        for member in guild.members:
            if member.guild_permissions.administrator and member != guild.owner:
                try:
                    await member.send(message_template.format(user_name=member.name, guild_name=guild.name))
                except Exception:
                    logger.warning(f"Could not DM admin {member} of {guild.name}")

    # --- Admin Commands ---
    @app_commands.command(name="addadmin", description="Add a user or role as Admin Manager")
    async def addadmin(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        try:
            if not self.check_admin_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized addadmin attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            guild = data["guilds"].setdefault(str(interaction.guild_id), {})
            if isinstance(target, discord.User):
                guild.setdefault("admins", [])
                if str(target.id) not in guild["admins"]:
                    guild["admins"].append(str(target.id))
            else:
                guild.setdefault("admin_roles", [])
                if str(target.id) not in guild["admin_roles"]:
                    guild["admin_roles"].append(str(target.id))
            save_data(data)
            await interaction.response.send_message(f"✅ {target} added as Admin.")
            logger.info(f"AM {interaction.user} added admin {target} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in addadmin command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while adding admin.")

    @app_commands.command(name="removeadmin", description="Remove a user or role from Admin Managers")
    async def removeadmin(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        try:
            if not self.check_admin_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized removeadmin attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            guild = data["guilds"].setdefault(str(interaction.guild_id), {})
            if isinstance(target, discord.User):
                if str(target.id) in guild.get("admins", []):
                    guild["admins"].remove(str(target.id))
            else:
                if str(target.id) in guild.get("admin_roles", []):
                    guild["admin_roles"].remove(str(target.id))
            save_data(data)
            await interaction.response.send_message(f"✅ {target} removed from Admins.")
            logger.info(f"AM {interaction.user} removed admin {target} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in removeadmin command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while removing admin.")

    @app_commands.command(name="listadmins", description="List all Admins and Admin roles")
    async def listadmins(self, interaction: discord.Interaction):
        try:
            guild = data["guilds"].get(str(interaction.guild_id), {})
            users = guild.get("admins", [])
            roles = guild.get("admin_roles", [])

            user_mentions = [interaction.guild.get_member(int(u)).mention if interaction.guild.get_member(int(u)) else f"<@{u}>" for u in users]
            role_mentions = [interaction.guild.get_role(int(r)).mention if interaction.guild.get_role(int(r)) else f"<@&{r}>" for r in roles]

            text = f"Admins: {', '.join(user_mentions) if user_mentions else 'None'}\nRoles: {', '.join(role_mentions) if role_mentions else 'None'}"
            await interaction.response.send_message(text)
            logger.info(f"AM {interaction.user} listed admins in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in listadmins command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while listing admins.")

    # --- User Manager Commands ---
    @app_commands.command(name="addusermanager", description="Add a user or role as User Manager")
    async def addusermanager(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        try:
            if not self.check_admin_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized addusermanager attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            guild = data["guilds"].setdefault(str(interaction.guild_id), {})
            if isinstance(target, discord.User):
                guild.setdefault("user_managers", [])
                if str(target.id) not in guild["user_managers"]:
                    guild["user_managers"].append(str(target.id))
            else:
                guild.setdefault("user_manager_roles", [])
                if str(target.id) not in guild["user_manager_roles"]:
                    guild["user_manager_roles"].append(str(target.id))
            save_data(data)
            await interaction.response.send_message(f"✅ {target} added as User Manager.")
            logger.info(f"AM {interaction.user} added user manager {target} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in addusermanager command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while adding user manager.")

    @app_commands.command(name="removeusermanager", description="Remove a user or role from User Managers")
    async def removeusermanager(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        try:
            if not self.check_admin_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized removeusermanager attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            guild = data["guilds"].setdefault(str(interaction.guild_id), {})
            if isinstance(target, discord.User):
                if str(target.id) in guild.get("user_managers", []):
                    guild["user_managers"].remove(str(target.id))
            else:
                if str(target.id) in guild.get("user_manager_roles", []):
                    guild["user_manager_roles"].remove(str(target.id))
            save_data(data)
            await interaction.response.send_message(f"✅ {target} removed from User Managers.")
            logger.info(f"AM {interaction.user} removed user manager {target} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in removeusermanager command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while removing user manager.")

    @app_commands.command(name="listusermanagers", description="List all User Managers and roles")
    async def listusermanagers(self, interaction: discord.Interaction):
        try:
            guild = data["guilds"].get(str(interaction.guild_id), {})
            users = guild.get("user_managers", [])
            roles = guild.get("user_manager_roles", [])

            user_mentions = [interaction.guild.get_member(int(u)).mention if interaction.guild.get_member(int(u)) else f"<@{u}>" for u in users]
            role_mentions = [interaction.guild.get_role(int(r)).mention if interaction.guild.get_role(int(r)) else f"<@&{r}>" for r in roles]

            text = f"User Managers: {', '.join(user_mentions) if user_mentions else 'None'}\nRoles: {', '.join(role_mentions) if role_mentions else 'None'}"
            await interaction.response.send_message(text)
            logger.info(f"AM {interaction.user} listed user managers in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in listusermanagers command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while listing user managers.")

    # --- Guild Default Delivery ---
    @app_commands.command(name="setdefaultdelivery", description="Set default reminder delivery for the guild")
    @app_commands.choices(
        delivery=[
            app_commands.Choice(name="DM only", value="dm"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="DM + Channel", value="both"),
        ]
    )
    async def setdefaultdelivery(self, interaction: discord.Interaction, delivery: app_commands.Choice[str]):
        try:
            if not self.check_user_manager_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized setdefaultdelivery attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            set_guild_default_delivery(data, interaction.guild_id, delivery.value)
            save_data(data)
            await interaction.response.send_message(f"✅ Default delivery set to **{delivery.name}**.")
            logger.info(f"UM {interaction.user} set default delivery to {delivery.value} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in setdefaultdelivery command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while setting default delivery.")

    # --- Reminder Control for Others ---
    @app_commands.command(name="reminderfor", description="Set a reminder for another user or role")
    @app_commands.describe(minutes="Minutes until the reminder", message="Reminder text", delivery="Delivery: dm / channel / forum / both", target="User, role, or 'everyone'")
    @app_commands.choices(
        delivery=[
            app_commands.Choice(name="DM only", value="dm"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="DM + Channel", value="both"),
        ]
    )
    async def reminderfor(self, interaction: discord.Interaction, minutes: int, message: str, delivery: app_commands.Choice[str] = None, target: str = None):
        try:
            guild_id = interaction.guild_id
            if not self.check_user_manager_permission(interaction.user, guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized reminderfor attempt by {interaction.user} in guild {guild_id}")
                return

            delivery_mode = delivery.value if delivery else get_guild_default_delivery(data, guild_id)
            if not delivery_mode:
                await interaction.response.send_message("❌ Specify a delivery mode or set guild default.")
                return

            mention_text = self.resolve_target(interaction, target)
            if not mention_text:
                await interaction.response.send_message(f"❌ Target `{target}` not found or you lack permissions.")
                return

            when = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
            channel_id = self.get_delivery_channel(interaction, delivery_mode)

            reminder_obj = add_reminder(data, interaction.user.id, guild_id, message, when)
            reminder_obj["delivery"] = delivery_mode
            reminder_obj["target_mention"] = mention_text
            if channel_id:
                reminder_obj["channel_id"] = channel_id

            save_data(data)
            await interaction.response.send_message(
                f"⏰ Reminder set for {mention_text} at {when.strftime('%Y-%m-%d %H:%M:%S %Z')} (Delivery: {delivery_mode})"
            )
            logger.info(f"UM {interaction.user} set reminder for {mention_text} in guild {guild_id} message='{message}' at {when}")
        except Exception as e:
            logger.exception(f"Error in reminderfor command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while setting reminder.")

    @app_commands.command(name="listremindersfor", description="List reminders set for a user or role")
    @app_commands.describe(target="User or role to list reminders for")
    async def listremindersfor(self, interaction: discord.Interaction, target: str):
        try:
            guild_id = interaction.guild_id
            if not self.check_user_manager_permission(interaction.user, guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized listremindersfor attempt by {interaction.user} in guild {guild_id}")
                return

            mention_text = self.resolve_target(interaction, target)
            if not mention_text:
                await interaction.response.send_message(f"❌ Target `{target}` not found or you lack permissions.")
                return

            all_reminders = get_user_reminders(data, guild_id)
            filtered = [r for r in all_reminders if r.get("target_mention") == mention_text]
            if not filtered:
                await interaction.response.send_message("No reminders found for this target.")
                return

            text = "\n".join([f"- {r['message']} (at {r['time']})" for r in filtered])
            await interaction.response.send_message(f"Reminders for {target}:\n{text}")
            logger.info(f"UM {interaction.user} listed reminders for {mention_text} in guild {guild_id}")
        except Exception as e:
            logger.exception(f"Error in listremindersfor command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while listing reminders.")

    @app_commands.command(name="cancelremindersfor", description="Cancel reminders set for a user or role")
    @app_commands.describe(target="User or role to cancel reminders for")
    async def cancelremindersfor(self, interaction: discord.Interaction, target: str):
        try:
            guild_id = interaction.guild_id
            if not self.check_user_manager_permission(interaction.user, guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized cancelremindersfor attempt by {interaction.user} in guild {guild_id}")
                return

            mention_text = self.resolve_target(interaction, target)
            if not mention_text:
                await interaction.response.send_message(f"❌ Target `{target}` not found or you lack permissions.")
                return

            all_reminders = get_user_reminders(data, guild_id)
            canceled_count = 0
            for r in all_reminders:
                if r.get("target_mention") == mention_text:
                    remove_reminder(data, r)
                    canceled_count += 1

            save_data(data)
            await interaction.response.send_message(f"✅ Canceled {canceled_count} reminders for {target}.")
            logger.info(f"UM {interaction.user} canceled {canceled_count} reminders for {mention_text} in guild {guild_id}")
        except Exception as e:
            logger.exception(f"Error in cancelremindersfor command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while canceling reminders.")

    # --- Update Channel Commands ---
    @app_commands.command(name="setupdatechannel", description="Add a channel as an update channel")
    @app_commands.describe(channel="Channel to add as update channel")
    async def setupdatechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            if not self.check_admin_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized setupdatechannel attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            guild = data["guilds"].setdefault(str(interaction.guild_id), {})
            guild.setdefault("update_channels", [])
            if str(channel.id) not in guild["update_channels"]:
                guild["update_channels"].append(str(channel.id))
            save_data(data)
            await interaction.response.send_message(f"✅ Channel {channel.mention} added as update channel.")
            logger.info(f"AM {interaction.user} set update channel {channel} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in setupdatechannel command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while adding update channel.")

    @app_commands.command(name="removeupdatechannel", description="Remove a channel from update channels")
    @app_commands.describe(channel="Channel to remove from update channels")
    async def removeupdatechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            if not self.check_admin_permission(interaction.user, interaction.guild_id):
                await interaction.response.send_message("❌ You do not have permission.")
                logger.warning(f"Unauthorized removeupdatechannel attempt by {interaction.user} in guild {interaction.guild_id}")
                return

            guild = data["guilds"].setdefault(str(interaction.guild_id), {})
            if str(channel.id) in guild.get("update_channels", []):
                guild["update_channels"].remove(str(channel.id))
            save_data(data)
            await interaction.response.send_message(f"✅ Channel {channel.mention} removed from update channels.")
            logger.info(f"AM {interaction.user} removed update channel {channel} in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in removeupdatechannel command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while removing update channel.")

    @app_commands.command(name="listupdatechannels", description="List all update channels in the guild")
    async def listupdatechannels(self, interaction: discord.Interaction):
        try:
            guild = data["guilds"].get(str(interaction.guild_id), {})
            channels = guild.get("update_channels", [])

            if not channels:
                await interaction.response.send_message("No update channels set for this guild.")
                return

            channel_mentions = [interaction.guild.get_channel(int(c)).mention if interaction.guild.get_channel(int(c)) else f"<#{c}>" for c in channels]
            await interaction.response.send_message(f"Update Channels: {', '.join(channel_mentions)}")
            logger.info(f"AM {interaction.user} listed update channels in guild {interaction.guild_id}")
        except Exception as e:
            logger.exception(f"Error in listupdatechannels command by {interaction.user}: {e}")
            await interaction.response.send_message("❌ An error occurred while listing update channels.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
