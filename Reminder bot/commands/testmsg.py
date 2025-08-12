import discord
from discord import app_commands

@discord.app_commands.command(
    name="testmsg",
    description="Send a custom message to a specific channel"
)
@app_commands.describe(
    channel="The channel to send the message in",
    message="The message text to send"
)
async def testmsg_command(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    await channel.send(message)
    await interaction.response.send_message(f"Message sent to {channel.mention}!", ephemeral=True)
