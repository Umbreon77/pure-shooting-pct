#!/usr/bin/env python3
"""
Feasibility test: scrape 5 PBP games from Basketball Reference (1996-97).
Parses the PBP table HTML directly with BeautifulSoup.
"""

import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.basketball-reference.com/boxscores/pbp/199611020CHI.html",
    "https://www.basketball-reference.com/boxscores/pbp/199611030NYK.html",
    "https://www.basketball-reference.com/boxscores/pbp/199611050BOS.html",
    "https://www.basketball-reference.com/boxscores/pbp/199611060CHI.html",
    "https://www.basketball-reference.com/boxscores/pbp/199611080CLE.html",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "bbref_pbp_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def parse_pbp_page(html, url):
    """Parse a BBRef PBP page into structured events."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract game ID from URL
    game_id = url.split("/")[-1].replace(".html", "")

    # Find the PBP table
    table = soup.find("table", id="pbp")
    if not table:
        return {"game_id": game_id, "error": "No PBP table found", "events": []}

    # Get team names from the header row
    header_rows = table.find_all("tr", class_="thead")
    teams = {"away": None, "home": None}
    for row in header_rows:
        ths = row.find_all("th")
        if len(ths) == 6:  # Column header row
            teams["away"] = ths[1].get_text(strip=True)
            teams["home"] = ths[5].get_text(strip=True)
            break

    events = []
    current_quarter = 0

    for row in table.find_all("tr"):
        # Quarter header rows
        if "thead" in row.get("class", []):
            th = row.find("th")
            if th and th.get("colspan"):
                qt = th.get_text(strip=True)
                if "1st" in qt: current_quarter = 1
                elif "2nd" in qt: current_quarter = 2
                elif "3rd" in qt: current_quarter = 3
                elif "4th" in qt: current_quarter = 4
                elif "OT" in qt:
                    # Handle OT, 2OT, etc.
                    m = re.search(r"(\d+)", qt)
                    current_quarter = 4 + (int(m.group(1)) if m else 1)
            continue

        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        time_str = tds[0].get_text(strip=True)

        # Handle colspan=5 rows (quarter start/end, jump balls)
        if len(tds) == 2 and tds[1].get("colspan"):
            desc = tds[1].get_text(strip=True)
            events.append({
                "quarter": current_quarter,
                "time": time_str,
                "type": "meta",
                "description": desc,
                "team": None,
            })
            continue

        # Standard 6-column rows: Time | Away | +/- | Score | +/- | Home
        if len(tds) == 6:
            away_text = tds[1].get_text(strip=True)
            home_text = tds[5].get_text(strip=True)
            score = tds[3].get_text(strip=True)

            # Determine which side has the event
            if away_text and away_text != "\xa0":
                desc = away_text
                team = teams["away"]
                side = "away"
            elif home_text and home_text != "\xa0":
                desc = home_text
                team = teams["home"]
                side = "home"
            else:
                continue

            # Classify the event
            event = {
                "quarter": current_quarter,
                "time": time_str,
                "score": score,
                "team": team,
                "side": side,
                "description": desc,
            }

            # Classify event type from description
            dl = desc.lower()
            if "makes 2-pt" in dl:
                event["type"] = "made_2pt"
            elif "makes 3-pt" in dl:
                event["type"] = "made_3pt"
            elif "misses 2-pt" in dl:
                event["type"] = "miss_2pt"
            elif "misses 3-pt" in dl:
                event["type"] = "miss_3pt"
            elif "makes free throw" in dl:
                event["type"] = "made_ft"
            elif "misses free throw" in dl:
                event["type"] = "miss_ft"
            elif "shooting foul" in dl:
                event["type"] = "shooting_foul"
            elif "personal foul" in dl:
                event["type"] = "personal_foul"
            elif "loose ball foul" in dl:
                event["type"] = "loose_ball_foul"
            elif "offensive foul" in dl:
                event["type"] = "offensive_foul"
            elif "flagrant foul" in dl:
                event["type"] = "flagrant_foul"
            elif "technical foul" in dl:
                event["type"] = "technical_foul"
            elif "foul" in dl:
                event["type"] = "other_foul"
            elif "turnover" in dl:
                event["type"] = "turnover"
            elif "rebound" in dl:
                event["type"] = "rebound"
            elif "steal" in dl:
                event["type"] = "steal"
            elif "block" in dl:
                event["type"] = "block"
            elif "substitution" in dl or "enters" in dl:
                event["type"] = "substitution"
            elif "timeout" in dl:
                event["type"] = "timeout"
            elif "violation" in dl:
                event["type"] = "violation"
            else:
                event["type"] = "other"

            # Extract player name (first linked player)
            link = tds[1].find("a") if side == "away" else tds[5].find("a")
            if link:
                event["player"] = link.get_text(strip=True)
                event["player_url"] = link.get("href", "")

            # Extract FT info (e.g., "free throw 1 of 2")
            ft_match = re.search(r"free throw (\d+) of (\d+)", dl)
            if ft_match:
                event["ft_num"] = int(ft_match.group(1))
                event["ft_total"] = int(ft_match.group(2))

            # Extract shot distance
            dist_match = re.search(r"from (\d+) ft", dl)
            if dist_match:
                event["distance_ft"] = int(dist_match.group(1))

            events.append(event)

    return {
        "game_id": game_id,
        "teams": teams,
        "event_count": len(events),
        "events": events,
    }


def summarize(game_data):
    """Print a summary of parsed PBP data."""
    events = game_data["events"]
    types = {}
    for e in events:
        t = e.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    teams = game_data.get("teams", {})
    print(f"\n{'='*60}")
    print(f"Game: {game_data['game_id']}")
    print(f"Teams: {teams.get('away', '?')} @ {teams.get('home', '?')}")
    print(f"Total events: {len(events)}")
    print(f"\nEvent breakdown:")
    for t in sorted(types.keys()):
        print(f"  {t:25s} {types[t]:4d}")

    # Check foul types
    foul_types = [t for t in types if "foul" in t]
    ft_events = types.get("made_ft", 0) + types.get("miss_ft", 0)
    print(f"\nFoul types identifiable: {', '.join(foul_types) if foul_types else 'NONE'}")
    print(f"Free throw events: {ft_events}")

    # Check if FT numbering works
    ft_with_nums = sum(1 for e in events if e.get("ft_num"))
    print(f"FTs with sequence info (1 of 2, etc.): {ft_with_nums}")

    # Check shot type breakdown
    shots_2 = types.get("made_2pt", 0) + types.get("miss_2pt", 0)
    shots_3 = types.get("made_3pt", 0) + types.get("miss_3pt", 0)
    print(f"2PT attempts: {shots_2}, 3PT attempts: {shots_3}")


def main():
    for i, url in enumerate(URLS):
        if i > 0:
            print(f"\n... waiting 4 seconds ...")
            time.sleep(4)

        game_id = url.split("/")[-1].replace(".html", "")
        cache_path = os.path.join(CACHE_DIR, f"{game_id}.json")

        print(f"\nFetching [{i+1}/5]: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        print(f"  Status: {resp.status_code}, Size: {len(resp.text):,} bytes")

        if resp.status_code != 200:
            print(f"  ERROR: Got status {resp.status_code}")
            continue

        game_data = parse_pbp_page(resp.text, url)

        # Save to cache
        with open(cache_path, "w") as f:
            json.dump(game_data, f, indent=2)
        print(f"  Saved: {cache_path}")

        summarize(game_data)

    print(f"\n{'='*60}")
    print("FEASIBILITY TEST COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
