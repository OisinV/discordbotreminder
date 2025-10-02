import discord
from discord import app_commands
from discord.ext import commands
import logging

from storage import (
    add_user_manager, remove_user_manager, list_user_managers, load_data,
    data, is_reminder_admin
)

logger = logging.getLogger("bot")
data = load_data()


def require_admin_manager(interaction: discord.Interaction) -> bool:
    return is_reminder_admin(data, interaction.guild_id, interaction.user)


class UserManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(
        name="usermanager",
        description="User Manager commands (limited privileges)"
    )

    @group.command(name="adduser", description="Add a user as User Manager")
    @app_commands.check(require_admin_manager)
    async def adduser(self, interaction: discord.Interaction, user: discord.User):
        add_user_manager(data, interaction.guild_id, user.id, "user")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} added USER {user} as User Manager"
        )
        await interaction.response.send_message(f"✅ Added {user.mention} as User Manager")

    @group.command(name="addrole", description="Add a role as User Manager")
    @app_commands.check(require_admin_manager)
    async def addrole(self, interaction: discord.Interaction, role: discord.Role):
        add_user_manager(data, interaction.guild_id, role.id, "role")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} added ROLE {role} as User Manager"
        )
        await interaction.response.send_message(f"✅ Added role {role.mention} as User Manager")

    @group.command(name="removeuser", description="Remove a user from User Manager")
    @app_commands.check(require_admin_manager)
    async def removeuser(self, interaction: discord.Interaction, user: discord.User):
        remove_user_manager(data, interaction.guild_id, user.id, "user")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} removed USER {user} from User Manager"
        )
        await interaction.response.send_message(f"❌ Removed {user.mention} from User Manager")

    @group.command(name="removerole", description="Remove a role from User Manager")
    @app_commands.check(require_admin_manager)
    async def removerole(self, interaction: discord.Interaction, role: discord.Role):
        remove_user_manager(data, interaction.guild_id, role.id, "role")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} removed ROLE {role} from User Manager"
        )
        await interaction.response.send_message(f"❌ Removed role {role.mention} from User Manager")

    @group.command(name="list", description="List User Managers for this server")
    @app_commands.check(require_admin_manager)
    async def list(self, interaction: discord.Interaction):
        managers = list_user_managers(data, interaction.guild_id)
        users = ", ".join(f"<@{uid}>" for uid in managers["users"]) or "None"
        roles = ", ".join(f"<@&{rid}>" for rid in managers["roles"]) or "None"

        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} requested User Manager list"
        )

        await interaction.response.send_message(
            f"👑 User Managers:\n**Users:** {users}\n**Roles:** {roles}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(UserManager(bot))
