# cogs/orange_bank.py

import discord
from discord.ext import commands
import asyncio
import logging
import config

logger = logging.getLogger('CustomCommandBot')

class OrangeBankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.orange_bank_id = 1090982396574306304  # Orange Bank UID

    async def send_orange_bank_request(self, user_id: int, request_type: str) -> str:
        """
        Sends a request to Orange Bank and retrieves the response by reading channel history.
        """
        if request_type not in config.PLACEHOLDERS["ob_"]["placeholders"]:
            logger.error(f"Invalid request type: {request_type}")
            return "Invalid request type."

        # Format the message as per Orange Bank's expected format
        message_content = f"""talktome
#feedback {request_type}
{user_id}"""

        try:
            # Get the Orange Bank user
            orange_bank_user = await self.bot.fetch_user(self.orange_bank_id)
            if not orange_bank_user:
                logger.error(f"Orange Bank user with ID {self.orange_bank_id} not found.")
                return "Orange Bank user not found."

            # Find the guild and the 'logs' channel
            guild = self.bot.get_guild(1079761115636043926)
            if not guild:
                logger.error("Guild with ID 1079761115636043926 not found.")
                return "Internal error: Guild not found."

            channel = discord.utils.get(guild.text_channels, name="logs")
            if not channel:
                logger.error("Logs channel not found in the guild.")
                return "Internal error: Logs channel not found."

            # Send the request message to the logs channel
            sent_message = await channel.send(message_content)
            logger.info(f"Sent request to Orange Bank for user_id {user_id}: {request_type}")

            # Wait for 2 seconds
            await asyncio.sleep(2)

            # Fetch messages after the sent message
            messages = await channel.history(after=sent_message, limit=10).flatten()

            # Find the first message from Orange Bank after the sent message
            response_message = None
            for msg in messages:
                if msg.author.id == self.orange_bank_id:
                    response_message = msg
                    break

            if not response_message:
                logger.error(f"No response from Orange Bank for user_id {user_id}: {request_type}")
                return "No response from Orange Bank."

            # Parse the response message
            response = self.parse_orange_bank_response(response_message.content)
            logger.info(f"Received response from Orange Bank for user_id {user_id}: {response}")

            return response

        except Exception as e:
            logger.error(f"Error sending request to Orange Bank: {e}")
            return "An error occurred while communicating with Orange Bank."

    def parse_orange_bank_response(self, content: str) -> str:
        """
        Parses the response from Orange Bank and extracts the required information.
        """
        content = content.strip()
        if not content.startswith("Sure."):
            logger.error("Unexpected response format from Orange Bank.")
            return "Unexpected response format."

        lines = content.split("\n")
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip()

        # Depending on the request type, extract the relevant data
        # Assuming that the response contains only the requested data
        # For example, if request_type was 'ob_balance', the response contains 'balance'

        # Extract the first key-value pair after 'uid'
        response = ""
        for key, value in data.items():
            if key == 'uid':
                continue  # Skip uid
            response = value
            break  # Return the first relevant value

        return response if response else "N/A"

    async def request_orange_bank(self, user_id: int, request_type: str) -> str:
        """
        Interface function to be called by other parts of the bot to request data from Orange Bank.
        """
        response = await self.send_orange_bank_request(user_id, request_type)
        return response

    # Remove the on_message listener since it's no longer needed
    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     # Existing listener code is removed
    #     pass

def setup(bot):
    bot.add_cog(OrangeBankCog(bot))
