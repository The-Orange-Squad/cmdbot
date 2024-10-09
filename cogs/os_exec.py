# cogs/os_exec.py

import discord
from discord.ext import commands
from discord.commands import Option
import logging
from cogs.filesystem import FileSystem, File, Directory
from data import load_filesystems, save_filesystems
import io
import os
import time
from discord.ui import Modal, InputText
from discord import InputTextStyle

logger = logging.getLogger('CustomCommandBot')

class NanoModal(Modal):
    def __init__(self, fs_cog, user_id, filename, content):
        super().__init__(title="Nano Editor")
        self.fs_cog = fs_cog
        self.user_id = user_id
        self.filename = filename  # Original filename
        self.add_item(InputText(
            label="Filename",
            value=filename,
            placeholder="Enter filename",
            max_length=100,  # Limit the filename length
            required=True
        ))
        self.add_item(InputText(
            label="File Content",
            value=content,
            style=InputTextStyle.long,
            max_length=4000,  # Discord's limit for large input text
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        new_filename = self.children[0].value.strip()
        new_content = self.children[1].value

        if len(new_content) > 4000:
            await interaction.response.send_message(
                "File content exceeds 4000 characters. Cannot save file.",
                ephemeral=True
            )
            return

        user_id = self.user_id
        fs = self.fs_cog.filesystems[user_id]

        old_file = fs.resolve_path(self.filename)
        old_content_size = 0
        if old_file and isinstance(old_file, File):
            old_content_size = old_file.size

        new_content_size = len(new_content.encode('utf-8'))

        size_difference = new_content_size - old_content_size

        if fs.total_size + size_difference > fs.max_size:
            await interaction.response.send_message(
                "Cannot save file. Storage limit exceeded.",
                ephemeral=True
            )
            return

        # Handle filename change
        if self.filename != new_filename:
            # Remove old file if it exists
            if old_file and isinstance(old_file, File):
                parent_dir = old_file.parent
                del parent_dir.children[old_file.name]
                fs.total_size -= old_file.size
                parent_dir.modified_at = time.time()

        # Check if a file with the new filename already exists
        existing_file = fs.resolve_path(new_filename)
        if existing_file and isinstance(existing_file, File):
            # Update the existing file
            existing_file.content = new_content.encode('utf-8')
            existing_file.size = new_content_size
            existing_file.modified_at = time.time()
            fs.total_size += size_difference
        elif existing_file and isinstance(existing_file, Directory):
            await interaction.response.send_message(
                f"Cannot save file. A directory with the name '{new_filename}' exists.",
                ephemeral=True
            )
            return
        else:
            # Create a new file
            parent_dir = fs.current_dir
            filename = new_filename
            if '/' in new_filename:
                parent_path = os.path.dirname(new_filename)
                parent_dir = fs.resolve_path(parent_path)
                filename = os.path.basename(new_filename)
                if not parent_dir:
                    await interaction.response.send_message(
                        f"Cannot save file. Directory '{parent_path}' does not exist.",
                        ephemeral=True
                    )
                    return
            new_file = File(name=filename, content=new_content.encode('utf-8'))
            new_file.parent = parent_dir
            parent_dir.children[filename] = new_file
            parent_dir.modified_at = time.time()
            fs.total_size += new_content_size

        # Save the filesystem
        save_filesystems(self.fs_cog.filesystems)
        await interaction.response.send_message(
            f"File '{new_filename}' saved successfully.",
            ephemeral=True
        )
        logger.info(f"User {interaction.user} saved file: {new_filename}")

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
            except Exception as e:
                logger.error(f"Failed to read uploaded file: {e}")
                await ctx.respond(
                    "Failed to read the uploaded file.", ephemeral=True
                )
                return

        output = fs.execute_command(command)

        if isinstance(output, tuple):
            # Handle 'download' command
            filepath, file_content = output
            buffer = io.BytesIO(file_content)
            file_to_send = discord.File(fp=buffer, filename=os.path.basename(filepath))
            await ctx.respond(
                f"File '{filepath}' downloaded successfully.",
                file=file_to_send,
                ephemeral=True
            )
        else:
            if not output.strip():
                output = "Command executed successfully with no output."
            logger.info(f"User {ctx.user} executed command: {command}\nOutput: {output}")

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

    @commands.slash_command(
        name="nano",
        description="Edit a file in your virtual filesystem."
    )
    async def nano(
        self,
        ctx: discord.ApplicationContext,
        filename: Option(str, "The name of the file to edit.")
    ):
        user_id = str(ctx.user.id)
        if user_id not in self.filesystems:
            self.filesystems[user_id] = FileSystem()
        fs = self.filesystems[user_id]

        # Try to get the file
        file = fs.resolve_path(filename)
        content = ''
        if file and isinstance(file, File):
            # Check content length
            try:
                content = file.content.decode('utf-8')
            except UnicodeDecodeError:
                await ctx.respond(
                    f"Cannot edit binary file '{filename}'.",
                    ephemeral=True
                )
                return
            if len(content) > 4000:
                await ctx.respond(
                    f"File content exceeds 4000 characters. Cannot edit file '{filename}'.",
                    ephemeral=True
                )
                return
        elif file and isinstance(file, Directory):
            await ctx.respond(
                f"'{filename}' is a directory. Cannot edit directories.",
                ephemeral=True
            )
            return
        else:
            # File does not exist, content remains empty
            pass

        # Open the modal
        modal = NanoModal(self, user_id, filename, content)
        await ctx.send_modal(modal)
        logger.info(f"User {ctx.user} is editing file: {filename}")

def setup(bot):
    bot.add_cog(OSExecCog(bot))
