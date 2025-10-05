import discord
from discord import app_commands
from discord.ext import commands

class TestMsg(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="testmsg",
        description="Send a custom message to a specific channel"
    )
    @app_commands.describe(
        channel="The channel to send the message in",
        message="The message text to send"
    )
    async def testmsg_command(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str
    ):
        await channel.send(message)
        await interaction.response.send_message(
            f"✅ Message sent to {channel.mention}!", ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(TestMsg(bot))
