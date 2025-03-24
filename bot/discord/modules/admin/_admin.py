import discord
from discord import ApplicationContext, slash_command
from discord.ext import commands, tasks
from pycord.multicog import subcommand

from bot.discord.helpers import permissions, command_utils
from bot.db import Database
from bot.db.models import GameStats, User
from bot.api import SMMOApi
from bot.api.model import GuildMemberInfo
from datetime import time, datetime, timezone, timedelta

class Admin(commands.Cog):
    def __init__(self, client) -> None:
        self.config = command_utils.get_config()
        self.client = client
        self.save_stats.start()
        self.check_stats.start()
        self.check_lb.start()
        self.save_stats_reset.start()

    def cog_unload(self) -> None:
        self.save_stats.cancel()
        self.check_stats.cancel()
        self.check_lb.cancel()
        self.save_stats_reset.cancel()


    # @subcommand("admin")
    # @slash_command()
    # @command_utils.auto_defer()
    # @discord.guild_only()
    # @permissions.require_admin_or_staff()
    # async def migrate(self, ctx: ApplicationContext) -> None:
    #     config = await Database2.select(Collection.CONFIG.value)
    #     users = await Database2.select(Collection.USER.value)
    #     stats = await Database2.select(Collection.STATS.value)

    #     await Database.create_table()
    #     for c in config:
    #         if "channel_id" in c:
    #             await Database.insert_config("chid",c["channel_id"])
    #         if "mult" in c:
    #             await Database.insert_config("mult",1)

    #     for u in users:
    #         await Database.insert_user(u["discord_id"],u["smmo_id"],u["ign"],u["ett"],u["btt"],u["daily"],u["weekly"],u["monthly"])
            
    #     for s in stats:
    #         await Database.insert_stats(s["smmo_id"],s["steps"],s["npc"],s["pvp"],datetime(s["year"],s["month"],s["day"],hour=12,minute=0,microsecond=0,tzinfo=timezone.utc))

    #     await ctx.followup.send("DONE")

    @subcommand("admin")
    @slash_command(description="Give BTT to one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def gbtt(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        db_user = await Database.select_user_discord(user.id)
        if db_user is None:
            return await ctx.followup.send(content="The user isn't registered.")

        db_user.btt += amount

        await Database.update_user(db_user.discord_id,db_user.ign,db_user.ett,db_user.btt,db_user.daily,db_user.weekly,db_user.monthly)
        await ctx.followup.send(content="BTT Added")


    @subcommand("admin")
    @slash_command(description="Remove BTT from one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def rbtt(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        db_user = await Database.select_user_discord(user.id)
        if db_user is None:
            return await ctx.followup.send(content="The user isn't registered.")

        db_user.btt -= amount

        await Database.update_user(db_user.discord_id,db_user.ign,db_user.ett,db_user.btt,db_user.daily,db_user.weekly,db_user.monthly)
        await ctx.followup.send(content="BTT Removed")


    @subcommand("admin")
    @slash_command(description="Give ETT to one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def gett(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        db_user = await Database.select_user_discord(user.id)
        if db_user is None:
            return await ctx.followup.send(content="The user isn't registered.")

        db_user.ett += amount

        await Database.update_user(db_user.discord_id,db_user.ign,db_user.ett,db_user.btt,db_user.daily,db_user.weekly,db_user.monthly)
        await ctx.followup.send(content="ETT Added")


    @subcommand("admin")
    @slash_command(description="Remove ETT from one user")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def rett(self, ctx: ApplicationContext, user: discord.User, amount: int) -> None:
        db_user = await Database.select_user_discord(user.id)
        if db_user is None:
            return await ctx.followup.send(content="The user isn't registered.")

        db_user.ett -= amount

        await Database.update_user(db_user.discord_id,db_user.ign,db_user.ett,db_user.btt,db_user.daily,db_user.weekly,db_user.monthly)
        await ctx.followup.send(content="ETT Removed")


    @subcommand("admin")
    @slash_command(description="Start event")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    @discord.option(name="multipler", description="multiply the gains by x times")
    async def start_event(self, ctx: ApplicationContext, multipler: int) -> None:
        cfn = await Database.select_config("mult")
        if cfn is not None or cfn.value != 1:
            return await ctx.followup.send("Event already on.")
        cfn.value = multipler
        await Database.update_config(cfn.name,cfn.value)
        await ctx.followup.send("Done")


    @subcommand("admin")
    @slash_command(description="End event")
    @command_utils.auto_defer()
    @discord.guild_only()
    @permissions.require_admin_or_staff()
    async def end_event(self, ctx: ApplicationContext, multipler: int) -> None:
        cfn = await Database.select_config("mult")
        if cfn is None or cfn.value == 1:
            return await ctx.followup.send("No Events on.")
        cfn.value = 1
        await Database.update_config(cfn.name,cfn.value)
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
        
        if not await Database.insert_config("chid",channel.id):
            await Database.update_config("chid",channel.id)

        await ctx.followup.send("Done")
    
    @tasks.loop(time=time(hour=12))
    async def save_stats_reset(self):
        self.check_stats.cancel()
        self.check_lb.cancel()
        guild_member:list[GuildMemberInfo] = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        date:datetime = command_utils.get_in_game_day()
        users = await Database.select_user_all()
        for member in guild_member:
            if not await Database.insert_stats(member.user_id,member.steps,member.npc_kills,member.user_kills,date):
                continue
            for user in users:
                if user.smmo_id != member.user_id:
                    continue
                user.daily = False
                if datetime.today().weekday() == 0:
                    user.weekly = False
                if datetime.today().day == 28:
                    user.monthly = False
                await Database.update_user(user.discord_id,member.name,user.ett,user.btt,user.daily,user.weekly,user.monthly)
        date -= timedelta(weeks=5)
        await Database.delete_stats(date)
        self.check_stats.start()
        self.check_lb.start()

    @tasks.loop(hours=1)
    async def save_stats(self):
        self.check_stats.cancel()
        self.check_lb.cancel()
        guild_member:list[GuildMemberInfo] = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        date:datetime = command_utils.get_in_game_day()
        users = await Database.select_user_all()
        for member in guild_member:
            if not await Database.insert_stats(member.user_id,member.steps,member.npc_kills,member.user_kills,date):
                continue
            for user in users:
                if user.smmo_id != member.user_id:
                    continue
                user.daily = False
                if datetime.today().weekday() == 0:
                    user.weekly = False
                if datetime.today().day == 28:
                    user.monthly = False
                await Database.update_user(user.discord_id,member.name,user.ett,user.btt,user.daily,user.weekly,user.monthly)
        date -= timedelta(weeks=5)
        await Database.delete_stats(date)
        self.check_stats.start()
        self.check_lb.start()


    @tasks.loop(minutes=15)
    async def check_stats(self):
        guild_member = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        cnf = await Database.select_config("chid")
        cnf2 = await Database.select_config("mult")
        reward_names:list[list[str]] = [["daily_steps","weekly_steps","monthly_steps"],["daily_npc","weekly_npc","monthly_npc"],["daily_pvp","weekly_pvp","monthly_pvp"]]
        reward:list[str] = ["daily_reward","weekly_reward","monthly_reward"]
        date = command_utils.get_in_game_day()
        time:list[datetime] = [date,date - timedelta(days=7),date - timedelta(weeks=4)]

        for member in guild_member:
            user = await Database.select_user_smmoid(member.user_id)
            if user is None:
                continue
            reward_got:list[bool] = [user.daily,user.weekly,user.weekly]
            for i in range(3):
                stats = await Database.select_stats(member.user_id,time[i])
                if stats is None:
                    continue
                if not reward_got[i] and ((int(self.config["REQUIREMENTS"][reward_names[0][i]]) != 0 and member.steps - stats.steps >= int(self.config["REQUIREMENTS"][reward_names[0][i]]))
                                        or (int(self.config["REQUIREMENTS"][reward_names[1][i]]) != 0 and member.npc_kills - stats.npc >= int(self.config["REQUIREMENTS"][reward_names[1][i]]))
                                        or (int(self.config["REQUIREMENTS"][reward_names[2][i]]) != 0 and member.user_kills - stats.pvp >= int(self.config["REQUIREMENTS"][reward_names[2][i]]))):
                    if i == 0:
                        user.daily = True
                    elif i == 1:
                        user.weekly = True
                    elif i == 2:
                        user.weekly = True

                    user.ett += int(self.config["REWARDS"][reward[i]]) * (int(cnf2.value) if cnf2 is not None else 1)
                    await Database.update_user(user.discord_id,member.name,user.ett,user.btt,user.daily,user.weekly,user.monthly)
                    if cnf is not None:
                        if int(self.config["REWARDS"][reward[i]]) == 0:
                            continue
                        try:
                            channel = await self.client.fetch_channel(int(cnf.value))
                            emb:discord.Embed = discord.Embed(title=f"{["Daily","Weekly","Monthly"][i]} Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
                            emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{int(user.discord_id)}> did it! your efforts are rewarded. +{int(self.config["REWARDS"][reward[i]]) * (int(cnf2.value) if cnf2 is not None else 1)} ETT")
                            await channel.send(embed=emb)
                        except discord.errors.NotFound:
                            print("Channel not found.")
                        except discord.errors.Forbidden:
                            print("Can't see/write on the channel")
                            
        # guild_member = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        # date = command_utils.get_in_game_day()
        # cnf = await Database.select_one(Collection.CONFIG.value,{"channel_id":{"$exists":True}})
        # cnf2 = await Database.select_one(Collection.CONFIG.value,{"mult":{"$exists":True}})
        # for member in guild_member:
        #     try:
        #         user = User(**(await Database.select_one(Collection.USER.value,{"smmo_id":member.user_id})))
        #     except TypeError:
        #         continue
        #     try:
        #         daily_stats = GameStats(**(await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date.year,"month":date.month,"day":date.day})))
        #     except TypeError:
        #         continue
        #     if not user.daily and ((int(self.config["REQUIREMENTS"]["daily_steps"]) != 0 and member.steps - daily_stats.steps >= int(self.config["REQUIREMENTS"]["daily_steps"]))
        #                             or (int(self.config["REQUIREMENTS"]["daily_npc"]) != 0 and member.npc_kills - daily_stats.npc >= int(self.config["REQUIREMENTS"]["daily_npc"]))
        #                             or (int(self.config["REQUIREMENTS"]["daily_pvp"]) != 0 and member.user_kills - daily_stats.pvp >= int(self.config["REQUIREMENTS"]["daily_pvp"]))):
        #         user.daily = True
        #         user.ett += int(self.config["REWARDS"]["daily_reward"]) * (int(cnf2["mult"]) if cnf2 is not None else 1)
        #         await Database.update_one(Collection.USER.value,user.as_dict(),user.as_dict())
        #         if cnf is not None:
        #             try:
        #                 channel = await self.client.fetch_channel(cnf["channel_id"])
        #                 emb:discord.Embed = discord.Embed(title=f"Daily Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
        #                 emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{user.discord_id}> did it! your efforts are rewarded. +{int(self.config["REWARDS"]["daily_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)} ETT")
        #                 await channel.send(embed=emb)
        #             except discord.errors.NotFound:
        #                 print("Channel not found.")
        #             except discord.errors.Forbidden:
        #                 print("Can't see/write on the channel")

        #     date_temp = date - timedelta(days=1)
         
        #     try:
        #         weekly_stats = GameStats(**(await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date_temp.year,"month":date_temp.month,"day":date_temp.day})))
        #     except TypeError:
        #         continue
        #     if not user.weekly and ((int(self.config["REQUIREMENTS"]["weekly_steps"]) != 0 and member.steps - weekly_stats.steps >= int(self.config["REQUIREMENTS"]["weekly_steps"]))
        #                             or (int(self.config["REQUIREMENTS"]["weekly_npc"]) != 0 and member.npc_kills - weekly_stats.npc >= int(self.config["REQUIREMENTS"]["weekly_npc"]))
        #                             or (int(self.config["REQUIREMENTS"]["weekly_pvp"]) != 0 and member.user_kills - weekly_stats.pvp >= int(self.config["REQUIREMENTS"]["weekly_pvp"]))):
        #         user.weekly = True
        #         user.ett += int(self.config["REWARDS"]["weekly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)
        #         await Database.update_one(Collection.USER.value,user.as_dict(),user.as_dict())
        #         if cnf is not None:
        #             try:
        #                 channel = await self.client.fetch_channel(cnf["channel_id"])
        #                 emb:discord.Embed = discord.Embed(title=f"Weekly Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
        #                 emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{user.discord_id}> did it! your efforts are rewarded. +{int(self.config["REWARDS"]["weekly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)} ETT")
        #                 await channel.send(embed=emb)
        #             except discord.errors.NotFound:
        #                 print("Channel not found.")
        #             except discord.errors.Forbidden:
        #                 print("Can't see/write on the channel")
        #     date_temp = date - timedelta(weeks=4)
        #     try:
        #         monthly_stats = GameStats(**(await Database.select_one(Collection.STATS.value, {"smmo_id":member.user_id,"year":date_temp.year,"month":date_temp.month,"day":date_temp.day})))
        #     except TypeError:
        #         continue
        #     if not user.monthly and ((int(self.config["REQUIREMENTS"]["monthly_steps"]) != 0 and member.steps - monthly_stats.steps >= int(self.config["REQUIREMENTS"]["monthly_steps"]))
        #                              or (int(self.config["REQUIREMENTS"]["monthly_npc"]) != 0 and member.npc_kills - monthly_stats.npc >= int(self.config["REQUIREMENTS"]["monthly_npc"]))
        #                              or (int(self.config["REQUIREMENTS"]["monthly_pvp"]) != 0 and member.user_kills - monthly_stats.pvp >= int(self.config["REQUIREMENTS"]["monthly_pvp"]))):
        #         user.monthly = True
        #         user.ett += int(self.config["REWARDS"]["monthly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)
        #         await Database.update_one(Collection.USER.value,user.as_dict(),user.as_dict())
                
        #         if cnf is not None:
        #             try:
        #                 channel = await self.client.fetch_channel(cnf["channel_id"])
        #                 emb:discord.Embed = discord.Embed(title=f"Monthly Quota Reached!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
        #                 emb.add_field(name=f"Congratulation You Did It! :sparkles:", value=f"<@{user.discord_id}> did it! your efforts are rewarded. +{int(self.config["REWARDS"]["monthly_reward"]) * (cnf2["mult"] if cnf2 is not None else 1)} ETT")
        #                 await channel.send(embed=emb)
        #             except discord.errors.NotFound:
        #                 print("Channel not found.")
        #             except discord.errors.Forbidden:
        #                 print("Can't see/write on the channel")

    @tasks.loop(time=time(hour=12))
    async def check_lb(self):
        # get guild member
        guild_member = await SMMOApi.get_guild_members(int(self.config["DEFAULT"]["guild_id"]))
        date = command_utils.get_in_game_day()
        cnf = await Database.select_config("chid")
        cnf2 = await Database.select_config("mult")

        lbs_npc = [[],[],[]]
        lbs_stp = [[],[],[]]
        lbs_pvp = [[],[],[]]
        # for each member do some checks:
        for member in guild_member:
            # check if member is registered; if not no reward!
            user = await Database.select_user_smmoid(member.user_id)
            if user is None:
                continue

            # if member registered take daily stats
            daily_stats = await Database.select_stats(member.user_id,date)
            if daily_stats is None:
                continue
            lbs_npc[0].append({"user":user,"stats":member.npc_kills - daily_stats.npc})
            lbs_stp[0].append({"user":user,"stats":member.steps - daily_stats.steps})
            lbs_pvp[0].append({"user":user,"stats":member.user_kills - daily_stats.pvp})

            # if not monday do not check for weekly rewards
            if datetime.today().weekday() != 0:
                continue
            date_temp = date - timedelta(days=1)
            weekly_stats = await Database.select_stats(member.user_id,date_temp)
            if weekly_stats is None:
                continue
            lbs_npc[1].append({"user":user,"stats":member.npc_kills - weekly_stats.npc})
            lbs_stp[1].append({"user":user,"stats":member.steps - weekly_stats.steps})
            lbs_pvp[1].append({"user":user,"stats":member.user_kills - weekly_stats.pvp})
            
            # if not on server reset (28th) do not check for monthly reward
            if datetime.today().day != 28:
                continue
            date_temp = date - timedelta(weeks=4)
            monthly_stats = await Database.select_stats(member.user_id,date_temp)
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
        names:list[str] = ["LEADERBOARD.daily","LEADERBOARD.weekly","LEADERBOARD.monthly"]
        cat:list[list[str]] = [
            ["daily_npc","weekly_npc","monthly_npc"],
            ["daily_steps","weekly_steps","monthly_steps"],
            ["daily_pvp","weekly_pvp","monthly_pvp"]
            ]
        for i in range(3):
            msg:list[str] = ["","",""]
            if int(self.config["REQUIREMENTS"][cat[0][i]]) != 0:
                for us,rew,index in zip(lbs_npc[i],self.config[names[i]],range(len(self.config[names[i]]))):
                    if index == 0:
                        msg[0] += "**NPC**\n"
                    us["user"].ett += int(rew) * (int(cnf2.value) if cnf2 is not None else 1)
                    await Database.update_user(us["user"].discord_id,us["user"].ign,us["user"].ett,us["user"].btt,us["user"].daily,us["user"].weekly,us["user"].monthly)
                    msg[0] += f"#{index+1} {us["user"].ign} +{int(rew) * (int(cnf2.value) if cnf2 is not None else 1)} ETT\n"
            if int(self.config["REQUIREMENTS"][cat[0][i]]) != 0:
                for us,rew,index in zip(lbs_stp[i],self.config[names[i]],range(len(self.config[names[i]]))):
                    if index == 0:
                        msg[1] += "**Steps**\n"
                    us["user"].ett += int(rew) * (int(cnf2.value) if cnf2 is not None else 1)
                    await Database.update_user(us["user"].discord_id,us["user"].ign,us["user"].ett,us["user"].btt,us["user"].daily,us["user"].weekly,us["user"].monthly)
                    msg[1] += f"#{index+1} {us["user"].ign} +{int(rew) * (int(cnf2.value) if cnf2 is not None else 1)} ETT\n"
            if int(self.config["REQUIREMENTS"][cat[0][i]]) != 0:
                for us,rew,index in zip(lbs_pvp[i],self.config[names[i]],range(len(self.config[names[i]]))):
                    if index == 0:
                        msg[2] += "**PVP**\n"
                    us["user"].ett += int(rew) * (int(cnf2.value) if cnf2 is not None else 1)
                    await Database.update_user(us["user"].discord_id,us["user"].ign,us["user"].ett,us["user"].btt,us["user"].daily,us["user"].weekly,us["user"].monthly)
                    msg[2] += f"#{index+1} {us["user"].ign} +{int(rew) * (int(cnf2.value) if cnf2 is not None else 1)} ETT\n"
            if cnf is not None:
                try:
                    channel = await self.client.fetch_channel(int(cnf.value))
                    emb:discord.Embed = discord.Embed(title=f"{["Daily","Weekly","Monthly"][i]} Leaderboard reward!! :tada:",color=int(self.config["DEFAULT"]["color"],16))
                    for i in range(3):
                        if len(msg[i]) == 0:
                            continue
                        emb.add_field(name="", value=msg[i],inline=False)
                    await channel.send(embed=emb)
                except discord.errors.NotFound:
                    print("Channel not found.")
                except discord.errors.Forbidden:
                    print("Can't see/write on the channel")

def setup(client: discord.Bot):
    client.add_cog(Admin(client))
