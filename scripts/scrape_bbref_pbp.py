#!/usr/bin/env python3
"""
Scrape play-by-play data from Basketball Reference and save as parsed JSON.

Usage:
    python scripts/scrape_bbref_pbp.py NBA_1998
    python scripts/scrape_bbref_pbp.py NBA_1997 NBA_2002
    python scripts/scrape_bbref_pbp.py NBA_1998 --regular-season-only
    python scripts/scrape_bbref_pbp.py NBA_1998 --playoffs-only

Architecture decision: BBRef PBP data is saved in its own format in
data/bbref_pbp_cache/ rather than converted to the NBA CDN JSON format.

Rationale:
  1. The NBA CDN format uses numeric IDs (personId, teamId), structured fields
     (actionType, subType, qualifiers, shotResult, foulDrawnPersonId), and
     metadata (x/y coordinates, shotDistance) that simply don't exist in BBRef's
     text-based PBP. Faking these fields would create a brittle translation
     layer that silently breaks when edge cases arise.
  2. The existing parser (pure_ts_pct_single_game.py) relies heavily on CDN-
     specific fields like qualifiers=['2freethrow'], isFieldGoal=1, and
     foulDrawnPersonId for component classification. A converter would need to
     reverse-engineer all of this from free text — essentially rewriting the
     parser anyway.
  3. A separate BBRef adapter can be purpose-built to handle BBRef's text
     descriptions directly (e.g. "Shooting foul by X", "makes free throw 1 of
     2"), which is cleaner than forcing text into a numeric-ID schema.
  4. Keeping formats separate means CDN data and BBRef data can be validated
     independently. If BBRef changes their HTML format, only the BBRef code
     needs updating.

The BBRef JSON format stores classified events with extracted metadata (player
names, shot types, foul types, FT sequencing, distances) ready for a dedicated
PS% component classifier.
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GAME_ID_DIR = os.path.join(PROJECT_ROOT, "data", "bbref_game_ids")
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "bbref_pbp_cache")

DELAY = 4  # seconds between requests


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def normalize_text(text):
    """Normalize unicode characters (e.g. Kukoč) to clean UTF-8."""
    if not text:
        return text
    # Normalize to NFC form (composed characters)
    return unicodedata.normalize("NFC", text)


def extract_player(text):
    """Extract player name from a BBRef description cell's first <a> tag."""
    # We receive the raw td element, not just text
    return None  # handled in parse_row


def classify_event(desc):
    """Classify a PBP event from its text description.

    Returns (event_type, metadata_dict).
    """
    dl = desc.lower()
    meta = {}

    # --- Field goals ---
    m = re.search(r"makes (\d)-pt (.+?)(?:\s+from\s+(\d+)\s+ft)?(?:\s*\(assist by .+\))?$", dl)
    if m:
        pts = int(m.group(1))
        meta["shot_type"] = m.group(2).strip()
        if m.group(3):
            meta["distance_ft"] = int(m.group(3))
        # Check for assist
        assist_m = re.search(r"\(assist by (.+?)\)", desc)
        if assist_m:
            meta["assist_by"] = normalize_text(assist_m.group(1).strip())
        return f"made_{pts}pt", meta

    m = re.search(r"misses (\d)-pt (.+?)(?:\s+from\s+(\d+)\s+ft)?", dl)
    if m:
        pts = int(m.group(1))
        meta["shot_type"] = m.group(2).strip()
        if m.group(3):
            meta["distance_ft"] = int(m.group(3))
        # Check for block
        block_m = re.search(r"\(block by (.+?)\)", desc)
        if block_m:
            meta["blocked_by"] = normalize_text(block_m.group(1).strip())
        return f"miss_{pts}pt", meta

    # --- Free throws ---
    ft_m = re.search(r"(makes|misses) (?:technical )?free throw (\d+) of (\d+)", dl)
    if ft_m:
        made = ft_m.group(1) == "makes"
        meta["ft_num"] = int(ft_m.group(2))
        meta["ft_total"] = int(ft_m.group(3))
        meta["is_technical"] = "technical" in dl
        return "made_ft" if made else "miss_ft", meta

    # Technical free throw (alternate phrasing)
    if "technical free throw" in dl:
        made = "makes" in dl
        meta["is_technical"] = True
        meta["ft_num"] = 1
        meta["ft_total"] = 1
        return "made_ft" if made else "miss_ft", meta

    # Flagrant free throw
    if "flagrant free throw" in dl:
        made = "makes" in dl
        ft_m2 = re.search(r"(\d+) of (\d+)", dl)
        if ft_m2:
            meta["ft_num"] = int(ft_m2.group(1))
            meta["ft_total"] = int(ft_m2.group(2))
        meta["is_flagrant_ft"] = True
        return "made_ft" if made else "miss_ft", meta

    # --- Fouls ---
    if "shooting foul" in dl:
        drawn_m = re.search(r"shooting foul by (.+)", desc, re.IGNORECASE)
        if drawn_m:
            meta["fouler"] = normalize_text(drawn_m.group(1).strip())
        return "shooting_foul", meta

    if "loose ball foul" in dl:
        return "loose_ball_foul", meta

    if "offensive foul" in dl:
        return "offensive_foul", meta

    if "flagrant foul" in dl:
        # Try to get type (type 1 or type 2)
        flag_m = re.search(r"flagrant foul type (\d)", dl)
        if flag_m:
            meta["flagrant_type"] = int(flag_m.group(1))
        return "flagrant_foul", meta

    if "technical foul" in dl:
        return "technical_foul", meta

    if "away from play foul" in dl or "away from the play foul" in dl:
        return "away_from_play_foul", meta

    if "clear path foul" in dl:
        return "clear_path_foul", meta

    if "team foul" in dl:
        return "team_foul", meta

    if "personal foul" in dl:
        return "personal_foul", meta

    if "foul" in dl:
        return "other_foul", meta

    # --- Other events ---
    if "turnover" in dl:
        # Extract turnover type
        to_m = re.search(r"turnover.*?\((.+?)\)", desc, re.IGNORECASE)
        if to_m:
            meta["turnover_type"] = to_m.group(1).strip()
        return "turnover", meta

    if "offensive rebound" in dl:
        return "offensive_rebound", meta
    if "defensive rebound" in dl:
        return "defensive_rebound", meta
    if "rebound" in dl:
        return "rebound", meta

    if "enters the game" in dl or "substitution" in dl:
        return "substitution", meta

    if "timeout" in dl:
        return "timeout", meta

    if "violation" in dl:
        return "violation", meta

    return "other", meta


def parse_pbp_page(html, game_id):
    """Parse a BBRef PBP HTML page into structured events.

    Returns a dict with game_id, teams, events list.
    """
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="pbp")
    if not table:
        return {"game_id": game_id, "error": "No PBP table found", "events": []}

    # Get team names from column headers
    teams = {"away": None, "home": None}
    for row in table.find_all("tr", class_="thead"):
        ths = row.find_all("th")
        if len(ths) == 6:
            teams["away"] = normalize_text(ths[1].get_text(strip=True))
            teams["home"] = normalize_text(ths[5].get_text(strip=True))
            break

    events = []
    current_quarter = 0
    errors = []

    for row in table.find_all("tr"):
        # Quarter header
        if "thead" in row.get("class", []):
            th = row.find("th")
            if th and th.get("colspan"):
                qt = th.get_text(strip=True)
                if "1st" in qt:
                    current_quarter = 1
                elif "2nd" in qt:
                    current_quarter = 2
                elif "3rd" in qt:
                    current_quarter = 3
                elif "4th" in qt:
                    current_quarter = 4
                elif "OT" in qt:
                    m = re.search(r"(\d+)", qt)
                    current_quarter = 4 + (int(m.group(1)) if m else 1)
            continue

        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        time_str = tds[0].get_text(strip=True)

        # Colspan rows: quarter start/end, jump balls
        if len(tds) == 2 and tds[1].get("colspan"):
            desc = normalize_text(tds[1].get_text(strip=True))
            event = {
                "quarter": current_quarter,
                "time": time_str,
                "type": "meta",
                "description": desc,
                "team": None,
                "side": None,
            }
            # Parse jump ball details
            if "jump ball" in desc.lower():
                event["type"] = "jump_ball"
            elif "start of" in desc.lower():
                event["type"] = "period_start"
            elif "end of" in desc.lower():
                event["type"] = "period_end"
            events.append(event)
            continue

        # Standard 6-column rows
        if len(tds) != 6:
            continue

        away_td = tds[1]
        home_td = tds[5]
        score_text = tds[3].get_text(strip=True)

        away_text = away_td.get_text(strip=True)
        home_text = home_td.get_text(strip=True)

        # Determine which side has the event
        # BBRef uses \xa0 (non-breaking space) for empty cells
        away_has = away_text and away_text not in ("\xa0", "")
        home_has = home_text and home_text not in ("\xa0", "")

        if away_has:
            desc_raw = away_text
            td_el = away_td
            team = teams["away"]
            side = "away"
        elif home_has:
            desc_raw = home_text
            td_el = home_td
            team = teams["home"]
            side = "home"
        else:
            continue

        desc = normalize_text(desc_raw)

        # Fix known BBRef spacing issue: "foul byX. Name" → "foul by X. Name"
        desc = re.sub(r"(foul by|Turnover by|rebound by)(\S)", r"\1 \2", desc)

        # Classify the event
        event_type, meta = classify_event(desc)

        event = {
            "quarter": current_quarter,
            "time": time_str,
            "score": score_text,
            "team": team,
            "side": side,
            "type": event_type,
            "description": desc,
        }

        # Extract player name (first <a> tag in the active cell)
        link = td_el.find("a")
        if link:
            event["player"] = normalize_text(link.get_text(strip=True))
            player_href = link.get("href", "")
            if player_href:
                event["player_id"] = player_href  # e.g. /players/j/jordami01.html

        # Merge classification metadata
        event.update(meta)

        events.append(event)

    return {
        "game_id": game_id,
        "teams": teams,
        "event_count": len(events),
        "events": events,
        "parse_errors": errors,
    }


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def load_urls(season, mode):
    """Load PBP URLs for a season. mode is 'both', 'regular', or 'playoffs'."""
    urls = []
    if mode in ("both", "regular"):
        path = os.path.join(GAME_ID_DIR, f"{season}_regular_season_pbp_urls.txt")
        if os.path.exists(path):
            with open(path) as f:
                urls.extend(line.strip() for line in f if line.strip())
        else:
            print(f"  Warning: {path} not found")
    if mode in ("both", "playoffs"):
        path = os.path.join(GAME_ID_DIR, f"{season}_playoffs_pbp_urls.txt")
        if os.path.exists(path):
            with open(path) as f:
                urls.extend(line.strip() for line in f if line.strip())
        else:
            print(f"  Warning: {path} not found")
    return urls


def game_id_from_url(url):
    """Extract game ID from a BBRef PBP URL."""
    return url.rstrip("/").split("/")[-1].replace(".html", "")


def scrape_season(season, mode):
    """Scrape all PBP games for a season."""
    urls = load_urls(season, mode)
    if not urls:
        print(f"  No URLs found for {season} (mode={mode})")
        return {"fetched": 0, "skipped": 0, "failed": 0, "errors": []}

    total = len(urls)
    fetched = 0
    skipped = 0
    failed = 0
    error_list = []
    start_time = time.time()

    print(f"  {total} games to process (mode={mode})")

    for i, url in enumerate(urls):
        game_id = game_id_from_url(url)
        cache_path = os.path.join(CACHE_DIR, f"{game_id}.json")

        # Resumable: skip if already cached
        if os.path.exists(cache_path):
            skipped += 1
            continue

        # Rate limiting
        if fetched > 0:
            time.sleep(DELAY)

        # Progress
        elapsed = time.time() - start_time
        if fetched > 0:
            rate = elapsed / fetched
            remaining = (total - i) * rate
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            eta_str = f" | ETA: {mins}m{secs:02d}s"
        else:
            eta_str = ""

        print(f"  [{i+1}/{total}] {game_id}{eta_str}", end="", flush=True)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
        except Exception as e:
            print(f" ERROR: {e}")
            failed += 1
            error_list.append((game_id, str(e)))
            continue

        if resp.status_code != 200:
            print(f" HTTP {resp.status_code}")
            failed += 1
            error_list.append((game_id, f"HTTP {resp.status_code}"))
            continue

        # Parse
        game_data = parse_pbp_page(resp.text, game_id)

        if game_data.get("error"):
            print(f" PARSE ERROR: {game_data['error']}")
            failed += 1
            error_list.append((game_id, game_data["error"]))
            continue

        # Save
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)

        fetched += 1
        print(f" → {game_data['event_count']} events")

    return {
        "fetched": fetched,
        "skipped": skipped,
        "failed": failed,
        "errors": error_list,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scrape BBRef play-by-play data for PS% analysis."
    )
    parser.add_argument(
        "seasons", nargs="+",
        help="Season identifiers (e.g. NBA_1998) or a range (NBA_1997 NBA_2002)"
    )
    parser.add_argument(
        "--regular-season-only", action="store_true",
        help="Only scrape regular season games"
    )
    parser.add_argument(
        "--playoffs-only", action="store_true",
        help="Only scrape playoff games"
    )
    args = parser.parse_args()

    # Determine mode
    if args.regular_season_only and args.playoffs_only:
        print("Error: cannot use both --regular-season-only and --playoffs-only")
        sys.exit(1)
    if args.regular_season_only:
        mode = "regular"
    elif args.playoffs_only:
        mode = "playoffs"
    else:
        mode = "both"

    # Expand season range: if two args like NBA_1997 NBA_2002, expand to all
    if len(args.seasons) == 2:
        try:
            start = int(args.seasons[0].replace("NBA_", ""))
            end = int(args.seasons[1].replace("NBA_", ""))
            if start < end:
                seasons = [f"NBA_{y}" for y in range(start, end + 1)]
            else:
                seasons = args.seasons
        except ValueError:
            seasons = args.seasons
    else:
        seasons = args.seasons

    os.makedirs(CACHE_DIR, exist_ok=True)

    # Run
    grand_totals = {"fetched": 0, "skipped": 0, "failed": 0}
    all_errors = []

    for season in seasons:
        print(f"\n{'='*60}")
        print(f"{season}")
        print(f"{'='*60}")
        result = scrape_season(season, mode)
        grand_totals["fetched"] += result["fetched"]
        grand_totals["skipped"] += result["skipped"]
        grand_totals["failed"] += result["failed"]
        all_errors.extend(result["errors"])

        print(f"\n  Summary: {result['fetched']} fetched, "
              f"{result['skipped']} skipped (cached), "
              f"{result['failed']} failed")

    # Grand summary
    print(f"\n{'='*60}")
    print(f"GRAND TOTAL")
    print(f"{'='*60}")
    print(f"  Fetched:  {grand_totals['fetched']}")
    print(f"  Skipped:  {grand_totals['skipped']} (already cached)")
    print(f"  Failed:   {grand_totals['failed']}")

    if all_errors:
        print(f"\n  Errors ({len(all_errors)}):")
        for gid, err in all_errors[:20]:
            print(f"    {gid}: {err}")
        if len(all_errors) > 20:
            print(f"    ... and {len(all_errors) - 20} more")


if __name__ == "__main__":
    main()
