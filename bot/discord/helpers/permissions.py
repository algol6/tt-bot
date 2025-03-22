import functools
from discord import ApplicationContext
from bot.db import Database
from bot.api import SMMOApi
from bot.discord.helpers import command_utils



async def is_admin_or_staff(ctx: ApplicationContext) -> bool:
    # user = await Database2.select_one(Collection.USER.value, {"discord_id":ctx.author.id})
    user = await Database.select_user_discord(ctx.author.id)
    if user is None:
        return False
    game_users = await SMMOApi.get_guild_members(int(command_utils.get_config()["DEFAULT"]["guild_id"]))
    if game_users is None:
        return False
    return any(user.smmo_id == x.user_id and x.position != "Member" for x in game_users)

def require_admin_or_staff():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if len(args) >= 2 and isinstance(args[1], ApplicationContext):
                ctx: ApplicationContext = args[1]
                if not await is_admin_or_staff(ctx):
                    await ctx.respond(
                        content="You do not have permission to run this command",
                        ephemeral=True
                    )
                    return
            return await func(*args, **kwargs)
        return wrapped
    return wrapper
