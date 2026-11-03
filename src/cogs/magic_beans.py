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
    uncommon_produce = ["magic bean", "silver eggplant", "bronze zucchini"]
    rare_produce = ["golden berry", "magic bean", "purple yam"]

    def __init__(self, bot):

        # Initialize
        self.bot = bot
        self.last_updated = None
        self.read_data()
        self.planted = self.bean_data["Planted"]
        self.bean_loop.start()

    # Open, read data from, and close json data file
    def read_data(self):
        with open(self.file_path) as json_file:
            self.bean_data = json.load(json_file)

        json_file.close()

    # Command handler for giving someone a magic bean.
    @discord.user_command(name="gift", description="Gift someone a magic bean.")
    async def gift(self, ctx: discord.ApplicationContext, member: discord.Member):

        self.add_bean(member)

        await ctx.respond(f"{ctx.author.mention} gave {member.mention} a magic bean!")

    # Command handler for checking number of beans a user has.
    @discord.user_command(name="beans", description="Get a count of how many magic beans a user has.")
    async def beans(self, ctx: discord.ApplicationContext, member: discord.Member):

        count = self.bean_count(member.id)
        if (str(member.id) not in self.bean_data["BeanCount"]) or count == 0:
            await ctx.respond(f"{member.name} has no magic beans.")
            self.bean_data["BeanCount"][str(member.id)] = 0

        else:
            await ctx.respond(f"{member.name} has " + str(count) + " magic beans.")

    # Process for writing data to the JSON file and closing.
    async def save_data(self):
        with open(self.file_path, 'w') as json_file:
            json.dump(self.bean_data, json_file, indent=4)

        json_file.close()
        self.last_updated = datetime.now()

    # Adds a bean to members bean count. Returns new total of beans
    def add_bean(self, member: discord.Member):
        if (str(member.id) not in self.bean_data["BeanCount"]):
            self.bean_data["BeanCount"][str(member.id)] = 1

        else:
            self.bean_data["BeanCount"][str(member.id)] += 1

        return self.bean_data["BeanCount"][str(member.id)]

    # Fetches bean count for member member_id
    def bean_count(self, member_id):
        return self.bean_data["BeanCount"][str(member_id)]

    # Removes a bean from member. Returns new total of beans.
    def remove_bean(self, member: discord.Member):
        if (str(member.id) not in self.bean_data["BeanCount"]):
            self.bean_data["BeanCount"][str(member.id)] = 0

        else:
            self.bean_data["BeanCount"][str(member.id)] -= 1

        return self.bean_data["BeanCount"][str(member.id)]

    # Command handler for planting mysterious plants in beanBot's garden.
    @discord.slash_command(name="plant", description="Plant a magic bean in my garden and see what it grows into!")
    async def plant(self, ctx: discord.ApplicationContext):

        # Make sure user has more beans
        if self.bean_data["BeanCount"][str(ctx.author.id)] == 0:
            await ctx.respond(f"You have no magic beans left to plant.")
            return

        # Initialize bean (dict with guild, member, channel, time, and rarity) and add it to the list of all planted beans
        bean_plant = {"guild": ctx.guild.id, "member": ctx.author.id,"channel": ctx.channel.id, "time": datetime.now().isoformat(), "rarity": random.choice(self.rarity_options)}
        self.planted.append(bean_plant)
        self.bean_data["Planted"] = self.planted

        # Remove a bean and grab count to report back.
        numbeans = self.remove_bean(ctx.author)
        await ctx.respond(f"{ctx.author.mention} planted a magic bean! They have {numbeans} magic beans left.")
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
                result = "Giant bean stalk! Amazing!! +5 magic beans and a golden egg!"
                for i in range(5):
                    self.add_bean(author)

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

            # If beans were selected but not the bean stalk, add beans
            if result == "magic bean":
                num = bean["rarity"]/3
                for i in num:
                    self.add_bean(author)

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

            # Add a bean back to whoevers plant this was.
            self.add_bean(author)

            # Say response
            await channel.send(f"{author.mention}'s mysterious magic bean plant has grown! Your plant grew: {option}{result}. You got {num} of them.")

        # Save bean data
        await self.save_data()

# I don't know what this does, but I know i need it! something about initializing the cog
def setup(bot):
    bot.add_cog(MagicBeans(bot))