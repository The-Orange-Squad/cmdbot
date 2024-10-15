# cogs/events.py
import discord
from discord.ext import commands
from discord import Embed
from utils import replace_placeholders
from data import save_commands
import logging
import re
import asyncio
import cogs.orange_bank as orange_bank
from datetime import datetime
from views import SelectExecuteCommandView

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
        args = parts[1:]  # Extract arguments here

        if prefix == "cc!":
            cmds = self.bot.custom_commands.get(user_id, {})
            command = next((cmd for cmd in cmds.get("private", []) if cmd['name'] == command_name), None)
            if not command:
                await message.channel.send(f"Custom command `{prefix}{command_name}` not found.")
                logger.warning(f"Command `{prefix}{command_name}` not found for user {message.author}")
                return

            # Extract arguments based on {[<arg_name>]} placeholders
            output = command["output"]
            arg_pattern = re.compile(r"\{\[\<(\w+)\>\]\}")
            arg_names = arg_pattern.findall(output)
            num_args = len(arg_names)
            if len(args) < num_args:
                await message.channel.send(f"Missing arguments. This command requires {num_args} arguments: {', '.join(arg_names)}.")
                return

            # Assign arguments to arg_names
            params = {}
            for i, arg_name in enumerate(arg_names):
                if i < len(args):
                    params[arg_name] = args[i]
                else:
                    params[arg_name] = ""

            # Replace placeholders
            try:
                orange_bank_cog = self.bot.get_cog('OrangeBankCog')
                if not orange_bank_cog:
                    await message.channel.send("Orange Bank Cog is not loaded.")
                    return

                # Create a mock Interaction-like object for utils.replace_placeholders
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

        elif prefix == "pc!":
            # Handle public commands by scanning all users
            matching_commands = []
            for uid, user_cmds in self.bot.custom_commands.items():
                for cmd in user_cmds.get("public", []):
                    if cmd['name'] == command_name:
                        matching_commands.append((uid, cmd))
                        if len(matching_commands) >= 5:
                            break
                if len(matching_commands) >= 5:
                    break

            if not matching_commands:
                await message.channel.send(f"Public command `{prefix}{command_name}` not found.")
                logger.warning(f"Public command `{prefix}{command_name}` not found for user {message.author}")
                return

            if len(matching_commands) == 1:
                # Only one match, execute it
                source_uid, command = matching_commands[0]
                await self.execute_public_command(message, command, source_uid, args)
            else:
                # Multiple matches, present a selection menu with args
                view = SelectExecuteCommandView(self.bot, message, command_name, matching_commands, args)
                embed = Embed(
                    title="Multiple Public Commands Found",
                    description=f"There are multiple public commands named `{command_name}`. Please select which one you want to execute.",
                    color=discord.Color.orange()
                )
                for i, (uid, cmd) in enumerate(matching_commands, start=1):
                    user = self.bot.get_user(int(uid))
                    embed.add_field(
                        name=f"Option {i}",
                        value=f"**User:** {user.name}#{user.discriminator}\n**Description:** {cmd.get('description', 'No description.')}",
                        inline=False
                    )
                await message.channel.send(embed=embed, view=view)

    async def execute_public_command(self, message: discord.Message, command, source_uid, args=None):
        prefix = "pc!"
        command_name = command['name']
        user_id = str(message.author.id)

        # Use provided args or parse from the message
        if args is None:
            parts = message.content[len(prefix):].strip().split()
            supplied_args = parts[1:]
        else:
            supplied_args = args

        # Extract arguments based on {[<arg_name>]} placeholders
        output = command["output"]
        arg_pattern = re.compile(r"\{\[\<(\w+)\>\]\}")
        arg_names = arg_pattern.findall(output)
        num_args = len(arg_names)
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

        # Replace placeholders
        try:
            orange_bank_cog = self.bot.get_cog('OrangeBankCog')
            if not orange_bank_cog:
                await message.channel.send("Orange Bank Cog is not loaded.")
                return

            # Create a mock Interaction-like object for utils.replace_placeholders
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
            logger.info(f"Public Command `pc!{command_name}` from user ID {source_uid} used by {message.author}")
        except Exception as e:
            logger.error(f"Error processing public command `pc!{command_name}`: {e}")
            await message.channel.send("An error occurred while processing your command.")

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        logger.info("------")
