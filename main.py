import discord
from discord import Option, Embed
from discord.ui import Modal, InputText, View, Button, Select
import json
import os
from typing import List, Dict, Union
from datetime import datetime
import dotenv
import logging
import random
import re  # Import regex module

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CustomCommandBot')

# Load environment variables
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for accessing member information

bot = discord.Bot(intents=intents)

# Path to store custom commands
COMMANDS_FILE = "custom_commands.json"

# Load existing custom commands or initialize empty dictionary
if os.path.exists(COMMANDS_FILE):
    with open(COMMANDS_FILE, "r") as f:
        custom_commands = json.load(f)
else:
    custom_commands = {}

# Define placeholders
PLACEHOLDERS = {
    "[]": {
        "type": "user",
        "placeholders": {
            "[username]": "The user's name",
            "[user_id]": "The user's ID",
            "[user_mention]": "The user's mention",
            "[user_avatar]": "URL of the user's avatar",
            "[user_discriminator]": "The user's discriminator",
            "[user_created_at]": "The date the user's account was created",
            "[user_joined_at]": "The date the user joined the server",
            "[user_roles]": "List of the user's roles",
            "[user_status]": "The user's current status",
        }
    },
    "{}": {
        "type": "server",
        "placeholders": {
            "{servername}": "The server's name",
            "{server_id}": "The server's ID",
            "{member_count}": "Number of members in the server",
            "{server_icon}": "URL of the server's icon",
            "{server_created_at}": "The date the server was created",
            "{server_region}": "The server's region",
            "{server_owner}": "The server's owner",
            "{server_boosts}": "Number of boosts the server has",
            "{server_banner}": "URL of the server's banner",
            "{server_description}": "The server's description",
        }
    },
    "<>": {
        "type": "dynamic",
        "placeholders": {
            "<input1>": "First input parameter",
            "<input2>": "Second input parameter",
            "<input3>": "Third input parameter",
            "<current_time>": "The current server time",
            "<current_date>": "The current server date",
            "<random_number>": "A random number",
            "<random_choice>": "A random choice from predefined options",
            "<channel_name>": "The name of the channel where the command was used",
            "<channel_id>": "The ID of the channel where the command was used",
            "<message_id>": "The ID of the triggering message",
        }
    },
    "{[ ]}": {  # New Arguments placeholder group
        "type": "arguments",
        "placeholders": {}  # Dynamic placeholders, handled via regex
    }
}

# Save custom commands to file
def save_commands():
    with open(COMMANDS_FILE, "w") as f:
        json.dump(custom_commands, f, indent=4)
    logger.info("Custom commands saved.")

# Modal for creating a custom command
class CreateCommandModal(Modal):
    def __init__(self):
        super().__init__(title="Create Custom Command")
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
        save_commands()
        logger.info(f"User {interaction.user} created command: {command_name}")
        await interaction.response.send_message(
            f"Custom command `cc!{command_name}` created successfully.",
            ephemeral=True
        )

# Modal for editing a custom command
class EditCommandModal(Modal):
    def __init__(self, command):
        super().__init__(title=f"Edit Command: cc!{command['name']}")
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
        save_commands()
        logger.info(f"User {interaction.user} edited command: {self.command['name']}")
        await interaction.response.send_message(
            f"Custom command `cc!{self.command['name']}` has been updated.",
            ephemeral=True
        )

class ManageCommandsView(View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        cmds = custom_commands.get(user_id, [])
        options = [
            discord.SelectOption(label=cmd['name'], description=cmd.get('description', 'No description.'))
            for cmd in cmds
        ]
        self.options = options
        if options:
            self.add_item(SelectCommandSelect(user_id, options))
        else:
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="No Commands", disabled=True))
        
    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)

class SelectCommandSelect(discord.ui.Select):
    def __init__(self, user_id, options):
        super().__init__(placeholder="Select a command to manage...", min_values=1, max_values=1, options=options)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        selected_cmd = self.values[0]
        user_id = str(interaction.user.id)
        cmds = custom_commands.get(user_id, [])
        command = next((cmd for cmd in cmds if cmd['name'] == selected_cmd), None)
        if not command:
            await interaction.response.send_message("Command not found.", ephemeral=True)
            return
        # Create buttons for Edit and Delete
        view = CommandManagementButtons(user_id, command)
        await interaction.response.send_message(
            f"Managing command `cc!{command['name']}`.",
            view=view,
            ephemeral=True
        )

class CommandManagementButtons(View):
    def __init__(self, user_id, command):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.command = command

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, button: Button, interaction: discord.Interaction):
        modal = EditCommandModal(self.command)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_modal(ConfirmDeleteModal(self.user_id, self.command))

class ConfirmDeleteModal(Modal):
    def __init__(self, user_id, command):
        super().__init__(title=f"Delete Command: cc!{command['name']}")
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
        cmds = custom_commands.get(self.user_id, [])
        custom_commands[self.user_id] = [cmd for cmd in cmds if cmd['name'] != self.command['name']]
        save_commands()
        logger.info(f"User {interaction.user} deleted command: {self.command['name']}")
        await interaction.response.send_message(
            f"Custom command `cc!{self.command['name']}` has been deleted.",
            ephemeral=True
        )

# Slash command to create a custom command
@bot.slash_command(name="createcmd", description="Create a custom command with cc! prefix")
async def createcmd(ctx: discord.ApplicationContext):
    modal = CreateCommandModal()
    await ctx.send_modal(modal)

# Slash command to list custom commands with management options
@bot.slash_command(name="cmdlist", description="List your custom commands")
async def cmdlist(ctx: discord.ApplicationContext):
    user_id = str(ctx.author.id)
    cmds = custom_commands.get(user_id, [])
    if not cmds:
        await ctx.respond("You have no custom commands.", ephemeral=True)
        return
    embed = Embed(
        title=f"{ctx.author.name}'s Custom Commands",
        color=discord.Color.blue(),
        description="Use the buttons below to manage your commands."
    )
    for cmd in cmds:
        embed.add_field(
            name=f"cc!{cmd['name']}",
            value=cmd.get('description', 'No description.'),
            inline=False
        )
    view = ManageCommandsView(user_id)
    await ctx.respond(embed=embed, view=view, ephemeral=True)

# Slash command to edit a custom command
@bot.slash_command(name="editcmd", description="Edit an existing custom command")
async def editcmd(ctx: discord.ApplicationContext):
    # Implementation can be similar to ManageCommandsView
    await ctx.respond("Please use `/cmdlist` to manage your commands.", ephemeral=True)

# Slash command to delete a custom command
@bot.slash_command(name="deletecmd", description="Delete an existing custom command")
async def deletecmd(ctx: discord.ApplicationContext):
    # Implementation can be similar to ManageCommandsView
    await ctx.respond("Please use `/cmdlist` to manage your commands.", ephemeral=True)

# Slash command to list available placeholders
@bot.slash_command(name="placeholders", description="List available placeholders for custom commands")
async def placeholders(ctx: discord.ApplicationContext):
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

# Helper function to replace placeholders
def replace_placeholders(output: str, ctx: Union[discord.Message, discord.ApplicationContext], params: Dict[str, str]) -> str:
    # Replace user placeholders []
    for placeholder, description in PLACEHOLDERS["[]"]["placeholders"].items():
        if placeholder in output:
            if placeholder == "[username]":
                output = output.replace(placeholder, ctx.author.name)
            elif placeholder == "[user_id]":
                output = output.replace(placeholder, str(ctx.author.id))
            elif placeholder == "[user_mention]":
                output = output.replace(placeholder, ctx.author.mention)
            elif placeholder == "[user_avatar]":
                output = output.replace(placeholder, str(ctx.author.avatar.url) if ctx.author.avatar else "No Avatar")
            elif placeholder == "[user_discriminator]":
                output = output.replace(placeholder, ctx.author.discriminator)
            elif placeholder == "[user_created_at]":
                output = output.replace(placeholder, ctx.author.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            elif placeholder == "[user_joined_at]":
                if isinstance(ctx, discord.Message):
                    member = ctx.guild.get_member(ctx.author.id)
                else:
                    member = ctx.guild.get_member(ctx.author.id)
                if member and member.joined_at:
                    output = output.replace(placeholder, member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    output = output.replace(placeholder, "N/A")
            elif placeholder == "[user_roles]":
                if isinstance(ctx, discord.Message):
                    roles = [role.name for role in ctx.author.roles if role.name != "@everyone"]
                else:
                    roles = [role.name for role in ctx.author.roles if role.name != "@everyone"]
                output = output.replace(placeholder, ", ".join(roles) if roles else "None")
            elif placeholder == "[user_status]":
                output = output.replace(placeholder, str(ctx.author.status).title())

    # Replace server placeholders {}
    for placeholder, description in PLACEHOLDERS["{}"]["placeholders"].items():
        if placeholder in output:
            if placeholder == "{servername}":
                output = output.replace(placeholder, ctx.guild.name)
            elif placeholder == "{server_id}":
                output = output.replace(placeholder, str(ctx.guild.id))
            elif placeholder == "{member_count}":
                output = output.replace(placeholder, str(ctx.guild.member_count))
            elif placeholder == "{server_icon}":
                output = output.replace(placeholder, str(ctx.guild.icon.url) if ctx.guild.icon else "No Icon")
            elif placeholder == "{server_created_at}":
                output = output.replace(placeholder, ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            elif placeholder == "{server_region}":
                # Note: Discord has removed server regions; you might want to update or remove this placeholder
                output = output.replace(placeholder, "N/A")
            elif placeholder == "{server_owner}":
                owner = ctx.guild.owner
                output = output.replace(placeholder, owner.name if owner else "Unknown")
            elif placeholder == "{server_boosts}":
                output = output.replace(placeholder, str(ctx.guild.premium_subscription_count))
            elif placeholder == "{server_banner}":
                output = output.replace(placeholder, str(ctx.guild.banner.url) if ctx.guild.banner else "No Banner")
            elif placeholder == "{server_description}":
                output = output.replace(placeholder, ctx.guild.description if ctx.guild.description else "No Description")

    # Replace dynamic placeholders <>
    for placeholder, description in PLACEHOLDERS["<>"]["placeholders"].items():
        if placeholder in output:
            if placeholder == "<input1>":
                output = output.replace(placeholder, params.get("input1", ""))
            elif placeholder == "<input2>":
                output = output.replace(placeholder, params.get("input2", ""))
            elif placeholder == "<input3>":
                output = output.replace(placeholder, params.get("input3", ""))
            elif placeholder == "<current_time>":
                output = output.replace(placeholder, datetime.now().strftime("%H:%M:%S"))
            elif placeholder == "<current_date>":
                output = output.replace(placeholder, datetime.now().strftime("%Y-%m-%d"))
            elif placeholder == "<random_number>":
                output = output.replace(placeholder, str(random.randint(1000, 9999)))
            elif placeholder == "<random_choice>":
                choices = ["Option1", "Option2", "Option3"]
                output = output.replace(placeholder, random.choice(choices))
            elif placeholder == "<channel_name>":
                output = output.replace(placeholder, ctx.channel.name)
            elif placeholder == "<channel_id>":
                output = output.replace(placeholder, str(ctx.channel.id))
            elif placeholder == "<message_id>":
                if isinstance(ctx, discord.Message):
                    output = output.replace(placeholder, str(ctx.id))
                else:
                    output = output.replace(placeholder, str(ctx.id))

    # Replace Arguments placeholders {[<arg_name>]}
    arg_pattern = re.compile(r"\{\[\<(\w+)\>\]\}")  # matches {[<arg_name>]}
    matches = arg_pattern.findall(output)
    for arg_name in matches:
        value = params.get(arg_name, "")
        output = re.sub(r"\{\[\<" + re.escape(arg_name) + r"\>\]\}", value.strip(), output)
    
    return output

# Slash command to show help
@bot.slash_command(name="help", description="Show help information")
async def help_command(ctx: discord.ApplicationContext):
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

# Slash command to send documentation
@bot.slash_command(name="docs", description="Get the bot's documentation")
async def docs(ctx: discord.ApplicationContext):
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

async def sharecmd_command_name_autocomplete(ctx: discord.AutocompleteContext):
    user_id = str(ctx.interaction.user.id)
    cmds = custom_commands.get(user_id, [])
    return [
        cmd.get('name', 'No Name') for cmd in cmds
    ]

# New Slash command to share custom commands
@bot.slash_command(name="sharecmd", description="Share your custom command with another user.")
async def sharecmd(
    ctx: discord.ApplicationContext,
    command_name: Option(str, "The name of the command you want to share.", autocomplete=sharecmd_command_name_autocomplete),
    target_user: Option(discord.User, "The user you want to share the command with.")
):
    user_id = str(ctx.author.id)
    cmds = custom_commands.get(user_id, [])
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

# Listen to messages for custom commands
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not message.content.startswith("cc!"):
        return
    content = message.content[3:].strip()
    if not content:
        await message.channel.send("Please provide a command name.")
        return
    parts = content.split()
    command_name = parts[0].lower()
    user_id = str(message.author.id)
    cmds = custom_commands.get(user_id, [])
    command = next((cmd for cmd in cmds if cmd['name'] == command_name), None)
    if not command:
        await message.channel.send("Custom command not found.")
        logger.warning(f"Command `cc!{command_name}` not found for user {message.author}")
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
    output = replace_placeholders(command["output"], message, params)
    await message.channel.send(output)
    logger.info(f"Command `cc!{command_name}` used by {message.author}")

# Run the bot
bot.run(os.getenv("TOKEN"))
