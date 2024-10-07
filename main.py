import discord
from discord import Option
from discord.ui import Modal, InputText, View, Button
import json
import os
from typing import List, Dict
from datetime import datetime
import dotenv

# Load environment variables
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

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
    }
}

# Save custom commands to file
def save_commands():
    with open(COMMANDS_FILE, "w") as f:
        json.dump(custom_commands, f, indent=4)

# Modal for creating a custom command
class CreateCommandModal(Modal):
    def __init__(self):
        super().__init__(title="Create Custom Command")
        self.add_item(InputText(label="Command Name (without cc!)", max_length=50))
        self.add_item(InputText(label="Command Output", style=discord.InputTextStyle.long, max_length=500))

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in custom_commands:
            custom_commands[user_id] = []
        if len(custom_commands[user_id]) >= 5:
            await interaction.response.send_message("You can only have up to 5 custom commands.", ephemeral=True)
            return
        command_name = self.children[0].value.strip()
        if not command_name.isalnum():
            await interaction.response.send_message("Command name must be alphanumeric.", ephemeral=True)
            return
        for cmd in custom_commands[user_id]:
            if cmd["name"] == command_name:
                await interaction.response.send_message("You already have a command with that name.", ephemeral=True)
                return
        command_output = self.children[1].value.strip()
        if len(command_output) > 500:
            await interaction.response.send_message("Command output exceeds 500 characters.", ephemeral=True)
            return
        custom_commands[user_id].append({
            "name": command_name,
            "output": command_output
        })
        save_commands()
        await interaction.response.send_message(f"Custom command `cc!{command_name}` created successfully.", ephemeral=True)

# Slash command to create a custom command
@bot.slash_command(name="createcmd", description="Create a custom command with cc! prefix")
async def createcmd(ctx: discord.ApplicationContext):
    modal = CreateCommandModal()
    await ctx.send_modal(modal)

# Slash command to list custom commands
@bot.slash_command(name="cmdlist", description="List your custom commands")
async def cmdlist(ctx: discord.ApplicationContext):
    user_id = str(ctx.author.id)
    cmds = custom_commands.get(user_id, [])
    if not cmds:
        await ctx.respond("You have no custom commands.", ephemeral=True)
        return
    embed = discord.Embed(title=f"{ctx.author.name}'s Custom Commands", color=discord.Color.blue())
    for cmd in cmds:
        embed.add_field(name=f"cc!{cmd['name']}", value=cmd['output'], inline=False)
    await ctx.respond(embed=embed, ephemeral=True)

# Helper function to replace placeholders
def replace_placeholders(output: str, ctx: discord.ApplicationContext, params: Dict[str, str]) -> str:
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
                output = output.replace(placeholder, str(ctx.author.avatar.url))
            elif placeholder == "[user_discriminator]":
                output = output.replace(placeholder, ctx.author.discriminator)
            elif placeholder == "[user_created_at]":
                output = output.replace(placeholder, ctx.author.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            elif placeholder == "[user_joined_at]":
                member = ctx.guild.get_member(ctx.author.id)
                if member:
                    output = output.replace(placeholder, member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    output = output.replace(placeholder, "N/A")
            elif placeholder == "[user_roles]":
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
                output = output.replace(placeholder, str(ctx.guild.region).title())
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
                output = output.replace(placeholder, str(discord.utils.utcnow().timestamp()).split(".")[0])
            elif placeholder == "<random_choice>":
                choices = ["Option1", "Option2", "Option3"]
                output = output.replace(placeholder, discord.utils.choice(choices))
            elif placeholder == "<channel_name>":
                output = output.replace(placeholder, ctx.channel.name)
            elif placeholder == "<channel_id>":
                output = output.replace(placeholder, str(ctx.channel.id))
            elif placeholder == "<message_id>":
                output = output.replace(placeholder, str(ctx.id))
    return output

# Slash command to show help
@bot.slash_command(name="help", description="Show help information")
async def help_command(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="Custom Command Bot Help", color=discord.Color.green())
    embed.add_field(name="/createcmd", value="Create a new custom command with cc! prefix.", inline=False)
    embed.add_field(name="/cmdlist", value="List your custom commands.", inline=False)
    embed.add_field(name="/help", value="Show this help message.", inline=False)
    embed.add_field(name="/docs", value="Get the bot's documentation.", inline=False)
    embed.add_field(name="Using Custom Commands", value="Use `cc!command_name` to execute your custom command.", inline=False)
    await ctx.respond(embed=embed, ephemeral=True)

# Slash command to send documentation
@bot.slash_command(name="docs", description="Get the bot's documentation")
async def docs(ctx: discord.ApplicationContext):
    documentation = """
# Custom Command Bot Documentation

## Overview

This bot allows users to create up to 5 custom text-based commands with the `cc!` prefix. Customize your server experience by defining your own commands using placeholders.

## Commands

### `/createcmd`
Create a new custom command.

- **Usage:** `/createcmd`
- **Process:** A modal will appear asking for the command name and output.

### `/cmdlist`
List your custom commands.

- **Usage:** `/cmdlist`
- **Description:** Displays all your custom commands with their outputs.

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

## Placeholders

Custom command outputs can include placeholders that will be dynamically replaced when the command is executed. There are three types of placeholders:

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

## Examples

### Creating a Greeting Command

1. Use `/createcmd`.
2. Enter `greet` as the command name.
3. Enter `Hello, [username]! Welcome to {servername}.` as the command output.
4. Save the command.

Now, when you type `cc!greet`, the bot will respond with `Hello, [YourName]! Welcome to [YourServer].`

## Limitations

- **Custom Commands per User:** Up to 5.
- **Command Input Length:** 350 characters.
- **Command Output Length:** 500 characters.

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

# Listen to messages for custom commands
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not message.content.startswith("cc!"):
        return
    command_name = message.content[3:].split()[0]
    user_id = str(message.author.id)
    cmds = custom_commands.get(user_id, [])
    for cmd in cmds:
        if cmd["name"] == command_name:
            # Extract parameters if any
            params = {}
            parts = message.content.split()
            if len(parts) > 1:
                for i, part in enumerate(parts[1:], start=1):
                    params[f"input{i}"] = part
            output = replace_placeholders(cmd["output"], await bot.fetch_user(message.author.id), params)
            await message.channel.send(output)
            return
    await message.channel.send("Custom command not found.")

# Run the bot
bot.run(os.getenv("TOKEN"))
