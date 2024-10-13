# utils.py
import re
import random
from datetime import datetime
import discord
from config import PLACEHOLDERS
import logging
import asyncio

logger = logging.getLogger('CustomCommandBot')

async def replace_placeholders(output: str, ctx: discord.Interaction, params: dict, orange_bank_cog, command: dict) -> str:
    # Replace user placeholders []
    for placeholder, description in PLACEHOLDERS["[]"]["placeholders"].items():
        if placeholder in output:
            if placeholder == "[username]":
                output = output.replace(placeholder, ctx.user.name)
            elif placeholder == "[user_id]":
                output = output.replace(placeholder, str(ctx.user.id))
            elif placeholder == "[user_mention]":
                output = output.replace(placeholder, ctx.user.mention)
            elif placeholder == "[user_avatar]":
                output = output.replace(placeholder, str(ctx.user.avatar.url) if ctx.user.avatar else "No Avatar")
            elif placeholder == "[user_discriminator]":
                output = output.replace(placeholder, ctx.user.discriminator)
            elif placeholder == "[user_created_at]":
                output = output.replace(placeholder, ctx.user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            elif placeholder == "[user_joined_at]":
                member = ctx.guild.get_member(ctx.user.id)
                if member and member.joined_at:
                    output = output.replace(placeholder, member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    output = output.replace(placeholder, "N/A")
            elif placeholder == "[user_roles]":
                member = ctx.guild.get_member(ctx.user.id)
                if member:
                    roles = [role.name for role in member.roles if role.name != "@everyone"]
                    output = output.replace(placeholder, ", ".join(roles) if roles else "None")
                else:
                    output = output.replace(placeholder, "None")
            elif placeholder == "[user_status]":
                member = ctx.guild.get_member(ctx.user.id)
                output = output.replace(placeholder, str(member.status).title() if member else "N/A")

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
                # Discord has removed server regions; update or remove this placeholder as needed
                output = output.replace(placeholder, "N/A")
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
                # Use custom range if available
                if "random_number" in command:
                    min_val = command["random_number"].get("min", 1000)
                    max_val = command["random_number"].get("max", 9999)
                else:
                    min_val, max_val = 1000, 9999
                output = output.replace(placeholder, str(random.randint(min_val, max_val)))
            elif placeholder == "<random_choice>":
                # Use custom choices if available
                if "random_choice" in command and command["random_choice"]:
                    choices = command["random_choice"]
                else:
                    choices = ["Option1", "Option2", "Option3"]
                output = output.replace(placeholder, random.choice(choices))
            elif placeholder == "<channel_name>":
                output = output.replace(placeholder, ctx.channel.name)
            elif placeholder == "<channel_id>":
                output = output.replace(placeholder, str(ctx.channel.id))
            elif placeholder == "<message_id>":
                output = output.replace(placeholder, str(ctx.id))

    # Replace Arguments placeholders {[<arg_name>]}
    arg_pattern = re.compile(r"\{\[\<(\w+)\>\]\}")  # matches {[<arg_name>]}
    matches = arg_pattern.findall(output)
    for arg_name in matches:
        value = params.get(arg_name, "")
        output = re.sub(r"\{\[\<" + re.escape(arg_name) + r"\>\]\}", value.strip(), output)

    # Replace Orange Bank placeholders ob_
    ob_pattern = re.compile(r"\bob_\w+\b")
    ob_matches = ob_pattern.findall(output)
    for ob_placeholder in ob_matches:
        placeholder_type = ob_placeholder  # e.g., ob_balance
        # Send request to Orange Bank and await response
        response = await orange_bank_cog.request_orange_bank(ctx.user.id, placeholder_type)
        if response is not None:
            output = output.replace(ob_placeholder, str(response))
        else:
            output = output.replace(ob_placeholder, "N/A")  # Fallback if no response

    return output
