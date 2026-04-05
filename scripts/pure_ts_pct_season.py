#!/usr/bin/env python3
"""
Pure TS% — Season Calculator

Calculates Pure True Shooting Percentage for a single player across an
entire NBA season, with per-game breakdowns and season-level aggregates.

Usage:
    python pure_ts_pct_season.py "Luka Doncic"
    python pure_ts_pct_season.py "Luka Doncic" --season 2025-26 --per-game
    python pure_ts_pct_season.py "Shai Gilgeous-Alexander" --save-csv --save-json

Requires: pure_ts_pct_single_game.py in the same directory.
"""

import argparse
import csv
import json
import os
import sys
import time
import unicodedata
import urllib.request
import urllib.error

from pure_ts_pct_single_game import (
    COMPONENTS,
    classify_scoring_events,
    calculate_pure_ts,
    box_score_from_components,
    normalize_name,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pbp_cache")
FETCH_DELAY = 1.5  # seconds between NBA CDN requests

NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nba.com/",
    "Accept": "application/json",
}

# ---------------------------------------------------------------------------
# NBA API helpers
# ---------------------------------------------------------------------------

def _nba_api_request(url):
    """Make a request to stats.nba.com with required headers."""
    req = urllib.request.Request(url, headers=NBA_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def resolve_player_from_api(player_name, season="2025-26"):
    """
    Resolve a player name to (person_id, display_name, team_abbrev)
    using the commonallplayers endpoint.
    """
    url = (
        "https://stats.nba.com/stats/commonallplayers"
        f"?LeagueID=00&Season={season}&IsOnlyCurrentSeason=1"
    )
    data = _nba_api_request(url)
    rows = data["resultSets"][0]["rowSet"]

    target = normalize_name(player_name)
    target_parts = target.split()
    target_last = target_parts[-1]
    target_first_init = target_parts[0][0] if len(target_parts) > 1 else None

    matches = []
    for row in rows:
        # row[2] = "Luka Dončić", row[11] = "LAL"
        display = row[2]
        normalized = normalize_name(display)
        parts = normalized.split()
        last = parts[-1] if parts else ""
        if last == target_last:
            matches.append(row)

    if len(matches) > 1 and target_first_init:
        refined = [
            r for r in matches
            if normalize_name(r[2]).split()[0][0] == target_first_init
        ]
        if refined:
            matches = refined

    if len(matches) == 1:
        r = matches[0]
        return r[0], r[2], r[11]  # person_id, display_name, team_abbrev
    if not matches:
        sys.exit(f"Error: No player found matching '{player_name}' in {season}")
    print(f"Error: Ambiguous name '{player_name}'. Matches:")
    for r in matches:
        print(f"  {r[0]}: {r[2]} ({r[11]})")
    sys.exit(1)


def get_game_log(player_id, season="2025-26"):
    """
    Fetch player's game log for the season.

    Returns a list of dicts sorted oldest-first:
      [{game_id, date, matchup, wl, pts, fga, fg3a, fta, fgm, fg3m, ftm}, ...]
    """
    url = (
        "https://stats.nba.com/stats/playergamelog"
        f"?PlayerID={player_id}&Season={season}&SeasonType=Regular+Season"
    )
    data = _nba_api_request(url)
    rs = data["resultSets"][0]
    headers = rs["headers"]
    rows = rs["rowSet"]

    col = {h: i for i, h in enumerate(headers)}
    games = []
    for row in rows:
        games.append({
            "game_id":  row[col["Game_ID"]],
            "date":     row[col["GAME_DATE"]],
            "matchup":  row[col["MATCHUP"]],
            "wl":       row[col["WL"]],
            "pts":      row[col["PTS"]],
            "fgm":      row[col["FGM"]],
            "fga":      row[col["FGA"]],
            "fg3m":     row[col["FG3M"]],
            "fg3a":     row[col["FG3A"]],
            "ftm":      row[col["FTM"]],
            "fta":      row[col["FTA"]],
            "min":      row[col["MIN"]],
        })

    # API returns most-recent first; reverse to chronological order
    games.reverse()
    return games

# ---------------------------------------------------------------------------
# PBP fetching with cache
# ---------------------------------------------------------------------------

def fetch_pbp_cached(game_id):
    """Fetch PBP JSON, using local cache if available."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{game_id}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f), True  # data, was_cached
    url = (
        f"https://cdn.nba.com/static/json/liveData/playbyplay/"
        f"playbyplay_{game_id}.json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    with open(cache_path, "w") as f:
        json.dump(data, f)
    return data, False  # data, was_cached

# ---------------------------------------------------------------------------
# Per-game processing
# ---------------------------------------------------------------------------

def process_single_game(game_id, player_id):
    """
    Run Phase 1 logic on one game.

    Returns (components, pure_ts, total_poss, details, box) or raises on failure.
    """
    data, _ = fetch_pbp_cached(game_id)
    actions = data["game"]["actions"]

    components = classify_scoring_events(actions, player_id)
    pure_ts, total_poss, details = calculate_pure_ts(components)
    box = box_score_from_components(components)

    return components, pure_ts, total_poss, details, box

# ---------------------------------------------------------------------------
# Season aggregation
# ---------------------------------------------------------------------------

def aggregate_season(all_game_components):
    """
    Sum raw component counts across all games, then compute season Pure TS%.

    Takes a list of per-game component dicts.
    Returns (season_components, pure_ts, total_poss, details, box).
    """
    season = {k: [] for k in COMPONENTS}
    for game_comps in all_game_components:
        for comp_id, events in game_comps.items():
            season[comp_id].extend(events)

    pure_ts, total_poss, details = calculate_pure_ts(season)
    box = box_score_from_components(season)
    return season, pure_ts, total_poss, details, box

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_season_summary(player_name, team, season_str, games_played,
                         games_failed, pure_ts, total_poss, details, box):
    """Print the season-level Pure TS% report."""
    W = 72
    tsa = box["fga"] + 0.44 * box["fta"]
    std_ts = box["pts"] / (2 * tsa) if tsa > 0 else 0.0

    print(f"\n{'=' * W}")
    print(f"  PURE TS% — SEASON REPORT")
    print(f"  Player:  {player_name} ({team})")
    print(f"  Season:  {season_str} Regular Season")
    print(f"  Games:   {games_played} played"
          + (f", {games_failed} failed" if games_failed else ""))
    print(f"{'=' * W}")

    print(f"\n  SEASON TOTALS\n")
    print(f"    {box['pts']} PTS | {box['fg_made']}-{box['fga']} FG | "
          f"{box['fg3_made']}-{box['fg3a']} 3PT | "
          f"{box['ft_made']}-{box['fta']} FT | "
          f"{total_poss} scoring possessions")

    # Component breakdown
    print(f"\n  COMPONENT BREAKDOWN\n")
    hdr = (f"  {'Comp':<6} {'Type':<28} "
           f"{'Ev':>5} {'PTS':>6} {'Max':>6} {'Eff':>8} {'Wt':>7}")
    print(hdr)
    print(f"  {'─' * 6} {'─' * 28} {'─' * 5} {'─' * 6} {'─' * 6} "
          f"{'─' * 8} {'─' * 7}")

    for cid in COMPONENTS:
        if cid not in details:
            continue
        d = details[cid]
        print(f"  {cid:<6} {COMPONENTS[cid]['name']:<28} "
              f"{d['events']:>5} {d['pts']:>6} {d['max_pts']:>6} "
              f"{d['eff']:>8.4f} {d['weight']:>7.4f}")

    print(f"  {'─' * 6} {'─' * 28} {'─' * 5} {'─' * 6} {'─' * 6} "
          f"{'─' * 8} {'─' * 7}")
    total_pts = sum(d["pts"] for d in details.values())
    total_max = sum(d["max_pts"] for d in details.values())
    print(f"  {'TOTAL':<6} {'':28} {total_poss:>5} {total_pts:>6} "
          f"{total_max:>6}")

    # Comparison box
    delta = (pure_ts - std_ts) * 100
    bw = 36
    print()
    print(f"  ┌{'─' * bw}┐")
    print(f"  │  {'Metric':<18} {'Value':>13}   │")
    print(f"  ├{'─' * bw}┤")
    print(f"  │  {'Pure TS%':<18} {pure_ts * 100:>12.1f}%  │")
    print(f"  │  {'Standard TS%':<18} {std_ts * 100:>12.1f}%  │")
    print(f"  ├{'─' * bw}┤")
    print(f"  │  {'Delta':<18} {delta:>+11.1f} pp  │")
    print(f"  └{'─' * bw}┘")
    print(f"\n{'=' * W}\n")


def print_per_game_table(game_results):
    """Print one row per game with Pure TS% vs Standard TS%."""
    W = 96
    print(f"\n{'=' * W}")
    print(f"  PER-GAME BREAKDOWN")
    print(f"{'=' * W}\n")

    hdr = (f"  {'Date':<14} {'Matchup':<16} {'PTS':>4} {'FG':>7} "
           f"{'FT':>6} {'SP':>4} {'Pure':>7} {'Std':>7} {'Delta':>8} ")
    print(hdr)
    print(f"  {'─' * 14} {'─' * 16} {'─' * 4} {'─' * 7} "
          f"{'─' * 6} {'─' * 4} {'─' * 7} {'─' * 7} {'─' * 8} ")

    for g in game_results:
        date = g["date"]
        matchup = g["matchup"]
        pts = g["pts"]
        fg_str = f"{g['fgm']}-{g['fga']}"
        ft_str = f"{g['ftm']}-{g['fta']}"
        sp = g["scoring_poss"]

        if g["pure_ts"] is None:
            pure_str = "  N/A"
            std_str = "  N/A"
            delta_str = "     N/A"
            marker = ""
        else:
            pure_str = f"{g['pure_ts'] * 100:>6.1f}%"
            std_str = f"{g['std_ts'] * 100:>6.1f}%"
            delta_val = (g["pure_ts"] - g["std_ts"]) * 100
            delta_str = f"{delta_val:>+7.1f}pp"
            marker = " ***" if abs(delta_val) >= 10.0 else ""

        print(f"  {date:<14} {matchup:<16} {pts:>4} {fg_str:>7} "
              f"{ft_str:>6} {sp:>4} {pure_str} {std_str} {delta_str}{marker}")

    # Count distortion games
    distortion = sum(
        1 for g in game_results
        if g["pure_ts"] is not None
        and abs((g["pure_ts"] - g["std_ts"]) * 100) >= 10.0
    )
    if distortion:
        print(f"\n  *** {distortion} game(s) with |delta| >= 10 pp")

    print(f"\n{'=' * W}\n")


def save_csv_output(game_results, player_name, season_str):
    """Export per-game results to CSV."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    safe_name = normalize_name(player_name.replace(" ", "_").lower())
    filename = os.path.join(data_dir, f"{safe_name}_pure_ts_{season_str}.csv")

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "game_id", "matchup", "wl", "pts", "fgm", "fga",
            "fg3m", "fg3a", "ftm", "fta", "scoring_poss",
            "pure_ts_pct", "standard_ts_pct", "delta_pp",
        ])
        for g in game_results:
            if g["pure_ts"] is not None:
                delta = (g["pure_ts"] - g["std_ts"]) * 100
                writer.writerow([
                    g["date"], g["game_id"], g["matchup"], g["wl"],
                    g["pts"], g["fgm"], g["fga"],
                    g["fg3m"], g["fg3a"], g["ftm"], g["fta"],
                    g["scoring_poss"],
                    round(g["pure_ts"] * 100, 2),
                    round(g["std_ts"] * 100, 2),
                    round(delta, 2),
                ])
            else:
                writer.writerow([
                    g["date"], g["game_id"], g["matchup"], g["wl"],
                    g["pts"], g["fgm"], g["fga"],
                    g["fg3m"], g["fg3a"], g["ftm"], g["fta"],
                    0, "", "", "",
                ])

    print(f"  CSV saved: {filename}")
    return filename


def save_json_output(game_results, all_game_components, player_name,
                     season_str):
    """Export full component-level data to JSON."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    safe_name = normalize_name(player_name.replace(" ", "_").lower())
    filename = os.path.join(data_dir, f"{safe_name}_pure_ts_{season_str}.json")

    output = {
        "player": player_name,
        "season": season_str,
        "games": [],
    }

    for g, comps in zip(game_results, all_game_components):
        game_data = {
            "game_id": g["game_id"],
            "date": g["date"],
            "matchup": g["matchup"],
            "wl": g["wl"],
            "box": {
                "pts": g["pts"], "fgm": g["fgm"], "fga": g["fga"],
                "fg3m": g["fg3m"], "fg3a": g["fg3a"],
                "ftm": g["ftm"], "fta": g["fta"],
            },
            "scoring_possessions": g["scoring_poss"],
            "pure_ts_pct": round(g["pure_ts"] * 100, 2) if g["pure_ts"] else None,
            "standard_ts_pct": round(g["std_ts"] * 100, 2) if g["std_ts"] else None,
            "components": {},
        }
        if comps:
            for comp_id, events in comps.items():
                if events:
                    game_data["components"][comp_id] = {
                        "name": COMPONENTS[comp_id]["name"],
                        "max_per_event": COMPONENTS[comp_id]["max"],
                        "events": len(events),
                        "pts": sum(e["pts"] for e in events),
                        "max_pts": len(events) * COMPONENTS[comp_id]["max"],
                    }
        output["games"].append(game_data)

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  JSON saved: {filename}")
    return filename

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Calculate Pure TS%% for a player across an NBA season."
    )
    parser.add_argument("player_name", help='Player name (e.g. "Luka Doncic")')
    parser.add_argument(
        "--season", default="2025-26",
        help="NBA season (e.g. 2025-26). Default: 2025-26",
    )
    parser.add_argument(
        "--per-game", action="store_true",
        help="Show per-game breakdown table",
    )
    parser.add_argument(
        "--save-csv", action="store_true",
        help="Export per-game results to CSV",
    )
    parser.add_argument(
        "--save-json", action="store_true",
        help="Export full component data to JSON",
    )
    args = parser.parse_args()

    # -- Step 1: Resolve player ---------------------------------------------
    print(f"Resolving '{args.player_name}' for {args.season}...")
    player_id, display_name, team = resolve_player_from_api(
        args.player_name, args.season
    )
    print(f"  {display_name} ({team}) — ID {player_id}")

    # -- Step 2: Get game log -----------------------------------------------
    print(f"Fetching game log...")
    games = get_game_log(player_id, args.season)
    print(f"  {len(games)} games found.")

    # -- Step 3: Process each game ------------------------------------------
    game_results = []
    all_game_components = []
    games_succeeded = 0
    games_failed = 0
    games_no_poss = 0
    failed_ids = []

    print(f"\nProcessing games...\n")
    for i, game in enumerate(games):
        gid = game["game_id"]
        label = f"  [{i + 1}/{len(games)}] {game['date']} {game['matchup']}"

        try:
            comps, pure_ts, total_poss, details, box = process_single_game(
                gid, player_id
            )

            # Reconciliation check
            recon_ok = (
                box["pts"] == game["pts"]
                and box["fga"] == game["fga"]
                and box["fta"] == game["fta"]
            )
            if not recon_ok:
                print(f"{label}  RECON MISMATCH "
                      f"(pbp: {box['pts']}p/{box['fga']}fga/{box['fta']}fta "
                      f"vs log: {game['pts']}p/{game['fga']}fga/{game['fta']}fta)")
                games_failed += 1
                failed_ids.append((gid, "reconciliation mismatch"))
                game_results.append({
                    **game, "scoring_poss": total_poss,
                    "pure_ts": None, "std_ts": None,
                })
                all_game_components.append(None)
                if not _was_cached(gid):
                    time.sleep(FETCH_DELAY)
                continue

            if total_poss == 0:
                # Player appeared but had no scoring possessions
                print(f"{label}  N/A (0 scoring possessions)")
                games_no_poss += 1
                game_results.append({
                    **game, "scoring_poss": 0,
                    "pure_ts": None, "std_ts": None,
                })
                all_game_components.append(None)
                if not _was_cached(gid):
                    time.sleep(FETCH_DELAY)
                continue

            tsa = box["fga"] + 0.44 * box["fta"]
            std_ts = box["pts"] / (2 * tsa) if tsa > 0 else 0.0

            delta = (pure_ts - std_ts) * 100
            flag = " ***" if abs(delta) >= 10.0 else ""
            print(f"{label}  {box['pts']:>3}pts  "
                  f"Pure={pure_ts * 100:5.1f}%  Std={std_ts * 100:5.1f}%  "
                  f"Δ={delta:+5.1f}pp{flag}")

            games_succeeded += 1
            game_results.append({
                **game, "scoring_poss": total_poss,
                "pure_ts": pure_ts, "std_ts": std_ts,
            })
            all_game_components.append(comps)

        except Exception as e:
            print(f"{label}  ERROR: {e}")
            games_failed += 1
            failed_ids.append((gid, str(e)))
            game_results.append({
                **game, "scoring_poss": 0,
                "pure_ts": None, "std_ts": None,
            })
            all_game_components.append(None)

        if not _was_cached(gid):
            time.sleep(FETCH_DELAY)

    # -- Step 4: Aggregate season -------------------------------------------
    valid_components = [c for c in all_game_components if c is not None]

    if not valid_components:
        sys.exit("\nError: No games processed successfully.")

    _, season_pure_ts, season_poss, season_details, season_box = (
        aggregate_season(valid_components)
    )

    # -- Step 5: Output -----------------------------------------------------
    print_season_summary(
        display_name, team, args.season, games_succeeded,
        games_failed, season_pure_ts, season_poss, season_details, season_box,
    )

    if args.per_game:
        print_per_game_table(game_results)

    if args.save_csv:
        save_csv_output(game_results, display_name, args.season)

    if args.save_json:
        save_json_output(
            game_results, all_game_components, display_name, args.season,
        )

    if failed_ids:
        print(f"  Failed games ({len(failed_ids)}):")
        for gid, reason in failed_ids:
            print(f"    {gid}: {reason}")
        print()


def _was_cached(game_id):
    """Check if a game's PBP is in the cache (to skip delay)."""
    return os.path.exists(os.path.join(CACHE_DIR, f"{game_id}.json"))


if __name__ == "__main__":
    main()
