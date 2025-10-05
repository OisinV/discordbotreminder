import discord
from discord import app_commands
from discord.ext import commands
import time
import logging
import json
import os
import traceback

from storage import load_data, save_data, get_guild_default_delivery
from bot import load_settings
from . import reminderadmin  # use module import to access reminderadmin.data
import logging
logger = logging.getLogger("bot")

logger.info("Backend command executed")
logger.warning("Permission denied for user X")
logger.error("Something went wrong", exc_info=True)

# Control file name used by the launcher
LAUNCHER_CONTROL_FILE = "launcher_control.json"
SETTINGS_FILE = "settings.json"

start_time = time.time()
logger = logging.getLogger("bot")


def read_launcher_control():
    if not os.path.exists(LAUNCHER_CONTROL_FILE):
        return {}
    try:
        with open(LAUNCHER_CONTROL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to read launcher control file.")
        return {}


def write_launcher_control(data: dict):
    try:
        with open(LAUNCHER_CONTROL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        logger.exception("Failed to write launcher control file.")


def set_launcher_flag(key: str, value: bool):
    control = read_launcher_control() or {}
    control[key] = bool(value)
    write_launcher_control(control)


class BackendControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    # ------------------------------------------------------------
    # Utility: Check if user is developer and in backend guild
    # ------------------------------------------------------------
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Central access gate for backend commands.
        Logs attempts to the central logger and (if configured) the backend_log_channel in settings.
        """
        # refresh settings in-case they've changed on disk
        try:
            self.settings = load_settings()
        except Exception:
            logger.exception("Could not reload settings in interaction_check")

        backend_guild_id = self.settings.get("backend_guild_id")
        dev_ids = self.settings.get("dev_ids", [])
        backend_log_channel_id = self.settings.get("backend_log_channel_id")

        user = interaction.user
        command_name = getattr(interaction.command, "qualified_name", "unknown")
        guild_name = interaction.guild.name if interaction.guild else "DM"
        channel_name = getattr(interaction.channel, "name", getattr(interaction.channel, "id", "unknown"))

        # build a small log message
        attempt_msg = f"[BACKEND ATTEMPT] User={user} ({user.id}) Command={command_name} Guild={guild_name} Channel={channel_name}"
        logger.info(attempt_msg)

        # If not in backend guild
        if interaction.guild_id != backend_guild_id:
            reason = "Not in backend guild"
            deny_msg = f"[BACKEND DENIED] {attempt_msg} - {reason}"
            logger.warning(deny_msg)
            try:
                await interaction.response.send_message("❌ This command is only available in the backend guild.", ephemeral=True)
            except Exception:
                # fallback if response already deferred or other
                try:
                    await interaction.followup.send("❌ This command is only available in the backend guild.", ephemeral=True)
                except Exception:
                    logger.exception("Failed to send guild restriction message.")
            # send log to backend channel if configured
            if backend_log_channel_id:
                try:
                    ch = self.bot.get_channel(int(backend_log_channel_id))
                    if ch:
                        embed = discord.Embed(title="🔒 Backend Access Denied", color=discord.Color.red())
                        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
                        embed.add_field(name="Command", value=command_name, inline=False)
                        embed.add_field(name="Guild", value=f"{guild_name} (`{interaction.guild_id}`)", inline=False)
                        embed.add_field(name="Reason", value=reason, inline=False)
                        await ch.send(embed=embed)
                except Exception:
                    logger.exception("Failed to send backend deny log to channel.")
            return False

        # If user is not developer
        if user.id not in dev_ids:
            reason = "Not in dev_ids"
            deny_msg = f"[BACKEND DENIED] {attempt_msg} - {reason}"
            logger.warning(deny_msg)
            try:
                await interaction.response.send_message("❌ You are not authorized to use backend commands.", ephemeral=True)
            except Exception:
                try:
                    await interaction.followup.send("❌ You are not authorized to use backend commands.", ephemeral=True)
                except Exception:
                    logger.exception("Failed to send unauthorized message.")
            if backend_log_channel_id:
                try:
                    ch = self.bot.get_channel(int(backend_log_channel_id))
                    if ch:
                        embed = discord.Embed(title="🔒 Backend Access Denied", color=discord.Color.red())
                        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
                        embed.add_field(name="Command", value=command_name, inline=False)
                        embed.add_field(name="Guild", value=f"{guild_name} (`{interaction.guild_id}`)", inline=False)
                        embed.add_field(name="Reason", value=reason, inline=False)
                        await ch.send(embed=embed)
                except Exception:
                    logger.exception("Failed to send backend deny log to channel.")
            return False

        # Allowed
        allow_msg = f"[BACKEND GRANTED] {attempt_msg}"
        logger.info(allow_msg)
        if backend_log_channel_id:
            try:
                ch = self.bot.get_channel(int(backend_log_channel_id))
                if ch:
                    embed = discord.Embed(title="✅ Backend Access Granted", color=discord.Color.green())
                    embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
                    embed.add_field(name="Command", value=command_name, inline=False)
                    embed.add_field(name="Guild", value=f"{guild_name} (`{interaction.guild_id}`)", inline=False)
                    await ch.send(embed=embed)
            except Exception:
                logger.exception("Failed to send backend grant log to channel.")
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
            logger.info(f"Manual reload by {interaction.user}: {msg}")
        except Exception as e:
            logger.exception(f"Reload command failed: {e}")
            try:
                await interaction.followup.send(f"❌ Reload failed: {e}", ephemeral=True)
            except Exception:
                logger.exception("Failed to send failure followup for reload")

    # ------------------------------------------------------------
    # /backend restart (soft restart = reload cogs)
    # ------------------------------------------------------------
    @backend_group.command(
        name="restart",
        description="Reload settings and all cogs (soft restart - hidden)"
    )
    async def backend_restart(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Reload settings first
        try:
            self.settings = load_settings(force=True)
            settings_msg = "✅ Settings reloaded successfully."
        except Exception as e:
            settings_msg = f"⚠️ Failed to reload settings: {e}"
            logger.exception("Failed to reload settings during backend restart.")

        # Reload all cogs
        reloaded = []
        failed = []

        for cog in list(self.bot.extensions.keys()):
            try:
                await self.bot.reload_extension(cog)
                reloaded.append(cog)
            except Exception as e:
                tb = traceback.format_exc()
                failed.append(f"{cog} ({e})\n{tb}")
                logger.error(f"Failed to reload cog {cog}: {tb}")

        # Compose summary
        msg = f"🔄 Backend Restart Attempted\n{settings_msg}\n✅ Reloaded: {len(reloaded)} cogs."
        if failed:
            msg += f"\n⚠️ Failed: {len(failed)} cogs. Check logs for details."
        else:
            msg += "\nAll cogs reloaded successfully."

        try:
            await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            logger.exception("Failed to send restart followup")

        logger.info(f"Backend restart by {interaction.user}: {msg}")

        # Detailed log in backend channel
        backend_log_channel_id = self.settings.get("backend_log_channel_id")
        if backend_log_channel_id:
            try:
                log_channel = self.bot.get_channel(int(backend_log_channel_id))
                if log_channel:
                    embed = discord.Embed(
                        title="🛠️ Backend Restart",
                        description=msg,
                        color=discord.Color.orange()
                    )
                    if failed:
                        fail_text = "\n\n".join(failed)
                        if len(fail_text) > 4000:
                            fail_text = fail_text[:3990] + "\n...(truncated)"
                        embed.add_field(name="Failed Cogs", value=fail_text, inline=False)
                    embed.set_footer(text=f"Executed by {interaction.user}")
                    await log_channel.send(embed=embed)
            except Exception:
                logger.exception("Failed to send backend restart log to channel.")

    # ------------------------------------------------------------
    # /backend hardrestart  <-- signals launcher_control file and closes bot process
    # ------------------------------------------------------------
    @backend_group.command(name="hardrestart", description="Fully restart the bot process (hidden)")
    async def backend_hardrestart(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            set_launcher_flag_key = "restart"
            # ensure launcher control exists and set restart True
            control = read_launcher_control()
            control[set_launcher_flag_key] = True
            write_launcher_control(control)
        except Exception:
            logger.exception("Failed to write launcher control for hardrestart")
            try:
                await interaction.followup.send("❌ Failed to signal launcher for restart.", ephemeral=True)
            except Exception:
                pass
            return

        try:
            await interaction.followup.send("♻️ Hard restart requested — shutting down now.", ephemeral=True)
            # close the bot to let launcher relaunch it
            await self.bot.close()
        except Exception:
            logger.exception("Failed to close bot during hardrestart")
            try:
                await interaction.followup.send("❌ Failed to close bot.", ephemeral=True)
            except Exception:
                pass

    # ------------------------------------------------------------
    # /backend update
    # ------------------------------------------------------------
    @backend_group.command(name="update", description="Send update message to all guilds (hidden)")
    @app_commands.describe(message="The message to broadcast to all update channels.")
    async def backend_update(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)

        data = load_data()
        update_channels = {}
        # Collect all channels properly from per-guild data (storage keeps per-guild lists)
        for gid, gdata in data.get("guilds", {}).items():
            for ch in gdata.get("update_channels", []):
                # if multiple channels exist per guild, keep the first (preserve older behavior)
                if gid not in update_channels:
                    update_channels[gid] = ch

        sent = 0
        failed = 0
        dmed = 0
        total_guilds = len(self.bot.guilds)

        embed_template = discord.Embed(
            title="📢 Bot Update",
            description=message,
            color=discord.Color.gold()
        )
        embed_template.set_footer(text=f"Sent by {interaction.user}")

        # Send updates
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            channel_id = update_channels.get(guild_id)

            if channel_id:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    try:
                        embed = embed_template.copy()
                        await channel.send(embed=embed)
                        sent += 1
                        continue
                    except Exception:
                        failed += 1
                        logger.warning(f"Failed to send update to {guild.name} ({guild_id})")
                else:
                    # channel not found (maybe bot lost view) -> treat as failure and fallback to owner DM
                    failed += 1
                    logger.warning(f"Update channel not found for guild {guild.name} ({channel_id})")

            # Fallback: DM owner
            if guild.owner:
                try:
                    await guild.owner.send(f"📢 **Bot Update for {guild.name}**\n\n{message}")
                    dmed += 1
                except discord.Forbidden:
                    failed += 1
                    logger.warning(f"Cannot DM owner of {guild.name} (DMs disabled).")
                except Exception:
                    failed += 1
                    logger.exception(f"Error DMing owner of {guild.name}")

        # Summary message
        summary = (
            f"✅ Sent to **{sent}** update channels, "
            f"📬 DMed **{dmed}** owners, "
            f"❌ Failed for **{failed}** guilds.\n"
            f"📊 Overall: **{sent + dmed}/{total_guilds} guilds** updated."
        )

        try:
            await interaction.followup.send(summary, ephemeral=True)
        except Exception:
            logger.exception("Failed to send update summary followup")

        logger.info(f"Backend update by {interaction.user}: {summary}")

        # also log to backend channel if configured
        backend_log_channel_id = self.settings.get("backend_log_channel_id")
        if backend_log_channel_id:
            try:
                ch = self.bot.get_channel(int(backend_log_channel_id))
                if ch:
                    log_embed = discord.Embed(
                        title="📢 Backend Update Broadcast",
                        description=f"{message}\n\n{summary}",
                        color=discord.Color.orange()
                    )
                    log_embed.set_footer(text=f"Executed by {interaction.user}")
                    await ch.send(embed=log_embed)
            except Exception:
                logger.exception("Failed to send backend update log to channel.")

    # ------------------------------------------------------------
    # /backend supportinvite
    # ------------------------------------------------------------
    @backend_group.command(
        name="supportinvite",
        description="DM all admins and guild owners an invite to the support server (hidden)"
    )
    async def backend_supportinvite(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        support_invite = self.settings.get("support_invite")
        if not support_invite:
            await interaction.followup.send("❌ No support server invite is set in settings.", ephemeral=True)
            return

        sent = 0
        failed = 0
        messaged_users = set()  # avoid duplicate DMs

        # access reminderadmin.data
        reminder_data = getattr(reminderadmin, "data", {})

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            gdata = reminder_data.get("guilds", {}).get(guild_id, {})
            user_ids = set(gdata.get("admins", []))
            if guild.owner:
                user_ids.add(str(guild.owner.id))

            for uid in user_ids:
                if uid in messaged_users:
                    continue
                try:
                    member = guild.get_member(int(uid))
                except Exception:
                    member = None

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
                        failed += 1
                    except Exception:
                        failed += 1
                        logger.exception(f"Failed to DM admin {uid} of guild {guild.name}")

        try:
            await interaction.followup.send(f"✅ Support invite sent to {sent} users, failed for {failed}.", ephemeral=True)
        except Exception:
            logger.exception("Failed to send supportinvite followup")

        logger.info(f"Backend support invite broadcast by {interaction.user} sent={sent} failed={failed}")

    # ------------------------------------------------------------
    # /backend listadmins
    # ------------------------------------------------------------
    @backend_group.command(name="listadmins", description="List all admins and admin roles (hidden)")
    async def backend_listadmins(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reminder_data = getattr(reminderadmin, "data", {})

        lines = []
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            gdata = reminder_data.get("guilds", {}).get(guild_id, {})
            users = gdata.get("admins", [])
            roles = gdata.get("admin_roles", [])

            user_mentions = [guild.get_member(int(u)).mention if guild.get_member(int(u)) else f"<@{u}>" for u in users]
            role_mentions = [guild.get_role(int(r)).mention if guild.get_role(int(r)) else f"<@&{r}>" for r in roles]

            lines.append(f"**{guild.name}**\nAdmins: {', '.join(user_mentions) or 'None'}\nRoles: {', '.join(role_mentions) or 'None'}")

        try:
            await interaction.followup.send("\n\n".join(lines) or "No admin data found.", ephemeral=True)
        except Exception:
            logger.exception("Failed to send listadmins followup")

    # ------------------------------------------------------------
    # /backend listusermanagers
    # ------------------------------------------------------------
    @backend_group.command(name="listusermanagers", description="List all user managers and roles (hidden)")
    async def backend_listusermanagers(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reminder_data = getattr(reminderadmin, "data", {})

        lines = []
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            gdata = reminder_data.get("guilds", {}).get(guild_id, {})
            users = gdata.get("user_managers", [])
            roles = gdata.get("user_manager_roles", [])

            user_mentions = [guild.get_member(int(u)).mention if guild.get_member(int(u)) else f"<@{u}>" for u in users]
            role_mentions = [guild.get_role(int(r)).mention if guild.get_role(int(r)) else f"<@&{r}>" for r in roles]

            lines.append(f"**{guild.name}**\nUser Managers: {', '.join(user_mentions) or 'None'}\nRoles: {', '.join(role_mentions) or 'None'}")

        try:
            await interaction.followup.send("\n\n".join(lines) or "No user manager data found.", ephemeral=True)
        except Exception:
            logger.exception("Failed to send listusermanagers followup")

    # ------------------------------------------------------------
    # /backend guilddefaults
    # ------------------------------------------------------------
    @backend_group.command(name="guilddefaults", description="Show default reminder delivery for all guilds")
    async def backend_guilddefaults(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reminder_data = getattr(reminderadmin, "data", {})

        lines = []
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            default_delivery = reminder_data.get("guilds", {}).get(guild_id, {}).get("default_delivery", "Not Set")
            lines.append(f"**{guild.name}**: {default_delivery}")

        try:
            await interaction.followup.send("\n".join(lines) or "No guild defaults set.", ephemeral=True)
        except Exception:
            logger.exception("Failed to send guilddefaults followup")

    # ------------------------------------------------------------
    # /backend autorestart (toggle in settings.json)
    # ------------------------------------------------------------
    @backend_group.command(name="autorestart", description="Toggle automatic crash restart (hidden)")
    async def backend_autorestart(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            # read settings.json
            if not os.path.exists(SETTINGS_FILE):
                # create base settings if missing
                try:
                    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                        json.dump({"auto_restart": True}, f, indent=4)
                except Exception:
                    logger.exception("Failed creating settings.json for autorestart toggle")
                    await interaction.followup.send("❌ Failed to create settings file.", ephemeral=True)
                    return

            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)

            current = settings.get("auto_restart", True)
            new_value = not bool(current)
            settings["auto_restart"] = new_value

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)

            state = "Enabled" if new_value else "Disabled"
            await interaction.followup.send(f"Auto-restart is now **{state}**.", ephemeral=True)
            logger.info(f"Auto-restart toggled by {interaction.user}: {state}")
        except Exception:
            logger.exception("Failed toggling auto-restart")
            try:
                await interaction.followup.send("❌ Failed to toggle auto-restart.", ephemeral=True)
            except Exception:
                pass

    # ------------------------------------------------------------
    # /backend stop (signals launcher to stop and closes bot)
    # ------------------------------------------------------------
    @backend_group.command(name="stop", description="Stop the bot and launcher completely (hidden)")
    async def backend_stop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            control = read_launcher_control()
            control["stop"] = True
            # ensure restart is False when stopping
            control["restart"] = False
            write_launcher_control(control)
        except Exception:
            logger.exception("Failed to write launcher control for stop")
            try:
                await interaction.followup.send("❌ Failed to signal launcher to stop.", ephemeral=True)
            except Exception:
                pass
            return

        try:
            await interaction.followup.send("🛑 Stopping bot and launcher...", ephemeral=True)
            await self.bot.close()
        except Exception:
            logger.exception("Failed to close bot during stop")
            try:
                await interaction.followup.send("❌ Failed to stop the bot.", ephemeral=True)
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(BackendControl(bot))
