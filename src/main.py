import discord
import os

from discord import Intents
from dotenv import load_dotenv

# Load info from dotENV file
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Cogs list referring to each by filename
cogs = ['poll','magic_beans','greetings','quotes','sausage']

# Set intents
intents = Intents.default()
intents.__setattr__("message_content", True)

# Create bot
bot = discord.Bot(intents=intents)

# On ready event
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.sync_commands()

# Add all cogs
for cog in cogs:
    bot.load_extension(f'cogs.{cog}')

# Run the bot using token loaded from ENV
bot.run(token)