# views.py
import discord
from discord.ui import View, Button, Select
from modals import EditCommandModal, ConfirmDeleteModal
from data import save_commands
import logging

logger = logging.getLogger('CustomCommandBot')

class ManageCommandsView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        custom_commands = self.bot.custom_commands
        cmds = custom_commands.get(user_id, [])
        options = [
            discord.SelectOption(label=cmd['name'], description=cmd.get('description', 'No description.'))
            for cmd in cmds
        ]
        if options:
            self.add_item(SelectCommandSelect(bot, user_id, options))
        else:
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="No Commands", disabled=True))

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)

class SelectCommandSelect(Select):
    def __init__(self, bot, user_id, options):
        super().__init__(placeholder="Select a command to manage...", min_values=1, max_values=1, options=options)
        self.bot = bot
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        selected_cmd = self.values[0]
        user_id = str(interaction.user.id)
        custom_commands = self.bot.custom_commands
        cmds = custom_commands.get(user_id, [])
        command = next((cmd for cmd in cmds if cmd['name'] == selected_cmd), None)
        if not command:
            await interaction.response.send_message("Command not found.", ephemeral=True)
            return
        # Create buttons for Edit and Delete
        view = CommandManagementButtons(self.bot, user_id, command)
        await interaction.response.send_message(
            f"Managing command `cc!{command['name']}`.",
            view=view,
            ephemeral=True
        )

class CommandManagementButtons(View):
    def __init__(self, bot, user_id, command):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.command = command

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, button: Button, interaction: discord.Interaction):
        modal = EditCommandModal(self.bot, self.command)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(self, button: Button, interaction: discord.Interaction):
        modal = ConfirmDeleteModal(self.bot, self.user_id, self.command)
        await interaction.response.send_modal(modal)
