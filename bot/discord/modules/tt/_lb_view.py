import discord

class LeaderBoardView(discord.ui.View):
    current_page: int = 1
    sep: int = 10

    async def send(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.message = await ctx.followup.send(view=self)
        await self.update_message(self.users[:self.sep])
        

    async def update_message(self, data):
        await self.update_buttons()
        try:
            await self.message.edit(embed=await self.create_embed(data), view=self)
        except discord.errors.Forbidden:
            await self.ctx.followup.send(content="Bot doesn't have the perms to see this channel, so the buttons of the message doesn't work.")


    async def update_buttons(self):
        if self.current_page == 1:
            self.prev_button.disabled = True
            self.prev_button.style = discord.ButtonStyle.gray
            self.first_button.disabled = True
            self.first_button.style = discord.ButtonStyle.gray
        else:
            self.prev_button.disabled = False
            self.prev_button.style = discord.ButtonStyle.primary
            self.first_button.disabled = False
            self.first_button.style = discord.ButtonStyle.green

        if self.current_page == int(len(self.users)/self.sep) + 1:
            self.next_button.disabled = True
            self.next_button.style = discord.ButtonStyle.gray
            self.last_button.disabled = True
            self.last_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.next_button.style = discord.ButtonStyle.primary
            self.last_button.disabled = False
            self.last_button.style = discord.ButtonStyle.green


    def get_current_page_data(self):
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        if self.current_page == 1:
            from_item = 0
            until_item = self.sep
        if self.current_page == int((len(self.users)) / self.sep) + 1:
            from_item = self.current_page * self.sep - self.sep
            until_item = len(self.users)
        return self.users[from_item:until_item]
    

    async def create_embed(self, data):
        emb = discord.Embed(title=f"TTs Leaderboard",
                            color=self.color)
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        emb.add_field(name="", value="\n".join([f"#{i} [{v.ign}](https://web.simple-mmo.com/user/view/{v.smmo_id}): **{format(v.ett+v.btt,",d")}**{f" ({format(v.ett,",d")} ETT | {format(v.btt,",d")} BTT)" if self.more_info else ""}" for v,i in zip(data,range(from_item + 1, until_item + 1))]))
        
        emb.set_footer(text=f"Page {self.current_page}/{(len(self.users)) // self.sep + 1}")
        return emb

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green)
    async def first_button(self, button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_message(self.get_current_page_data())
            

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page_data())


    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page_data())


    @discord.ui.button(label=">|", style=discord.ButtonStyle.green)
    async def last_button(self, button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.defer()
        self.current_page = int((len(self.users)) / self.sep) + 1
        await self.update_message(self.get_current_page_data())