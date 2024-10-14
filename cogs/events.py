# cogs/events.py
import discord
from discord.ext import commands
from utils import replace_placeholders
from data import save_commands
import logging
import re
import asyncio
import cogs.orange_bank as orange_bank
from datetime import datetime

logger = logging.getLogger('CustomCommandBot')

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        prefixes = ["cc!", "pc!"]
        for prefix in prefixes:
            if message.content.startswith(prefix):
                await self.handle_command(message, prefix)
                break  # Prevent processing the same message multiple times

    async def handle_command(self, message: discord.Message, prefix: str):
        content = message.content[len(prefix):].strip()
        if not content:
            await message.channel.send("Please provide a command name.")
            return
        parts = content.split()
        command_name = parts[0].lower()
        user_id = str(message.author.id)
        cmds = self.bot.custom_commands.get(user_id, {})
        
        if prefix == "cc!":
            command = next((cmd for cmd in cmds.get("private", []) if cmd['name'] == command_name), None)
        elif prefix == "pc!":
            command = next((cmd for cmd in cmds.get("public", []) if cmd['name'] == command_name), None)
        else:
            command = None

        if not command:
            await message.channel.send(f"Custom command `{prefix}{command_name}` not found.")
            logger.warning(f"Command `{prefix}{command_name}` not found for user {message.author}")
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

            # Create a temporary Interaction-like object for utils.replace_placeholders
            # Since replace_placeholders expects an Interaction, we'll create a mock
            class MockInteraction:
                def __init__(self, user, guild, channel, id):
                    self.user = user
                    self.guild = guild
                    self.channel = channel
                    self.id = id

            mock_interaction = MockInteraction(
                user=message.author,
                guild=message.guild,
                channel=message.channel,
                id=message.id
            )

            processed_output = await replace_placeholders(output, mock_interaction, params, orange_bank_cog, command)
            await message.channel.send(processed_output)
            logger.info(f"Command `{prefix}{command_name}` used by {message.author}")
        except Exception as e:
            logger.error(f"Error processing command `{prefix}{command_name}`: {e}")
            await message.channel.send("An error occurred while processing your command.")

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        logger.info("------")
