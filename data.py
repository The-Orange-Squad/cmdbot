# data.py
import json
import os
from config import COMMANDS_FILE
import logging

logger = logging.getLogger('CustomCommandBot')

# Load existing custom commands or initialize empty dictionary
def load_commands():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from custom_commands.json. Initializing empty commands.")
                return {}
    else:
        return {}

# Save custom commands to file
def save_commands(custom_commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(custom_commands, f, indent=4)
    logger.info("Custom commands saved.")
