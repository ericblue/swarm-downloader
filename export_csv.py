#!/usr/bin/env python3
"""Export Foursquare/Swarm checkins to CSV."""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone, timedelta


def parse_checkin(c):
    """Extract flat fields from a checkin object."""
    venue = c.get("venue", {})
    location = venue.get("location", {})
    categories = venue.get("categories", [])
    category = categories[0] if categories else {}

    ts = c.get("createdAt")
    tz_offset_min = c.get("timeZoneOffset", 0)
    if ts:
        utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        local_dt = utc_dt + timedelta(minutes=tz_offset_min)
    else:
        utc_dt = local_dt = None

    photos = c.get("photos", {}).get("items", [])
    photo_url = ""
    if photos:
        p = photos[0]
        photo_url = f"{p.get('prefix', '')}original{p.get('suffix', '')}"

    return {
        "id": c.get("id", ""),
        "date_utc": utc_dt.strftime("%Y-%m-%d %H:%M:%S") if utc_dt else "",
        "date_local": local_dt.strftime("%Y-%m-%d %H:%M:%S") if local_dt else "",
        "year": local_dt.year if local_dt else "",
        "month": local_dt.month if local_dt else "",
        "day_of_week": local_dt.strftime("%A") if local_dt else "",
        "venue_name": venue.get("name", ""),
        "category": category.get("name", ""),
        "category_short": category.get("shortName", ""),
        "address": location.get("address", ""),
        "cross_street": location.get("crossStreet", ""),
        "city": location.get("city", ""),
        "state": location.get("state", ""),
        "postal_code": location.get("postalCode", ""),
        "country": location.get("country", ""),
        "country_code": location.get("cc", ""),
        "neighborhood": location.get("neighborhood", ""),
        "lat": location.get("lat", ""),
        "lng": location.get("lng", ""),
        "shout": c.get("shout", ""),
        "type": c.get("type", ""),
        "photo_url": photo_url,
        "venue_url": venue.get("url", ""),
        "foursquare_url": c.get("canonicalUrl", ""),
    }


FIELDS = [
    "id", "date_utc", "date_local", "year", "month", "day_of_week",
    "venue_name", "category", "category_short",
    "address", "cross_street", "city", "state", "postal_code",
    "country", "country_code", "neighborhood",
    "lat", "lng", "shout", "type", "photo_url", "venue_url", "foursquare_url",
]


def main():
    parser = argparse.ArgumentParser(description="Export Swarm checkins to CSV")
    parser.add_argument(
        "-i", "--input", default="data/all_checkins.json",
        help="Input JSON file (default: data/all_checkins.json)",
    )
    parser.add_argument(
        "-o", "--output", default="data/checkins.csv",
        help="Output CSV file (default: data/checkins.csv)",
    )
    parser.add_argument(
        "--year", type=int, help="Filter to a specific year",
    )
    parser.add_argument(
        "--city", help="Filter to a specific city (case-insensitive)",
    )
    parser.add_argument(
        "--category", help="Filter to a specific category (case-insensitive substring)",
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    checkins = data.get("checkins", data if isinstance(data, list) else [])
    rows = [parse_checkin(c) for c in checkins]

    # Apply filters
    if args.year:
        rows = [r for r in rows if r["year"] == args.year]
    if args.city:
        city_lower = args.city.lower()
        rows = [r for r in rows if city_lower in str(r["city"]).lower()]
    if args.category:
        cat_lower = args.category.lower()
        rows = [r for r in rows if cat_lower in str(r["category"]).lower()]

    # Sort by date (newest first)
    rows.sort(key=lambda r: r["date_local"], reverse=True)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} checkins to {args.output}")


if __name__ == "__main__":
    main()
