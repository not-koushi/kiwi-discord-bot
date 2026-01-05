import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Check if Kiwi is online and running")
    async def ping(self, ctx):
        await ctx.respond(f"""Kiwi is currently active.
    `Latency: {round(self.bot.latency * 1000)} ms`
        """)

def setup(bot):
    bot.add_cog(General(bot))