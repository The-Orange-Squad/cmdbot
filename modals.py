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
        # Add fields for custom random_number
        self.add_item(InputText(
            label="Random Number Range (Optional)",
            placeholder="e.g., 1-100",
            max_length=20,
            required=False
        ))
        # Add fields for custom random_choice
        self.add_item(InputText(
            label="Random Choice Options (Optional)",
            placeholder="e.g., Option1, Option2, Option3",
            max_length=100,
            required=False
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

        # Initialize user's command categories if not present
        if user_id not in custom_commands:
            custom_commands[user_id] = {
                "private": [],
                "public": []
            }

        # Check total number of commands across both categories
        total_commands = len(custom_commands[user_id].get("private", [])) + len(custom_commands[user_id].get("public", []))
        if total_commands >= 10:
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

        # Check for duplicate command names across both categories
        for cmd in custom_commands[user_id].get("private", []) + custom_commands[user_id].get("public", []):
            if cmd["name"] == command_name:
                await interaction.response.send_message(
                    "You already have a command with that name.",
                    ephemeral=True
                )
                return

        command_output = self.children[1].value.strip()
        description = self.children[4].value.strip() if self.children[4].value else "No description."
        
        # Handle custom random_number range
        random_number_input = self.children[2].value.strip()
        random_number = {}
        if random_number_input:
            try:
                min_val, max_val = map(int, random_number_input.split('-'))
                if min_val >= max_val:
                    await interaction.response.send_message(
                        "Random Number Range: Minimum must be less than Maximum.",
                        ephemeral=True
                    )
                    return
                random_number = {"min": min_val, "max": max_val}
            except ValueError:
                await interaction.response.send_message(
                    "Random Number Range: Please enter in the format `min-max`, e.g., `1-100`.",
                    ephemeral=True
                )
                return
        
        # Handle custom random_choice options
        random_choice_input = self.children[3].value.strip()
        random_choice = []
        if random_choice_input:
            choices = [choice.strip() for choice in random_choice_input.split(',') if choice.strip()]
            if not choices:
                await interaction.response.send_message(
                    "Random Choice Options: Please provide at least one valid option.",
                    ephemeral=True
                )
                return
            random_choice = choices
        
        if len(command_output) > 500:
            await interaction.response.send_message(
                "Command output exceeds 500 characters.",
                ephemeral=True
            )
            return
        
        # Determine category for the new command (default to 'private')
        # Optionally, you can add another field to allow users to choose the category
        category = 'private'  # For simplicity, defaulting to 'private'
        
        command_data = {
            "name": command_name,
            "output": command_output,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if random_number:
            command_data["random_number"] = random_number
        if random_choice:
            command_data["random_choice"] = random_choice
        
        # Add to private commands
        custom_commands[user_id][category].append(command_data)
        save_commands(custom_commands)
        logger.info(f"User {interaction.user} created command: {command_name} in category: {category}")
        await interaction.response.send_message(
            f"Custom command `{'cc!' if category == 'private' else 'pc!'}{command_name}` created successfully.",
            ephemeral=True
        )

class EditCommandModal(Modal):
    def __init__(self, bot, command, category):
        super().__init__(title=f"Edit Command: {'cc!' if category=='private' else 'pc!'}{command['name']}")
        self.bot = bot
        self.command = command
        self.category = category
        self.add_item(InputText(
            label="Command Output",
            style=discord.InputTextStyle.long,
            value=command['output'],
            max_length=500,
            required=True
        ))
        # Add fields for random_number and random_choice if needed
        random_number = command.get("random_number", {})
        random_number_range = f"{random_number.get('min', '')}-{random_number.get('max', '')}" if random_number else ""
        self.add_item(InputText(
            label="Random Number Range (Optional)",
            placeholder="e.g., 1-100",
            value=random_number_range,
            max_length=20,
            required=False
        ))
        random_choice_options = ', '.join(command.get("random_choice", []))
        self.add_item(InputText(
            label="Random Choice Options (Optional)",
            placeholder="e.g., Option1, Option2, Option3",
            value=random_choice_options,
            max_length=100,
            required=False
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
        description = self.children[4].value.strip() if self.children[4].value else self.command.get("description", "No description.")

        # Handle random number range
        random_number_input = self.children[1].value.strip()
        random_number = {}
        if random_number_input:
            try:
                min_val, max_val = map(int, random_number_input.split('-'))
                if min_val >= max_val:
                    await interaction.response.send_message(
                        "Random Number Range: Minimum must be less than Maximum.",
                        ephemeral=True
                    )
                    return
                random_number = {"min": min_val, "max": max_val}
            except ValueError:
                await interaction.response.send_message(
                    "Random Number Range: Please enter in the format `min-max`, e.g., `1-100`.",
                    ephemeral=True
                )
                return

        # Handle random choice options
        random_choice_input = self.children[2].value.strip()
        random_choice = []
        if random_choice_input:
            choices = [choice.strip() for choice in random_choice_input.split(',') if choice.strip()]
            if not choices:
                await interaction.response.send_message(
                    "Random Choice Options: Please provide at least one valid option.",
                    ephemeral=True
                )
                return
            random_choice = choices

        if len(command_output) > 500:
            await interaction.response.send_message(
                "Command output exceeds 500 characters.",
                ephemeral=True
            )
            return

        # Update the command in the correct category
        cmds = custom_commands.get(user_id, {})
        commands_list = cmds.get(self.category, [])
        for cmd in commands_list:
            if cmd["name"] == self.command['name']:
                cmd['output'] = command_output
                cmd['description'] = description
                cmd['edited_at'] = datetime.utcnow().isoformat()
                if random_number:
                    cmd['random_number'] = random_number
                else:
                    cmd.pop('random_number', None)
                if random_choice:
                    cmd['random_choice'] = random_choice
                else:
                    cmd.pop('random_choice', None)
                break

        save_commands(custom_commands)
        logger.info(f"User {interaction.user} edited command: {self.command['name']} in category: {self.category}")
        await interaction.response.send_message(
            f"Custom command `{'cc!' if self.category=='private' else 'pc!'}{self.command['name']}` has been updated.",
            ephemeral=True
        )

class ConfirmDeleteModal(Modal):
    def __init__(self, bot, user_id, command, category):
        super().__init__(title=f"Delete Command: {'cc!' if category=='private' else 'pc!'}{command['name']}")
        self.bot = bot
        self.user_id = user_id
        self.command = command
        self.category = category
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

        # Delete the command from the correct category
        custom_commands = self.bot.custom_commands
        cmds = custom_commands.get(self.user_id, {})
        commands_list = cmds.get(self.category, [])
        cmds[self.category] = [cmd for cmd in commands_list if cmd['name'] != self.command['name']]
        save_commands(custom_commands)
        logger.info(f"User {interaction.user} deleted command: {self.command['name']} from category: {self.category}")
        await interaction.response.send_message(
            f"Custom command `{'cc!' if self.category=='private' else 'pc!'}{self.command['name']}` has been deleted.",
            ephemeral=True
        )
