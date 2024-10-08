# data.py

import json
import os
from config import COMMANDS_FILE
import logging
from cogs.filesystem import FileSystem

logger = logging.getLogger('CustomCommandBot')

# Load existing custom commands or initialize empty dictionary
def load_commands():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(
                    "Failed to decode JSON from custom_commands.json. "
                    "Initializing empty commands."
                )
                return {}
    else:
        return {}

# Save custom commands to file
def save_commands(custom_commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(custom_commands, f, indent=4)
    logger.info("Custom commands saved.")

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
    with open(FILESYSTEMS_FILE, "w") as f:
        json.dump(data, f)
    logger.info("Filesystems saved.")
