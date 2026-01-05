import discord
import platform
import sys

from discord.ext import commands
from datetime import datetime, timezone
from kiwi_bot import BOT_START_TIME

class Utility(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # /serverinfo
    # ─────────────────────────────────────────────

    @discord.slash_command(
        name="serverinfo",
        description="View detailed information about this server"
    )
    async def serverinfo(self, ctx: discord.ApplicationContext):
        guild = ctx.guild

        embed = discord.Embed(
            title=f"Server Information",
            description=guild.name,
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(
            name="Server Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True
        )

        embed.add_field(
            name="Server created on",
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=True
        )

        embed.add_field(
            name="Members",
            value=str(guild.member_count),
            inline=True
        )

        embed.add_field(
            name="Roles",
            value=str(len(guild.roles) - 1),  # excluding @everyone
            inline=True
        )

        embed.add_field(
            name="Emojis",
            value=str(len(guild.emojis)),
            inline=True
        )

        # Soundboard sounds (safe fallback)
        soundboard_count = (
            len(guild.soundboard_sounds)
            if hasattr(guild, "soundboard_sounds")
            else 0
        )

        embed.add_field(
            name="Soundboards",
            value=str(soundboard_count),
            inline=True
        )

        embed.set_footer(text=f"Server ID: {guild.id}")

        await ctx.respond(embed=embed)

    # ─────────────────────────────────────────────
    # /userinfo [@user]
    # ─────────────────────────────────────────────

    @discord.slash_command(
        name="userinfo",
        description="View detailed information about a user"
    )
    async def userinfo(
        self,
        ctx: discord.ApplicationContext,
        user: discord.User = None
    ):
        user = user or ctx.author
        member = ctx.guild.get_member(user.id)

        embed = discord.Embed(
            title="User Information",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_author(
            name=f"{user} ({user.id})",
            icon_url=user.display_avatar.url
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        if user.discriminator == "0":
            display_name = user.name 
        else:
            display_name = f"{user.name}#{user.discriminator}"

        embed.add_field(
            name="Username",
            value=display_name,
            inline=True
        )

        embed.add_field(
            name="Bot Account",
            value="Yes" if user.bot else "No",
            inline=True
        )

        embed.add_field(
            name="Account Created",
            value=f"<t:{int(user.created_at.timestamp())}:F>",
            inline=False
        )

        if member:
            embed.add_field(
                name="Joined Server",
                value=f"<t:{int(member.joined_at.timestamp())}:F>",
                inline=False
            )

            roles = [
                role.mention
                for role in member.roles
                if role.name != "@everyone"
            ]

            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=", ".join(roles) if roles else "None",
                inline=False
            )

            embed.add_field(
                name="Top Role",
                value=member.top_role.mention,
                inline=True
            )

            embed.add_field(
                name="Nickname",
                value=member.nick if member.nick else "None",
                inline=True
            )

            if member.status == discord.Status.online:
                status_display = "Online 🟢"
            elif member.status == discord.Status.idle:
                status_display = "Idle 🌙"
            elif member.status == discord.Status.dnd:
                status_display = "DND ⛔"
            else:
                status_display = "Offline ⚪"

            embed.add_field(
                name="Status",
                value=status_display,
                inline=True
            )

        embed.set_footer(text="User profile data")

        await ctx.respond(embed=embed)

    # ─────────────────────────────────────────────
    # /avatar [@user]
    # ─────────────────────────────────────────────

    @discord.slash_command(
        name="avatar",
        description="View a user's avatar in full size"
    )
    async def avatar(
        self,
        ctx: discord.ApplicationContext,
        user: discord.User = None
    ):
        user = user or ctx.author

        embed = discord.Embed(
            title=f"{user}'s Avatar",
            color=discord.Color.orange()
        )

        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")

        await ctx.respond(embed=embed)

    # ─────────────────────────────────────────────
    # /uptime
    # ─────────────────────────────────────────────

    @discord.slash_command(
        name="uptime",
        description="Show how long Kiwi has been running"
    )
    async def uptime(self, ctx: discord.ApplicationContext):
        now = datetime.now(timezone.utc)
        delta = now - BOT_START_TIME

        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="Kiwi Uptime",
            description=uptime_str,
            color=discord.Color.blue(),
            timestamp=now
        )

        await ctx.respond(embed=embed)

    # ─────────────────────────────────────────────
    # /botinfo
    # ─────────────────────────────────────────────

    @discord.slash_command(
        name="kiwinfo",
        description="View detailed information about Kiwi"
    )
    async def kiwinfo(self, ctx: discord.ApplicationContext):
        now = datetime.now(timezone.utc)
        delta = now - BOT_START_TIME

        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="Kiwi Information",
            color=discord.Color.purple(),
            timestamp=now
        )

        embed.set_author(
            name=str(self.bot.user),
            icon_url=self.bot.user.display_avatar.url
        )

        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)

        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Library", value=f"Pycord {discord.__version__}", inline=True)

        embed.set_footer(text=f"Kiwi ID: {self.bot.user.id}")

        await ctx.respond(embed=embed)

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def setup(bot: discord.Bot):
    bot.add_cog(Utility(bot))