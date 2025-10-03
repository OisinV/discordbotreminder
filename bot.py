import discord
from discord.ext import commands
import asyncio
import logging

from storage import load_data, get_due_reminders, remove_reminder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

data = load_data()


async def deliver_reminder(r, missed=False):
    try:
        guild = bot.get_guild(r["guild_id"])
        delivery_mode = r.get("delivery", "dm")
        target_mention = r.get("target_mention", f"<@{r['user_id']}>")
        status = "MISSED " if missed else ""

        # DM delivery
        if delivery_mode in ("dm", "both"):
            user = await bot.fetch_user(r["user_id"])
            if user:
                await user.send(f"⏰ {status}Reminder: {r['message']}")
                logging.info(
                    f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                    f"Delivered {status}reminder via DM to {user}: '{r['message']}' "
                    f"(⏰ {r['time']})"
                )

        # Channel delivery
        if delivery_mode in ("channel", "both") and "channel_id" in r:
            channel = bot.get_channel(r["channel_id"])
            if channel:
                await channel.send(f"⏰ {status}Reminder for {target_mention}: {r['message']}")
                logging.info(
                    f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                    f"Delivered {status}reminder in channel #{channel} for {target_mention}: '{r['message']}' "
                    f"(⏰ {r['time']})"
                )

        # Forum delivery
        if delivery_mode == "forum" and "channel_id" in r:
            forum = bot.get_channel(r["channel_id"])
            if isinstance(forum, discord.ForumChannel):
                thread_name = f"{status}Reminder: {r['message'][:50]}"
                thread = await forum.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.public_thread
                )
                await thread.send(f"{target_mention} ⏰ {r['message']}")
                logging.info(
                    f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                    f"Delivered {status}reminder in forum {forum.name} thread {thread.name} for {target_mention}: '{r['message']}' "
                    f"(⏰ {r['time']})"
                )

    except Exception as e:
        logging.error(
            f"[GUILD {r['guild_id']}] Failed to deliver {status.lower()}reminder to {r['user_id']}: {e}"
        )


async def reminder_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        due = get_due_reminders(data)
        for r in due:
            await deliver_reminder(r)
            remove_reminder(data, r)
        await asyncio.sleep(60)


@bot.event
async def on_ready():
    logging.info(f"Bot online as {bot.user}")
    # Deliver missed reminders
    for r in get_due_reminders(data):
        await deliver_reminder(r, missed=True)
        remove_reminder(data, r)
    bot.loop.create_task(reminder_loop())


async def load_commands():
    await bot.load_extension("commands.reminder")
    await bot.load_extension("commands.reminderadmin")
    await bot.load_extension("commands.testmsg")


async def main():
    async with bot:
        await load_commands()
        await bot.start("YOUR_TOKEN_HERE")  # Replace with your bot token


if __name__ == "__main__":
    asyncio.run(main())

