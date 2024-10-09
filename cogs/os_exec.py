# cogs/os_exec.py

import discord
from discord.ext import commands
from discord.commands import Option
import logging
from cogs.filesystem import FileSystem
from data import load_filesystems, save_filesystems
import io

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
    async def os_exec(
        self,
        ctx: discord.ApplicationContext,
        command: Option(str, "The command to execute."),
        file: Option(discord.Attachment, "File to upload.", required=False)
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
            try:
                file_content = await file.read()
                # if it is binary, fail
                if not file_content.decode('utf-8', errors='ignore').isprintable():
                    await ctx.respond(
                        "Cannot upload binary files. Please upload a text file.", ephemeral=True
                    )
                    return
            except Exception as e:
                logger.error(f"Failed to read uploaded file: {e}")
                await ctx.respond(
                    "Failed to read the uploaded file.", ephemeral=True
                )
                return
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
                response = f"File '{filename}' uploaded successfully."
                logger.info(f"User {ctx.user} uploaded file: {filename}")
            else:
                response = f"Failed to upload file '{filename}'. It may already exist or exceed storage limits."
                logger.warning(f"User {ctx.user} failed to upload file: {filename}")
            await ctx.respond(response, ephemeral=True)
            save_filesystems(self.filesystems)
            return

        output, _ = fs.execute_command(command)
        
        if not output.strip():
            output = "Command executed successfully with no output."
        logger.info(f"User {ctx.user} executed command: {command}\nOutput: {output}")
    
        if _:
            # if the command is "download", send _ as a file attachment
            buffer = io.BytesIO(_.encode('utf-8'))
            file_to_send = discord.File(fp=buffer, filename=output)
            await ctx.respond(
                "File downloaded successfully.",
                file=file_to_send,
                ephemeral=True
            )
            return


        # Check if output exceeds 2000 characters (approx. 2KB)
        if len(output) <= 2000:
            await ctx.respond(f"```\n{output}\n```", ephemeral=True)
        else:
            # Create a text file with the output
            buffer = io.BytesIO(output.encode('utf-8'))
            file_to_send = discord.File(fp=buffer, filename='output.txt')
            await ctx.respond(
                "Output exceeds 2KB and has been sent as a file attachment.",
                file=file_to_send,
                ephemeral=True
            )

        # Save the filesystem
        save_filesystems(self.filesystems)

def setup(bot):
    bot.add_cog(OSExecCog(bot))
