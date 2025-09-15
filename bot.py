import discord
from discord.ext import commands
from commands import testmsg_command  # Import from commands package
from commands import remindme_command # This is eccentially the invite for remind me
from commands import cancelreminder_command # Invite fo cancel
import asyncio
import uuid
from shared import reminder_tasks

TOKEN = "Insert discordtoken here"
intents = discord.Intents.default()
intents.message_content = True

class MyClient(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Add the commands here
        self.tree.add_command(testmsg_command)
        self.tree.add_command(remindme_command)
        self.tree.add_command(cancelreminder_command)
        await self.tree.sync()

client = MyClient()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

client.run(TOKEN)
