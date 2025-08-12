import discord
from discord import app_commands
from shared import reminder_tasks

@app_commands.command(name="cancelreminder", description="Cancel a scheduled reminder by ID")
@app_commands.describe(reminder_id="The ID of the reminder to cancel")
async def cancelreminder_command(interaction: discord.Interaction, reminder_id: int):
    task = reminder_tasks.get(reminder_id)
    if not task:
        await interaction.response.send_message(
            f"❌ No reminder found with ID `{reminder_id}`.",
            ephemeral=True
        )
        return

    task.cancel()
    reminder_tasks.pop(reminder_id, None)

    await interaction.response.send_message(
        f"✅ Reminder `{reminder_id}` has been cancelled.",
        ephemeral=True
    )
