import functools
from configparser import ConfigParser
from discord import ApplicationContext
from datetime import datetime, timezone, timedelta

def auto_defer(ephemeral: bool = True):
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if len(args) >= 2 and isinstance(args[1], ApplicationContext):
                ctx: ApplicationContext = args[1]
                await ctx.defer(ephemeral=ephemeral)

            return await func(*args, **kwargs)
        return wrapped
    return wrapper

def get_config() -> list[str]:
    config = ConfigParser()
    config.read("config.ini")
    return config

def get_in_game_day() -> datetime:
    da:datetime = datetime.now(tz=timezone.utc)
    return da.replace(hour=12, minute=0, second=0, microsecond=0) if da.hour >= 12 else da.replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(days=1)