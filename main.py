import discord
from discord import Option, File
from discord.ext import commands
import json
import os
from datetime import datetime
import random
import io
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = discord.Bot(intents=intents)

# Path to the JSON file for storing custom commands
COMMANDS_FILE = "commands.json"

# Ensure the commands file exists
if not os.path.exists(COMMANDS_FILE):
    with open(COMMANDS_FILE, "w") as f:
        json.dump({}, f)

# Load custom commands from the JSON file
def load_commands():
    with open(COMMANDS_FILE, "r") as f:
        return json.load(f)

# Save custom commands to the JSON file
def save_commands(commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=4)

# Define placeholders
PLACEHOLDERS = {
    "server": {
        "[]": [
            "[server_name]",
            "[server_id]",
            "[server_region]",
            "[server_member_count]",
            "[server_owner]",
            "[server_created_at]",
            "[server_icon]",
            "[server_boost_level]",
            "[server_emojis]",
            "[server_channels]"
        ]
    },
    "user": {
        "{}": [
            "{user_name}",
            "{user_id}",
            "{user_discriminator}",
            "{user_avatar}",
            "{user_joined_at}",
            "{user_roles}",
            "{user_status}",
            "{user_activity}",
            "{user_nickname}",
            "{user_top_role}"
        ]
    },
    "misc": {
        "<>": [
            "<current_date>",
            "<current_time>",
            "<bot_name>",
            "<bot_latency>",
            "<random_number>",
            "<random_user>",
            "<server_count>",
            "<user_count>",
            "<invite_link>",
            "<support_server>"
        ]
    }
}

# Function to replace placeholders with actual data
async def replace_placeholders(ctx, text):
    commands = load_commands()
    server = ctx.guild
    user = ctx.author
    bot_user = bot.user

    replacements = {
        # Server placeholders
        "[server_name]": server.name if server else "DM",
        "[server_id]": str(server.id) if server else "DM",
        "[server_member_count]": str(server.member_count) if server else "1",
        "[server_created_at]": server.created_at.strftime("%Y-%m-%d") if server else "N/A",
        "[server_icon]": server.icon.url if server and server.icon else "No Icon",
        "[server_boost_level]": str(server.premium_tier) if server else "0",
        "[server_emojis]": ", ".join([str(e) for e in server.emojis]) if server else "None",
        "[server_channels]": ", ".join([channel.name for channel in server.channels]) if server else "DM",
        
        # User placeholders
        "{user_name}": user.name,
        "{user_id}": str(user.id),
        "{user_discriminator}": user.discriminator,
        "{user_avatar}": user.avatar.url if user.avatar else "No Avatar",
        "{user_joined_at}": user.joined_at.strftime("%Y-%m-%d") if isinstance(user, discord.Member) else "N/A",
        "{user_roles}": ", ".join([role.name for role in user.roles]) if isinstance(user, discord.Member) else "None",
        "{user_status}": str(user.status),
        "{user_activity}": str(user.activity) if user.activity else "None",
        "{user_nickname}": user.nick if isinstance(user, discord.Member) and user.nick else user.name,
        "{user_top_role}": user.top_role.name if isinstance(user, discord.Member) else "None",
        
        # Misc placeholders
        "<current_date>": datetime.utcnow().strftime("%Y-%m-%d"),
        "<current_time>": datetime.utcnow().strftime("%H:%M:%S UTC"),
        "<bot_name>": bot_user.name if bot_user else "Bot",
        "<bot_latency>": f"{bot.latency * 1000:.2f}ms",
        "<random_number>": str(random.randint(1, 100)),
        "<random_user>": random.choice([member.name for member in server.members]) if server and server.members else user.name,
        "<server_count>": str(len(bot.guilds)),
        "<user_count>": str(len(bot.users)),
        "<invite_link>": "https://discord.gg/your-invite",
        "<support_server>": "https://discord.gg/your-support-server"
    }

    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    
    return text

# Modal for creating a custom command
class CreateCommandModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create Custom Command")
        self.add_item(discord.ui.InputText(label="Command Name (without prefix)", max_length=50))
        self.add_item(discord.ui.InputText(label="Command Syntax", style=discord.InputTextStyle.long, max_length=350))
        self.add_item(discord.ui.InputText(label="Command Output", style=discord.InputTextStyle.long, max_length=500))
    
    async def callback(self, interaction: discord.Interaction):
        command_name = self.children[0].value.strip().lower()
        command_syntax = self.children[1].value.strip()
        command_output = self.children[2].value.strip()

        # Validate command name
        if not command_name.isalnum():
            await interaction.response.send_message("Command name must be alphanumeric.", ephemeral=True)
            return
        
        commands = load_commands()
        user_commands = commands.get(str(interaction.user.id), [])
        
        if len(user_commands) >= 5:
            await interaction.response.send_message("You can only create up to 5 custom commands.", ephemeral=True)
            return
        
        # Check if command already exists
        if any(cmd["name"] == command_name for cmd in user_commands):
            await interaction.response.send_message("You already have a command with that name.", ephemeral=True)
            return
        
        # Add the new command
        user_commands.append({
            "name": command_name,
            "syntax": command_syntax,
            "output": command_output
        })
        commands[str(interaction.user.id)] = user_commands
        save_commands(commands)
        
        await interaction.response.send_message(f"Custom command `cc!{command_name}` created successfully!", ephemeral=True)

# Slash command to create a custom command
@bot.slash_command(name="createcmd", description="Create a custom command with the 'cc!' prefix")
async def createcmd(ctx: discord.ApplicationContext):
    modal = CreateCommandModal()
    await ctx.send_modal(modal)

# Slash command to list user's custom commands
@bot.slash_command(name="cmdlist", description="View your custom commands")
async def cmdlist(ctx: discord.ApplicationContext):
    commands = load_commands()
    user_commands = commands.get(str(ctx.author.id), [])
    
    if not user_commands:
        await ctx.respond("You have no custom commands. Use /createcmd to add one!", ephemeral=True)
        return
    
    embed = discord.Embed(title="Your Custom Commands", color=discord.Color.blue())
    for cmd in user_commands:
        embed.add_field(name=f"cc!{cmd['name']}", value=f"Syntax: {cmd['syntax']}\nOutput: {cmd['output']}", inline=False)
    
    await ctx.respond(embed=embed)

# Slash command to show help
@bot.slash_command(name="help", description="Show available commands")
async def help_command(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="Help - Custom Command Bot", color=discord.Color.green())
    embed.add_field(name="/createcmd", value="Create a new custom command with the 'cc!' prefix.", inline=False)
    embed.add_field(name="/cmdlist", value="List your existing custom commands.", inline=False)
    embed.add_field(name="/help", value="Show this help message.", inline=False)
    embed.add_field(name="/docs", value="Get the documentation for the bot.", inline=False)
    embed.add_field(name="cc!<command>", value="Execute your custom command.", inline=False)
    await ctx.respond(embed=embed)

# Slash command to send documentation as a .md file
@bot.slash_command(name="docs", description="Get the documentation for the bot")
async def docs(ctx: discord.ApplicationContext):
    documentation = """
# Custom Command Bot Documentation

## Overview
This Discord bot allows users to create up to **5 custom commands** with the `cc!` prefix. These commands can include placeholders that dynamically insert server, user, and miscellaneous information.

## Commands

### /createcmd
**Description:** Create a new custom command.

**Usage:**
1. Invoke the `/createcmd` command.
2. Fill out the modal with:
   - **Command Name:** The name of your command (without the `cc!` prefix). Must be alphanumeric.
   - **Command Syntax:** The syntax for the command. Maximum 350 characters.
   - **Command Output:** The response the bot will send when the command is used. Maximum 500 characters.
3. Submit the modal to create the command.

**Notes:**
- You can create up to 5 custom commands.
- Command names must be unique and alphanumeric.

### /cmdlist
**Description:** View your existing custom commands.

**Usage:** Simply invoke the `/cmdlist` command to see a list of your custom commands along with their syntax and output.

### /help
**Description:** Show available commands.

**Usage:** Invoke the `/help` command to see a list of all available commands and their descriptions.

### /docs
**Description:** Get the documentation for the bot.

**Usage:** Invoke the `/docs` command to receive this documentation as a markdown file.

### cc!<command>
**Description:** Execute your custom command.

**Usage:** Type `cc!` followed by your custom command name. For example, `cc!greet`.

## Placeholders

Custom commands can include placeholders that will be dynamically replaced when the command is executed. There are three types of placeholders:

### Server Placeholders `[]`
- `[server_name]`: The name of the server.
- `[server_id]`: The ID of the server.
- `[server_region]`: The region of the server.
- `[server_member_count]`: The total number of members in the server.
- `[server_owner]`: The owner of the server.
- `[server_created_at]`: The creation date of the server.
- `[server_icon]`: The server's icon URL.
- `[server_boost_level]`: The server's boost level.
- `[server_emojis]`: A list of server emojis.
- `[server_channels]`: A list of server channels.

### User Placeholders `{}`
- `{user_name}`: Your username.
- `{user_id}`: Your user ID.
- `{user_discriminator}`: Your discriminator.
- `{user_avatar}`: Your avatar URL.
- `{user_joined_at}`: The date you joined the server.
- `{user_roles}`: A list of your roles.
- `{user_status}`: Your current status.
- `{user_activity}`: Your current activity.
- `{user_nickname}`: Your nickname in the server.
- `{user_top_role}`: Your highest role in the server.

### Miscellaneous Placeholders `<>`
- `<current_date>`: The current date (UTC).
- `<current_time>`: The current time (UTC).
- `<bot_name>`: The bot's name.
- `<bot_latency>`: The bot's latency.
- `<random_number>`: A random number between 1 and 100.
- `<random_user>`: A random user's name from the server.
- `<server_count>`: The total number of servers the bot is in.
- `<user_count>`: The total number of users the bot can see.
- `<invite_link>`: A link to invite the bot.
- `<support_server>`: A link to the support server.

**Example:**
```
Command Name: greet
Syntax: Hello [server_name]! I'm {user_name}.
Output: Welcome to the server! Today is <current_date>.
```

When a user types `cc!greet`, the bot will respond with:
```
Welcome to the server! Today is 2024-04-27.
```

## Restrictions
- **Command Limit:** Each user can create up to 5 custom commands.
- **Character Limits:**
  - **Command Syntax:** 350 characters.
  - **Command Output:** 500 characters.
- **Access Control:** Only you can execute your custom commands, but others can view your command list.

## Support
If you need help or encounter issues, join our [Support Server](<support_server>).

---

**Enjoy creating your custom commands!**
    """
    file = File(io.BytesIO(documentation.encode()), filename="Documentation.md")
    await ctx.respond("Here is the documentation:", file=file)

# Event listener for processing custom commands with 'cc!' prefix
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("cc!"):
        command_name = message.content[3:].strip().lower()
        if not command_name:
            return

        commands = load_commands()
        user_commands = commands.get(str(message.author.id), [])
        command = next((cmd for cmd in user_commands if cmd["name"] == command_name), None)
        
        if command:
            output = await replace_placeholders(message, command["output"])
            if len(output) > 500:
                output = output[:497] + "..."
            await message.channel.send(output)

# Run the bot with your token
bot.run(os.getenv("TOKEN"))