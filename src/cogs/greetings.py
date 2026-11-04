import discord
import random
import logging
import re

from discord.ext import commands

'''
    BeanBot cog for handling commands that let beanbot speak.
'''
class Greetings(commands.Cog) :

    magic_words = re.compile(
        r"\b(?:mages?|wizards?|wizardry|magic(?:al|ally)?|magicians?|"
        r"witch(?:es|craft)?|warlocks?|sorcer(?:y|ers?|ess(?:es)?)|"
        r"enchant(?:ed|ing|ments?)?|spells?|potions?|"
        r"necroman(?:cy|cers?)|arcane|conjur(?:e|es|ed|ing|ation)|"
        r"space\s+eggs?)\b",
        re.IGNORECASE,
    )
    magic_emoji_name = "magegg~1"

    def __init__(self, bot):
        self.bot = bot

        # Connect to beans cog to obtain data and use save_data
        target_cog = self.bot.get_cog('MagicBeans')
        self.bean_cog = target_cog
        self.bean_data = target_cog.bean_data

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if not self.magic_words.search(message.content):
            return

        emoji = discord.utils.get(message.guild.emojis, name=self.magic_emoji_name)
        if emoji is None:
            return

        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            logging.getLogger(__name__).warning(
                "Could not add magic reaction to message %s", message.id, exc_info=True
            )

    # Command handler for basic hello
    @commands.slash_command(name="hello", description="Say hello to beanbot, and get a response")
    async def hello(self, ctx: discord.ApplicationContext):

        # Grab a random greeting from bean data and respond with it
        greetings = self.bean_data['Greetings']
        choice = random.choice(greetings)
        await ctx.respond(choice + f"{ctx.author.mention}.")

    # Command handler for adding new greetings to the list
    @commands.slash_command(name="addgreeting", description="Add a greeting message.")
    async def add_greeting(self, ctx: discord.ApplicationContext):

        # Add provided greeting to the list of greetings and save to data file
        self.bean_data['greetings'].append(ctx.message.content)
        await self.bean_cog.save_data()

    # Command handler for say command. Allows users to make beanbot talk wherever they choose in the server.
    @commands.slash_command(name="say", description="Make beanbot say something in a channel of your choice.")
    async def say(self, ctx: discord.ApplicationContext, message, channel_id: str = None):

        # Delete initial call as soon as possible
        await ctx.delete()

        # If not used in a guild, this command doesn't work. Respond as such
        if ctx.guild is None:
            ctx.respond("This command can only be used in a server.")

        # If no channel ID provided, send message to the same channel the original request was sent in
        if channel_id is None:
            await ctx.channel.send(message)

        # Otherwise post message to chosen channel
        else:
            channel = await ctx.guild.fetch_channel(int(channel_id))
            await channel.send(message)

# I don't know what this does, but I know i need it! something about initializing the cog
def setup(bot):
    bot.add_cog(Greetings(bot))