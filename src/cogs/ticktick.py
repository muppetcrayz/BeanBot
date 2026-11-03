import discord
import random
import os
import json
import vote

from dida365 import Dida365Client
from discord.ext import commands
from discord import Bot, Reaction

class TickTick(commands.Cog) :
    num_voters = 0
    active_vote = None
    vote_react = "✅"
    veto_react = "❎"

    def __init__(self, bot):
        self.bot = bot
        self.client = Dida365Client()
        self.client.save_to_env = True

    @commands.slash_command(name="dinner", description="Start a vote based on meal planning options in ticktick.")
    async def dinner(self, ctx: discord.ApplicationContext):
        # Check the number of people voting (will probably always be 3 lol) subtract one for bean bot
        self.num_voters = ctx.guild.member_count - 1
        if self.num_voters < 3: self.num_voters = 3

        # Grab food project and all items therein
        project_data = await self.client.get_project_with_data("683f58d1d32551f6c25c2bc9")
        tasks = project_data.tasks

        await ctx.respond("Here are today's meal planning options. You may veto one selection, please vote only once and veto once.")
        # For all options, post a message for voting on! Keep track of all messages in this voting block
        messages = []
        for task in tasks:
            message = await ctx.send(task.title)
            messages.append(message.id)

        vote_obj = vote.Vote(messages, self.num_voters)
        self.active_vote = vote_obj

    @commands.slash_command(name="auth", description="Check ticktick authentication status.")
    async def auth(self, ctx: discord.ApplicationContext):
        # If there is no token_info, get it
        token_info = os.getenv("DIDA365_ACCESS_TOKEN")
        if token_info is None:
            token_info = await self.client.authenticate()
            print("Authenticating...")
            await ctx.respond("Please check bot server to authenticate. I need help!")

        else : await ctx.respond("I am authenticated.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if (self.active_vote is None) or (payload.message_id not in self.active_vote.messages) or (self.active_vote.winners is not None):
            return None

        if payload.emoji.name == self.vote_react:
            self.active_vote.add_vote(payload.message_id, str(payload.member.id))

        elif payload.emoji.name == self.veto_react:
            self.active_vote.veto(payload.message_id, str(payload.member.id))

        final_message = ""
        winners, vetos = self.active_vote.check_vote()
        channel : discord.ChannelType = await self.bot.fetch_channel(payload.channel_id)
        if winners is not None :
            win_text = ""
            if len(winners) > 1 :
                final_message = "The following meals tied: "
                for winner in winners:
                    win_m = await channel.fetch_message(int(winner[0]))
                    win_text = win_m.content
                    final_message = final_message + win_text + ", "

                final_message = final_message[:-2]
                final_message = final_message + ". "

            else:
                win_m = await channel.fetch_message(int(winners[0][0]))
                win_text = win_m.content
                final_message = "The winning selection was: " + win_text + ". "

            if len(vetos) > 0:
                final_message = final_message + "The following was vetoed: "
                for veto in vetos:
                    veto_m = await channel.fetch_message(int(veto[0]))
                    veto_text = veto_m.content
                    final_message = final_message + veto_text + ", "

                final_message = final_message[:-2]
                final_message = final_message + "."

            self.active_vote = None
            return await channel.send(final_message)
        return None



def setup(bot):
    bot.add_cog(TickTick(bot))