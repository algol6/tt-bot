import discord
from discord import ApplicationContext, slash_command
from discord.ext import commands, tasks
from pycord.multicog import subcommand

from bot.discord.helpers import permissions, command_utils
from bot.db import Database, Collection
from bot.db.models import GameStats, User
from bot.api import SMMOApi
from datetime import time, datetime, timezone, timedelta

from bot.discord.modules.tt._lb_view import LeaderBoardView

class TT(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client
        self.config = command_utils.get_config()

    def cog_unload(self) -> None:
        pass

    @subcommand("tt")
    @slash_command(description="Show your TT's balance")
    @command_utils.auto_defer(False)
    @discord.guild_only()
    async def balance(self, ctx: ApplicationContext) -> None:
        tmp = await Database.select_one(Collection.USER.value,{"discord_id":ctx.user.id})
        if tmp is None:
            return await ctx.followup.send(content="You are not registered.")
        db_user = User(**tmp)
        emb:discord.Embed = discord.Embed(title=f"{db_user.ign}'s TT Balance :bank:", description=f"*Last Update*: <t:{int(datetime.now().timestamp())}:R>",color=int(self.config["DEFAULT"]["color"],16))

        emb.add_field(name="ETT",value=f"{db_user.ett}",inline=True)
        emb.add_field(name="BTT",value=f"{db_user.btt}",inline=True)
        emb.add_field(name="Total TT",value=f"{db_user.ett + db_user.btt}",inline=False)
        emb.set_footer(text=f"")

        await ctx.followup.send(embed=emb)

    @subcommand("tt")
    @slash_command(description="Show your progress")
    @command_utils.auto_defer(False)
    @discord.guild_only()
    async def progress(self, ctx: ApplicationContext, user: discord.User = None) -> None:
        if user is None:
            user = ctx.user
        try:
            db_user = User(**(await Database.select_one(Collection.USER.value,{"discord_id":user.id})))
        except TypeError:
            return await ctx.followup.send(content="User not registered.")

        gm_user = await SMMOApi.get_player_info(db_user.smmo_id)
        emb:discord.Embed = discord.Embed(title=f"{db_user.ign}'s progress", description=f"*Last Update*: <t:{int(datetime.now().timestamp())}:R>",color=int(self.config["DEFAULT"]["color"],16))
        date = command_utils.get_in_game_day()
        reward_names:list[list[str]] = [["daily_steps","weekly_steps","monthly_steps"],["daily_npc","weekly_npc","monthly_npc"],["daily_pvp","weekly_pvp","monthly_pvp"]]
        time:list[datetime] = [date ,date - timedelta(days=date.weekday()),date.replace(day=28) if date.day > 28 or (date.day == 28 and date.hour >= 12) else (date - timedelta(weeks=4)).replace(day=28)]

        for i in range(3):
            msg:str = ""    
            perc:int = 0
            stat:dict|None = await Database.select_one(Collection.STATS.value, {"smmo_id":db_user.smmo_id,"year":time[i].year,"month":time[i].month,"day":time[i].day})
            if self.config["REQUIREMENTS"][reward_names[0][i]] != "0":
                try:
                    msg += f"**Steps**: {0 if stat is None else gm_user.steps - stat["steps"]}/{self.config["REQUIREMENTS"][reward_names[0][i]]}\n"
                except AttributeError:
                    pass
                try:
                    perc = ((gm_user.steps - stat["steps"])/int(self.config["REQUIREMENTS"][reward_names[0][i]])) * 10
                except KeyError:
                    pass
                except TypeError:
                    pass
            if self.config["REQUIREMENTS"][reward_names[1][i]] != "0":
                try:
                    msg += f"**Npc Kills**: {0 if stat is None else gm_user.npc_kills - stat["npc"]}/{self.config["REQUIREMENTS"][reward_names[1][i]]}\n"
                except AttributeError:
                    pass
                try:
                    perc = max(((gm_user.npc_kills - stat["npc"])/int(self.config["REQUIREMENTS"][reward_names[1][i]])) * 10,perc)
                except KeyError:
                    pass
                except TypeError:
                    pass
            if self.config["REQUIREMENTS"][reward_names[2][i]] != "0":
                try:
                    msg += f"**Pvp Kills**: {0 if stat is None else gm_user.user_kills - stat["pvp"]}/{self.config["REQUIREMENTS"][reward_names[2][i]]}\n"
                except AttributeError:
                    pass
                try:
                    perc = max(((gm_user.user_kills - stat["pvp"])/int(self.config["REQUIREMENTS"][reward_names[2][i]])) * 10,perc)
                except KeyError:
                    pass
                except TypeError:
                    pass
            msg += f"[{"".join(":green_square:" if x+1<round(perc) else ":white_large_square:" for x in range(10))}] *{max(min(perc*10, 100), 0):.2f}*%"
            emb.add_field(name=["Daily","Weekly","Monthly"][i],value=msg,inline=False)

        await ctx.followup.send(embed=emb)
        
        
    @subcommand("admin")
    @slash_command(description="Register a user into TT system")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def register(self, ctx: ApplicationContext, user: discord.User, smmo_id: int) -> None:
        game_user = await SMMOApi.get_player_info(smmo_id)
        db_user = await Database.select_one(Collection.USER.value,{"smmo_id":smmo_id})
        db_user2 = await Database.select_one(Collection.USER.value,{"discord_id":user.id})
        if db_user2 is not None:
            return await ctx.followup.send(content="User already registered")
        if db_user is not None:
            return await ctx.followup.send(content="SMMO ID already registered")
        if game_user is None:
            return await ctx.followup.send(content="SMMO ID not found")
        db_user = {"ign":game_user.name,
                   "discord_id": user.id,
                   "smmo_id": game_user.id,
                   "ett": 0,
                   "btt": 0,
                   "daily": False,
                   "weekly": False,
                   "monthly": False}
        await Database.insert_one(Collection.USER.value,db_user)
        date = command_utils.get_in_game_day()
        await Database.insert_one(Collection.STATS.value,{"smmo_id": game_user.id,"steps": game_user.steps,"npc": game_user.npc_kills,"pvp": game_user.user_kills,"year": date.year,"month": date.month,"day": date.day,"time":int(date.timestamp())})

        if game_user.guild.id is None or game_user.guild.id != int(self.config["DEFAULT"]["guild_id"]):
            return await ctx.followup.send(content=f"User '{game_user.name}' Added, but not found in the guild so the system won't work")
        await ctx.followup.send(content=f"User '{game_user.name}' Added")

    @subcommand("tt")
    @slash_command(description="Show TT leaderboard")
    @command_utils.auto_defer(False)
    @discord.guild_only()
    async def lb(self, ctx: ApplicationContext, more_info:bool = False) -> None:
        users = await Database.select(Collection.USER.value)
        view = LeaderBoardView()

        view.users = sorted(users, key=lambda item: item["ett"]+item["btt"],reverse=True)
        view.more_info = more_info
        view.color = int(self.config["DEFAULT"]["color"],16)

        await view.send(ctx)


def setup(client: discord.Bot):
    client.add_cog(TT(client))
