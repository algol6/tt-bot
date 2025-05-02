import discord
from os import getenv
from pycord.multicog import Bot
from bot.db._database import Database

intent = discord.Intents.default()
client = Bot(intents=intent, activity=discord.Activity(name=getenv("DISCORD_ACTIVITY"), type=discord.ActivityType.watching))

client.load_extension("bot.discord.modules.command_groups")
client.load_extension("bot.discord.modules.admin")
client.load_extension("bot.discord.modules.tt")

@client.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    await ctx.respond("Unexpected error. Try again later.")
    from datetime import datetime
    if ctx.guild is not None:
        print(f"[{datetime.now()}]ERROR from: #{ctx.channel.name}")
    await Database.insert_log(error,datetime.now())
    print(error)


def run() -> None:
    import asyncio
    asyncio.run(Database.create_table())
    client.run(getenv("DISCORD_TOKEN"))
