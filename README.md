# Swarm Download

Download and explore your complete Foursquare Swarm checkin history. No waiting for a data export — pull all your checkins directly via the API.

## Quick Start

```bash
# 1. Get your OAuth token (see instructions below)
# 2. Create your .env file from the template
cp .env.example .env    # or: make env
# 3. Paste your token into .env
# 4. Download all checkins
make download           # or: python3 download_checkins.py
# 5. Export to CSV
make csv                # or: python3 export_csv.py
# 6. Explore your data
make search             # or: python3 search_checkins.py
```

All scripts automatically load `.env` — no need to `source` it or use the Makefile.

## Getting Your OAuth Token

The Foursquare/Swarm API requires an OAuth token. There is no "generate personal token" button — Foursquare only supports full OAuth2 app flows. The two practical options are below.

### Option A: Browser Dev Console (Recommended)

The quickest method — grab the token from an active Swarm web session:

1. Open your browser and go to [swarmapp.com](https://swarmapp.com)
2. Log in with your Foursquare/Swarm account
3. Navigate to [swarmapp.com/history](https://swarmapp.com/history)
4. Open **Developer Tools** (F12 or Cmd+Option+I on Mac)
5. Go to the **Network** tab
6. Scroll down on the history page to trigger an API request (or refresh the page)
7. In the network list, filter by `historysearch` to find the API call
8. Click the request and look at the **URL parameters** or **Query String Parameters**
9. Copy the value of `oauth_token`

It will look something like: `QPWTXL3LLNZMCTWURRSLJRKONUTJDHPL0G0NI4AJD3AUIU5S`

### Option B: Register a Foursquare App

The more "official" route via the Foursquare developer portal:

1. Go to [foursquare.com/developers](https://foursquare.com/developers/) and sign up / log in
2. Create a new app in your developer console
3. Note your **Client ID** and **Client Secret**
4. Open this URL in your browser (replace `YOUR_CLIENT_ID`):
   ```
   https://foursquare.com/oauth2/authenticate?client_id=YOUR_CLIENT_ID&response_type=token&redirect_uri=http://localhost
   ```
5. Approve the permissions when prompted
6. You'll be redirected to `http://localhost#access_token=YOUR_TOKEN` — copy the token from the URL bar

This gives you a longer-lived token tied to your registered app rather than your browser session.

> **Note:** Both token types can expire. If you get 401 errors, grab a fresh token using either method above.

### Save Your Token

Copy the example file and paste in your token:

```bash
cp .env.example .env
```

Then edit `.env`:

```
OAUTH_TOKEN=your_token_here

# Optional: Foursquare user ID (defaults to "self" which uses the authenticated user)
# USER_ID=12345678
```

Or run `make env` to create it from the template. All scripts automatically load `.env` — you can run them directly with `python3` or via `make`.

## Scripts

### `download_checkins.py` — Download Checkins

Paginates through the Foursquare API to download all your checkins (50 per request with rate limiting). Uses `"self"` as the user ID by default (resolves to the authenticated user), or set `USER_ID` in `.env` to specify a numeric ID.

```bash
make download
# or
python3 download_checkins.py
```

Output:
- `data/all_checkins.json` — complete raw API data
- `data/checkins_summary.json` — lightweight summary

### `export_csv.py` — Export to CSV

Converts checkins to a flat CSV with 24 columns including date, venue, category, full address, lat/lng, shout, and photo URLs.

```bash
make csv                              # export all
make csv-year Y=2023                  # export a single year
make csv-city C="san francisco"       # export a single city
```

CLI options:
```bash
python3 export_csv.py --year 2019 --city tokyo -o data/tokyo_2019.csv
python3 export_csv.py --category restaurant -o data/restaurants.csv
```

### `search_checkins.py` — Search & Explore

Interactive tool with colored output for searching and analyzing your checkin history.

#### Interactive Mode

```bash
make search
# or
python3 search_checkins.py
```

Then type queries at the `swarm>` prompt:

```
swarm> starbucks                    # free-text search
swarm> year 2019 city tokyo         # combined filters
swarm> cat sushi                    # category search
swarm> stats 2023                   # year stats dashboard
swarm> venues                       # top venue rankings
swarm> timeline 2019                # monthly bar chart
swarm> help                         # full command reference
```

#### CLI Mode

```bash
# Search
make find Q=starbucks
make find-cat Q=sushi
make find-city Q="san francisco"
make find-year Y=2019

# Dashboards
make stats                          # overall stats
make stats-year Y=2023              # year stats
make venues                         # top venues
make timeline                       # monthly timeline
make categories                     # category breakdown
```

Full CLI options:
```bash
python3 search_checkins.py search --venue "yard house" --year 2019 --limit 50
python3 search_checkins.py stats --year 2023
python3 search_checkins.py venues --city "los angeles"
python3 search_checkins.py timeline --year 2020
python3 search_checkins.py categories --state CA
```

## Make Targets

| Target | Description |
|---|---|
| `make help` | Show all available targets |
| `make env` | Create `.env` template |
| `make download` | Download all checkins from API |
| `make csv` | Export to CSV |
| `make csv-year Y=YYYY` | Export a single year |
| `make csv-city C=name` | Export a single city |
| `make search` | Interactive search mode |
| `make stats` | Overall stats dashboard |
| `make stats-year Y=YYYY` | Stats for a year |
| `make venues` | Top venues ranking |
| `make timeline` | Monthly timeline chart |
| `make categories` | Category breakdown |
| `make find Q=query` | Search by venue name |
| `make find-cat Q=query` | Search by category |
| `make find-city Q=query` | Search by city |
| `make find-year Y=YYYY` | List all checkins for a year |
| `make info` | Show data file stats |
| `make clean` | Remove downloaded data |

## Data Formats

### `data/all_checkins.json`

The complete raw API response. Top-level structure:

```json
{
  "downloaded_at": "2026-02-21T18:29:40.469758",
  "user_id": "12345678",
  "total_checkins": 4108,
  "checkins": [ ... ]
}
```

Each checkin object contains the full Foursquare API response:

```json
{
  "id": "abc123def456789012345678",
  "createdAt": 1700000000,
  "type": "checkin",
  "timeZoneOffset": -480,
  "displayGeo": {
    "id": "72057594043287713",
    "name": "San Francisco, United States"
  },
  "exactContextLine": "SoMa, San Francisco, CA, United States",
  "canonicalUrl": "https://app.foursquare.com/user/12345678/checkin/abc123...",
  "venue": {
    "id": "4a1234b5f964a520001234e3",
    "name": "Blue Bottle Coffee",
    "contact": {
      "phone": "5551234567",
      "formattedPhone": "(555) 123-4567"
    },
    "location": {
      "city": "San Francisco",
      "state": "CA",
      "postalCode": "94107",
      "cc": "US",
      "country": "United States",
      "neighborhood": "SoMa",
      "lat": 37.7825,
      "lng": -122.3930
    },
    "categories": [
      {
        "id": "4bf58dd8d48988d1e0931735",
        "name": "Coffee Shop",
        "shortName": "Coffee Shop",
        "primary": true
      }
    ],
    "url": "https://bluebottlecoffee.com",
    "stats": {
      "tipCount": 85,
      "usersCount": 2450,
      "checkinsCount": 12340
    }
  },
  "shout": "Great pour-over!",
  "isMayor": false,
  "photos": { "count": 0, "items": [] },
  "comments": { "count": 0 },
  "location": { "lat": 37.7826, "lng": -122.3931 }
}
```

Key fields: `createdAt` (unix timestamp), `timeZoneOffset` (minutes from UTC), `venue` (full venue details with location, categories, stats), `shout` (user's comment text), `photos`, `type` (`"checkin"` or `"passive"`).

### `data/checkins_summary.json`

A lightweight flat array — one object per checkin with just the essentials:

```json
[
  {
    "id": "abc123def456789012345678",
    "createdAt": 1700000000,
    "date": "2023-11-14T12:13:20",
    "venue_name": "Blue Bottle Coffee",
    "venue_category": "Coffee Shop",
    "city": "San Francisco",
    "state": "CA",
    "country": "US",
    "shout": "Great pour-over!"
  }
]
```

### `data/checkins.csv`

Flat CSV with 24 columns. Generated by `export_csv.py`.

## CSV Columns

| Column | Example |
|---|---|
| `id` | `55291a68498e0b6d97ba1b22` |
| `date_utc` | `2023-06-15 02:30:00` |
| `date_local` | `2023-06-14 19:30:00` |
| `year` | `2023` |
| `month` | `6` |
| `day_of_week` | `Wednesday` |
| `venue_name` | `Yard House` |
| `category` | `American Restaurant` |
| `category_short` | `American` |
| `address` | `3333 Bear St` |
| `cross_street` | `at The District` |
| `city` | `Irvine` |
| `state` | `CA` |
| `postal_code` | `92612` |
| `country` | `United States` |
| `country_code` | `US` |
| `neighborhood` | `Irvine Center` |
| `lat` | `33.684` |
| `lng` | `-117.825` |
| `shout` | `Great beer selection!` |
| `type` | `checkin` |
| `photo_url` | `https://...original...jpg` |
| `venue_url` | `https://yardhouse.com` |
| `foursquare_url` | `https://app.foursquare.com/...` |

## Requirements

- Python 3.6+
- No external dependencies (stdlib only)

## Project Structure

```
swarm-download/
├── .env                    # Your OAuth token (not committed)
├── .env.example            # Template for .env
├── .gitignore
├── LICENSE
├── Makefile                # Make targets
├── README.md               # This file
├── download_checkins.py    # API downloader (auto-loads .env)
├── export_csv.py           # CSV exporter
├── search_checkins.py      # Interactive search tool
└── data/                   # Downloaded data (not committed)
    ├── all_checkins.json   # Raw API response
    ├── checkins_summary.json
    └── checkins.csv        # Exported CSV
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-21 | Initial release with `download_checkins.py` (paginated API download), `export_csv.py` (CSV export with filtering), and `search_checkins.py` (interactive search & stats tool with colored output). Makefile with targets for download, export, search, stats, venues, timeline, and categories. |

## License

MIT License - See [LICENSE](LICENSE) for details.

## About

Download and explore your complete Foursquare Swarm checkin history without waiting for a data export. Pull all your checkins directly via the API, export to CSV, and search/analyze your data with an interactive CLI tool.

Created by [Eric Blue](https://about.ericblue.com)
