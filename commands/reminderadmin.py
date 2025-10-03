import discord
from discord import app_commands
from discord.ext import commands

from storage import (
    data,
    save_data,
    is_admin_manager,
    is_user_manager,
    add_admin_manager,
    remove_admin_manager,
    add_user_manager,
    remove_user_manager,
    get_default_delivery,
    set_default_delivery,
)


class ReminderAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return False
        return True

    # ------------------------------
    # Admin Manager Commands
    # ------------------------------
    @app_commands.command(name="addadmin", description="Add a user or role as an Admin Manager.")
    async def add_admin(self, interaction: discord.Interaction, member_or_role: discord.Object):
        if not is_admin_manager(interaction.guild_id, interaction.user.id):
            await interaction.response.send_message("❌ You must be an Admin Manager to do this.", ephemeral=True)
            return

        if isinstance(member_or_role, discord.Role):
            add_admin_manager(interaction.guild_id, role_id=member_or_role.id)
            await interaction.response.send_message(f"✅ Role {member_or_role.mention} added as Admin Manager.")
        else:
            add_admin_manager(interaction.guild_id, user_id=member_or_role.id)
            await interaction.response.send_message(f"✅ User <@{member_or_role.id}> added as Admin Manager.")

        save_data(data)

    @app_commands.command(name="removeadmin", description="Remove a user or role from Admin Managers.")
    async def remove_admin(self, interaction: discord.Interaction, member_or_role: discord.Object):
        if not is_admin_manager(interaction.guild_id, interaction.user.id):
            await interaction.response.send_message("❌ You must be an Admin Manager to do this.", ephemeral=True)
            return

        if isinstance(member_or_role, discord.Role):
            remove_admin_manager(interaction.guild_id, role_id=member_or_role.id)
            await interaction.response.send_message(f"✅ Role {member_or_role.mention} removed from Admin Managers.")
        else:
            remove_admin_manager(interaction.guild_id, user_id=member_or_role.id)
            await interaction.response.send_message(f"✅ User <@{member_or_role.id}> removed from Admin Managers.")

        save_data(data)

    @app_commands.command(name="listadmins", description="List all Admin Managers in this server.")
    async def list_admins(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_data = data.get("guilds", {}).get(guild_id, {})
        user_ids = guild_data.get("admin_users", [])
        role_ids = guild_data.get("admin_roles", [])

        mentions = []
        for uid in user_ids:
            member = interaction.guild.get_member(int(uid))
            if member:
                mentions.append(member.mention)
        for rid in role_ids:
            role = interaction.guild.get_role(int(rid))
            if role:
                mentions.append(role.mention)

        text = "👑 **Admin Managers:** " + (", ".join(mentions) if mentions else "None")
        await interaction.response.send_message(text)

    # ------------------------------
    # User Manager Commands
    # ------------------------------
    @app_commands.command(name="addusermanager", description="Add a user or role as a User Manager.")
    async def add_um(self, interaction: discord.Interaction, member_or_role: discord.Object):
        if not is_admin_manager(interaction.guild_id, interaction.user.id):
            await interaction.response.send_message("❌ Only Admin Managers can add User Managers.", ephemeral=True)
            return

        if isinstance(member_or_role, discord.Role):
            add_user_manager(interaction.guild_id, role_id=member_or_role.id)
            await interaction.response.send_message(f"✅ Role {member_or_role.mention} added as User Manager.")
        else:
            add_user_manager(interaction.guild_id, user_id=member_or_role.id)
            await interaction.response.send_message(f"✅ User <@{member_or_role.id}> added as User Manager.")

        save_data(data)

    @app_commands.command(name="removeusermanager", description="Remove a user or role from User Managers.")
    async def remove_um(self, interaction: discord.Interaction, member_or_role: discord.Object):
        if not is_admin_manager(interaction.guild_id, interaction.user.id):
            await interaction.response.send_message("❌ Only Admin Managers can remove User Managers.", ephemeral=True)
            return

        if isinstance(member_or_role, discord.Role):
            remove_user_manager(interaction.guild_id, role_id=member_or_role.id)
            await interaction.response.send_message(f"✅ Role {member_or_role.mention} removed from User Managers.")
        else:
            remove_user_manager(interaction.guild_id, user_id=member_or_role.id)
            await interaction.response.send_message(f"✅ User <@{member_or_role.id}> removed from User Managers.")

        save_data(data)

    @app_commands.command(name="listusermanagers", description="List all User Managers in this server.")
    async def list_um(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_data = data.get("guilds", {}).get(guild_id, {})
        user_ids = guild_data.get("um_users", [])
        role_ids = guild_data.get("um_roles", [])

        mentions = []
        for uid in user_ids:
            member = interaction.guild.get_member(int(uid))
            if member:
                mentions.append(member.mention)
        for rid in role_ids:
            role = interaction.guild.get_role(int(rid))
            if role:
                mentions.append(role.mention)

        text = "👥 **User Managers:** " + (", ".join(mentions) if mentions else "None")
        await interaction.response.send_message(text)

    # ------------------------------
    # Default Delivery System
    # ------------------------------
    @app_commands.command(name="setdefaultdelivery", description="Set the default reminder delivery mode for this server.")
    async def set_default_delivery_cmd(self, interaction: discord.Interaction, mode: str):
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        if not (is_admin_manager(guild_id, user_id) or is_user_manager(guild_id, user_id)):
            await interaction.response.send_message("❌ You must be a User Manager or Admin Manager to set this.", ephemeral=True)
            return

        valid_modes = ["dm", "channel", "forum", "both"]
        if mode not in valid_modes:
            await interaction.response.send_message(f"❌ Invalid mode. Choose one of: {', '.join(valid_modes)}", ephemeral=True)
            return

        set_default_delivery(guild_id, mode)
        save_data(data)
        await interaction.response.send_message(f"✅ Default delivery mode set to **{mode}** for this server.")

    @app_commands.command(name="getdefaultdelivery", description="Check the current default delivery mode.")
    async def get_default_delivery_cmd(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        mode = get_default_delivery(guild_id) or "dm"
        await interaction.response.send_message(f"ℹ️ Current default delivery mode: **{mode}**")


# ------------------------------
# Mention Verification
# ------------------------------
def can_ping(interaction: discord.Interaction, content: str) -> bool:
    """
    Check if the user is allowed to ping @everyone, @here, or roles.
    """
    if "@everyone" in content or "@here" in content:
        if not interaction.user.guild_permissions.mention_everyone:
            return False

    for role in interaction.guild.roles:
        if role.mention in content:
            if role not in interaction.user.roles and not interaction.user.guild_permissions.mention_everyone:
                return False
    return True


async def setup(bot):
    await bot.add_cog(ReminderAdmin(bot))
