# cogs/events.py
import discord
from discord.ext import commands
from utils import replace_placeholders
from data import save_commands
import logging
import re
import asyncio
import cogs.orange_bank as orange_bank

logger = logging.getLogger('CustomCommandBot')

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content.startswith("cc!"):
            return
        content = message.content[3:].strip()
        if not content:
            await message.channel.send("Please provide a command name.")
            return
        parts = content.split()
        command_name = parts[0].lower()
        user_id = str(message.author.id)
        cmds = self.bot.custom_commands.get(user_id, [])
        command = next((cmd for cmd in cmds if cmd['name'] == command_name), None)
        if not command:
            await message.channel.send("Custom command not found.")
            logger.warning(f"Command `cc!{command_name}` not found for user {message.author}")
            return
        # Extract arguments based on {[<arg_name>]} placeholders
        output = command["output"]
        arg_pattern = re.compile(r"\{\[\<(\w+)\>\]\}")
        arg_names = arg_pattern.findall(output)
        num_args = len(arg_names)
        supplied_args = parts[1:]
        if len(supplied_args) < num_args:
            await message.channel.send(f"Missing arguments. This command requires {num_args} arguments: {', '.join(arg_names)}.")
            return
        # Assign arguments to arg_names
        params = {}
        for i, arg_name in enumerate(arg_names):
            if i < len(supplied_args):
                params[arg_name] = supplied_args[i]
            else:
                params[arg_name] = ""
        # Optionally, handle extra arguments if necessary
        # Now, replace placeholders
        try:
            orange_bank_cog = self.bot.get_cog('OrangeBankCog')
            if not orange_bank_cog:
                await message.channel.send("Orange Bank Cog is not loaded.")
                return

            # Replace placeholders asynchronously
            # get ctx from message
            ctx = await self.bot.get_context(message)
            processed_output = await replace_placeholders(output, ctx, params, orange_bank_cog, command)
            await message.channel.send(processed_output)
            logger.info(f"Command `cc!{command_name}` used by {message.author}")
        except Exception as e:
            logger.error(f"Error processing command `cc!{command_name}`: {e}")
            await message.channel.send("An error occurred while processing your command.")
