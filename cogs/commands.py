# cogs/commands.py
import discord
from discord.ext import commands
from discord.commands import Option
from discord import Embed
from modals import CreateCommandModal
from views import ManageCommandsView, SelectDuplicateCommandView
from utils import replace_placeholders
from data import load_commands, save_commands
import logging
import json
import os
from discord.ui import Select, View
from datetime import datetime

logger = logging.getLogger('CustomCommandBot')

def global_autocomplete_commands(ctx, cmd_type):
    user_id = str(ctx.interaction.user.id)
    cmds = ctx.bot.custom_commands.get(user_id, {})
    commands = cmds.get(cmd_type, [])
    # return a simple list of command names
    return [cmd['name'] for cmd in commands]

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.custom_commands = load_commands()
        self.active_views = []  # List to store active Views

    @commands.slash_command(name="createcmd", description="Create a custom command with cc! prefix")
    async def createcmd(self, ctx: discord.ApplicationContext):
        modal = CreateCommandModal(self.bot)
        await ctx.send_modal(modal)

    @commands.slash_command(name="cmdlist", description="List your custom commands")
    async def cmdlist(self, ctx: discord.ApplicationContext):
        user_id = str(ctx.author.id)
        cmds = self.bot.custom_commands.get(user_id, {})
        private_cmds = cmds.get("private", [])
        public_cmds = cmds.get("public", [])
        if not private_cmds and not public_cmds:
            await ctx.respond("You have no custom commands.", ephemeral=True)
            return
        embed = Embed(
            title=f"{ctx.author.name}'s Custom Commands",
            color=discord.Color.blue(),
            description="Use the menus below to manage your commands."
        )
        if private_cmds:
            embed.add_field(
                name="Private Commands (cc!)",
                value="\n".join([f"`cc!{cmd['name']}`: {cmd.get('description', 'No description.')}" for cmd in private_cmds]),
                inline=False
            )
        if public_cmds:
            embed.add_field(
                name="Public Commands (pc!)",
                value="\n".join([f"`pc!{cmd['name']}`: {cmd.get('description', 'No description.')}" for cmd in public_cmds]),
                inline=False
            )
        view = ManageCommandsView(self.bot, user_id)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @commands.slash_command(name="editcmd", description="Edit an existing custom command")
    async def editcmd(self, ctx: discord.ApplicationContext):
        await ctx.respond("Please use `/cmdlist` to manage your commands.", ephemeral=True)

    @commands.slash_command(name="deletecmd", description="Delete an existing custom command")
    async def deletecmd(self, ctx: discord.ApplicationContext):
        await ctx.respond("Please use `/cmdlist` to manage your commands.", ephemeral=True)

    @commands.slash_command(name="dtpcmd", description="Duplicate a private command to your public commands")
    async def dtpcmd(
        self,
        ctx: discord.ApplicationContext,
        command_name: Option(
            str,
            "The name of the private command you want to duplicate.",
            autocomplete=lambda ctx: global_autocomplete_commands(ctx, "private")
        )
    ):
        user_id = str(ctx.author.id)
        cmds = self.bot.custom_commands.get(user_id, {})
        private_cmds = cmds.get("private", [])
        public_cmds = cmds.get("public", [])

        # Check if the user has reached the public commands limit
        if len(public_cmds) >= 10:
            await ctx.respond("You have reached the maximum of 10 public commands.", ephemeral=True)
            return

        # Check global limit for the command name
        global_public_commands = []
        for uid, user_cmds in self.bot.custom_commands.items():
            for cmd in user_cmds.get("public", []):
                if cmd['name'] == command_name.lower():
                    global_public_commands.append((uid, cmd))
        if len(global_public_commands) >= 5:
            await ctx.respond(f"The public command name `{command_name}` has reached the global limit of 5.", ephemeral=True)
            return

        # Find the private command to duplicate
        command = next((cmd for cmd in private_cmds if cmd['name'] == command_name.lower()), None)
        if not command:
            await ctx.respond(f"You do not have a private command named `{command_name}`.", ephemeral=True)
            return

        # Check if a public command with the same name already exists for the user
        if any(cmd['name'] == command_name.lower() for cmd in public_cmds):
            await ctx.respond(f"You already have a public command named `{command_name}`.", ephemeral=True)
            return

        # Duplicate the command
        duplicated_command = {
            "name": command["name"],
            "output": command["output"],
            "description": command.get("description", "No description."),
            "created_at": datetime.utcnow().isoformat()
        }
        # Include random_number and random_choice if they exist
        if "random_number" in command:
            duplicated_command["random_number"] = command["random_number"]
        if "random_choice" in command:
            duplicated_command["random_choice"] = command["random_choice"]

        public_cmds.append(duplicated_command)
        cmds["public"] = public_cmds
        self.bot.custom_commands[user_id] = cmds
        save_commands(self.bot.custom_commands)

        logger.info(f"User {ctx.author} duplicated command `cc!{command_name}` to public commands.")
        await ctx.respond(f"Successfully duplicated `cc!{command_name}` to your public commands as `pc!{command_name}`.", ephemeral=True)

    async def autocomplete_commands(self, ctx: discord.AutocompleteContext, cmd_type: str):
        user_id = str(ctx.interaction.user.id)
        cmds = self.bot.custom_commands.get(user_id, {})
        commands = cmds.get(cmd_type, [])
        return [
            discord.SelectOption(label=cmd['name'], description=cmd.get('description', 'No description.'))
            for cmd in commands
        ]

    @commands.slash_command(name="placeholders", description="List available placeholders for custom commands")
    async def placeholders_cmd(self, ctx: discord.ApplicationContext):
        from config import PLACEHOLDERS
        embed = Embed(
            title="Available Placeholders",
            color=discord.Color.purple()
        )
        for group, data in PLACEHOLDERS.items():
            if group == "{[ ]}":
                # Special handling for Arguments placeholders
                embed.add_field(
                    name="Arguments Placeholders `{[<arg_name>]}`",
                    value="Use `{[<arg_name>]}` to include arguments in your command output. Provide corresponding arguments when invoking the command.",
                    inline=False
                )
                continue
            description = "\n".join([f"`{ph}`: {desc}" for ph, desc in data['placeholders'].items()])
            embed.add_field(name=f"{group} Placeholders ({data['type']})", value=description, inline=False)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="help", description="Show help information")
    async def help_command(self, ctx: discord.ApplicationContext):
        embed = Embed(
            title="Custom Command Bot Help",
            color=discord.Color.green(),
            description="Here are the commands you can use:"
        )
        embed.add_field(
            name="/createcmd",
            value="Create a new custom command with cc! prefix.",
            inline=False
        )
        embed.add_field(
            name="/cmdlist",
            value="List your custom commands and manage them.",
            inline=False
        )
        embed.add_field(
            name="/editcmd",
            value="Edit an existing custom command.",
            inline=False
        )
        embed.add_field(
            name="/deletecmd",
            value="Delete an existing custom command.",
            inline=False
        )
        embed.add_field(
            name="/dtpcmd",
            value="Duplicate a private command to your public commands.",
            inline=False
        )
        embed.add_field(
            name="/sfmcmd",
            value="Save a public command to your private commands.",
            inline=False
        )
        embed.add_field(
            name="/placeholders",
            value="List available placeholders you can use in your commands.",
            inline=False
        )
        embed.add_field(
            name="/sharecmd",
            value="Share your custom command with another user.",
            inline=False
        )
        embed.add_field(
            name="/help",
            value="Show this help message.",
            inline=False
        )
        embed.add_field(
            name="/docs",
            value="Get the bot's documentation.",
            inline=False
        )
        embed.add_field(
            name="Using Nano",
            value="Edit a file in your virtual filesystem.",
            inline=False
        )
        embed.set_footer(text="Use `cc!command_name` or `pc!command_name` to execute your custom commands.")
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="docs", description="Get the bot's documentation")
    async def docs(self, ctx: discord.ApplicationContext):
        documentation = """
# Custom Command Bot Documentation

## Overview

This bot allows users to create up to 10 custom text-based commands with the `cc!` prefix and 10 public commands with the `pc!` prefix. Customize your server experience by defining your own commands using placeholders.

## Commands

### `/createcmd`
Create a new private custom command.

- **Usage:** `/createcmd`
- **Process:** A modal will appear asking for the command name, output, optional random number range, optional random choice options, and an optional description.
- **Note:** You can include arguments in your command output using `{[<arg_name>]}`. Provide corresponding arguments when invoking the command.

### `/dtpcmd`
Duplicate a private custom command to your public commands.

- **Usage:** `/dtpcmd command_name:<command_name>`
- **Description:** Copies one of your private commands (`cc!command_name`) to your public commands (`pc!command_name`).
- **Note:** You can have up to 10 public commands and the global limit for each command name is 5.

### `/sfmcmd`
Save a public custom command to your private commands.

- **Usage:** `/sfmcmd command_name:<command_name>`
- **Description:** Copies a public command (`pc!command_name`) from any user to your private commands (`cc!command_name`).
- **Note:** If multiple users have a public command with the same name, you will be prompted to select which one to duplicate. You can only duplicate up to 5 public commands with the same name across all users.

### `/cmdlist`
List and manage your custom commands.

- **Usage:** `/cmdlist`
- **Description:** Displays all your private and public custom commands with options to edit or delete them.

### `/editcmd`
Edit an existing custom command.

- **Usage:** `/editcmd`
- **Description:** Use `/cmdlist` to select and edit your commands.

### `/deletecmd`
Delete an existing custom command.

- **Usage:** `/deletecmd`
- **Description:** Use `/cmdlist` to select and delete your commands.

### `/placeholders`
List available placeholders for custom commands.

- **Usage:** `/placeholders`
- **Description:** Displays all the placeholders you can use to make your commands dynamic.

### `/sharecmd`
Share your custom command with another user.

- **Usage:** `/sharecmd command:<command_name> target_user:<user>`
- **Description:** Sends the data of your custom command to the specified user via DM.

### `/help`
Show help information.

- **Usage:** `/help`
- **Description:** Provides information about all available commands.

### `/docs`
Get the bot's documentation.

- **Usage:** `/docs`
- **Description:** Sends this documentation as a Markdown file.

### `/nano`
Edit a file in your virtual filesystem.

- **Usage:** `/nano filename:<file_name>`
- **Description:** Opens a modal to edit the specified file. Note that this command will fail if the file is a binary file or exceeds 4000 characters.

## Using Custom Commands

- **Private Prefix:** `cc!`
- **Public Prefix:** `pc!`
- **Example:** If you create a private command named `greet`, use it by typing `cc!greet`. If you duplicate it to public, use it by typing `pc!greet`.

### Including Arguments

You can include arguments in your custom command outputs using the `{[<arg_name>]}` syntax. When invoking the command, provide the corresponding arguments in order.

**Example:**

1. **Creating a Command with Arguments:**
   - **Command Name:** `welcome`
   - **Command Output:** `Hello, {[<name>]}! Welcome to {servername}.`

2. **Invoking the Command:**
   - **Usage:** `cc!welcome Alice`
   - **Bot Response:** `Hello, Alice! Welcome to YourServerName.`

**Note:** Ensure that the number of arguments provided matches the number of `{[<arg_name>]}` placeholders in your command output.

## Placeholders

Custom command outputs can include placeholders that will be dynamically replaced when the command is executed. There are five types of placeholders:

### User Placeholders `[]`

- `[username]`: The user's name.
- `[user_id]`: The user's ID.
- `[user_mention]`: The user's mention.
- `[user_avatar]`: URL of the user's avatar.
- `[user_discriminator]`: The user's discriminator.
- `[user_created_at]`: The date the user's account was created.
- `[user_joined_at]`: The date the user joined the server.
- `[user_roles]`: List of the user's roles.
- `[user_status]`: The user's current status.

### Server Placeholders `{}`

- `{servername}`: The server's name.
- `{server_id}`: The server's ID.
- `{member_count}`: Number of members in the server.
- `{server_icon}`: URL of the server's icon.
- `{server_created_at}`: The date the server was created.
- `{server_region}`: The server's region.
- `{server_owner}`: The server's owner.
- `{server_boosts}`: Number of boosts the server has.
- `{server_banner}`: URL of the server's banner.
- `{server_description}`: The server's description.

### Dynamic Placeholders `<>`

- `<input1>`: First input parameter.
- `<input2>`: Second input parameter.
- `<input3>`: Third input parameter.
- `<current_time>`: The current server time.
- `<current_date>`: The current server date.
- `<random_number>`: A random number.
- `<random_choice>`: A random choice from predefined options.
- `<channel_name>`: The name of the channel where the command was used.
- `<channel_id>`: The ID of the channel where the command was used.
- `<message_id>`: The ID of the triggering message.

### Arguments Placeholders `{[<arg_name>]}`

- `{[<arg1>]}`: First argument provided when invoking the command.
- `{[<arg2>]}`: Second argument provided when invoking the command.
- *...and so on.*

### Orange Bank Placeholders `ob_`

- `ob_balance`: The user's balance from Orange Bank.
- `ob_inventory`: The user's inventory from Orange Bank.
- `ob_streak`: The user's bump streak from Orange Bank.
- `ob_messages`: The user's message count from Orange Bank.
- `ob_position_in_leaderboard`: The user's position in the message leaderboard from Orange Bank.
- `ob_daily_leaderboard_stats`: The user's daily leaderboard stats from Orange Bank.
- `ob_balance_leaderboard_stats`: The user's balance leaderboard stats from Orange Bank.
- `ob_all`: All data from Orange Bank.

## Limitations

- **Custom Commands per User:** Up to 10 private commands and 10 public commands.
- **Command Output Length:** 500 characters.
- **Command Description Length:** 150 characters.
- **Global Public Command Limit:** Up to 5 public commands with the same name across all users.

## Notes

- Only you can manage your own custom commands.
- Others can view your public commands using `/cmdlist`.
- Use placeholders to make your commands dynamic and personalized.

Enjoy customizing your Discord experience!
"""
        # Create a temporary file with the documentation
        with open("documentation.md", "w") as f:
            f.write(documentation)
        file = discord.File("documentation.md")
        await ctx.respond("Here is the documentation:", file=file, ephemeral=True)
        # Optionally, remove the file after sending
        os.remove("documentation.md")

    async def sharecmd_command_name_autocomplete(self, ctx: discord.AutocompleteContext):
        user_id = str(ctx.interaction.user.id)
        cmds = self.bot.custom_commands.get(user_id, {})
        private_cmds = cmds.get("private", [])
        return [
            cmd.get('name', 'No Name') for cmd in private_cmds
        ]

    @commands.slash_command(name="sharecmd", description="Share your custom command with another user.")
    async def sharecmd(
        self,
        ctx: discord.ApplicationContext,
        command_name: Option(str, "The name of the command you want to share.", autocomplete=sharecmd_command_name_autocomplete),
        target_user: Option(discord.User, "The user you want to share the command with.")
    ):
        user_id = str(ctx.author.id)
        cmds = self.bot.custom_commands.get(user_id, {})
        private_cmds = cmds.get("private", [])
        command = next((cmd for cmd in private_cmds if cmd['name'] == command_name.lower()), None)
        if not command:
            await ctx.respond(f"You do not have a command named `{command_name}`.", ephemeral=True)
            return

        # Prepare the command data to send
        command_data = {
            "name": command["name"],
            "output": command["output"],
            "description": command.get("description", "No description."),
            "created_at": command["created_at"]
        }
        if "random_number" in command:
            command_data["random_number"] = command["random_number"]
        if "random_choice" in command:
            command_data["random_choice"] = command["random_choice"]

        try:
            # Send DM to the target user
            dm_embed = Embed(
                title=f"Custom Command Shared by {ctx.author.name}",
                color=discord.Color.green(),
                description=f"You have received a custom command from {ctx.author.mention}."
            )
            dm_embed.add_field(name="Command Name", value=f"cc!{command_data['name']}", inline=False)
            dm_embed.add_field(name="Command Output", value=command_data['output'], inline=False)
            dm_embed.add_field(name="Description", value=command_data['description'], inline=False)
            dm_embed.add_field(name="Created At", value=command_data['created_at'], inline=False)
            if "random_number" in command_data:
                rn = command_data["random_number"]
                dm_embed.add_field(name="Random Number Range", value=f"{rn['min']} - {rn['max']}", inline=False)
            if "random_choice" in command_data:
                rc = command_data["random_choice"]
                dm_embed.add_field(name="Random Choice Options", value=', '.join(rc), inline=False)
            await target_user.send(embed=dm_embed)
            logger.info(f"{ctx.author} shared command `cc!{command_name}` with {target_user}")
            await ctx.respond(f"Successfully shared `cc!{command_name}` with {target_user}.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond(f"Could not send a DM to {target_user}. They might have DMs disabled.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error sharing command: {e}")
            await ctx.respond("An error occurred while trying to share the command.", ephemeral=True)

    @commands.slash_command(name="sfmcmd", description="Save a public command to your private commands.")
    async def sfmcmd(
        self,
        ctx: discord.ApplicationContext,
        command_name: Option(
            str,
            "The name of the public command you want to save.",
            autocomplete=lambda ctx: global_autocomplete_commands(ctx, "public")
        )
    ):
        command_name = command_name.lower()
        user_id = str(ctx.author.id)

        # Find all public commands with the given name across all users
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
            await ctx.respond(f"No public command named `{command_name}` found.", ephemeral=True)
            return

        if len(matching_commands) == 1:
            # Only one match, duplicate directly
            source_uid, source_cmd = matching_commands[0]
            await self.duplicate_public_to_private(ctx, user_id, source_uid, source_cmd)
        else:
            embed = Embed(
                title="Multiple Public Commands Found",
                description=f"There are multiple public commands named `{command_name}`. Please select which one you want to save to your private commands.",
                color=discord.Color.orange()
            )
            for i, (uid, cmd) in enumerate(matching_commands, start=1):
                user = self.bot.get_user(int(uid))
                embed.add_field(
                    name=f"Option {i}",
                    value=f"**User:** {user.name}#{user.discriminator}\n**Description:** {cmd.get('description', 'No description.')}",
                    inline=False
                )
            view = SelectDuplicateCommandView(self.bot, ctx, command_name, matching_commands)
            self.active_views.append(view)  # Store the View
            await ctx.respond(embed=embed, view=view, ephemeral=True)

    async def duplicate_public_to_private(self, interaction, target_user_id, source_user_id, command):
        # Ensure the target user has not exceeded private commands limit
        cmds = self.bot.custom_commands.get(target_user_id, {})
        private_cmds = cmds.get("private", [])

        if len(private_cmds) >= 10:
            await interaction.response.send_message("You have reached the maximum of 10 private commands.", ephemeral=True)
            return

        # Check for duplicate in private commands
        if any(cmd['name'] == command['name'] for cmd in private_cmds):
            await interaction.response.send_message(f"You already have a private command named `cc!{command['name']}`.", ephemeral=True)
            return

        # Duplicate the command
        duplicated_command = {
            "name": command["name"],
            "output": command["output"],
            "description": command.get("description", "No description."),
            "created_at": datetime.utcnow().isoformat()
        }
        # Include random_number and random_choice if they exist
        if "random_number" in command:
            duplicated_command["random_number"] = command["random_number"]
        if "random_choice" in command:
            duplicated_command["random_choice"] = command["random_choice"]

        private_cmds.append(duplicated_command)
        cmds["private"] = private_cmds
        self.bot.custom_commands[target_user_id] = cmds
        save_commands(self.bot.custom_commands)

        source_user = self.bot.get_user(int(source_user_id))
        await interaction.response.send_message(f"Successfully saved `pc!{command['name']}` from <@{source_user_id}> to your private commands as `cc!{command['name']}`.", ephemeral=True)
        logger.info(f"User {interaction.user} saved command `pc!{command['name']}` from user {source_user_id} to private commands.")

