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
                user = await bot.fetch_user(r["user_id"])
                if user:
                    await user.send(f"⏰ Reminder: {r['message']}")
                    logging.info(f"Sent reminder to {user}: {r['message']}")
            except Exception as e:
                logging.error(f"Error sending reminder to {r['user_id']}: {e}")
            remove_reminder(data, r)
        await asyncio.sleep(60)


@bot.event
async def on_ready():
    logging.info(f"Bot online as {bot.user}")
    # Deliver missed reminders
    for r in get_due_reminders(data):
        try:
            user = await bot.fetch_user(r["user_id"])
            if user:
                await user.send(f"⏰ Missed reminder while offline: {r['message']}")
                logging.info(f"Delivered missed reminder to {user}: {r['message']}")
        except Exception as e:
            logging.error(f"Error delivering missed reminder to {r['user_id']}: {e}")
        remove_reminder(data, r)

    bot.loop.create_task(reminder_loop())


async def load_commands():
    await bot.load_extension("commands.reminder")


async def main():
    async with bot:
        await load_commands()
        await bot.start("YOUR_TOKEN_HERE")  # <--- Replace with your bot token


if __name__ == "__main__":
    asyncio.run(main())
    
