import discord
from discord import app_commands
from discord.ext import commands

from storage import add_admin, remove_admin, list_admins, load_data

data = load_data()


def require_admin(interaction: discord.Interaction) -> bool:
    """Check if the user has Administrator permission in the guild."""
    return interaction.user.guild_permissions.administrator


class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(
        name="reminderadmin",
        description="Manage reminder admins (requires Administrator permission)"
    )

    @group.command(name="adduser", description="Add a user as reminder admin")
    @app_commands.check(require_admin)
    async def adduser(self, interaction: discord.Interaction, user: discord.User):
        add_admin(data, interaction.guild_id, user.id, "user")
        await interaction.response.send_message(f"✅ Added {user.mention} as reminder admin.")

    @group.command(name="addrole", description="Add a role as reminder admin")
    @app_commands.check(require_admin)
    async def addrole(self, interaction: discord.Interaction, role: discord.Role):
        add_admin(data, interaction.guild_id, role.id, "role")
        await interaction.response.send_message(f"✅ Added role {role.mention} as reminder admin.")

    @group.command(name="removeuser", description="Remove a user from reminder admins")
    @app_commands.check(require_admin)
    async def removeuser(self, interaction: discord.Interaction, user: discord.User):
        remove_admin(data, interaction.guild_id, user.id, "user")
        await interaction.response.send_message(f"❌ Removed {user.mention} from reminder admins.")

    @group.command(name="removerole", description="Remove a role from reminder admins")
    @app_commands.check(require_admin)
    async def removerole(self, interaction: discord.Interaction, role: discord.Role):
        remove_admin(data, interaction.guild_id, role.id, "role")
        await interaction.response.send_message(f"❌ Removed role {role.mention} from reminder admins.")

    @group.command(name="list", description="List reminder admins for this server")
    @app_commands.check(require_admin)
    async def list(self, interaction: discord.Interaction):
        guild_admins = list_admins(data, interaction.guild_id)
        users = ", ".join(f"<@{uid}>" for uid in guild_admins["users"]) or "None"
        roles = ", ".join(f"<@&{rid}>" for rid in guild_admins["roles"]) or "None"
        await interaction.response.send_message(
            f"👑 Reminder admins in this server:\n**Users:** {users}\n**Roles:** {roles}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
