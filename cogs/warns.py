import discord
from discord.ext import commands
from datetime import datetime, timezone
import sqlite3
import os

DB_PATH = "data/warns.db"


class Warns(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self._init_db()

    # ─────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────
    def _init_db(self):
        os.makedirs("data", exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    timestamp INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    guild_id INTEGER PRIMARY KEY,
                    autoban_threshold INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def _get_autoban_threshold(self, guild_id: int) -> int:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT autoban_threshold FROM settings WHERE guild_id = ?",
                (guild_id,)
            )
            row = cur.fetchone()
        return row[0] if row else 0

    def _add_warn(self, guild_id, user_id, moderator_id, reason):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                guild_id,
                user_id,
                moderator_id,
                reason,
                int(datetime.now(timezone.utc).timestamp())
            ))
            conn.commit()

    def _get_warn_count(self, guild_id, user_id) -> int:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM warns
                WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id))
            return cur.fetchone()[0]

    def _get_recent_server_warns(self, guild_id, limit=10):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, moderator_id, reason, timestamp
                FROM warns
                WHERE guild_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (guild_id, limit))
            return cur.fetchall()

    # ─────────────────────────────────────────────
    # /warn
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="warn",
        description="Warn a member (logged)"
    )
    @commands.has_permissions(moderate_members=True)
    async def warn(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        reason: str
    ):
        if user.bot:
            await ctx.respond("❌ You cannot warn a bot.", ephemeral=True)
            return

        if user == ctx.author:
            await ctx.respond("❌ You cannot warn yourself.", ephemeral=True)
            return

        self._add_warn(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            reason
        )

        warn_count = self._get_warn_count(ctx.guild.id, user.id)
        threshold = self._get_autoban_threshold(ctx.guild.id)

        embed = discord.Embed(
            title="⚠️ User Warned",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Moderator", value=ctx.author.mention)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warns", value=warn_count)

        await ctx.respond(embed=embed)

        # Auto-ban check
        if threshold > 0 and warn_count >= threshold:
            if ctx.guild.me.guild_permissions.ban_members:
                await ctx.guild.ban(
                    user,
                    reason=f"Auto-ban after {warn_count} warns"
                )

    # ─────────────────────────────────────────────
    # /warns (SERVER-WIDE)
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="warns",
        description="View recent warnings in this server"
    )
    @commands.has_permissions(moderate_members=True)
    async def warns(self, ctx: discord.ApplicationContext):
        warns = self._get_recent_server_warns(ctx.guild.id)

        if not warns:
            await ctx.respond(
                "✅ No warnings have been issued in this server.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚠️ Recent Warnings (Server)",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        for i, (user_id, mod_id, reason, ts) in enumerate(warns, start=1):
            user = ctx.guild.get_member(user_id)
            moderator = ctx.guild.get_member(mod_id)

            embed.add_field(
                name=f"#{i}",
                value=(
                    f"**User:** {user.mention if user else user_id}\n"
                    f"**Moderator:** {moderator.mention if moderator else mod_id}\n"
                    f"**Reason:** {reason}\n"
                    f"**Time:** <t:{ts}:R>"
                ),
                inline=False
            )

        await ctx.respond(embed=embed, ephemeral=True)

    # ─────────────────────────────────────────────
    # /autoban
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="autoban",
        description="Set auto-ban threshold based on warns"
    )
    @commands.has_permissions(administrator=True)
    async def autoban(
        self,
        ctx: discord.ApplicationContext,
        number_of_warns: int
    ):
        if number_of_warns < 0:
            await ctx.respond("❌ Warn count cannot be negative.", ephemeral=True)
            return

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO settings (guild_id, autoban_threshold)
                VALUES (?, ?)
                ON CONFLICT(guild_id)
                DO UPDATE SET autoban_threshold = excluded.autoban_threshold
            """, (ctx.guild.id, number_of_warns))
            conn.commit()

        if number_of_warns == 0:
            await ctx.respond("✅ Auto-ban has been disabled.", ephemeral=True)
        else:
            await ctx.respond(
                f"✅ Members will now be auto-banned after **{number_of_warns}** warnings.",
                ephemeral=True
            )

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def setup(bot: discord.Bot):
    bot.add_cog(Warns(bot))