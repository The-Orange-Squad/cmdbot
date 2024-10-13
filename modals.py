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
        
        custom_commands[user_id].append(command_data)
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
        # Add fields for custom random_number
        random_number = command.get("random_number", {})
        random_number_range = f"{random_number['min']}-{random_number['max']}" if random_number else ""
        self.add_item(InputText(
            label="Random Number Range (Optional)",
            placeholder="e.g., 1-100",
            value=random_number_range,
            max_length=20,
            required=False
        ))
        # Add fields for custom random_choice
        random_choice_options = ', '.join(command["random_choice"]) if "random_choice" in command else ""
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
        
        # Handle custom random_number range
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
        
        # Handle custom random_choice options
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
        
        # Update the command
        for cmd in custom_commands[user_id]:
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
