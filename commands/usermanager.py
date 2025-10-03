import discord
from discord.ext import commands
from storage import (
    add_user_manager,
    remove_user_manager,
    add_admin_manager,
    remove_admin_manager,
    is_admin_manager,
    is_user_manager,
    get_guild_settings
)
from bot import data

class UserManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Add user manager (admin only) ---
    @commands.command(name="addusermanager")
    async def add_user_manager_cmd(self, ctx, target: discord.Member | discord.Role):
        """Add a user or role as User Manager (Admins only)."""
        if not is_admin_manager(data, ctx.guild.id, ctx.author.id):
            return await ctx.send("❌ You don’t have permission to do this.")

        add_user_manager(data, ctx.guild.id, target.id)
        await ctx.send(f"✅ {target.mention if isinstance(target, discord.Member) else target.name} added as **User Manager**.")

    # --- Remove user manager (admin only) ---
    @commands.command(name="removeusermanager")
    async def remove_user_manager_cmd(self, ctx, target: discord.Member | discord.Role):
        """Remove a user or role from User Managers (Admins only)."""
        if not is_admin_manager(data, ctx.guild.id, ctx.author.id):
            return await ctx.send("❌ You don’t have permission to do this.")

        remove_user_manager(data, ctx.guild.id, target.id)
        await ctx.send(f"🗑️ {target.mention if isinstance(target, discord.Member) else target.name} removed from **User Managers**.")

    # --- Add admin manager (admin only) ---
    @commands.command(name="addadminmanager")
    async def add_admin_manager_cmd(self, ctx, target: discord.Member | discord.Role):
        """Add a user or role as Admin Manager (Admins only)."""
        if not is_admin_manager(data, ctx.guild.id, ctx.author.id):
            return await ctx.send("❌ You don’t have permission to do this.")

        add_admin_manager(data, ctx.guild.id, target.id)
        await ctx.send(f"✅ {target.mention if isinstance(target, discord.Member) else target.name} added as **Admin Manager**.")

    # --- Remove admin manager (admin only) ---
    @commands.command(name="removeadminmanager")
    async def remove_admin_manager_cmd(self, ctx, target: discord.Member | discord.Role):
        """Remove a user or role from Admin Managers (Admins only)."""
        if not is_admin_manager(data, ctx.guild.id, ctx.author.id):
            return await ctx.send("❌ You don’t have permission to do this.")

        remove_admin_manager(data, ctx.guild.id, target.id)
        await ctx.send(f"🗑️ {target.mention if isinstance(target, discord.Member) else target.name} removed from **Admin Managers**.")

    # --- List managers ---
    @commands.command(name="listmanagers")
    async def list_managers(self, ctx):
        """List current User Managers and Admin Managers for this guild."""
        settings = get_guild_settings(data, ctx.guild.id)
        user_managers = settings.get("user_managers", [])
        admin_managers = settings.get("admin_managers", [])

        def format_entries(entries):
            result = []
            for entry_id in entries:
                obj = ctx.guild.get_member(entry_id) or ctx.guild.get_role(entry_id)
                result.append(obj.mention if obj else f"`{entry_id}` (left server)")
            return result or ["None"]

        embed = discord.Embed(title=f"Manager Roles in {ctx.guild.name}", color=discord.Color.blue())
        embed.add_field(name="👥 User Managers", value="\n".join(format_entries(user_managers)), inline=False)
        embed.add_field(name="🛡️ Admin Managers", value="\n".join(format_entries(admin_managers)), inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UserManager(bot))
