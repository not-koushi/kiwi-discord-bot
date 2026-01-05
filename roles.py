import discord
from discord.ext import commands
from datetime import datetime, timezone


# ─────────────────────────────────────────────
# Confirmation View for Role Cleanup
# ─────────────────────────────────────────────
class RoleCleanupConfirmView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext, roles_to_delete: list[discord.Role]):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.roles_to_delete = roles_to_delete

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ You cannot interact with this confirmation.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Delete Roles", style=discord.ButtonStyle.danger)
    async def confirm(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction
    ):
        deleted = 0

        for role in self.roles_to_delete:
            if role < self.ctx.guild.me.top_role:
                await role.delete(reason=f"Role cleanup by {self.ctx.author}")
                deleted += 1

        self.disable_all_items()

        success_embed = discord.Embed(
            title="✅ Role Cleanup Complete",
            description=f"Successfully deleted **{deleted}** unused role(s).",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        await interaction.response.edit_message(
            embed=success_embed,
            view=self
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction
    ):
        self.disable_all_items()

        cancel_embed = discord.Embed(
            title="❌ Role Cleanup Cancelled",
            description="No roles were deleted.",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )

        await interaction.response.edit_message(
            embed=cancel_embed,
            view=self
        )


# ─────────────────────────────────────────────
# Roles Cog
# ─────────────────────────────────────────────
class Roles(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # /roleinfo
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="roleinfo",
        description="View detailed information about a role"
    )
    async def roleinfo(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Role
    ):
        embed = discord.Embed(
            title="Role Information",
            color=role.color,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name="Name", value=role.name, inline=True)
        embed.add_field(name="Role ID", value=role.id, inline=True)
        embed.add_field(
            name="Created",
            value=f"<t:{int(role.created_at.timestamp())}:F>",
            inline=False
        )

        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)

        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Managed", value="Yes" if role.managed else "No", inline=True)

        await ctx.respond(embed=embed)

    # ─────────────────────────────────────────────
    # /rolemembers
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="rolemembers",
        description="List members that have a specific role"
    )
    @commands.has_permissions(manage_roles=True)
    async def rolemembers(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Role
    ):
        members = role.members
        count = len(members)

        if count == 0:
            await ctx.respond(
                f"No members currently have {role.mention}.",
                ephemeral=True
            )
            return

        display_limit = 25
        names = ", ".join(member.display_name for member in members[:display_limit])

        if count > display_limit:
            names += f", … (+{count - display_limit} more)"

        embed = discord.Embed(
            title=f"Members with {role.name}",
            description=names,
            color=role.color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Total members: {count}")

        await ctx.respond(embed=embed)

    # ─────────────────────────────────────────────
    # /roleadd
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="roleadd",
        description="Add a role to a user"
    )
    @commands.has_permissions(manage_roles=True)
    async def roleadd(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        role: discord.Role
    ):
        if role.name == "@everyone":
            await ctx.respond(
                "❌ The **@everyone** role cannot be assigned.",
                ephemeral=True
            )
            return

        if role.managed:
            await ctx.respond(
                "❌ This role is managed by an integration.",
                ephemeral=True
            )
            return

        if role >= ctx.guild.me.top_role:
            await ctx.respond(
                "❌ I cannot manage a role higher than or equal to my highest role.",
                ephemeral=True
            )
            return

        await user.add_roles(role, reason=f"Added by {ctx.author}")
        await ctx.respond(f"✅ {role.mention} added to {user.mention}")

    # ─────────────────────────────────────────────
    # /roleremove
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="roleremove",
        description="Remove a role from a user"
    )
    @commands.has_permissions(manage_roles=True)
    async def roleremove(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        role: discord.Role
    ):
        if role.name == "@everyone":
            await ctx.respond(
                "❌ The **@everyone** role cannot be removed.",
                ephemeral=True
            )
            return

        if role.managed:
            await ctx.respond(
                "❌ This role is managed by an integration.",
                ephemeral=True
            )
            return

        if role not in user.roles:
            await ctx.respond(
                "❌ That user does not have this role.",
                ephemeral=True
            )
            return

        await user.remove_roles(role, reason=f"Removed by {ctx.author}")
        await ctx.respond(f"✅ {role.mention} removed from {user.mention}")

    # ─────────────────────────────────────────────
    # /roleclone
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="roleclone",
        description="Clone an existing role"
    )
    @commands.has_permissions(administrator=True)
    async def roleclone(
        self,
        ctx: discord.ApplicationContext,
        source_role: discord.Role,
        new_name: str
    ):
        if source_role.managed:
            await ctx.respond(
                "❌ Managed roles cannot be cloned.",
                ephemeral=True
            )
            return

        new_role = await ctx.guild.create_role(
            name=new_name,
            permissions=source_role.permissions,
            colour=source_role.colour,
            hoist=source_role.hoist,
            mentionable=source_role.mentionable,
            reason=f"Cloned by {ctx.author}"
        )

        await ctx.respond(
            f"✅ Role `{source_role.name}` cloned as {new_role.mention}"
        )

    # ─────────────────────────────────────────────
    # /rolecleanup (buttons + confirmation)
    # ─────────────────────────────────────────────
    @discord.slash_command(
        name="rolecleanup",
        description="Delete roles with zero members (confirmation required)"
    )
    @commands.has_permissions(administrator=True)
    async def rolecleanup(self, ctx: discord.ApplicationContext):
        unused_roles = [
            role for role in ctx.guild.roles
            if role.name != "@everyone"
            and not role.managed
            and len(role.members) == 0
        ]

        if not unused_roles:
            await ctx.respond(
                "✅ No unused roles found.",
                ephemeral=True
            )
            return

        role_list = ", ".join(role.name for role in unused_roles[:15])
        if len(unused_roles) > 15:
            role_list += f", … (+{len(unused_roles) - 15} more)"

        embed = discord.Embed(
            title="⚠️ Role Cleanup Confirmation",
            description=(
                f"**Unused roles found ({len(unused_roles)}):**\n"
                f"{role_list}\n\n"
                "Do you want to permanently delete these roles?"
            ),
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        view = RoleCleanupConfirmView(ctx, unused_roles)

        await ctx.respond(embed=embed, view=view, ephemeral=True)

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def setup(bot: discord.Bot):
    bot.add_cog(Roles(bot))