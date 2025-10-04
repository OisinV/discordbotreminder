import discord
from discord import app_commands
from discord.ext import commands
import time
import logging
from storage import load_data, save_data, get_guild_default_delivery
from bot import load_settings
from .reminderadmin import ReminderAdmin  # relative import

start_time = time.time()


class BackendControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    # ------------------------------------------------------------
    # Utility: Check if user is developer and in backend guild
    # ------------------------------------------------------------
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        backend_guild_id = self.settings.get("backend_guild_id")
        dev_ids = self.settings.get("dev_ids", [])
        if interaction.guild_id != backend_guild_id:
            await interaction.response.send_message(
                "❌ This command is only available in the backend guild.",
                ephemeral=True
            )
            return False
        if interaction.user.id not in dev_ids:
            await interaction.response.send_message(
                "❌ You are not authorized to use backend commands.",
                ephemeral=True
            )
            return False
        return True

    # ------------------------------------------------------------
    # Hidden Command Group
    # ------------------------------------------------------------
    backend_group = app_commands.Group(
        name="backend",
        description="Hidden backend commands for bot control",
        default_permissions=discord.Permissions(administrator=True),
        guild_only=True
    )

    # ------------------------------------------------------------
    # /backend status
    # ------------------------------------------------------------
    @backend_group.command(name="status", description="Get bot status and uptime (hidden)")
    async def backend_status(self, interaction: discord.Interaction):
        uptime = time.time() - start_time
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)
        data = load_data()
        reminder_count = len(data.get("reminders", []))

        embed = discord.Embed(
            title="🛰️ Bot Status",
            color=discord.Color.blurple()
        )
        embed.add_field(name="🕒 Uptime", value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s", inline=False)
        embed.add_field(name="⏰ Reminders Stored", value=str(reminder_count), inline=True)
        embed.add_field(name="🧩 Cogs Loaded", value=", ".join(self.bot.cogs.keys()), inline=False)
        embed.add_field(name="⚙️ Log Level", value=self.settings.get("log_level", "INFO"), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------
    # /backend reload
    # ------------------------------------------------------------
    @backend_group.command(name="reload", description="Reload settings and command cogs (hidden)")
    async def backend_reload(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            self.settings = load_settings(force=True)
            reloaded = []
            failed = []

            for cog in list(self.bot.extensions.keys()):
                try:
                    await self.bot.reload_extension(cog)
                    reloaded.append(cog)
                except Exception as e:
                    failed.append(f"{cog} ({e})")

            msg = f"✅ Reloaded {len(reloaded)} cogs.\n"
            if failed:
                msg += f"⚠️ Failed: {', '.join(failed)}"
            else:
                msg += "All reloaded successfully."

            await interaction.followup.send(msg, ephemeral=True)
            logging.info(f"Manual reload by {interaction.user}: {msg}")
        except Exception as e:
            logging.exception(f"Reload command failed: {e}")
            await interaction.followup.send(f"❌ Reload failed: {e}", ephemeral=True)

    # ------------------------------------------------------------
    # /backend update
    # ------------------------------------------------------------
    @backend_group.command(name="update", description="Send update message to all guilds (hidden)")
    @app_commands.describe(message="The message to broadcast to all update channels.")
    async def backend_update(self, interaction: discord.Interaction, message: str):
        data = load_data()
        sent = 0
        failed = 0
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            update_channel_id = data.get("update_channels", {}).get(guild_id)
            if not update_channel_id:
                continue
            channel = self.bot.get_channel(int(update_channel_id))
            if channel:
                try:
                    embed = discord.Embed(
                        title="📢 Bot Update",
                        description=message,
                        color=discord.Color.gold()
                    )
                    embed.set_footer(text=f"Sent by {interaction.user}")
                    await channel.send(embed=embed)
                    sent += 1
                except Exception as e:
                    failed += 1
                    logging.warning(f"Failed to send update to {guild.name}: {e}")

        await interaction.response.send_message(
            f"✅ Update sent to {sent} servers, failed on {failed}.",
            ephemeral=True
        )
        logging.info(f"Backend update broadcast by {interaction.user}: {message}")

        # ------------------------------------------------------------
        # /backend supportinvite
        # ------------------------------------------------------------
        @backend_group.command(
            name="supportinvite",
            description="DM all admins and guild owners an invite to the support server (hidden)"
        )
        async def backend_supportinvite(self, interaction: discord.Interaction):
            from .reminderadmin import data as reminder_data

            support_invite = self.settings.get("support_invite")
            if not support_invite:
                await interaction.response.send_message(
                    "❌ No support server invite is set in settings.",
                    ephemeral=True
                )
                return

            sent = 0
            failed = 0
            messaged_users = set()  # avoid duplicate DMs

            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                gdata = reminder_data.get("guilds", {}).get(guild_id, {})
                user_ids = set(gdata.get("admins", []))
                if guild.owner:
                    user_ids.add(str(guild.owner.id))

                for uid in user_ids:
                    if uid in messaged_users:
                        continue
                    member = guild.get_member(int(uid))
                    if member:
                        try:
                            await member.send(
                                f"Hello {member.name},\n\n"
                                f"You are listed as an admin on **{guild.name}**.\n"
                                f"Join our support server here: {support_invite}"
                            )
                            sent += 1
                            messaged_users.add(uid)
                        except discord.Forbidden:
                            # user has DMs closed or bot is blocked
                            failed += 1
                        except Exception as e:
                            logging.warning(f"Failed to DM {member} in {guild.name}: {e}")
                            failed += 1

            await interaction.response.send_message(
                f"✅ Support invite sent to {sent} users, failed for {failed}.",
                ephemeral=True
            )
            logging.info(f"Backend support invite broadcast by {interaction.user}")

    # ------------------------------------------------------------
    # /backend listadmins
    # ------------------------------------------------------------
    @backend_group.command(name="listadmins", description="List all admins and admin roles (hidden)")
    async def backend_listadmins(self, interaction: discord.Interaction):
        from .reminderadmin import data as reminder_data

        lines = []
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            gdata = reminder_data.get("guilds", {}).get(guild_id, {})
            users = gdata.get("admins", [])
            roles = gdata.get("admin_roles", [])

            user_mentions = [guild.get_member(int(u)).mention if guild.get_member(int(u)) else f"<@{u}>" for u in users]
            role_mentions = [guild.get_role(int(r)).mention if guild.get_role(int(r)) else f"<@&{r}>" for r in roles]

            lines.append(
                f"**{guild.name}**\nAdmins: {', '.join(user_mentions) or 'None'}\nRoles: {', '.join(role_mentions) or 'None'}"
            )

        await interaction.response.send_message("\n\n".join(lines), ephemeral=True)

    # ------------------------------------------------------------
    # /backend listusermanagers
    # ------------------------------------------------------------
    @backend_group.command(name="listusermanagers", description="List all user managers and roles (hidden)")
    async def backend_listusermanagers(self, interaction: discord.Interaction):
        from .reminderadmin import data as reminder_data

        lines = []
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            gdata = reminder_data.get("guilds", {}).get(guild_id, {})
            users = gdata.get("user_managers", [])
            roles = gdata.get("user_manager_roles", [])

            user_mentions = [guild.get_member(int(u)).mention if guild.get_member(int(u)) else f"<@{u}>" for u in users]
            role_mentions = [guild.get_role(int(r)).mention if guild.get_role(int(r)) else f"<@&{r}>" for r in roles]

            lines.append(
                f"**{guild.name}**\nUser Managers: {', '.join(user_mentions) or 'None'}\nRoles: {', '.join(role_mentions) or 'None'}"
            )

        await interaction.response.send_message("\n\n".join(lines), ephemeral=True)

    # ------------------------------------------------------------
    # /backend guilddefaults
    # ------------------------------------------------------------
    @backend_group.command(name="guilddefaults", description="Show default reminder delivery for all guilds")
    async def backend_guilddefaults(self, interaction: discord.Interaction):
        from .reminderadmin import data as reminder_data

        lines = []
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            default_delivery = reminder_data.get("guilds", {}).get(guild_id, {}).get("default_delivery", "Not Set")
            lines.append(f"**{guild.name}**: {default_delivery}")

        await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def setup(bot):
    await bot.add_cog(BackendControl(bot))
