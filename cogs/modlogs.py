import discord
from discord.ext import commands
from datetime import datetime, timezone
import sqlite3
import os

DB_PATH = "data/modlogs.db"


class ModLogs(commands.Cog):
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
                CREATE TABLE IF NOT EXISTS settings (
                    guild_id INTEGER PRIMARY KEY,
                    log_channel INTEGER
                )
            """)
            conn.commit()

    def _get_log_channel(self, guild: discord.Guild):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT log_channel FROM settings WHERE guild_id = ?",
                (guild.id,)
            )
            row = cur.fetchone()

        if row and row[0]:
            return guild.get_channel(row[0])
        return None

    async def _send_log(self, guild: discord.Guild, embed: discord.Embed):
        channel = self._get_log_channel(guild)
        if channel:
            await channel.send(embed=embed)

    # ─────────────────────────────────────────────
    # Audit Log Helpers
    # ─────────────────────────────────────────────
    async def _get_ban_executor(self, guild: discord.Guild, user: discord.User):
        try:
            async for entry in guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.ban
            ):
                if entry.target.id == user.id:
                    return entry.user
        except discord.Forbidden:
            pass
        return None

    async def _was_recently_banned(self, guild: discord.Guild, user: discord.User) -> bool:
        try:
            async for entry in guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.ban
            ):
                if entry.target.id == user.id:
                    return True
        except discord.Forbidden:
            pass
        return False

    async def _get_timeout_executor(self, guild: discord.Guild, target: discord.Member):
        try:
            async for entry in guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.member_update
            ):
                if entry.target.id == target.id:
                    return entry.user
        except discord.Forbidden:
            pass
        return None

    # ─────────────────────────────────────────────
    # /setlogchannel
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="setlogchannel",
        description="Set the moderation log channel"
    )
    @commands.has_permissions(administrator=True)
    async def setlogchannel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel
    ):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO settings (guild_id, log_channel)
                VALUES (?, ?)
                ON CONFLICT(guild_id)
                DO UPDATE SET log_channel = excluded.log_channel
            """, (ctx.guild.id, channel.id))
            conn.commit()

        await ctx.respond(
            f"✅ Moderation logs will be sent to {channel.mention}",
            ephemeral=True
        )

    # ─────────────────────────────────────────────
    # Member Join / Leave
    # ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(
            title="🟢 Member Joined",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.add_field(
            name="Account Created",
            value=f"<t:{int(member.created_at.timestamp())}:F>",
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await self._send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Suppress leave log if this was a ban
        if await self._was_recently_banned(member.guild, member):
            return

        embed = discord.Embed(
            title="🔴 Member Left",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{member} ({member.id})")

        await self._send_log(member.guild, embed)

    # ─────────────────────────────────────────────
    # Member Updates (Nicknames, Roles, Timeouts)
    # ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Nickname change
        if before.nick != after.nick:
            embed = discord.Embed(
                title="✏️ Nickname Changed",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=after.mention)
            embed.add_field(name="Before", value=before.nick or before.name)
            embed.add_field(name="After", value=after.nick or after.name)

            await self._send_log(after.guild, embed)

        # Role added / removed
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        for role in after_roles - before_roles:
            if role.name != "@everyone":
                embed = discord.Embed(
                    title="🟢 Role Added",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="User", value=after.mention)
                embed.add_field(name="Role", value=role.mention)
                await self._send_log(after.guild, embed)

        for role in before_roles - after_roles:
            if role.name != "@everyone":
                embed = discord.Embed(
                    title="🔴 Role Removed",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="User", value=after.mention)
                embed.add_field(name="Role", value=role.name)
                await self._send_log(after.guild, embed)

        # Timeout applied / removed
        if before.communication_disabled_until != after.communication_disabled_until:
            moderator = await self._get_timeout_executor(after.guild, after)

            if after.communication_disabled_until:
                embed = discord.Embed(
                    title="⏱️ Timeout Applied",
                    color=discord.Color.purple(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="User", value=after.mention)
                embed.add_field(
                    name="Until",
                    value=f"<t:{int(after.communication_disabled_until.timestamp())}:F>"
                )
            else:
                embed = discord.Embed(
                    title="✅ Timeout Removed",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="User", value=after.mention)

            embed.add_field(
                name="Moderator",
                value=moderator.mention if moderator else "Unknown"
            )

            await self._send_log(after.guild, embed)

    # ─────────────────────────────────────────────
    # Role Create / Delete
    # ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        embed = discord.Embed(
            title="🆕 Role Created",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Role", value=role.name)
        embed.add_field(name="Role ID", value=role.id)

        await self._send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = discord.Embed(
            title="🗑️ Role Deleted",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Role", value=role.name)
        embed.add_field(name="Role ID", value=role.id)

        await self._send_log(role.guild, embed)

    # ─────────────────────────────────────────────
    # Bans / Unbans
    # ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        moderator = await self._get_ban_executor(guild, user)

        embed = discord.Embed(
            title="⛔ User Banned",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{user} ({user.id})")
        embed.add_field(
            name="Moderator",
            value=moderator.mention if moderator else "Unknown"
        )

        await self._send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = discord.Embed(
            title="♻️ User Unbanned",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{user} ({user.id})")

        await self._send_log(guild, embed)

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def setup(bot: discord.Bot):
    bot.add_cog(ModLogs(bot))