import discord
from discord import app_commands
from discord.ext import commands
import logging

from storage import (
    add_admin, remove_admin, list_admins, load_data,
    data, add_admin, remove_admin
)

logger = logging.getLogger("bot")
data = load_data()


def require_admin_manager(interaction: discord.Interaction) -> bool:
    from storage import is_reminder_admin
    return is_reminder_admin(data, interaction.guild_id, interaction.user)


class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(
        name="reminderadmin",
        description="Admin Manager commands (full privileges)"
    )

    @group.command(name="adduser", description="Add a user as admin manager")
    @app_commands.check(require_admin_manager)
    async def adduser(self, interaction: discord.Interaction, user: discord.User):
        add_admin(data, interaction.guild_id, user.id, "user")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} added USER {user} as Admin Manager"
        )
        await interaction.response.send_message(f"✅ Added {user.mention} as Admin Manager")

    @group.command(name="addrole", description="Add a role as admin manager")
    @app_commands.check(require_admin_manager)
    async def addrole(self, interaction: discord.Interaction, role: discord.Role):
        add_admin(data, interaction.guild_id, role.id, "role")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} added ROLE {role} as Admin Manager"
        )
        await interaction.response.send_message(f"✅ Added role {role.mention} as Admin Manager")

    @group.command(name="removeuser", description="Remove a user from admin manager")
    @app_commands.check(require_admin_manager)
    async def removeuser(self, interaction: discord.Interaction, user: discord.User):
        remove_admin(data, interaction.guild_id, user.id, "user")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} removed USER {user} from Admin Manager"
        )
        await interaction.response.send_message(f"❌ Removed {user.mention} from Admin Manager")

    @group.command(name="removerole", description="Remove a role from admin manager")
    @app_commands.check(require_admin_manager)
    async def removerole(self, interaction: discord.Interaction, role: discord.Role):
        remove_admin(data, interaction.guild_id, role.id, "role")
        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} removed ROLE {role} from Admin Manager"
        )
        await interaction.response.send_message(f"❌ Removed role {role.mention} from Admin Manager")

    @group.command(name="list", description="List admin managers for this server")
    @app_commands.check(require_admin_manager)
    async def list(self, interaction: discord.Interaction):
        admins = list_admins(data, interaction.guild_id)
        users = ", ".join(f"<@{uid}>" for uid in admins["users"]) or "None"
        roles = ", ".join(f"<@&{rid}>" for rid in admins["roles"]) or "None"

        logger.info(
            f"[GUILD {interaction.guild.name} ({interaction.guild_id})] "
            f"{interaction.user} requested Admin Manager list"
        )

        await interaction.response.send_message(
            f"👑 Admin Managers:\n**Users:** {users}\n**Roles:** {roles}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
