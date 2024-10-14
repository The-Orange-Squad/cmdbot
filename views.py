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
        self.current_category = 'private'  # Default to 'private'
        self.message = None  # Reference to the message for editing

        # Add a select menu to choose between Private and Public commands
        category_options = [
            discord.SelectOption(label='Private Commands', value='private', description='Your cc! commands'),
            discord.SelectOption(label='Public Commands', value='public', description='Your pc! commands')
        ]
        self.category_select = CommandCategorySelect(self, category_options)
        self.add_item(self.category_select)

        # Initialize the commands select menu
        self.commands_select = None
        self.update_commands_select()

    async def send_initial_message(self, ctx, embed):
        self.message = await ctx.respond(embed=embed, view=self, ephemeral=True)

    def update_commands_select(self):
        # Retrieve the commands based on the current category
        custom_commands = self.bot.custom_commands
        cmds = custom_commands.get(self.user_id, {})
        commands_list = cmds.get(self.current_category, [])

        # Create options for the commands select menu
        options = [
            discord.SelectOption(
                label=cmd['name'],
                description=cmd.get('description', 'No description.')
            )
            for cmd in commands_list
        ]

        # Remove the old commands select if it exists
        if self.commands_select:
            self.remove_item(self.commands_select)

        # Create a new commands select menu
        if options:
            self.commands_select = CommandSelect(self, options)
            self.add_item(self.commands_select)
        else:
            self.commands_select = None  # No commands to display

        # Remove existing management buttons if any
        self.remove_management_buttons()

    def remove_management_buttons(self):
        for child in self.children[:]:
            if isinstance(child, CommandManagementButtons):
                self.remove_item(child)

    async def update_view(self, interaction):
        # Update the embed and view when the category changes
        embed = discord.Embed(
            title=f"{interaction.user.name}'s {self.current_category.capitalize()} Commands",
            color=discord.Color.blue(),
            description="Select a command to manage."
        )
        self.update_commands_select()
        await interaction.response.edit_message(embed=embed, view=self)

class CommandCategorySelect(Select):
    def __init__(self, parent_view, options):
        super().__init__(placeholder="Select command category...", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Update the current category in the parent view
        self.parent_view.current_category = self.values[0]
        # Remove any existing management buttons
        self.parent_view.remove_management_buttons()
        # Update the view
        await self.parent_view.update_view(interaction)

class CommandSelect(Select):
    def __init__(self, parent_view, options):
        super().__init__(
            placeholder="Select a command to manage...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        selected_cmd_name = self.values[0]
        user_id = self.parent_view.user_id
        custom_commands = self.parent_view.bot.custom_commands
        cmds = custom_commands.get(user_id, {})
        commands_list = cmds.get(self.parent_view.current_category, [])

        # Find the selected command
        command = next((cmd for cmd in commands_list if cmd['name'] == selected_cmd_name), None)

        if not command:
            await interaction.response.send_message("Command not found.", ephemeral=True)
            return

        # Remove existing management buttons
        self.parent_view.remove_management_buttons()

        # Add new management buttons
        management_buttons = CommandManagementButtons(
            self.parent_view.bot,
            self.parent_view.user_id,
            command,
            self.parent_view.current_category
        )
        # add the buttons one by one
        self.parent_view.add_item(management_buttons.edit_button)
        self.parent_view.add_item(management_buttons.delete_button)

        await interaction.response.edit_message(view=self.parent_view)

class CommandManagementButtons(View):
    def __init__(self, bot, user_id, command, category):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.command = command
        self.category = category  # 'private' or 'public'

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, button: Button, interaction: discord.Interaction):
        modal = EditCommandModal(self.bot, self.command, self.category)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(self, button: Button, interaction: discord.Interaction):
        modal = ConfirmDeleteModal(self.bot, self.user_id, self.command, self.category)
        await interaction.response.send_modal(modal)