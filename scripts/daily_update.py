#!/usr/bin/env python3
"""
Pure TS% — Daily Incremental Update

Fetches last night's games, reprocesses only the affected players, updates
their result files, regenerates the league CSVs, and rebuilds the viewer.

Instead of the ~15-minute full league run, this typically finishes in ~30
seconds because:
  - PBP files are already cached from the nightly CDN fetch
  - Only ~30 players (those who played last night) are reprocessed
  - Game logs for those players are updated individually, not bulk-fetched

Usage:
    python scripts/daily_update.py
    python scripts/daily_update.py --date 2026-03-20
    python scripts/daily_update.py --date 2026-03-20 --no-viewer
    python scripts/daily_update.py --season 2024-25 --date 2025-03-20
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Path constants (all absolute)
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
PBP_CACHE = os.path.join(DATA_DIR, "pbp_cache")
RESULTS_DIR = os.path.join(DATA_DIR, "league_results")

# ---------------------------------------------------------------------------
# Imports from existing scripts (same sys.path approach used by league.py)
# ---------------------------------------------------------------------------

sys.path.insert(0, SCRIPT_DIR)

from pure_ts_pct_single_game import (
    COMPONENTS,
    classify_scoring_events,
    calculate_pure_ts,
    box_score_from_components,
)

from pure_ts_pct_season import (
    NBA_HEADERS,
    FETCH_DELAY,
    fetch_pbp_cached,
)

from pure_ts_pct_league import (
    COMP_IDS,
    _result_path,
    is_player_done,
    save_player_result,
    load_player_result,
    load_player_list,
    process_player_season,
    generate_csvs,
    _game_log_cache_path,
)

# ---------------------------------------------------------------------------
# CDN fetch with retry
# ---------------------------------------------------------------------------

RETRY_DELAY = 30  # seconds between retries when rate-limited
MAX_RETRIES = 3


def _fetch_pbp_with_retry(game_id):
    """
    Fetch PBP for game_id from CDN, writing to cache.  Returns True on
    success, False if all retries failed.  Skips the network call if already
    cached.
    """
    cache_path = os.path.join(PBP_CACHE, f"{game_id}.json")
    if os.path.exists(cache_path):
        return True  # already cached — nothing to do

    url = (
        f"https://cdn.nba.com/static/json/liveData/playbyplay/"
        f"playbyplay_{game_id}.json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            os.makedirs(PBP_CACHE, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(data, f)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                print(f"    Rate-limited on {game_id}; waiting {RETRY_DELAY}s "
                      f"(attempt {attempt}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                print(f"    WARNING: PBP fetch failed for {game_id} — {e}")
                return False
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"    Retry {attempt} for {game_id} after error: {e}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"    WARNING: PBP fetch failed for {game_id} — {e}")
                return False

    return False

# ---------------------------------------------------------------------------
# Step 1: Discover last night's games via ScoreboardV3
# ---------------------------------------------------------------------------

def get_games_for_date(date_str):
    """
    Use nba_api ScoreboardV3 to get all game IDs played on date_str
    (format: 'YYYY-MM-DD').

    Returns a list of game_id strings.  Returns [] if no games.
    """
    try:
        from nba_api.stats.endpoints import scoreboardv3
    except ImportError:
        sys.exit(
            "ERROR: nba_api is not installed. "
            "Run: pip install nba_api"
        )

    try:
        sb = scoreboardv3.ScoreboardV3(game_date=date_str, league_id="00")
        data = sb.get_dict()
        games = data["scoreboard"]["games"]
        return [g["gameId"] for g in games]
    except Exception as e:
        print(f"  WARNING: ScoreboardV3 call failed — {e}")
        return []

# ---------------------------------------------------------------------------
# Step 2: Fetch PBP for new games
# ---------------------------------------------------------------------------

def fetch_pbp_for_games(game_ids):
    """
    Ensure PBP JSON is cached for every game_id in the list.

    Prints progress and returns (fetched_count, error_count).
    """
    os.makedirs(PBP_CACHE, exist_ok=True)

    already_cached = [
        gid for gid in game_ids
        if os.path.exists(os.path.join(PBP_CACHE, f"{gid}.json"))
    ]
    to_fetch = [
        gid for gid in game_ids
        if not os.path.exists(os.path.join(PBP_CACHE, f"{gid}.json"))
    ]

    if already_cached:
        print(f"  PBP: {len(already_cached)}/{len(game_ids)} already cached")

    fetched = 0
    errors = 0
    for gid in to_fetch:
        print(f"  Fetching PBP: {gid}", end=" ... ", flush=True)
        ok = _fetch_pbp_with_retry(gid)
        if ok:
            fetched += 1
            print("OK")
        else:
            errors += 1
            print("FAILED")
        time.sleep(FETCH_DELAY)

    return fetched, errors

# ---------------------------------------------------------------------------
# Step 3: Identify players who had scoring events in the new games
# ---------------------------------------------------------------------------

def extract_scoring_player_ids(game_ids):
    """
    Read each PBP cache file and collect the set of player IDs who had at
    least one field goal attempt or free throw event.

    Returns a set of integer player IDs.
    """
    player_ids = set()
    for gid in game_ids:
        cache_path = os.path.join(PBP_CACHE, f"{gid}.json")
        if not os.path.exists(cache_path):
            print(f"  WARNING: PBP not cached for {gid} — cannot identify players")
            continue
        try:
            with open(cache_path) as f:
                data = json.load(f)
            actions = data["game"]["actions"]
            for a in actions:
                if a.get("isFieldGoal") == 1 or a.get("actionType") == "freethrow":
                    pid = a.get("personId", 0)
                    if pid:
                        player_ids.add(pid)
        except Exception as e:
            print(f"  WARNING: Could not parse PBP for {gid} — {e}")

    return player_ids

# ---------------------------------------------------------------------------
# Step 4: Fetch box scores per game and update game logs
# ---------------------------------------------------------------------------

def _parse_minutes(minutes_str):
    """
    Convert BoxScoreTraditionalV3 minutes string (e.g. "13:45") to an integer
    (minutes truncated, matching the format stored by get_game_log).
    Returns 0 if the value is missing or unparseable.
    """
    if not minutes_str:
        return 0
    try:
        return int(str(minutes_str).split(":")[0])
    except (ValueError, IndexError):
        return 0


def fetch_box_scores_and_update_logs(game_ids, game_date, season):
    """
    For each game ID, call BoxScoreTraditionalV3 (one API call per game) to
    retrieve all players' box score lines.  Appends a new game log entry for
    every player found, then saves the updated league_game_logs cache.

    game_date is a datetime.date object used to format the "date" field as
    "Mar 21, 2026" to match the format produced by get_game_log().

    Returns the updated game_logs dict (str player_id -> list of game dicts).
    """
    try:
        from nba_api.stats.endpoints import boxscoretraditionalv3
    except ImportError:
        sys.exit(
            "ERROR: nba_api is not installed. "
            "Run: pip install nba_api"
        )

    # Format date to match existing cache entries: "Mar 21, 2026"
    game_date_str = game_date.strftime("%b %-d, %Y")

    cache_path = _game_log_cache_path(season)

    # Load existing cache
    game_logs = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            game_logs = json.load(f)

    total_games = len(game_ids)
    appended_entries = 0
    skipped_dupes = 0
    api_errors = 0

    for i, game_id in enumerate(game_ids, 1):
        print(f"  [{i}/{total_games}] BoxScore: {game_id}", end=" ... ", flush=True)
        try:
            bs = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
            data = bs.get_dict()
            bst = data["boxScoreTraditional"]

            home_tricode = bst["homeTeam"]["teamTricode"]
            away_tricode = bst["awayTeam"]["teamTricode"]

            teams = [
                (bst["homeTeam"]["players"], home_tricode, away_tricode, "vs."),
                (bst["awayTeam"]["players"], away_tricode, home_tricode, "@"),
            ]

            new_for_game = 0
            for players, team_tricode, opp_tricode, sep in teams:
                matchup_str = f"{team_tricode} {sep} {opp_tricode}"
                for player in players:
                    pid = player["personId"]
                    pid_str = str(pid)
                    stats = player["statistics"]

                    entry = {
                        "game_id": game_id,
                        "date":    game_date_str,
                        "matchup": matchup_str,
                        "wl":      None,
                        "pts":     stats["points"],
                        "fgm":     stats["fieldGoalsMade"],
                        "fga":     stats["fieldGoalsAttempted"],
                        "fg3m":    stats["threePointersMade"],
                        "fg3a":    stats["threePointersAttempted"],
                        "ftm":     stats["freeThrowsMade"],
                        "fta":     stats["freeThrowsAttempted"],
                        "min":     _parse_minutes(stats.get("minutes")),
                    }

                    if pid_str not in game_logs:
                        game_logs[pid_str] = []

                    # Skip if this game_id is already in the player's log
                    existing_ids = {g["game_id"] for g in game_logs[pid_str]}
                    if game_id in existing_ids:
                        skipped_dupes += 1
                        continue

                    game_logs[pid_str].append(entry)
                    new_for_game += 1
                    appended_entries += 1

            print(f"{new_for_game} player entries")

        except Exception as e:
            print(f"FAILED ({e})")
            api_errors += 1

        if i < total_games:
            time.sleep(2.0)  # polite delay between box score API calls

    # Sort each player's log by game_id (chronological proxy) to keep order
    # consistent with the format produced by get_game_log()
    for pid_str in game_logs:
        game_logs[pid_str].sort(key=lambda g: g["game_id"])

    # Save merged cache atomically
    tmp = cache_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(game_logs, f)
    os.replace(tmp, cache_path)

    notes = []
    if skipped_dupes:
        notes.append(f"{skipped_dupes} duplicate entries skipped")
    if api_errors:
        notes.append(f"{api_errors} API error(s)")
    note_str = f" ({', '.join(notes)})" if notes else ""
    print(f"  Game log cache updated: {appended_entries} new entries across "
          f"{total_games} game(s){note_str}")

    return game_logs

# ---------------------------------------------------------------------------
# Step 5: Reprocess affected players
# ---------------------------------------------------------------------------

def reprocess_players(player_ids_to_update, roster_by_id, game_logs, season):
    """
    Re-run the full season Pure TS% computation for each affected player using
    all of their cached PBP files, then save the updated result file.

    Returns (processed_ok, processed_failed).
    """
    processed_ok = 0
    processed_failed = 0
    total = len(player_ids_to_update)

    for i, pid in enumerate(sorted(player_ids_to_update), 1):
        player = roster_by_id.get(pid)
        if not player:
            print(f"  [{i}/{total}] Player ID {pid} not in roster — skipping")
            processed_failed += 1
            continue

        pid_str = str(pid)
        name = player["player_name"]
        team = player.get("team_abbr") or "-"
        games = game_logs.get(pid_str, [])

        if not games:
            print(f"  [{i}/{total}] {name} ({team}) — 0 games — skipping")
            processed_failed += 1
            continue

        print(f"  [{i}/{total}] {name} ({team}) — {len(games)} games", end=" ... ", flush=True)

        try:
            summary, per_game_rows = process_player_season(player, games, game_logs)
            save_player_result(pid, summary, per_game_rows)

            if summary is None:
                print("0 scoring possessions")
            else:
                fail_note = (f", {summary['games_failed']} game errors"
                             if summary.get("games_failed") else "")
                print(f"Pure TS%: {summary['pure_ts_pct']:.1f}%"
                      f" ({summary['games_played']} gp{fail_note})")
            processed_ok += 1

        except Exception as e:
            print(f"FAILED — {e}")
            processed_failed += 1

    return processed_ok, processed_failed

# ---------------------------------------------------------------------------
# Step 6: Regenerate CSVs
# ---------------------------------------------------------------------------

def regenerate_csvs(players, season, min_games=0, min_poss=0):
    """Call generate_csvs from the league script and print the result."""
    summary_path, summary_count, pergame_path, pergame_count, _ = \
        generate_csvs(players, season, min_games, min_poss)
    print(f"  {summary_path} ({summary_count} rows)")
    print(f"  {pergame_path} ({pergame_count} rows)")
    return summary_path, pergame_path

# ---------------------------------------------------------------------------
# Step 7: Rebuild viewer
# ---------------------------------------------------------------------------

def rebuild_viewer():
    """Run viewer/build_viewer.py as a subprocess."""
    viewer_script = os.path.join(PROJECT_DIR, "viewer", "build_viewer.py")
    if not os.path.exists(viewer_script):
        print(f"  WARNING: viewer script not found at {viewer_script}")
        return False

    print(f"  Running: python3 {viewer_script}")
    result = subprocess.run(
        [sys.executable, viewer_script],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Print any informational lines from the viewer build
        for line in result.stdout.strip().splitlines():
            print(f"    {line}")
        print("  Viewer rebuilt successfully.")
        return True
    else:
        print(f"  WARNING: Viewer build failed (exit code {result.returncode})")
        for line in result.stderr.strip().splitlines()[-10:]:
            print(f"    {line}")
        return False

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Incremental Pure TS%% update for last night's games."
    )
    parser.add_argument(
        "--date",
        help="Date to update (YYYY-MM-DD). Defaults to yesterday.",
    )
    parser.add_argument("--season", default="2025-26",
                        help="NBA season (e.g. 2025-26). Default: 2025-26")
    parser.add_argument(
        "--no-viewer", action="store_true",
        help="Skip rebuilding the HTML viewer.",
    )
    parser.add_argument("--min-games", type=int, default=0,
                        help="Min games for summary CSV inclusion")
    parser.add_argument("--min-possessions", type=int, default=0,
                        help="Min scoring possessions for summary CSV inclusion")
    args = parser.parse_args()

    # Resolve target date
    if args.date:
        try:
            target_date = datetime.date.fromisoformat(args.date)
        except ValueError:
            sys.exit(f"ERROR: Invalid date format '{args.date}'. Use YYYY-MM-DD.")
    else:
        target_date = datetime.date.today() - datetime.timedelta(days=1)

    date_str = target_date.strftime("%Y-%m-%d")
    season = args.season

    start_time = datetime.datetime.now()

    print(f"\n{'=' * 60}")
    print(f"  PURE TS% — DAILY INCREMENTAL UPDATE")
    print(f"  Date:    {date_str}")
    print(f"  Season:  {season}")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    # Load roster
    players = load_player_list(season)
    roster_by_id = {p["player_id"]: p for p in players}
    print(f"Roster: {len(players)} players\n")

    # ---- Step 1: Discover last night's games --------------------------------
    print(f"=== STEP 1: Discover games on {date_str} ===")
    time.sleep(1.0)  # polite delay before first API call
    game_ids = get_games_for_date(date_str)

    if not game_ids:
        print(f"  No games found on {date_str}. Nothing to update.\n")
        print(f"{'=' * 60}\n")
        return

    print(f"  Found {len(game_ids)} game(s):")
    for gid in game_ids:
        print(f"    {gid}")

    # ---- Step 2: Fetch PBP --------------------------------------------------
    print(f"\n=== STEP 2: Fetch PBP ===")
    fetched, errors = fetch_pbp_for_games(game_ids)
    if fetched:
        print(f"  Fetched {fetched} new PBP file(s).")
    if errors:
        print(f"  WARNING: {errors} PBP fetch(es) failed — those games skipped.")

    # Trim game_ids to only those with a cached PBP (fetched or pre-existing)
    available_game_ids = [
        gid for gid in game_ids
        if os.path.exists(os.path.join(PBP_CACHE, f"{gid}.json"))
    ]
    if not available_game_ids:
        print("  No PBP data available. Cannot identify affected players. Exiting.")
        return

    # ---- Step 3: Identify affected players ----------------------------------
    print(f"\n=== STEP 3: Identify affected players ===")
    scoring_player_ids = extract_scoring_player_ids(available_game_ids)

    # Only reprocess players who are in our roster
    roster_player_ids = {
        pid for pid in scoring_player_ids if pid in roster_by_id
    }
    outside_roster = scoring_player_ids - roster_player_ids

    print(f"  Players with scoring events: {len(scoring_player_ids)}")
    print(f"  In our roster:               {len(roster_player_ids)}")
    if outside_roster:
        print(f"  Not in roster (skipped):     {len(outside_roster)}")

    if not roster_player_ids:
        print("  No roster players to reprocess. Exiting.")
        return

    # ---- Step 4: Fetch box scores and update game logs ----------------------
    print(f"\n=== STEP 4: Fetch box scores and update game logs ===")
    game_logs = fetch_box_scores_and_update_logs(available_game_ids, target_date, season)

    # ---- Step 5: Reprocess players ------------------------------------------
    print(f"\n=== STEP 5: Reprocess {len(roster_player_ids)} player(s) ===")
    processed_ok, processed_failed = reprocess_players(
        roster_player_ids, roster_by_id, game_logs, season
    )

    # ---- Step 6: Regenerate CSVs --------------------------------------------
    print(f"\n=== STEP 6: Regenerate CSVs ===")
    regenerate_csvs(players, season, args.min_games, args.min_possessions)

    # ---- Step 7: Rebuild viewer ---------------------------------------------
    if not args.no_viewer:
        print(f"\n=== STEP 7: Rebuild viewer ===")
        rebuild_viewer()
    else:
        viewer_script = os.path.join(PROJECT_DIR, "viewer", "build_viewer.py")
        print(f"\nViewer rebuild skipped. To rebuild manually:")
        print(f"  python3 {viewer_script}")

    # ---- Summary ------------------------------------------------------------
    end_time = datetime.datetime.now()
    runtime = (end_time - start_time).total_seconds()

    print(f"\n{'=' * 60}")
    print(f"  COMPLETE")
    print(f"  Date processed: {date_str}")
    print(f"  Games:          {len(available_game_ids)}")
    print(f"  Players updated: {processed_ok}")
    if processed_failed:
        print(f"  Players failed:  {processed_failed}")
    print(f"  Runtime:         {runtime:.1f}s")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
