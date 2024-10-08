# cogs/commands.py
import discord
from discord.ext import commands
from discord import Option, Embed
from modals import CreateCommandModal
from views import ManageCommandsView
from utils import replace_placeholders
from data import load_commands, save_commands
import logging
import json
import os

logger = logging.getLogger('CustomCommandBot')

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.custom_commands = load_commands()

    @commands.slash_command(name="createcmd", description="Create a custom command with cc! prefix")
    async def createcmd(self, ctx: discord.ApplicationContext):
        modal = CreateCommandModal(self.bot)
        await ctx.send_modal(modal)

    @commands.slash_command(name="cmdlist", description="List your custom commands")
    async def cmdlist(self, ctx: discord.ApplicationContext):
        user_id = str(ctx.author.id)
        cmds = self.bot.custom_commands.get(user_id, [])
        if not cmds:
            await ctx.respond("You have no custom commands.", ephemeral=True)
            return
        embed = Embed(
            title=f"{ctx.author.name}'s Custom Commands",
            color=discord.Color.blue(),
            description="Use the menus below to manage your commands."
        )
        for cmd in cmds:
            embed.add_field(
                name=f"cc!{cmd['name']}",
                value=cmd.get('description', 'No description.'),
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
        embed.set_footer(text="Use `cc!command_name` to execute your custom command.")
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="docs", description="Get the bot's documentation")
    async def docs(self, ctx: discord.ApplicationContext):
        documentation = """
# Custom Command Bot Documentation

## Overview

This bot allows users to create up to 10 custom text-based commands with the `cc!` prefix. Customize your server experience by defining your own commands using placeholders.

## Commands

### `/createcmd`
Create a new custom command.

- **Usage:** `/createcmd`
- **Process:** A modal will appear asking for the command name, output, and an optional description.
- **Note:** You can include arguments in your command output using `{[<arg_name>]}`. Provide corresponding arguments when invoking the command.

### `/cmdlist`
List and manage your custom commands.

- **Usage:** `/cmdlist`
- **Description:** Displays all your custom commands with options to edit or delete them.

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

## Using Custom Commands

- **Prefix:** `cc!`
- **Example:** If you create a command named `greet`, use it by typing `cc!greet`.

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

Custom command outputs can include placeholders that will be dynamically replaced when the command is executed. There are four types of placeholders:

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

## Examples

### Creating a Greeting Command with Arguments

1. Use `/createcmd`.
2. Enter `greet` as the command name.
3. Enter `Hello, {[<name>]}! Welcome to {servername}.` as the command output.
4. (Optional) Add a description like "Greets the user with their name."
5. Save the command.

Now, when you type `cc!greet Alice`, the bot will respond with `Hello, Alice! Welcome to YourServerName.`

## Sharing Commands

### Sharing a Command with Another User

1. Use `/sharecmd`.
2. Select the command you want to share.
3. Specify the target user you want to share the command with.
4. Confirm the sharing action.

The target user will receive a DM containing the data of your shared command, which they can choose to add to their own custom commands.

## Limitations

- **Custom Commands per User:** Up to 10.
- **Command Output Length:** 500 characters.
- **Command Description Length:** 150 characters.

## Notes

- Only you can manage your own custom commands.
- Others can view your command list using `/cmdlist`.
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
        cmds = self.bot.custom_commands.get(user_id, [])
        return [
            cmd.get('name', 'No Name') for cmd in cmds
        ]

    @commands.slash_command(name="sharecmd", description="Share your custom command with another user.")
    async def sharecmd(
        self,
        ctx: discord.ApplicationContext,
        command_name: Option(str, "The name of the command you want to share.", autocomplete=sharecmd_command_name_autocomplete),
        target_user: Option(discord.User, "The user you want to share the command with.")
    ):
        user_id = str(ctx.author.id)
        cmds = self.bot.custom_commands.get(user_id, [])
        command = next((cmd for cmd in cmds if cmd['name'] == command_name.lower()), None)
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
            await target_user.send(embed=dm_embed)
            logger.info(f"{ctx.author} shared command `cc!{command_name}` with {target_user}")
            await ctx.respond(f"Successfully shared `cc!{command_name}` with {target_user}.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond(f"Could not send a DM to {target_user}. They might have DMs disabled.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error sharing command: {e}")
            await ctx.respond("An error occurred while trying to share the command.", ephemeral=True)
