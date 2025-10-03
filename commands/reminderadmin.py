import discord
from discord import app_commands
from discord.ext import commands
from storage import load_data, save_data, set_guild_default_delivery

data = load_data()

class ReminderAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        from storage import is_reminder_admin

        user = interaction.user
        guild_id = interaction.guild_id

        if not is_reminder_admin(data, guild_id, user):
            await interaction.response.send_message("❌ You do not have permission to set the default delivery.")
            return

        set_guild_default_delivery(data, guild_id, delivery.value)
        await interaction.response.send_message(f"✅ Default delivery set to **{delivery.name}** for this guild.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderAdmin(bot))
