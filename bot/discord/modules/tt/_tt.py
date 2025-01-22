import discord
from discord import ApplicationContext, slash_command
from discord.ext import commands, tasks
from pycord.multicog import subcommand

from bot.discord.helpers import permissions, command_utils
from bot.db import Database, Collection
from bot.db.models import GameStats, User
from bot.api import SMMOApi
from datetime import time, datetime, timezone, timedelta

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
    async def progress(self, ctx: ApplicationContext) -> None:
        tmp = await Database.select_one(Collection.USER.value,{"discord_id":ctx.user.id})
        if tmp is None:
            return await ctx.followup.send(content="You are not registered.")
        db_user = User(**tmp)
        gm_user = await SMMOApi.get_player_info(db_user.smmo_id)
        emb:discord.Embed = discord.Embed(title=f"{db_user.ign}'s progress", description=f"*Last Update*: <t:{int(datetime.now().timestamp())}:R>",color=int(self.config["DEFAULT"]["color"],16))
        date = command_utils.get_in_game_day()
        daily = await Database.select_one(Collection.STATS.value, {"smmo_id":db_user.smmo_id,"year":date.year,"month":date.month,"day":date.day})

        msg:str = ""
        perc = 0
        if self.config["REQUIREMENTS"]["daily_steps"] != "0":
            msg += f"**Steps**: {0 if daily is None else gm_user.steps - daily["steps"]}/{self.config["REQUIREMENTS"]["daily_steps"]}\n"
            if daily is not None:
                perc = ((gm_user.steps - daily["steps"])/int(self.config["REQUIREMENTS"]["daily_steps"])) * 10
        if self.config["REQUIREMENTS"]["daily_npc"] != "0":
            msg += f"**Npc Kills**: {0 if daily is None else gm_user.npc_kills - daily["npc"]}/{self.config["REQUIREMENTS"]["daily_npc"]}\n"
            if daily is not None:
                perc = max(((gm_user.npc_kills - daily["npc"])/int(self.config["REQUIREMENTS"]["daily_npc"])) * 10,perc)
        if self.config["REQUIREMENTS"]["daily_pvp"] != "0":
            msg += f"**Pvp Kills**: {0 if daily is None else gm_user.user_kills - daily["pvp"]}/{self.config["REQUIREMENTS"]["daily_pvp"]}\n"
            if daily is not None:
                perc = max(((gm_user.user_kills - daily["pvp"])/int(self.config["REQUIREMENTS"]["daily_pvp"])) * 10,perc)
        
        msg += f"[{"".join(":green_square:" if x+1<round(perc) else ":white_large_square:" for x in range(10))}] *{max(min(perc*10, 100), 0):.2f}*%"
        emb.add_field(name="Daily",value=msg,inline=False)
        
        w_date = date - timedelta(days=date.weekday())
        weekly = await Database.select_one(Collection.STATS.value, {"smmo_id":db_user.smmo_id,"year":w_date.year,"month":w_date.month,"day":w_date.day})

        msg:str = ""
        perc = 0
        if self.config["REQUIREMENTS"]["weekly_steps"] != "0":
            msg += f"**Steps**: {0 if weekly is None else gm_user.steps - weekly["steps"]}/{self.config["REQUIREMENTS"]["weekly_steps"]}\n"
            if weekly is not None:
                perc = ((gm_user.steps - weekly["steps"])/int(self.config["REQUIREMENTS"]["weekly_steps"])) * 10
        if self.config["REQUIREMENTS"]["weekly_npc"] != "0":
            msg += f"**Npc Kills**: {0 if weekly is None else gm_user.npc_kills - weekly["npc"]}/{self.config["REQUIREMENTS"]["weekly_npc"]}\n"
            if weekly is not None:
                perc = max(((gm_user.npc_kills - weekly["npc"])/int(self.config["REQUIREMENTS"]["weekly_npc"])) * 10,perc)
        if self.config["REQUIREMENTS"]["weekly_pvp"] != "0":
            msg += f"**Pvp Kills**: {0 if weekly is None else gm_user.user_kills - weekly["pvp"]}/{self.config["REQUIREMENTS"]["weekly_pvp"]}\n"
            if weekly is not None:
                perc = max(((gm_user.user_kills - weekly["pvp"])/int(self.config["REQUIREMENTS"]["weekly_pvp"])) * 10,perc)
                
        msg += f"[{"".join(":green_square:" if x+1<round(perc) else ":white_large_square:" for x in range(10))}] *{max(min(perc*10, 100), 0):.2f}*%"
        emb.add_field(name="Weekly",value=msg,inline=False)
        
        m_date = date
        if date.day > 28:
            m_date = m_date.replace(day=29)
        else:
            m_date -= timedelta(weeks=4)
            m_date = m_date.replace(day=29)

        monthly = await Database.select_one(Collection.STATS.value, {"smmo_id":db_user.smmo_id,"year":m_date.year,"month":m_date.month,"day":m_date.day})

        msg:str = ""
        perc = 0
        if self.config["REQUIREMENTS"]["monthly_steps"] != "0":
            msg += f"**Steps**: {0 if monthly is None else gm_user.steps - monthly["steps"]}/{self.config["REQUIREMENTS"]["monthly_steps"]}\n"
            if monthly is not None:
                perc = ((gm_user.steps - monthly["steps"])/int(self.config["REQUIREMENTS"]["monthly_steps"])) * 10
        if self.config["REQUIREMENTS"]["monthly_npc"] != "0":
            msg += f"**Npc Kills**: {0 if monthly is None else gm_user.npc_kills - monthly["npc"]}/{self.config["REQUIREMENTS"]["monthly_npc"]}\n"
            if monthly is not None:
                perc = max(((gm_user.npc_kills - monthly["npc"])/int(self.config["REQUIREMENTS"]["monthly_npc"])) * 10,perc)
        if self.config["REQUIREMENTS"]["monthly_pvp"] != "0":
            msg += f"**Pvp Kills**: {0 if monthly is None else gm_user.user_kills - monthly["pvp"]}/{self.config["REQUIREMENTS"]["monthly_pvp"]}\n"
            if monthly is not None:
                perc = max(((gm_user.user_kills - monthly["pvp"])/int(self.config["REQUIREMENTS"]["monthly_pvp"])) * 10,perc)
                
        msg += f"[{"".join(":green_square:" if x+1<round(perc) else ":white_large_square:" for x in range(10))}] *{max(min(perc*10, 100), 0):.2f}*%"
        emb.add_field(name="Monthly",value=msg,inline=False)

        await ctx.followup.send(embed=emb)
        
    @subcommand("tt")
    @slash_command(description="Register a user into TT system")
    @command_utils.auto_defer()
    @discord.guild_only()
    async def register(self, ctx: ApplicationContext, smmo_id: int) -> None:
        game_user = await SMMOApi.get_player_info(smmo_id)

        if game_user is None:
            return await ctx.followup.send(content="SMMO ID not found")
        db_user = {"ign":game_user.name,
                   "discord_id": ctx.user.id,
                   "smmo_id": game_user.id,
                   "ett": 0,
                   "btt": 0,
                   "daily": False,
                   "weekly": False,
                   "monthly": False}
        await Database.insert_one(Collection.USER.value,db_user)
        date = command_utils.get_in_game_day()
        await Database.insert_one(Collection.STATS.value,{"smmo_id": game_user.id   ,"steps": game_user.steps,"npc": game_user.npc_kills,"pvp": game_user.user_kills,"year": date.year,"month": date.month,"day": date.day})

        if game_user.guild.id is None or game_user.guild.id != int(self.config["DEFAULT"]["guild_id"]):
            return await ctx.followup.send(content=f"User '{game_user.name}' Added, but not found in the guild so the system won't work")
        await ctx.followup.send(content=f"User '{game_user.name}' Added")
def setup(client: discord.Bot):
    client.add_cog(TT(client))
