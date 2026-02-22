#!/usr/bin/env python3
"""Interactive search tool for Foursquare/Swarm checkins."""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

# ── ANSI colors ──────────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
WHITE = "\033[97m"
BLUE = "\033[34m"
RED = "\033[31m"

# ── Data loading ─────────────────────────────────────────────────────────────

DATA_FILE = "data/all_checkins.json"


def load_checkins(path=DATA_FILE):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("checkins", data if isinstance(data, list) else [])

    checkins = []
    for c in raw:
        venue = c.get("venue", {})
        location = venue.get("location", {})
        categories = venue.get("categories", [])
        category = categories[0].get("name", "") if categories else ""
        category_short = categories[0].get("shortName", "") if categories else ""

        ts = c.get("createdAt")
        tz_offset = c.get("timeZoneOffset", 0)
        if ts:
            utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            local_dt = utc_dt + timedelta(minutes=tz_offset)
        else:
            local_dt = None

        checkins.append({
            "id": c.get("id", ""),
            "dt": local_dt,
            "venue": venue.get("name", ""),
            "category": category,
            "category_short": category_short,
            "address": location.get("address", ""),
            "city": location.get("city", ""),
            "state": location.get("state", ""),
            "country": location.get("cc", ""),
            "neighborhood": location.get("neighborhood", ""),
            "lat": location.get("lat"),
            "lng": location.get("lng"),
            "shout": c.get("shout", ""),
            "type": c.get("type", ""),
        })
    return checkins


# ── Formatting helpers ───────────────────────────────────────────────────────

def fmt_date(dt):
    if not dt:
        return "unknown date"
    return dt.strftime("%a %b %d, %Y  %I:%M %p")


def fmt_checkin(c, show_category=True, index=None):
    """Format a single checkin as a colored string."""
    parts = []
    if index is not None:
        parts.append(f"{DIM}{index:>4}.{RESET}")

    parts.append(f"  {CYAN}{fmt_date(c['dt'])}{RESET}")
    parts.append(f"  {BOLD}{WHITE}{c['venue']}{RESET}")

    details = []
    if show_category and c["category"]:
        details.append(f"{MAGENTA}{c['category']}{RESET}")
    if c["city"]:
        loc = c["city"]
        if c["state"]:
            loc += f", {c['state']}"
        details.append(f"{GREEN}{loc}{RESET}")
    if c["neighborhood"]:
        details.append(f"{DIM}{c['neighborhood']}{RESET}")
    if details:
        parts.append(f"  {DIM}|{RESET} " + f" {DIM}|{RESET} ".join(details))

    if c["shout"]:
        parts.append(f"\n        {YELLOW}\"{c['shout']}\"{RESET}")

    return "".join(parts)


def print_header(text):
    width = 70
    print(f"\n{BOLD}{BLUE}{'─' * width}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'─' * width}{RESET}\n")


def print_count(n, label="checkins"):
    print(f"  {DIM}{n} {label}{RESET}\n")


def print_bar_chart(counter, max_bars=25, top_n=20):
    """Print a horizontal bar chart from a Counter."""
    items = counter.most_common(top_n)
    if not items:
        return
    max_count = items[0][1]
    max_label_len = max(len(str(k)) for k, _ in items)

    for label, count in items:
        bar_len = int((count / max_count) * max_bars)
        bar = "█" * bar_len
        print(f"  {str(label):>{max_label_len}}  {GREEN}{bar}{RESET} {BOLD}{count}{RESET}")
    print()


# ── Search/filter functions ──────────────────────────────────────────────────

def filter_checkins(checkins, year=None, month=None, venue=None, category=None,
                    city=None, state=None, shout=None):
    results = checkins
    if year:
        results = [c for c in results if c["dt"] and c["dt"].year == year]
    if month:
        results = [c for c in results if c["dt"] and c["dt"].month == month]
    if venue:
        v = venue.lower()
        results = [c for c in results if v in c["venue"].lower()]
    if category:
        cat = category.lower()
        results = [c for c in results if cat in c["category"].lower() or cat in c["category_short"].lower()]
    if city:
        ci = city.lower()
        results = [c for c in results if ci in c["city"].lower()]
    if state:
        st = state.lower()
        results = [c for c in results if st == c["state"].lower()]
    if shout:
        sh = shout.lower()
        results = [c for c in results if c["shout"] and sh in c["shout"].lower()]
    return results


# ── Command handlers ─────────────────────────────────────────────────────────

def cmd_search(checkins, args):
    results = filter_checkins(
        checkins, year=args.year, month=args.month, venue=args.venue,
        category=args.category, city=args.city, state=args.state, shout=args.shout,
    )
    results.sort(key=lambda c: c["dt"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    limit = args.limit or 25
    total = len(results)
    shown = results[:limit]

    # Build a header describing the search
    filters = []
    if args.year:
        filters.append(f"year={args.year}")
    if args.month:
        filters.append(f"month={args.month}")
    if args.venue:
        filters.append(f"venue~\"{args.venue}\"")
    if args.category:
        filters.append(f"category~\"{args.category}\"")
    if args.city:
        filters.append(f"city~\"{args.city}\"")
    if args.state:
        filters.append(f"state={args.state}")
    if args.shout:
        filters.append(f"shout~\"{args.shout}\"")
    title = "Search: " + ", ".join(filters) if filters else "All Checkins"
    print_header(title)
    print_count(total)

    for i, c in enumerate(shown, 1):
        print(fmt_checkin(c, index=i))
    print()

    if total > limit:
        print(f"  {DIM}Showing {limit} of {total} results. Use --limit to see more.{RESET}\n")


def cmd_stats(checkins, args):
    results = filter_checkins(
        checkins, year=args.year, month=args.month, venue=args.venue,
        category=args.category, city=args.city, state=args.state,
    )
    title = "Stats"
    if args.year:
        title += f" for {args.year}"
    if args.month:
        months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        title += f" {months[args.month]}"
    print_header(title)
    print_count(len(results))

    # Top venues
    print(f"  {BOLD}Top Venues{RESET}")
    print_bar_chart(Counter(c["venue"] for c in results if c["venue"]))

    # Top categories
    print(f"  {BOLD}Top Categories{RESET}")
    print_bar_chart(Counter(c["category"] for c in results if c["category"]))

    # Top cities
    print(f"  {BOLD}Top Cities{RESET}")
    print_bar_chart(Counter(c["city"] for c in results if c["city"]))

    # By month (if not filtering by month)
    if not args.month and results:
        print(f"  {BOLD}By Month{RESET}")
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_counter = Counter(c["dt"].month for c in results if c["dt"])
        ordered = {month_names[m]: month_counter.get(m, 0) for m in range(1, 13)}
        print_bar_chart(Counter(ordered))

    # By day of week
    if results:
        print(f"  {BOLD}By Day of Week{RESET}")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_counter = Counter(c["dt"].strftime("%A") for c in results if c["dt"])
        ordered = {d: day_counter.get(d, 0) for d in days}
        print_bar_chart(Counter(ordered))


def cmd_venues(checkins, args):
    results = filter_checkins(
        checkins, year=args.year, month=args.month, category=args.category,
        city=args.city, state=args.state,
    )
    print_header("Venue Rankings")
    print_count(len(results))

    venue_counts = Counter(c["venue"] for c in results if c["venue"])
    top_n = args.limit or 30

    items = venue_counts.most_common(top_n)
    max_count = items[0][1] if items else 0
    max_label = max(len(v) for v, _ in items) if items else 0

    for rank, (venue, count) in enumerate(items, 1):
        # Find latest visit and category for this venue
        venue_checkins = [c for c in results if c["venue"] == venue]
        latest = max(venue_checkins, key=lambda c: c["dt"] or datetime.min.replace(tzinfo=timezone.utc))
        cat = latest["category_short"] or latest["category"]
        city = latest["city"]

        bar_len = int((count / max_count) * 20)
        bar = "█" * bar_len

        print(
            f"  {BOLD}{rank:>3}.{RESET} {WHITE}{venue:{max_label}}{RESET}  "
            f"{GREEN}{bar}{RESET} {BOLD}{count:>3}{RESET}  "
            f"{DIM}{cat}{RESET}  {DIM}{city}{RESET}"
        )
    print()


def cmd_timeline(checkins, args):
    results = filter_checkins(
        checkins, year=args.year, venue=args.venue, category=args.category,
        city=args.city, state=args.state,
    )
    results.sort(key=lambda c: c["dt"] or datetime.min.replace(tzinfo=timezone.utc))

    title = "Timeline"
    if args.year:
        title += f" {args.year}"
    print_header(title)
    print_count(len(results))

    # Group by year-month
    groups = {}
    for c in results:
        if c["dt"]:
            key = c["dt"].strftime("%Y-%m")
            groups.setdefault(key, []).append(c)

    for ym in sorted(groups):
        items = groups[ym]
        dt = items[0]["dt"]
        label = dt.strftime("%B %Y")
        bar_len = min(len(items), 50)
        bar = "█" * bar_len
        print(f"  {BOLD}{label:>18}{RESET}  {GREEN}{bar}{RESET} {len(items)}")
    print()


def cmd_categories(checkins, args):
    results = filter_checkins(
        checkins, year=args.year, month=args.month, city=args.city, state=args.state,
    )
    print_header("Category Breakdown")
    print_count(len(results))

    cat_counts = Counter(c["category"] for c in results if c["category"])
    print_bar_chart(cat_counts, top_n=30, max_bars=30)


def cmd_interactive(checkins):
    """Interactive REPL mode."""
    print_header("Swarm Checkin Explorer")
    print(f"  {len(checkins)} checkins loaded")
    print(f"  Type a search query or command. {DIM}Type 'help' for options.{RESET}\n")

    while True:
        try:
            raw = input(f"{BOLD}{BLUE}swarm>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not raw:
            continue

        if raw.lower() in ("quit", "exit", "q"):
            break

        if raw.lower() == "help":
            print(f"""
  {BOLD}Quick Search:{RESET}
    Just type a venue name, city, or category to search across all fields.

  {BOLD}Filters{RESET} (can combine):
    {CYAN}year YYYY{RESET}         Filter by year          (e.g., year 2019)
    {CYAN}month N{RESET}           Filter by month 1-12    (e.g., month 12)
    {CYAN}city NAME{RESET}         Filter by city           (e.g., city irvine)
    {CYAN}state XX{RESET}          Filter by state          (e.g., state CA)
    {CYAN}cat NAME{RESET}          Filter by category       (e.g., cat sushi)

  {BOLD}Commands:{RESET}
    {CYAN}stats{RESET}             Show overall stats
    {CYAN}stats YYYY{RESET}        Stats for a year         (e.g., stats 2023)
    {CYAN}venues{RESET}            Top venues ranking
    {CYAN}timeline{RESET}          Monthly timeline chart
    {CYAN}categories{RESET}        Category breakdown
    {CYAN}help{RESET}              This help
    {CYAN}quit{RESET}              Exit
""")
            continue

        # Parse the input
        tokens = raw.split()
        cmd = tokens[0].lower()

        # Stats command
        if cmd == "stats":
            year = int(tokens[1]) if len(tokens) > 1 and tokens[1].isdigit() else None
            ns = argparse.Namespace(
                year=year, month=None, venue=None, category=None,
                city=None, state=None, shout=None, limit=None,
            )
            cmd_stats(checkins, ns)
            continue

        # Venues command
        if cmd == "venues":
            year = int(tokens[1]) if len(tokens) > 1 and tokens[1].isdigit() else None
            ns = argparse.Namespace(
                year=year, month=None, venue=None, category=None,
                city=None, state=None, limit=30,
            )
            cmd_venues(checkins, ns)
            continue

        # Timeline command
        if cmd == "timeline":
            year = int(tokens[1]) if len(tokens) > 1 and tokens[1].isdigit() else None
            ns = argparse.Namespace(
                year=year, month=None, venue=None, category=None,
                city=None, state=None,
            )
            cmd_timeline(checkins, ns)
            continue

        # Categories command
        if cmd in ("categories", "cats"):
            year = int(tokens[1]) if len(tokens) > 1 and tokens[1].isdigit() else None
            ns = argparse.Namespace(
                year=year, month=None, city=None, state=None,
            )
            cmd_categories(checkins, ns)
            continue

        # Filter-based search: year YYYY, month N, city X, state X, cat X
        year = month = venue = category = city = state = None
        free_text = []
        i = 0
        while i < len(tokens):
            t = tokens[i].lower()
            if t == "year" and i + 1 < len(tokens) and tokens[i + 1].isdigit():
                year = int(tokens[i + 1])
                i += 2
            elif t == "month" and i + 1 < len(tokens) and tokens[i + 1].isdigit():
                month = int(tokens[i + 1])
                i += 2
            elif t == "city" and i + 1 < len(tokens):
                city = tokens[i + 1]
                i += 2
            elif t == "state" and i + 1 < len(tokens):
                state = tokens[i + 1]
                i += 2
            elif t == "cat" and i + 1 < len(tokens):
                category = " ".join(tokens[i + 1:])
                i = len(tokens)
            else:
                free_text.append(tokens[i])
                i += 1

        query = " ".join(free_text)

        # Free text: search across venue, category, city, shout
        if query and not any([year, month, category, city, state]):
            # Try broad search
            q = query.lower()
            results = [
                c for c in checkins
                if q in c["venue"].lower()
                or q in c["category"].lower()
                or q in c["city"].lower()
                or (c["shout"] and q in c["shout"].lower())
                or q in c["neighborhood"].lower()
            ]
        else:
            results = filter_checkins(
                checkins, year=year, month=month, venue=query or None,
                category=category, city=city, state=state,
            )

        results.sort(key=lambda c: c["dt"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        if not results:
            print(f"\n  {DIM}No results found.{RESET}\n")
            continue

        # Show results
        show_n = min(len(results), 25)
        print_header(f"Results for \"{raw}\"")
        print_count(len(results))

        for i, c in enumerate(results[:show_n], 1):
            print(fmt_checkin(c, index=i))
        print()

        if len(results) > show_n:
            print(f"  {DIM}Showing {show_n} of {len(results)}. Narrow your search to see more.{RESET}\n")

        # Quick stats for the results
        if len(results) > 5:
            top_venues = Counter(c["venue"] for c in results).most_common(5)
            venue_str = ", ".join(f"{v} ({n})" for v, n in top_venues)
            print(f"  {DIM}Top venues: {venue_str}{RESET}\n")


# ── CLI argument parsing ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Search and explore Swarm checkins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s                                 Interactive mode
  %(prog)s search --venue starbucks        Find all Starbucks visits
  %(prog)s search --year 2019 --city "san francisco"
  %(prog)s search --category sushi         Find sushi restaurants
  %(prog)s stats                           Overall stats
  %(prog)s stats --year 2023               Stats for 2023
  %(prog)s venues --city "los angeles"     Top LA venues
  %(prog)s timeline                        Monthly checkin chart
  %(prog)s categories --year 2020          Category breakdown for 2020
        """,
    )
    parser.add_argument(
        "-i", "--input", default=DATA_FILE,
        help="Input JSON file (default: data/all_checkins.json)",
    )

    sub = parser.add_subparsers(dest="command")

    # Shared filter args
    def add_filters(p, with_limit=True):
        p.add_argument("--year", type=int, help="Filter by year")
        p.add_argument("--month", type=int, help="Filter by month (1-12)")
        p.add_argument("--venue", help="Search venue name (substring)")
        p.add_argument("--category", help="Search category (substring)")
        p.add_argument("--city", help="Search city (substring)")
        p.add_argument("--state", help="Filter by state code (e.g. CA)")
        p.add_argument("--shout", help="Search shout text (substring)")
        if with_limit:
            p.add_argument("--limit", type=int, help="Max results to show")

    # search
    p_search = sub.add_parser("search", help="Search checkins with filters")
    add_filters(p_search)

    # stats
    p_stats = sub.add_parser("stats", help="Show stats and charts")
    add_filters(p_stats, with_limit=False)

    # venues
    p_venues = sub.add_parser("venues", help="Top venues ranking")
    add_filters(p_venues)

    # timeline
    p_timeline = sub.add_parser("timeline", help="Monthly timeline chart")
    add_filters(p_timeline, with_limit=False)

    # categories
    p_cats = sub.add_parser("categories", help="Category breakdown")
    p_cats.add_argument("--year", type=int, help="Filter by year")
    p_cats.add_argument("--month", type=int, help="Filter by month (1-12)")
    p_cats.add_argument("--city", help="Search city (substring)")
    p_cats.add_argument("--state", help="Filter by state code")

    args = parser.parse_args()

    checkins = load_checkins(args.input)

    if args.command is None:
        cmd_interactive(checkins)
    elif args.command == "search":
        cmd_search(checkins, args)
    elif args.command == "stats":
        cmd_stats(checkins, args)
    elif args.command == "venues":
        cmd_venues(checkins, args)
    elif args.command == "timeline":
        cmd_timeline(checkins, args)
    elif args.command == "categories":
        cmd_categories(checkins, args)


if __name__ == "__main__":
    main()
