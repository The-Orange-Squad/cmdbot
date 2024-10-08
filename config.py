# config.py
COMMANDS_FILE = "custom_commands.json"

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
