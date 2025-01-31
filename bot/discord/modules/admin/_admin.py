import discord
from discord import ApplicationContext, slash_command
from discord.ext import commands, tasks
from pycord.multicog import subcommand

from bot.discord.helpers import permissions, command_utils
from bot.db import Database, Collection
from bot.db.models import GameStats, User
from bot.api import SMMOApi
from datetime import time, datetime, timezone, timedelta

class Admin(commands.Cog):
    def __init__(self, client) -> None:
        self.config = command_utils.get_config()
        self.client = client
        self.save_stats.start()
        self.check_stats.start()
        self.check_lb.start()

    def cog_unload(self) -> None:
        self.save_stats.cancel()
        self.check_stats.cancel()
        self.check_lb.cancel()

    @subcommand("admin")
    @slash_command(description="Give BTT to one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def gbtt(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        tmp = await Database.select_one(Collection.USER.value,{"discord_id":user.id})
        if tmp is None:
            return await ctx.followup.send(content="The user isn't registered.")
        db_user:User = User(**tmp)

        db_user.btt += amount

        await Database.update_one(Collection.USER.value,db_user.as_dict(),db_user.as_dict())
        await ctx.followup.send(content="BTT Added")


    @subcommand("admin")
    @slash_command(description="Remove BTT from one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def rbtt(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        tmp = await Database.select_one(Collection.USER.value,{"discord_id":user.id})
        if tmp is None:
            return await ctx.followup.send(content="The user isn't registered.")
        db_user = User(**tmp)

        db_user.btt -= amount

        await Database.update_one(Collection.USER.value,db_user.as_dict(),db_user.as_dict())
        await ctx.followup.send(content="BTT Removed")


    @subcommand("admin")
    @slash_command(description="Give ETT to one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def gett(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        tmp = await Database.select_one(Collection.USER.value,{"discord_id":user.id})
        if tmp is None:
            return await ctx.followup.send(content="The user isn't registered.")
        db_user = User(**tmp)

        db_user.ett += amount

        await Database.update_one(Collection.USER.value,db_user.as_dict(),db_user.as_dict())
        await ctx.followup.send(content="ETT Added")


    @subcommand("admin")
    @slash_command(description="Remove ETT from one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def rett(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        tmp = await Database.select_one(Collection.USER.value,{"discord_id":user.id})
        if tmp is None:
            return await ctx.followup.send(content="The user isn't registered.")
        db_user = User(**tmp)

        db_user.ett -= amount

        await Database.update_one(Collection.USER.value,db_user.as_dict(),db_user.as_dict())
        await ctx.followup.send(content="ETT Removed")


    @subcommand("admin")
    @slash_command(description="Start event")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    @discord.option(name="multipler", description="multiply the gains by x times")
    async def start_event(self, ctx: ApplicationContext, multipler: int) -> None:
        cfn = await Database.select_one(Collection.CONFIG.value,{"mult":{"$exists":True}})
        if cfn is not None and cfn["mult"] != 1:
            return await ctx.followup.send("Event already on.")
        cfn["mult"] = multipler
        await Database.update_one(Collection.CONFIG.value,cfn,cfn)
        await ctx.followup.send("Done")


    @subcommand("admin")
    @slash_command(description="End event")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def end_event(self, ctx: ApplicationContext, multipler: int) -> None:
        cfn = await Database.select_one(Collection.CONFIG.value,{"mult":multipler})
        if cfn is None:
            return await ctx.followup.send("No Events on.")
        cfn["mult"] = 1
        await Database.update_one(Collection.CONFIG.value,cfn,cfn)
        await ctx.followup.send("Done")

    @subcommand("admin")
    @slash_command(description="Select notification channel")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def notification_channel(self, ctx: ApplicationContext, channel: discord.TextChannel) -> None:
        try:
            ch = await self.client.fetch_channel(channel.id)
            await ch.send(content="test message.", delete_after=1)
        except discord.errors.Forbidden:
            return await ctx.followup.send(content="Bot doesn't have the perms to see/write the channel.")
        
        await Database.insert_one(Collection.CONFIG.value, {"channel_id":channel.id})
        await Database.insert_one(Collection.CONFIG.value, {"mult":1})
        await ctx.followup.send("Done")
    
    @tasks.loop(time=time(hour=12))
    async def save_stats(self):
        guild_member = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))

        date = command_utils.get_in_game_day()

        await Database.insert(Collection.STATS.value, [{"smmo_id": member.user_id,"steps": member.steps,"npc": member.npc_kills,"pvp": member.user_kills,"year": date.year,"month": date.month,"day": date.day, "time":date.timestamp()} for member in guild_member])

        users = await Database.select(Collection.USER.value)
        for member in guild_member:
            for user in users:
                if user["smmo_id"] != member.user_id:
                    continue
                tmp_u = User(**user)
                await Database.update_one_user_reward_status(tmp_u,"daily",False)
                if datetime.today().weekday() == 0:
                    await Database.update_one_user_reward_status(tmp_u,"weekly",False)
                if datetime.today().day == 28:
                    await Database.update_one_user_reward_status(tmp_u,"monthly",False)


    @tasks.loop(minutes=30)
    async def check_stats(self):
        guild_member = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        date = command_utils.get_in_game_day()
        cnf = await Database.select_one(Collection.CONFIG.value,{"channel_id":{"$exists":True}})
        cnf2 = await Database.select_one(Collection.CONFIG.value,{"mult":{"$exists":True}})
        for member in guild_member:
            user = await Database.select_one(Collection.USER.value,{"smmo_id":member.user_id})
            if user is None:
                continue

            user = User(**user)
            try:
                daily_stats = GameStats(**(await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date.year,"month":date.month,"day":date.day})))
            except TypeError:
                continue
            if not user.daily and ((int(self.config["REQUIREMENTS"]["daily_steps"]) != 0 and member.steps - daily_stats.steps >= int(self.config["REQUIREMENTS"]["daily_steps"]))
                                    or (int(self.config["REQUIREMENTS"]["daily_npc"]) != 0 and member.npc_kills - daily_stats.npc >= int(self.config["REQUIREMENTS"]["daily_npc"]))
                                    or (int(self.config["REQUIREMENTS"]["daily_pvp"]) != 0 and member.user_kills - daily_stats.pvp >= int(self.config["REQUIREMENTS"]["daily_pvp"]))):
                user.daily = True
                user.ett += int(self.config["REWARDS"]["daily_reward"]) * (int(cnf2["mult"]) if cnf2 is not None else 1)
                await Database.update_one(Collection.USER.value,user.as_dict(),user.as_dict())
                if cnf is not None:
                    try:
                        channel = await self.client.fetch_channel(cnf["channel_id"])
                        emb:discord.Embed = discord.Embed(title=f"Daily Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
                        emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{user.discord_id}> did it! your efforts are rewarded. +{int(self.config["REWARDS"]["daily_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)} ETT")
                        await channel.send(embed=emb)
                    except discord.errors.NotFound:
                        print("Channel not found.")
                    except discord.errors.Forbidden:
                        print("Can't see/write on the channel")

            date_temp = date - timedelta(days=1)
         
            try:
                weekly_stats = GameStats(**(await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date_temp.year,"month":date_temp.month,"day":date_temp.day})))
            except TypeError:
                continue
            if not user.weekly and ((int(self.config["REQUIREMENTS"]["weekly_steps"]) != 0 and member.steps - weekly_stats.steps >= int(self.config["REQUIREMENTS"]["weekly_steps"]))
                                    or (int(self.config["REQUIREMENTS"]["weekly_npc"]) != 0 and member.npc_kills - weekly_stats.npc >= int(self.config["REQUIREMENTS"]["weekly_npc"]))
                                    or (int(self.config["REQUIREMENTS"]["weekly_pvp"]) != 0 and member.user_kills - weekly_stats.pvp >= int(self.config["REQUIREMENTS"]["weekly_pvp"]))):
                user.weekly = True
                user.ett += int(self.config["REWARDS"]["weekly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)
                await Database.update_one(Collection.USER.value,user.as_dict(),user.as_dict())
                if cnf is not None:
                    try:
                        channel = await self.client.fetch_channel(cnf["channel_id"])
                        emb:discord.Embed = discord.Embed(title=f"Weekly Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
                        emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{user.discord_id}> did it! your efforts are rewarded. +{int(self.config["REWARDS"]["weekly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)} ETT")
                        await channel.send(embed=emb)
                    except discord.errors.NotFound:
                        print("Channel not found.")
                    except discord.errors.Forbidden:
                        print("Can't see/write on the channel")
            date_temp = date - timedelta(weeks=4)
            try:
                monthly_stats = GameStats(**(await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date_temp.year,"month":date_temp.month,"day":date_temp.day})))
            except TypeError:
                continue
            if not user.monthly and ((int(self.config["REQUIREMENTS"]["monthly_steps"]) != 0 and member.steps - monthly_stats.steps >= int(self.config["REQUIREMENTS"]["monthly_steps"]))
                                     or (int(self.config["REQUIREMENTS"]["monthly_npc"]) != 0 and member.npc_kills - monthly_stats.npc >= int(self.config["REQUIREMENTS"]["monthly_npc"]))
                                     or (int(self.config["REQUIREMENTS"]["monthly_pvp"]) != 0 and member.user_kills - monthly_stats.pvp >= int(self.config["REQUIREMENTS"]["monthly_pvp"]))):
                user.monthly = True
                user.ett += int(self.config["REWARDS"]["monthly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)
                await Database.update_one(Collection.USER.value,user.as_dict(),user.as_dict())
                
                if cnf is not None:
                    try:
                        channel = await self.client.fetch_channel(cnf["channel_id"])
                        emb:discord.Embed = discord.Embed(title=f"Monthly Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
                        emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{user.discord_id}> did it! your efforts are rewarded. +{int(self.config["REWARDS"]["monthly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)} ETT")
                        await channel.send(embed=emb)
                    except discord.errors.NotFound:
                        print("Channel not found.")
                    except discord.errors.Forbidden:
                        print("Can't see/write on the channel")

    @tasks.loop(time=time(hour=12))
    async def check_lb(self):
        # get guild member
        guild_member = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        date = command_utils.get_in_game_day()
        cnf2 = await Database.select_one(Collection.CONFIG.value,{"mult"})

        lbs_npc = [[],[],[]]
        lbs_stp = [[],[],[]]
        lbs_pvp = [[],[],[]]
        # for each member do some checks:
        for member in guild_member:
            # check if member is registered; if not no reward!
            user = await Database.select_one(Collection.USER.value,{"smmo_id":member.user_id})
            if user is None:
                continue

            # if member registered take daily stats
            user = User(**user)
            daily_stats = await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date.year,"month":date.month,"day":date.day})
            if daily_stats is None:
                continue
            daily_stats = GameStats(**daily_stats)
            lbs_npc[0].append({"user":user,"stats":member.npc_kills - daily_stats.npc})
            lbs_stp[0].append({"user":user,"stats":member.steps - daily_stats.steps})
            lbs_pvp[0].append({"user":user,"stats":member.user_kills - daily_stats.pvp})

            # if not monday do not check for weekly rewards
            if datetime.today().weekday() != 0:
                continue
            date_temp = date - timedelta(days=1)
            weekly_stats = await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date_temp.year,"month":date_temp.month,"day":date_temp.day})
            if weekly_stats is None:
                continue
            lbs_npc[1].append({"user":user,"stats":member.npc_kills - weekly_stats.npc})
            lbs_stp[1].append({"user":user,"stats":member.steps - weekly_stats.steps})
            lbs_pvp[1].append({"user":user,"stats":member.user_kills - weekly_stats.pvp})
            
            # if not on server reset (28th) do not check for monthly reward
            if datetime.today().day != 28:
                continue
            date_temp = date - timedelta(weeks=4)
            monthly_stats = await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date_temp.year,"month":date_temp.month,"day":date_temp.day})
            if monthly_stats is None:
                continue
            lbs_npc[2].append({"user":user,"stats":member.npc_kills - monthly_stats.npc})
            lbs_stp[2].append({"user":user,"stats":member.steps - monthly_stats.steps})
            lbs_pvp[2].append({"user":user,"stats":member.user_kills - monthly_stats.pvp})
        
        # do a lb for each category/timeframe
        lbs_npc = [
            sorted(lbs_npc[0], key=lambda item: -item["stats"]),
            sorted(lbs_npc[1], key=lambda item: -item["stats"]),
            sorted(lbs_npc[2], key=lambda item: -item["stats"])
        ]
        lbs_stp = [
            sorted(lbs_stp[0], key=lambda item: -item["stats"]),
            sorted(lbs_stp[1], key=lambda item: -item["stats"]),
            sorted(lbs_stp[2], key=lambda item: -item["stats"])
        ]
        lbs_pvp = [
            sorted(lbs_pvp[0], key=lambda item: -item["stats"]),
            sorted(lbs_pvp[1], key=lambda item: -item["stats"]),
            sorted(lbs_pvp[2], key=lambda item: -item["stats"])
        ]

        # and finally give the reward to the top player of the day/week/month
        names = ["LEADERBOARD.daily","LEADERBOARD.weekly","LEADERBOARD.monthly"]
        for i in range(3):
            for us,rew in zip(lbs_npc[i],self.config[names[i]]):
                us["user"].ett += rew * (cnf2["mult"] if cnf2 is not None else 1)
                await Database.update_one(Collection.USER.value,us["user"],us["user"])

            for us,rew in zip(lbs_stp[i],self.config[names[i]]):
                us["user"].ett += rew * (cnf2["mult"] if cnf2 is not None else 1)
                await Database.update_one(Collection.USER.value,us["user"],us["user"])

            for us,rew in zip(lbs_pvp[i],self.config[names[i]]):
                us["user"].ett += rew * (cnf2["mult"] if cnf2 is not None else 1)
                await Database.update_one(Collection.USER.value,us["user"],us["user"])

def setup(client: discord.Bot):
    client.add_cog(Admin(client))
