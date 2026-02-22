#!/usr/bin/env python3
"""Download all Foursquare/Swarm checkins via the history search API."""

import json
import os
import time
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime

def load_dotenv(path=".env"):
    """Load key=value pairs from a .env file into os.environ."""
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


load_dotenv()
OAUTH_TOKEN = os.environ.get("OAUTH_TOKEN", "")
USER_ID = os.environ.get("USER_ID", "self")
BASE_URL = "https://api.foursquare.com/v2/users/{user_id}/historysearch"
LIMIT = 50  # max per request
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "all_checkins.json")
RATE_LIMIT_DELAY = 0.5  # seconds between requests


def fetch_page(offset):
    """Fetch a single page of checkins."""
    url = (
        f"{BASE_URL.format(user_id=USER_ID)}"
        f"?locale=en&explicit-lang=false&v=20260220"
        f"&offset={offset}&limit={LIMIT}"
        f"&m=swarm&clusters=false&sort=newestfirst"
        f"&oauth_token={OAUTH_TOKEN}"
    )
    req = Request(url)
    resp = urlopen(req, timeout=30)
    data = json.loads(resp.read().decode("utf-8"))
    return data


def main():
    if not OAUTH_TOKEN:
        print("Error: OAUTH_TOKEN not set. Export it or add to .env")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_checkins = []
    offset = 0
    total_expected = None

    print(f"Starting download of checkins for user {USER_ID}...")
    print(f"Using limit={LIMIT} per request\n")

    while True:
        try:
            data = fetch_page(offset)
        except HTTPError as e:
            print(f"\nHTTP Error at offset {offset}: {e.code} {e.reason}")
            if e.code == 401:
                print("OAuth token may be expired. Get a fresh token.")
            elif e.code == 429:
                print("Rate limited. Waiting 60s...")
                time.sleep(60)
                continue
            else:
                body = e.read().decode("utf-8", errors="replace")
                print(f"Response: {body[:500]}")
            break
        except URLError as e:
            print(f"\nNetwork error at offset {offset}: {e}")
            print("Retrying in 5s...")
            time.sleep(5)
            continue

        meta = data.get("meta", {})
        if meta.get("code") != 200:
            print(f"\nAPI error: {meta}")
            break

        response = data.get("response", {})
        checkins_data = response.get("checkins", {})

        # Get total count on first request
        if total_expected is None:
            total_expected = checkins_data.get("count", "unknown")
            print(f"Total checkins reported by API: {total_expected}\n")

        items = checkins_data.get("items", [])
        if not items:
            print(f"\nNo more items at offset {offset}. Done!")
            break

        all_checkins.extend(items)
        print(
            f"  Fetched offset {offset:>5} - {offset + len(items) - 1:>5}  "
            f"| Got {len(items):>3} items  "
            f"| Total so far: {len(all_checkins)}"
        )

        if len(items) < LIMIT:
            print(f"\nReceived partial page ({len(items)} < {LIMIT}). Done!")
            break

        offset += LIMIT
        time.sleep(RATE_LIMIT_DELAY)

    print(f"\n{'='*60}")
    print(f"Downloaded {len(all_checkins)} total checkins")

    # Save all checkins
    output = {
        "downloaded_at": datetime.now().isoformat(),
        "user_id": USER_ID,
        "total_checkins": len(all_checkins),
        "checkins": all_checkins,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Saved to {OUTPUT_FILE} ({file_size_mb:.1f} MB)")

    # Also save a lightweight summary
    summary_file = os.path.join(OUTPUT_DIR, "checkins_summary.json")
    summary = []
    for c in all_checkins:
        venue = c.get("venue", {})
        entry = {
            "id": c.get("id"),
            "createdAt": c.get("createdAt"),
            "date": datetime.fromtimestamp(c.get("createdAt", 0)).isoformat()
            if c.get("createdAt")
            else None,
            "venue_name": venue.get("name"),
            "venue_category": (
                venue.get("categories", [{}])[0].get("name")
                if venue.get("categories")
                else None
            ),
            "city": venue.get("location", {}).get("city"),
            "state": venue.get("location", {}).get("state"),
            "country": venue.get("location", {}).get("cc"),
            "shout": c.get("shout"),
        }
        summary.append(entry)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Saved summary to {summary_file}")


if __name__ == "__main__":
    main()
