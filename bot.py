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


async def reminder_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        due = get_due_reminders(data)
        for r in due:
            try:
                guild = bot.get_guild(r["guild_id"])
                delivery_mode = r.get("delivery", "dm")

                # DM delivery
                if delivery_mode == "dm" or delivery_mode == "both":
                    user = await bot.fetch_user(r["user_id"])
                    if user:
                        await user.send(f"⏰ Reminder: {r['message']}")
                        logging.info(
                            f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                            f"Delivered reminder via DM to {user} ({r['user_id']}): '{r['message']}' "
                            f"(⏰ {r['time']})"
                        )

                # Channel delivery
                if delivery_mode in ("channel", "both") and "channel_id" in r:
                    channel = bot.get_channel(r["channel_id"])
                    if channel:
                        await channel.send(f"⏰ Reminder for <@{r['user_id']}>: {r['message']}")
                        logging.info(
                            f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                            f"Delivered reminder in channel #{channel} ({channel.id}) "
                            f"for user {r['user_id']}: '{r['message']}' "
                            f"(⏰ {r['time']})"
                        )

                # Forum delivery
                if delivery_mode == "forum" and "channel_id" in r:
                    forum = bot.get_channel(r["channel_id"])
                    if isinstance(forum, discord.ForumChannel):
                        thread = await forum.create_thread(
                            name=f"Reminder: {r['message'][:50]}",
                            type=discord.ChannelType.public_thread
                        )
                        await thread.send(f"<@{r['user_id']}> ⏰ {r['message']}")
                        logging.info(
                            f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                            f"Delivered reminder in forum {forum.name} ({forum.id}) "
                            f"thread {thread.name} for user {r['user_id']}: '{r['message']}' "
                            f"(⏰ {r['time']})"
                        )

            except Exception as e:
                logging.error(
                    f"[GUILD {r['guild_id']}] Failed to deliver reminder "
                    f"to {r['user_id']}: {e}"
                )

            remove_reminder(data, r)

        await asyncio.sleep(60)


@bot.event
async def on_ready():
    logging.info(f"Bot online as {bot.user}")
    # Deliver missed reminders
    for r in get_due_reminders(data):
        try:
            guild = bot.get_guild(r["guild_id"])
            delivery_mode = r.get("delivery", "dm")

            if delivery_mode in ("dm", "both"):
                user = await bot.fetch_user(r["user_id"])
                if user:
                    await user.send(f"⏰ Missed reminder while offline: {r['message']}")
                    logging.info(
                        f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                        f"Delivered MISSED reminder via DM to {user} ({r['user_id']}): '{r['message']}' "
                        f"(⏰ {r['time']})"
                    )

            if delivery_mode in ("channel", "both") and "channel_id" in r:
                channel = bot.get_channel(r["channel_id"])
                if channel:
                    await channel.send(f"⏰ Missed reminder for <@{r['user_id']}>: {r['message']}")
                    logging.info(
                        f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                        f"Delivered MISSED reminder in channel #{channel} ({channel.id}) "
                        f"for user {r['user_id']}: '{r['message']}' "
                        f"(⏰ {r['time']})"
                    )

            if delivery_mode == "forum" and "channel_id" in r:
                forum = bot.get_channel(r["channel_id"])
                if isinstance(forum, discord.ForumChannel):
                    thread = await forum.create_thread(
                        name=f"Missed Reminder: {r['message'][:50]}",
                        type=discord.ChannelType.public_thread
                    )
                    await thread.send(f"<@{r['user_id']}> ⏰ {r['message']}")
                    logging.info(
                        f"[GUILD {guild.name if guild else 'Unknown'} ({r['guild_id']})] "
                        f"Delivered MISSED reminder in forum {forum.name} ({forum.id}) "
                        f"thread {thread.name} for user {r['user_id']}: '{r['message']}' "
                        f"(⏰ {r['time']})"
                    )

        except Exception as e:
            logging.error(
                f"[GUILD {r['guild_id']}] Failed to deliver MISSED reminder "
                f"to {r['user_id']}: {e}"
            )
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


