# modals.py
import discord
from discord.ui import Modal, InputText
from datetime import datetime
from data import save_commands
import logging

logger = logging.getLogger('CustomCommandBot')

class CreateCommandModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Create Custom Command")
        self.bot = bot
        self.add_item(InputText(
            label="Command Name (without cc!)",
            placeholder="e.g., greet",
            max_length=50,
            required=True
        ))
        self.add_item(InputText(
            label="Command Output",
            style=discord.InputTextStyle.long,
            placeholder="e.g., Hello, [username]! Welcome to {servername}. {[<arg1>]}",
            max_length=500,
            required=True
        ))
        # Add a description field to guide users
        self.add_item(InputText(
            label="Description (Optional)",
            placeholder="Describe what your command does.",
            max_length=150,
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        custom_commands = self.bot.custom_commands
        if user_id not in custom_commands:
            custom_commands[user_id] = []
        if len(custom_commands[user_id]) >= 10:
            await interaction.response.send_message(
                "You can only have up to 10 custom commands.",
                ephemeral=True
            )
            return
        command_name = self.children[0].value.strip().lower()
        if not command_name.isalnum():
            await interaction.response.send_message(
                "Command name must be alphanumeric.",
                ephemeral=True
            )
            return
        for cmd in custom_commands[user_id]:
            if cmd["name"] == command_name:
                await interaction.response.send_message(
                    "You already have a command with that name.",
                    ephemeral=True
                )
                return
        command_output = self.children[1].value.strip()
        description = self.children[2].value.strip() if self.children[2].value else "No description."
        if len(command_output) > 500:
            await interaction.response.send_message(
                "Command output exceeds 500 characters.",
                ephemeral=True
            )
            return
        custom_commands[user_id].append({
            "name": command_name,
            "output": command_output,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        })
        save_commands(custom_commands)
        logger.info(f"User {interaction.user} created command: {command_name}")
        await interaction.response.send_message(
            f"Custom command `cc!{command_name}` created successfully.",
            ephemeral=True
        )

class EditCommandModal(Modal):
    def __init__(self, bot, command):
        super().__init__(title=f"Edit Command: cc!{command['name']}")
        self.bot = bot
        self.command = command
        self.add_item(InputText(
            label="Command Output",
            style=discord.InputTextStyle.long,
            value=command['output'],
            max_length=500,
            required=True
        ))
        self.add_item(InputText(
            label="Description (Optional)",
            value=command.get('description', ''),
            max_length=150,
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        custom_commands = self.bot.custom_commands
        command_output = self.children[0].value.strip()
        description = self.children[1].value.strip() if self.children[1].value else self.command.get("description", "")
        if len(command_output) > 500:
            await interaction.response.send_message(
                "Command output exceeds 500 characters.",
                ephemeral=True
            )
            return
        # Update the command
        for cmd in custom_commands[user_id]:
            if cmd["name"] == self.command['name']:
                cmd['output'] = command_output
                cmd['description'] = description
                cmd['edited_at'] = datetime.utcnow().isoformat()
                break
        save_commands(custom_commands)
        logger.info(f"User {interaction.user} edited command: {self.command['name']}")
        await interaction.response.send_message(
            f"Custom command `cc!{self.command['name']}` has been updated.",
            ephemeral=True
        )

class ConfirmDeleteModal(Modal):
    def __init__(self, bot, user_id, command):
        super().__init__(title=f"Delete Command: cc!{command['name']}")
        self.bot = bot
        self.user_id = user_id
        self.command = command
        self.add_item(InputText(
            label="Type the command name to confirm deletion",
            placeholder=command['name'],
            max_length=50,
            required=True
        ))

    async def callback(self, interaction: discord.Interaction):
        confirmation = self.children[0].value.strip().lower()
        if confirmation != self.command['name']:
            await interaction.response.send_message(
                "Command name does not match. Deletion cancelled.",
                ephemeral=True
            )
            return
        # Delete the command
        custom_commands = self.bot.custom_commands
        cmds = custom_commands.get(self.user_id, [])
        custom_commands[self.user_id] = [cmd for cmd in cmds if cmd['name'] != self.command['name']]
        save_commands(custom_commands)
        logger.info(f"User {interaction.user} deleted command: {self.command['name']}")
        await interaction.response.send_message(
            f"Custom command `cc!{self.command['name']}` has been deleted.",
            ephemeral=True
        )
