# main.py
import discord
from discord.ext import commands
import dotenv
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CustomCommandBot')

# Load environment variables
dotenv.load_dotenv()

# Import Cogs
from cogs.commands import CommandsCog
from cogs.events import EventsCog

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for accessing member information

# Initialize bot
bot = commands.Bot(intents=intents, command_prefix="!", help_command=None)

# Load Cogs
bot.add_cog(CommandsCog(bot))
bot.add_cog(EventsCog(bot))

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        logger.error("TOKEN environment variable not set.")
        exit(1)
    bot.run(TOKEN)
