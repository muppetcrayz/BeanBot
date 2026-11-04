import discord
import json
import os
import random

from datetime import datetime
from discord.ext import commands, tasks

''' 
    Beanbot cog for handling reading data from file and performing tasks related to the bean / planting system. 
    This cog will be accessed by others for access to the data this cog reads from file and maintains.
'''
class MagicBeans(commands.Cog) :

    # Variables for this cog. This cog will be accessed by others to see bean_data
    bean_data : dict[dict[str, int]]
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", 'beandata.json')
    rarity_options = [1,2,3,4,5,6,7,8,9,10]
    common_produce = ["onion", "cucumber", "apple", "blueberry", "broccoli", "asparagus", "peach", "grapes", "banana","dragon fruit"]
    uncommon_produce = ["silver eggplant", "bronze zucchini"]
    rare_produce = ["golden berry", "purple yam"]

    def __init__(self, bot):

        # Initialize
        self.bot = bot
        self.last_updated = None
        self.read_data()
        self.planted = self.bean_data["Planted"]
        self.inventory = self.bean_data["Inventory"]
        self.bean_loop.start()

    # Open, read data from, and close json data file
    def read_data(self):
        with open(self.file_path) as json_file:
            self.bean_data = json.load(json_file)

        json_file.close()

    # Process for writing data to the JSON file and closing.
    async def save_data(self):
        with open(self.file_path, 'w') as json_file:
            json.dump(self.bean_data, json_file, indent=4)

        json_file.close()
        self.last_updated = datetime.now()

    # Command handler for planting mysterious plants in beanBot's garden.
    @discord.slash_command(name="plant", description="Plant a magic bean in my garden and see what it grows into!")
    async def plant(self, ctx: discord.ApplicationContext):

        # Initialize bean (dict with guild, member, channel, time, and rarity) and add it to the list of all planted beans
        bean_plant = {"guild": ctx.guild.id, "member": ctx.author.id,"channel": ctx.channel.id, "time": datetime.now().isoformat(), "rarity": random.choice(self.rarity_options)}
        self.planted.append(bean_plant)
        self.bean_data["Planted"] = self.planted

        await ctx.respond(f"{ctx.author.mention} planted a magic bean!")
        await self.save_data()

    # Command handler for checking the garden,
    @discord.slash_command(name="garden", description="Check my garden for growing magic beans.")
    async def garden(self, ctx: discord.ApplicationContext):

        message = ""

        # Go through all planted beans list
        for bean in self.planted:

            # If in a guild grab member associated
            if ctx.guild is not None:
                member = await ctx.guild.fetch_member(bean["member"])
                mem_name = member.name

            else:
                mem_name = str(bean["member"])

            # determine how much time has passed / how much remains
            timespan = (datetime.now() - datetime.fromisoformat(bean["time"]))
            time_left = (10 + 3*bean['rarity']) - int(timespan.seconds/60)
            message = message + (mem_name + " has a mysterious plant with approximately " + str(time_left) + " minutes remaining. \n")

        # If nothing happened, the garden must be empty
        if message == "":
            message = ("My garden is empty!")
            await ctx.respond(f"{message}")

        # Respond with message only if there are things in the garden
        else: await ctx.respond(f"Here is a list of things in my garden: \n{message}")

    @discord.slash_command(name="inventory", description="Check your inventory for items you've obtained from planting magic beans.")
    async def slash_inventory(self, ctx: discord.ApplicationContext):
        # Check the member's inventory
        if str(ctx.author.id) in self.inventory:
            items = self.inventory[str(ctx.author.id)]
            if items:
                message = "Here is your inventory: \n"
                for item, count in items.items():
                    message += f"- {item}: {count}\n"
                await ctx.respond(message)
            else:
                await ctx.respond("Your inventory is empty!")
        else:
            await ctx.respond("Your inventory is empty!")

    async def add_inventory(self, member, item, num):
        # If the member is not in the inventory, add them
        if str(member.id) not in self.inventory:
            self.inventory[str(member.id)] = {}

        # If the item is not in the member's inventory, add it
        if item not in self.inventory[str(member.id)]:
            self.inventory[str(member.id)][item] = 0

        # Add the number of items to the member's inventory
        self.inventory[str(member.id)][item] += num
        self.bean_data["Inventory"] = self.inventory
    
    # Every couple of minutes, check the progress on any planted beans with bean_loop
    @tasks.loop(minutes=2)
    async def bean_loop(self):

        # Determine if any have reached their end growth
        grown_beans = []
        for plant in self.planted:
            time = datetime.now() - datetime.fromisoformat(plant["time"])
            remaining = (10 + 3*plant['rarity']) - int(time.seconds/60)
            if remaining <= 0:
                grown_beans.append(plant)
                self.planted.remove(plant)

        # Loop through any which have grown
        for bean in grown_beans:

            # Determine where and who to alert
            guild = await self.bot.fetch_guild(bean["guild"])
            channel = await guild.fetch_channel(bean["channel"])
            author = await guild.fetch_member(bean["member"])

            # Ultra rare beanstalk chance
            stalk_rarity = 10
            if bean["rarity"] == stalk_rarity:
                result = "Giant bean stalk! Amazing!! You get a golden egg!"

            # 8, 9 yield a rare produce
            elif bean["rarity"] > 7:
                result = random.choice(self.rare_produce)

            # 5, 6, 7 uncommon
            elif bean["rarity"] >= 5:
                result = random.choice(self.uncommon_produce)

            # 1, 2, 3, 4 yield common tier
            else:
                result = random.choice(self.common_produce)

            # Select a size and set the starting num obtained to the rarity / 2
            sizes = ["", "Giant ", "Large ", "Tiny ", ""]
            num = bean["rarity"]/2
            sizes.remove("Giant ")
            option = random.choice(sizes)
            sizes.append("Giant ")

            # Re-add giant as an option for anything that isn't the bottom rarities
            if bean["rarity"] > 2:
                option = random.choice(sizes)
                if option == "Giant ": num = int(bean["rarity"]/4)
                else: num = bean["rarity"] - 1
                if option == "Large ": num = int(bean["rarity"]-2)

            # Minimum rarity items can only get tiny or regular
            if bean["rarity"] == 1:
                option = random.choice(["","Tiny "])
                num = 1

            # If beanstalk, only one can grow
            if bean["rarity"] == stalk_rarity:
                option = ""
                num = 1

            # Say response
            await channel.send(f"{author.mention}'s mysterious magic bean plant has grown! Your plant grew: {option}{result}. You got {num} of them.")
            inventory_item = f"{option.lower()}{result}"
            await self.add_inventory(author, inventory_item, num)

        # Save bean data
        await self.save_data()

# I don't know what this does, but I know i need it! something about initializing the cog
def setup(bot):
    bot.add_cog(MagicBeans(bot))