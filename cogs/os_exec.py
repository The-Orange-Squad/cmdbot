# cogs/os_exec.py

import discord
from discord.ext import commands
from discord import option
import logging
from cogs.filesystem import FileSystem
from data import load_filesystems, save_filesystems

logger = logging.getLogger('CustomCommandBot')

class OSExecCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load per-user filesystems
        self.filesystems = load_filesystems()

    @commands.slash_command(
        name="os_exec",
        description="Simulate OS commands in a virtual environment."
    )
    @option("command", str, description="The OS command to execute", required=True)
    @option(
        "file",
        discord.Attachment,
        description="Optional file to upload",
        required=False
    )
    async def os_exec(
        self,
        ctx: discord.ApplicationContext,
        command: str,
        file: discord.Attachment = None
    ):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.user.id)
        # Ensure the user has a filesystem
        if user_id not in self.filesystems:
            self.filesystems[user_id] = FileSystem()

        fs = self.filesystems[user_id]

        # Handle file upload
        if file is not None:
            # Download the file and add it to the user's filesystem
            file_content = await file.read()
            # Check if adding this file exceeds the 5MB limit
            if fs.total_size + len(file_content) > fs.max_size:
                await ctx.respond(
                    "Cannot upload file. Storage limit exceeded.", ephemeral=True
                )
                return
            # Add the file to the current directory
            filename = file.filename
            result = fs.add_file(filename, file_content)
            if result:
                await ctx.respond(
                    f"File '{filename}' uploaded successfully.", ephemeral=True
                )
            else:
                await ctx.respond(
                    f"Failed to upload file '{filename}'.", ephemeral=True
                )
            save_filesystems(self.filesystems)
            return

        # Handle command execution
        output = fs.execute_command(command)
        await ctx.respond(f"```\n{output}\n```", ephemeral=True)

        # Save the filesystem
        save_filesystems(self.filesystems)

def setup(bot):
    bot.add_cog(OSExecCog(bot))
