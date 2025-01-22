import discord
from discord import SlashCommandGroup
from discord.ext import commands

class CommandGroups(commands.Cog):
    group_admin = SlashCommandGroup(name="admin", description="Admin commands")
    admin_subgroup = group_admin.create_subgroup("admin")

    group_tt = SlashCommandGroup(name="tt", description="TT commands")
    tt_subgroup = group_admin.create_subgroup("tt")

    def __init__(self, client):
        self.client: discord.Bot = client

def setup(client: discord.Bot):
    client.add_cog(CommandGroups(client))