import discord
from discord import app_commands
from discord.ext import commands
from typing import Union
from storage import (
    load_data,
    save_data,
    is_reminder_admin,
    is_user_manager,
    set_guild_default_delivery
)

data = load_data()

class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Helpers ---
    def check_admin_permission(self, user: discord.User, guild_id: int):
        return is_reminder_admin(data, guild_id, user)

    def check_user_manager_permission(self, user: discord.User, guild_id: int):
        return is_reminder_admin(data, guild_id, user) or is_user_manager(data, guild_id, user)

    # --- Admin Commands ---
    @app_commands.command(name="addadmin", description="Add a user or role as Admin Manager")
    async def addadmin(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        if not self.check_admin_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        if isinstance(target, discord.User):
            admins = guild.setdefault("admins", [])
            if str(target.id) not in admins:
                admins.append(str(target.id))
        else:
            admin_roles = guild.setdefault("admin_roles", [])
            if str(target.id) not in admin_roles:
                admin_roles.append(str(target.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {target} added as Admin.")

    @app_commands.command(name="removeadmin", description="Remove a user or role from Admin Managers")
    async def removeadmin(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        if not self.check_admin_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        if isinstance(target, discord.User):
            admins = guild.setdefault("admins", [])
            if str(target.id) in admins:
                admins.remove(str(target.id))
        else:
            admin_roles = guild.setdefault("admin_roles", [])
            if str(target.id) in admin_roles:
                admin_roles.remove(str(target.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {target} removed from Admins.")

    @app_commands.command(name="listadmins", description="List all Admins and Admin roles")
    async def listadmins(self, interaction: discord.Interaction):
        guild = data["guilds"].get(str(interaction.guild_id), {})
        users = guild.get("admins", [])
        roles = guild.get("admin_roles", [])
        user_mentions = [interaction.guild.get_member(int(u)).mention for u in users if interaction.guild.get_member(int(u))]
        role_mentions = [interaction.guild.get_role(int(r)).mention for r in roles if interaction.guild.get_role(int(r))]
        text = f"Admins: {', '.join(user_mentions) if user_mentions else 'None'}\nRoles: {', '.join(role_mentions) if role_mentions else 'None'}"
        await interaction.response.send_message(text)

    # --- User Manager Commands ---
    @app_commands.command(name="addusermanager", description="Add a user or role as User Manager")
    async def addusermanager(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        if not self.check_admin_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        if isinstance(target, discord.User):
            managers = guild.setdefault("user_managers", [])
            if str(target.id) not in managers:
                managers.append(str(target.id))
        else:
            manager_roles = guild.setdefault("user_manager_roles", [])
            if str(target.id) not in manager_roles:
                manager_roles.append(str(target.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {target} added as User Manager.")

    @app_commands.command(name="removeusermanager", description="Remove a user or role from User Managers")
    async def removeusermanager(self, interaction: discord.Interaction, target: Union[discord.User, discord.Role]):
        if not self.check_admin_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        if isinstance(target, discord.User):
            managers = guild.setdefault("user_managers", [])
            if str(target.id) in managers:
                managers.remove(str(target.id))
        else:
            manager_roles = guild.setdefault("user_manager_roles", [])
            if str(target.id) in manager_roles:
                manager_roles.remove(str(target.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {target} removed from User Managers.")

    @app_commands.command(name="listusermanagers", description="List all User Managers and roles")
    async def listusermanagers(self, interaction: discord.Interaction):
        guild = data["guilds"].get(str(interaction.guild_id), {})
        users = guild.get("user_managers", [])
        roles = guild.get("user_manager_roles", [])
        user_mentions = [interaction.guild.get_member(int(u)).mention for u in users if interaction.guild.get_member(int(u))]
        role_mentions = [interaction.guild.get_role(int(r)).mention for r in roles if interaction.guild.get_role(int(r))]
        text = f"User Managers: {', '.join(user_mentions) if user_mentions else 'None'}\nRoles: {', '.join(role_mentions) if role_mentions else 'None'}"
        await interaction.response.send_message(text)

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
        if not self.check_user_manager_permission(interaction.user, interaction.guild_id):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        set_guild_default_delivery(data, interaction.guild_id, delivery.value)
        await interaction.response.send_message(f"✅ Default delivery set to **{delivery.name}**.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
