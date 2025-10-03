import discord
from discord import app_commands
from discord.ext import commands
from storage import load_data, save_data, is_reminder_admin, is_user_manager, set_guild_default_delivery

data = load_data()

class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Existing Admin Commands ---

    @app_commands.command(name="addadmin", description="Add an admin to the guild")
    async def addadmin(self, interaction: discord.Interaction, user: discord.User):
        if not is_reminder_admin(data, interaction.guild_id, interaction.user):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        admins = guild.setdefault("admins", [])
        if str(user.id) in admins:
            await interaction.response.send_message("❌ User is already an admin.")
            return
        admins.append(str(user.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {user} added as Admin.")

    @app_commands.command(name="removeadmin", description="Remove an admin from the guild")
    async def removeadmin(self, interaction: discord.Interaction, user: discord.User):
        if not is_reminder_admin(data, interaction.guild_id, interaction.user):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        admins = guild.setdefault("admins", [])
        if str(user.id) not in admins:
            await interaction.response.send_message("❌ User is not an admin.")
            return
        admins.remove(str(user.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {user} removed from Admins.")

    @app_commands.command(name="listadmins", description="List all admins in the guild")
    async def listadmins(self, interaction: discord.Interaction):
        guild = data["guilds"].get(str(interaction.guild_id), {})
        admins = guild.get("admins", [])
        await interaction.response.send_message(f"Admins: {', '.join(admins) if admins else 'None'}")

    @app_commands.command(name="addusermanager", description="Add a user manager to the guild")
    async def addusermanager(self, interaction: discord.Interaction, user: discord.User):
        if not is_reminder_admin(data, interaction.guild_id, interaction.user):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        managers = guild.setdefault("user_managers", [])
        if str(user.id) in managers:
            await interaction.response.send_message("❌ User is already a User Manager.")
            return
        managers.append(str(user.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {user} added as User Manager.")

    @app_commands.command(name="removeusermanager", description="Remove a user manager from the guild")
    async def removeusermanager(self, interaction: discord.Interaction, user: discord.User):
        if not is_reminder_admin(data, interaction.guild_id, interaction.user):
            await interaction.response.send_message("❌ You do not have permission.")
            return
        guild = data["guilds"].setdefault(str(interaction.guild_id), {})
        managers = guild.setdefault("user_managers", [])
        if str(user.id) not in managers:
            await interaction.response.send_message("❌ User is not a User Manager.")
            return
        managers.remove(str(user.id))
        save_data(data)
        await interaction.response.send_message(f"✅ {user} removed from User Managers.")

    @app_commands.command(name="listusermanagers", description="List all user managers in the guild")
    async def listusermanagers(self, interaction: discord.Interaction):
        guild = data["guilds"].get(str(interaction.guild_id), {})
        managers = guild.get("user_managers", [])
        await interaction.response.send_message(f"User Managers: {', '.join(managers) if managers else 'None'}")

    # --- New Command: Default Delivery ---

    @app_commands.command(
        name="setdefaultdelivery",
        description="Set default reminder delivery for the guild (for User Managers)"
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
        if not is_reminder_admin(data, interaction.guild_id, interaction.user):
            await interaction.response.send_message("❌ You do not have permission to set the default delivery.")
            return
        set_guild_default_delivery(data, interaction.guild_id, delivery.value)
        await interaction.response.send_message(f"✅ Default delivery set to **{delivery.name}** for this guild.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
