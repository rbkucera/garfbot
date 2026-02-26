"""
Garfield Discord Bot - Webhook Interactions Endpoint
Handles Discord slash command interactions via HTTP POST.
Run with a WSGI server (e.g. gunicorn) or as a CGI script on Dreamhost.
"""

import os
import json
import random
import datetime
import requests
from flask import Flask, request, jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration – set these as environment variables on your server,
# or in a .env file loaded at startup (never hard-code secrets).
# ---------------------------------------------------------------------------
DISCORD_PUBLIC_KEY = os.environ["DISCORD_PUBLIC_KEY"]   # From Discord Developer Portal
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"] # Channel webhook URL for daily posts

# Garfield launched on 1978-06-19; pick strips up to yesterday to be safe.
GARFIELD_START = datetime.date(1978, 6, 19)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_garfield_date() -> datetime.date:
    """Return a random date between Garfield's debut and yesterday."""
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    delta = (yesterday - GARFIELD_START).days
    return GARFIELD_START + datetime.timedelta(days=random.randint(0, delta))


def fetch_comic_url(date: datetime.date) -> str | None:
    """
    Query the GoComics asset API and return the image URL for the given date,
    or None if the request fails.
    """
    iso = date.strftime("%Y-%m-%d")
    api_url = f"https://www.gocomics.com/api/service/v2/assets/recent/garfield?date={iso}"
    try:
        resp = requests.get(api_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        resp.raise_for_status()
        data = resp.json()
        return data[0]["url"] if data else None
    except Exception as exc:
        app.logger.error("GoComics API error: %s", exc)
        return None


def verify_discord_signature():
    """
    Verify the Ed25519 signature Discord sends with every interaction.
    Raises BadSignatureError (-> 401) if invalid.
    Discord will periodically probe this; failing it disables your endpoint.
    """
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp  = request.headers.get("X-Signature-Timestamp", "")
    raw_body   = request.data  # must be raw bytes, not parsed JSON

    verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
    verify_key.verify(
        f"{timestamp}".encode() + raw_body,
        bytes.fromhex(signature),
    )


def build_comic_message(date: datetime.date, image_url: str) -> dict:
    """Build a Discord message payload featuring the comic strip."""
    return {
        "content": f"🌟 **Garfield** – {date.strftime('%B %-d, %Y')}",
        "embeds": [
            {
                "image": {"url": image_url},
                "color": 0xFFA500,  # orange
            }
        ],
    }


# ---------------------------------------------------------------------------
# Health check – used by uptime monitors to keep the free Render instance warm
# ---------------------------------------------------------------------------

@app.get("/")
def health():
    return "OK", 200


# ---------------------------------------------------------------------------
# Discord interaction endpoint
# ---------------------------------------------------------------------------

@app.post("/interactions")
def interactions():
    # 1. Verify signature – Discord requires this.
    try:
        verify_discord_signature()
    except (BadSignatureError, Exception):
        return jsonify({"error": "Invalid request signature"}), 401

    body = request.get_json()
    interaction_type = body.get("type")

    # 2. Respond to Discord's PING health-check.
    if interaction_type == 1:
        return jsonify({"type": 1})

    # 3. Handle APPLICATION_COMMAND (slash commands).
    if interaction_type == 2:
        command = body.get("data", {}).get("name", "")
        if command == "garfield":
            date = random_garfield_date()
            image_url = fetch_comic_url(date)
            if image_url:
                return jsonify({
                    "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                    "data": build_comic_message(date, image_url),
                })
            else:
                return jsonify({
                    "type": 4,
                    "data": {"content": "⚠️ Couldn't fetch a Garfield strip right now. Try again!"},
                })

    return jsonify({"error": "Unknown interaction type"}), 400


# ---------------------------------------------------------------------------
# Entry point for local development only
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
