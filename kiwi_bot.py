import discord
import os
from datetime import datetime, timezone

import logging
import traceback

from config import TOKEN

# Intents
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
intents.guilds = True
intents.messages = True

# ─────────────────────────────────────────────
bot = discord.Bot(intents=intents)

BOT_START_TIME = datetime.now(timezone.utc)
# ─────────────────────────────────────────────


# Error Logging Setup
# ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("kiwi-errors")
logger.setLevel(logging.ERROR)

file_handler = logging.FileHandler(
    "logs/errors.log",
    encoding="utf-8"
)
file_handler.setLevel(logging.ERROR)

formatter = logging.Formatter(
    "%(asctime)s UTC\n"
    "Guild: %(guild)s\n"
    "User: %(user)s\n"
    "Command: %(command)s\n"
    "Error:\n%(message)s\n"
    "────────────────────────────────────────────\n"
)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# ─────────────────────────────────────────────


# Bot ready
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"""
 █████   ████  ███                   ███ 
░░███   ███░  ░░░                   ░░░  
 ░███  ███    ████  █████ ███ █████ ████ 
 ░███████    ░░███ ░░███ ░███░░███ ░░███ 
 ░███░░███    ░███  ░███ ░███ ░███  ░███ 
 ░███ ░░███   ░███  ░░███████████   ░███ 
 █████ ░░████ █████  ░░████░████    █████
░░░░░   ░░░░ ░░░░░    ░░░░ ░░░░    ░░░░░  
""")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Timestamp: {current_time}")
    print(f"Servers  : {len(bot.guilds)}")
    print(f"Latency  : {round(bot.latency * 1000)} ms")
    print("Initialization complete")
    print(f"Standing by as {bot.user}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# ─────────────────────────────────────────────


# Global Slash Command Error Handler
# ─────────────────────────────────────────────
@bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext,
    error: Exception
):
    # Ignore harmless errors
    if isinstance(error, (discord.Forbidden, discord.NotFound)):
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    guild_name = ctx.guild.name if ctx.guild else "DM"
    guild_id = ctx.guild.id if ctx.guild else "N/A"

    # Minimal terminal output
    print(f"[{timestamp}] ERROR in Guild: {guild_name} ({guild_id})")

    # Full traceback
    tb = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )

    logger.error(
        tb,
        extra={
            "guild": f"{guild_name} ({guild_id})",
            "user": f"{ctx.author} ({ctx.author.id})",
            "command": ctx.command.name if ctx.command else "Unknown"
        }
    )

    # Safe user-facing message
    try:
        await ctx.respond(
            "❌ An unexpected error occurred while executing this command.\n"
            "The issue has been logged and will be reviewed.",
            ephemeral=True
        )
    except discord.InteractionResponded:
        pass
# ─────────────────────────────────────────────


# Load all cogs
# ─────────────────────────────────────────────
for file in os.listdir("./cogs"):
    if file.endswith(".py") and not file.startswith("_"):
        bot.load_extension(f"cogs.{file[:-3]}")
# ─────────────────────────────────────────────


bot.run(TOKEN)