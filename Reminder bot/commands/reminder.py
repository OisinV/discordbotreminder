import discord
import asyncio
import random
from typing import Optional
from discord import app_commands
from shared import reminder_tasks

def parse_time(time_str: str) -> int | None:
    """Convert a string like '1w2d3h4m5s' into total seconds. Return None if invalid."""
    time_str = time_str.strip().lower()
    total_seconds = 0
    num = ''

    for char in time_str:
        if char.isdigit():
            num += char
        else:
            if char in ['s', 'm', 'h', 'd', 'w'] and num:
                if char == 's':
                    total_seconds += int(num)
                elif char == 'm':
                    total_seconds += int(num) * 60
                elif char == 'h':
                    total_seconds += int(num) * 3600
                elif char == 'd':
                    total_seconds += int(num) * 86400
                elif char == 'w':
                    total_seconds += int(num) * 604800
                num = ''
            else:
                return None  # Invalid format

    return total_seconds if total_seconds > 0 else None

@app_commands.command(name="remindme", description="Set a reminder")
@app_commands.describe(
    time="When to send the reminder (e.g. 1w2d3h4m5s)",
    reminder="The message to send when time is up",
    role="Optional role to ping",
    channel="Channel to send the reminder in (leave empty if using forum_post)",
    forum_post="Forum post to send the reminder in (leave empty if using channel)"
)
async def remindme_command(
    interaction: discord.Interaction,
    time: str,
    reminder: str,
    role: Optional[discord.Role] = None,
    channel: Optional[discord.TextChannel] = None,
    forum_post: Optional[discord.Thread] = None
):
    # Check mutually exclusive fields
    if channel and forum_post:
        await interaction.response.send_message(
            "❌ Please specify **either** a channel **or** a forum post, not both.",
            ephemeral=True
        )
        return
    if not channel and not forum_post:
        await interaction.response.send_message(
            "❌ You must specify **either** a channel or a forum post.",
            ephemeral=True
        )
        return

    delay_seconds = parse_time(time)
    if delay_seconds is None:
        await interaction.response.send_message(
            "❌ Invalid time format! Use examples like `10s`, `5m`, `2h`, `1d2h30m`, or `1w`.",
            ephemeral=True
        )
        return

    reminder_id = random.randint(10000000, 99999999)

    async def send_reminder():
        try:
            await asyncio.sleep(delay_seconds)
            destination = channel or forum_post
            if destination:
                ping_part = f"{role.mention} " if role else ""
                await destination.send(f"⏰ Reminder ({reminder_id}): {ping_part}{reminder}")
        finally:
            reminder_tasks.pop(reminder_id, None)

    task = asyncio.create_task(send_reminder())
    reminder_tasks[reminder_id] = task

    await interaction.response.send_message(
        f"✅ Reminder set for `{time}` from now. ID: **{reminder_id}**",
        ephemeral=True
    )
