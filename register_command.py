#!/usr/bin/env python3
"""
register_command.py – register (or re-register) the /garfield slash command.

Run this once, or whenever you change the command definition.
Guild commands go live instantly; global commands take up to an hour.

Required environment variables:
    DISCORD_BOT_TOKEN    – Bot token from the Discord Developer Portal
    DISCORD_APP_ID       – Application ID (also called Client ID)
    DISCORD_GUILD_ID     – (optional) Guild ID for instant guild-scoped command
"""

import os
import sys
import requests

BOT_TOKEN  = os.environ.get("DISCORD_BOT_TOKEN")
APP_ID     = os.environ.get("DISCORD_APP_ID")
GUILD_ID   = os.environ.get("DISCORD_GUILD_ID")  # leave unset for global command

if not BOT_TOKEN or not APP_ID:
    sys.exit("ERROR: DISCORD_BOT_TOKEN and DISCORD_APP_ID must be set.")

COMMAND = {
    "name": "garfield",
    "description": "Post a random Garfield comic strip 😺",
    "type": 1,  # CHAT_INPUT
}

headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
}

if GUILD_ID:
    url = f"https://discord.com/api/v10/applications/{APP_ID}/guilds/{GUILD_ID}/commands"
    scope = f"guild {GUILD_ID} (instant)"
else:
    url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
    scope = "global (up to 1 hour to propagate)"

resp = requests.post(url, json=COMMAND, headers=headers, timeout=10)
if resp.status_code in (200, 201):
    print(f"✅  /garfield registered as {scope}")
else:
    print(f"❌  Registration failed: {resp.status_code} – {resp.text}", file=sys.stderr)
    sys.exit(1)
