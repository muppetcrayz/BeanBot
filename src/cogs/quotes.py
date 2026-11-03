import discord
import random

from datetime import datetime
from discord import Option, SlashCommandOptionType
from discord.ext import commands

'''
    Beanbot cog for handling any and all quote related things. Adding them, displaying them, you name it. Exciting
'''
class Quotes(commands.Cog) :

    def __init__(self, bot):
        self.bot = bot

        # Connect to beans cog to obtain data and use save_data
        target_cog = self.bot.get_cog('MagicBeans')
        self.bean_cog = target_cog
        self.bean_data = target_cog.bean_data
        self.quotes = self.bean_data['Quotes']

    # Command handler that checks the history of quotes channel archive to ensure it has all of them. Shouldn't need used beyond first time setup
    @commands.slash_command(name="sync", description="Check if beanbots quotes data is up-to-date with quotes channel")
    async def sync(self, ctx: discord.ApplicationContext) :

        # Find the guild and select quotes channel specifically (ID 1357017737821687908)
        guild = ctx.guild
        channel = guild.get_channel(1357017737821687908)

        # If quotes have never been updated get all history
        if self.quotes['updated'] == "":
            message_list = await channel.history(limit=None).flatten()
            fresh_update = datetime.now()

        # Otherwise, only get history after last update
        else:
            last_update = datetime.fromisoformat(self.quotes['updated'])
            fresh_update = datetime.now()
            message_list = await channel.history(limit=None, after=last_update).flatten()

        # For all new messages, add them to the quotes dictionary with message_id as key and content as value
        for message in message_list :
            self.quotes[message.id] = message.content

        # Change last update time to now and save all data
        self.quotes['updated'] = fresh_update.isoformat()
        await self.bean_cog.save_data()

        # Determine final message based on number of quotes processed
        if len(message_list) > 0 :
            await ctx.respond("Quotes data has been updated. "+ str(len(message_list)) + " quotes saved.")

        else :
            await ctx.respond("I can't find any new quotes to save.")

    # Command handler to add a quote. Takes only a string to be added, inserts into data object and posts to quotes channel
    @commands.slash_command(name="addquote", description="Adds a new quote to the quotes channel and beanbots data file.")
    async def addquote(self, ctx: discord.ApplicationContext, quote : Option(str, required=True)) :

        # Grab the guild and look for the quotes channel
        guild = ctx.guild
        channel = guild.get_channel(1357017737821687908)

        # Send a message with quote to the channel. Store message to grab its id
        message_sent = await channel.send(quote)

        # Set the latest update time and add this quote to quotes
        self.quotes['updated'] = datetime.now().isoformat()
        self.quotes[message_sent.id] = quote

        # Save beandata to the beans cog
        await self.bean_cog.save_data()
        await ctx.delete()

    # Command handler for obtaining a random quote
    @commands.slash_command(name="randomquote", description="Bean bot will randomly select a quote and say it.")
    async def randomquote(self, ctx: discord.ApplicationContext) :

        # Get a list of all quotes
        quotes_list = list(self.quotes.values())

        # I flattened a dictionary valueset so this one's gotta go
        quotes_list.remove(self.quotes['updated'])

        # Pick a quote at random and respond with the chosen quote
        quote = random.choice(quotes_list)
        await ctx.respond(quote)

# I don't know what this does, but I know i need it! something about initializing the cog
def setup(bot):
    bot.add_cog(Quotes(bot))