import discord
import random
import requests

from discord import Option
from discord.ext import commands

''' 
    Beanbot cog for handling OrdinarySausage database related functions.
'''
class Sausage(commands.Cog) :

    def __init__(self, bot):
        self.bot = bot

    # Command handler for a random OrdinarySausage video
    @commands.slash_command(name="sausage", description="Fetch a random Ordinary Sausage video. There are 3 options available nse, sausage, all.")
    async def sausage(self, ctx: discord.ApplicationContext, type : Option(str, required=True, description="sausage, nse, or all. This flag indicates what should be included by random pick.")) :

        # Grab all sausages of type and select one at random
        sausages = await self.get_sausages(type)
        sausage = random.choice(sausages)

        # Construct youtube link and fetch rating before responding
        link = "https://www.youtube.com/watch?v=" + sausage['episodeID']
        rating = sausage['rating']
        await ctx.respond("Here's a random Ordinary Sausage video! \n " + link + "\n Rating: " + str(rating))

    # Grab list of sausages of type
    async def get_sausages(self, type):

        # based on type, determine if source url(s) should be sausages, nse's, or both
        urls = []
        if type == "nse" or type == "all":
            urls.append("https://schatt3npakt.github.io/sausage-data/nse.json")

        if type == "sausage" or type == "all":
            urls.append("https://schatt3npakt.github.io/sausage-data/sausages.json")

        sausages = []

        # Go to all endpoints in url list and fetch video info
        for url in urls:
            response = requests.get(url)
            response.raise_for_status()
            json_data = response.json()
            response.close()

            # Add each sausage in the json response to the sausages list
            for sausage in json_data :
                sausages.append(sausage)

        # Return final list
        return sausages

# I don't know what this does, but I know i need it! something about initializing the cog
def setup(bot):
    bot.add_cog(Sausage(bot))