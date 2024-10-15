# views.py
import discord
from discord.ui import View, Button, Select
from modals import EditCommandModal, ConfirmDeleteModal
from data import save_commands
import logging

logger = logging.getLogger('CustomCommandBot')

class ManageCommandsView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
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

class SelectDuplicateCommandView(View):
    def __init__(self, bot, ctx, command_name, matching_commands):
        super().__init__(timeout=60)  # Set a timeout for the View
        self.bot = bot
        self.ctx = ctx  # Store the context to reference later
        self.command_name = command_name
        self.matching_commands = matching_commands  # List of tuples (uid, cmd)

        # Create Select Options
        options = [
            discord.SelectOption(
                label=f"User: {self.bot.get_user(int(uid)).name}#{self.bot.get_user(int(uid)).discriminator}",
                value=uid,
                description=cmd.get('description', 'No description.')
            )
            for uid, cmd in matching_commands
        ]

        # Add the Select to the View
        self.add_item(SelectDuplicateCommandSelect(self, options))

    async def on_timeout(self):
        # Disable all components when the View times out
        for child in self.children:
            child.disabled = True
        try:
            await self.ctx.edit_original_response(view=self)
        except Exception as e:
            logger.error(f"Error disabling View on timeout: {e}")

class SelectDuplicateCommandSelect(Select):
    def __init__(self, parent_view, options):
        super().__init__(
            placeholder="Select which user's command to duplicate...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Manually verify the user
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message(
                "You are not authorized to use this select menu.",
                ephemeral=True
            )
            return

        selected_uid = self.values[0]
        command = next((cmd for uid, cmd in self.parent_view.matching_commands if uid == selected_uid), None)
        if not command:
            await interaction.response.send_message("Selected command not found.", ephemeral=True)
            return

        try:
            # Duplicate the command
            commands_cog = self.parent_view.bot.get_cog('CommandsCog')
            if not commands_cog:
                await interaction.response.send_message("CommandsCog not found.", ephemeral=True)
                return

            await commands_cog.duplicate_public_to_private(
                ctx=interaction,  # Use interaction as ctx
                target_user_id=str(interaction.user.id),
                source_user_id=selected_uid,
                command=command
            )

            # Stop the View to prevent further interactions
            self.parent_view.stop()
        except Exception as e:
            logger.error(f"Error duplicating command: {e}")
            await interaction.response.send_message(
                "An error occurred while duplicating the command.",
                ephemeral=True
            )

class SelectExecuteCommandView(View):
    def __init__(self, bot, ctx, command_name, matching_commands, args):
        super().__init__(timeout=60)  # Set a timeout for the View
        self.bot = bot
        self.ctx = ctx  # Original message
        self.command_name = command_name
        self.matching_commands = matching_commands  # List of tuples (uid, cmd)
        self.args = args  # Store the original arguments

        # Create Select Options
        options = [
            discord.SelectOption(
                label=f"User: {self.bot.get_user(int(uid)).name}#{self.bot.get_user(int(uid)).discriminator}",
                value=uid,
                description=cmd.get('description', 'No description.')
            )
            for uid, cmd in matching_commands
        ]

        # Add the Select to the View
        self.add_item(SelectExecuteCommandSelect(self, options))

    async def on_timeout(self):
        # Disable all components when the View times out
        for child in self.children:
            child.disabled = True
        try:
            await self.ctx.edit_original_response(view=self)
        except Exception as e:
            logger.error(f"Error disabling View on timeout: {e}")

class SelectExecuteCommandSelect(Select):
    def __init__(self, parent_view, options):
        super().__init__(
            placeholder="Select which user's command to execute...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Verify the user is the one who initiated the command
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message(
                "You are not authorized to use this select menu.",
                ephemeral=True
            )
            return

        selected_uid = self.values[0]
        command = next((cmd for uid, cmd in self.parent_view.matching_commands if uid == selected_uid), None)
        if not command:
            await interaction.response.send_message("Selected command not found.", ephemeral=True)
            return

        try:
            # Execute the command with stored arguments
            events_cog = self.parent_view.bot.get_cog('EventsCog')
            if not events_cog:
                await interaction.response.send_message("EventsCog not found.", ephemeral=True)
                return

            await events_cog.execute_public_command(
                message=self.parent_view.ctx,  # Pass the original message
                command=command,
                source_uid=selected_uid,
                args=self.parent_view.args  # Pass the stored arguments
            )

            await interaction.response.send_message(
                f"Executed `pc!{command['name']}` from <@{selected_uid}>.",
                ephemeral=True
            )

            # Stop the View to prevent further interactions
            self.parent_view.stop()
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )