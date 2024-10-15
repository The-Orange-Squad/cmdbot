# data.py

import json
import os
from config import COMMANDS_FILE
import logging
from cogs.filesystem import FileSystem
from datetime import datetime
import shutil

logger = logging.getLogger('CustomCommandBot')

# Backup the existing custom_commands.json
def backup_commands_file():
    if os.path.exists(COMMANDS_FILE):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_file = f"{COMMANDS_FILE}.backup.{timestamp}"
        try:
            shutil.copy(COMMANDS_FILE, backup_file)
            logger.info(f"Backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Failed to create backup of {COMMANDS_FILE}: {e}")

# Migrate commands from old format to new format
def migrate_commands(data):
    """
    Migrates custom_commands data from old format to new format.
    Old Format: { "user_id": [command1, command2, ...], ... }
    New Format: { "user_id": { "private": [command1, ...], "public": [command2, ...] }, ... }
    """
    migrated = False
    for user_id, cmds in data.items():
        if isinstance(cmds, list):
            # Migrate to new structure
            data[user_id] = {
                "private": cmds,
                "public": []
            }
            migrated = True
            logger.info(f"Migrated commands for user ID {user_id} to new format.")
        elif isinstance(cmds, dict):
            # Already in new format; no action needed
            if "private" not in cmds:
                cmds["private"] = cmds.get("commands", [])
                cmds["public"] = []
                migrated = True
                logger.info(f"Adjusted commands for user ID {user_id} to include 'private' and 'public' keys.")
    return migrated

# Load existing custom commands or initialize empty dictionary
def load_commands():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logger.error(
                    "Failed to decode JSON from custom_commands.json. "
                    "Initializing empty commands."
                )
                data = {}

        # Check if migration is needed
        # If any user has a list as their commands, migration is required
        needs_migration = False
        for cmds in data.values():
            if isinstance(cmds, list):
                needs_migration = True
                break

        if needs_migration:
            logger.info("Migration from old format to new format is required.")
            backup_commands_file()
            migrated = migrate_commands(data)
            if migrated:
                # Save the migrated data
                save_commands(data)
                logger.info("Migration completed and changes saved to custom_commands.json.")
            else:
                logger.info("No migration was necessary.")

        return data
    else:
        return {}

# Save custom commands to file
def save_commands(custom_commands):
    try:
        with open(COMMANDS_FILE, "w") as f:
            json.dump(custom_commands, f, indent=4)
        logger.info("Custom commands saved.")
    except Exception as e:
        logger.error(f"Failed to save custom commands: {e}")

# New functions for filesystem
FILESYSTEMS_FILE = "filesystems.json"

def load_filesystems():
    if os.path.exists(FILESYSTEMS_FILE):
        with open(FILESYSTEMS_FILE, "r") as f:
            try:
                data = json.load(f)
                # Convert data back to FileSystem objects
                filesystems = {}
                for user_id, fs_data in data.items():
                    fs = FileSystem()
                    fs.from_dict(fs_data)
                    filesystems[user_id] = fs
                return filesystems
            except json.JSONDecodeError:
                logger.error(
                    "Failed to decode JSON from filesystems.json. "
                    "Initializing empty filesystems."
                )
                return {}
    else:
        return {}

def save_filesystems(filesystems):
    data = {}
    for user_id, fs in filesystems.items():
        data[user_id] = fs.to_dict()
    try:
        with open(FILESYSTEMS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        logger.info("Filesystems saved.")
    except Exception as e:
        logger.error(f"Failed to save filesystems: {e}")

def count_global_public_commands(command_name):
    """
    Counts the number of public commands with the given name across all users.
    """
    count = 0
    for user_cmds in load_commands().values():
        public_cmds = user_cmds.get("public", [])
        count += sum(1 for cmd in public_cmds if cmd['name'] == command_name)
    return count
