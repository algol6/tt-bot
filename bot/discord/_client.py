from os import getenv
import discord
from pycord.multicog import Bot
from bot.db import Database
import asyncio

intent = discord.Intents.default()
client = Bot(intents=intent, activity=discord.Activity(name=getenv("DISCORD_ACTIVITY"), type=discord.ActivityType.playing))

client.load_extension("bot.discord.modules.command_groups")
client.load_extension("bot.discord.modules.admin")

@client.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    await ctx.respond("Unexpected error. Try again later.\nIf keep getting this error please report to Algol https://discord.gg/bPRJkpnySB")
    from datetime import datetime
    if ctx.guild is not None:
        print(f"[{datetime.now()}]ERROR from: [{ctx.guild.name}] #{ctx.channel.name}")
    print(error)


def run() -> None:
    try:
        asyncio.run(Database.create_table())
    except Exception as e:
        print(e)
    client.run(getenv("DISCORD_TOKEN"))
