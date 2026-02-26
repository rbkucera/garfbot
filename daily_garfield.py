#!/usr/bin/env python3
"""
daily_garfield.py – post a random Garfield comic strip to a Discord channel.

Schedule this with cron, e.g. every day at 09:00:
    0 9 * * * /path/to/venv/bin/python /path/to/daily_garfield.py

Required environment variables (add to ~/.bashrc or a .env file):
    DISCORD_WEBHOOK_URL   – the incoming webhook URL for your Discord channel
"""

import os
import sys
import random
import datetime
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    sys.exit("ERROR: DISCORD_WEBHOOK_URL environment variable is not set.")

GARFIELD_START = datetime.date(1978, 6, 19)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_garfield_date() -> datetime.date:
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    delta = (yesterday - GARFIELD_START).days
    return GARFIELD_START + datetime.timedelta(days=random.randint(0, delta))


def fetch_comic_url(date: datetime.date) -> str | None:
    iso = date.strftime("%Y-%m-%d")
    url = f"https://www.gocomics.com/api/service/v2/assets/recent/garfield?date={iso}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data[0]["url"] if data else None
    except Exception as exc:
        print(f"ERROR fetching comic: {exc}", file=sys.stderr)
        return None


def post_to_discord(date: datetime.date, image_url: str) -> None:
    payload = {
        "content": f"🌟 **Garfield** – {date.strftime('%B %-d, %Y')}",
        "embeds": [
            {
                "image": {"url": image_url},
                "color": 0xFFA500,
            }
        ],
    }
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    resp.raise_for_status()
    print(f"Posted strip for {date} – HTTP {resp.status_code}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    date = random_garfield_date()
    print(f"Fetching Garfield strip for {date} …")
    image_url = fetch_comic_url(date)
    if not image_url:
        sys.exit(f"ERROR: Could not retrieve comic URL for {date}.")
    post_to_discord(date, image_url)
