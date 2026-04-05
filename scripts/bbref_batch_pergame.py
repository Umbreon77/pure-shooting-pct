#!/usr/bin/env python3
"""
BBRef Batch Per-Game Runner — Generate per-season pergame CSVs from BBRef PBP cache.

Outputs CSV files matching the format of existing
pure_ts_pct_league_pergame_YYYY-YY.csv files from the CDN pipeline.

Usage:
    python3 scripts/bbref_batch_pergame.py
    python3 scripts/bbref_batch_pergame.py --season 1997-98
"""

import csv
import json
import os
import re
import sys
import time
import warnings
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from bbref_pbp_parser import classify_all_players, COMPONENTS
from pure_ts_pct_single_game import calculate_pure_ts, box_score_from_components
from bbref_batch_seasons import (
    SEASONS, TEAM_ABBR, DATA_DIR, GAME_IDS_DIR, CACHE_DIR,
    load_game_ids, build_nba_api_lookup, resolve_nba_api,
)

COMP_IDS = list(COMPONENTS.keys())

PERGAME_COLUMNS = [
    "player_id", "player_name", "team_abbr", "game_id", "game_date",
    "opponent", "pts", "fga", "fta", "scoring_poss",
    "pure_ts_pct", "standard_ts_pct", "delta_pp",
] + [f"{cid}_{f}" for cid in COMP_IDS for f in ("events", "pts")]


def _format_date(yyyymmdd):
    """Convert '19971031' to 'Oct 31, 1997'."""
    try:
        dt = datetime.strptime(yyyymmdd, "%Y%m%d")
        return dt.strftime("%b %d, %Y").replace(" 0", " ")
    except ValueError:
        return yyyymmdd


def _get_opponent(game, player_team_name):
    """Determine opponent team name from game metadata."""
    away = game["teams"]["away"]
    home = game["teams"]["home"]
    if player_team_name == home:
        return TEAM_ABBR.get(away, away[:3].upper())
    return TEAM_ABBR.get(home, home[:3].upper())


def process_season_pergame(season_label, bbref_prefix, playoffs=False):
    """Process all games in a season, emitting per-player per-game rows."""
    game_ids = load_game_ids(bbref_prefix, playoffs=playoffs)
    if not game_ids:
        return None, {"season": season_label, "error": f"No game IDs found for {bbref_prefix}"}

    api_lookup = build_nba_api_lookup(season_label)

    rows = []
    total_games = 0
    failed = 0
    warned = 0

    for gid in game_ids:
        gf = os.path.join(CACHE_DIR, f"{gid}.json")
        if not os.path.exists(gf):
            failed += 1
            continue

        try:
            with open(gf) as f:
                game = json.load(f)

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                results = classify_all_players(game)
                if w:
                    warned += 1

            total_games += 1
            events = game["events"]
            date_str = gid[:8]
            game_date = _format_date(date_str)

            for pname, comps in results.items():
                # Find player_id and team
                pid = None
                team_name = None
                for e in events:
                    if e.get("player") == pname and e.get("player_id"):
                        pid = e["player_id"]
                        team_name = e.get("team")
                        break
                if not pid:
                    continue

                team_abbr = TEAM_ABBR.get(team_name, (team_name or "")[:3].upper())
                opponent = _get_opponent(game, team_name)

                # Resolve name and NBA ID
                full_name, nba_pid = resolve_nba_api(pname, team_abbr, api_lookup)

                pure_ts, total_poss, details = calculate_pure_ts(comps)
                box = box_score_from_components(comps)

                if box["pts"] == 0 and box["fga"] == 0 and box["fta"] == 0:
                    continue

                max_pts = 2 * box["fga"] + box["fg3a"] + box["fta"]
                ps_pct = round(box["pts"] / max_pts * 100, 2) if max_pts > 0 else ""
                ts_denom = 2 * (box["fga"] + 0.44 * box["fta"])
                ts_pct = round(box["pts"] / ts_denom * 100, 2) if ts_denom > 0 else ""
                delta = round(ps_pct - ts_pct, 2) if ps_pct != "" and ts_pct != "" else ""

                row = {
                    "player_id": nba_pid or pid.split("/")[-1].replace(".html", ""),
                    "player_name": full_name,
                    "team_abbr": team_abbr,
                    "game_id": gid,
                    "game_date": game_date,
                    "opponent": opponent,
                    "pts": box["pts"],
                    "fga": box["fga"],
                    "fta": box["fta"],
                    "scoring_poss": total_poss,
                    "pure_ts_pct": ps_pct,
                    "standard_ts_pct": ts_pct,
                    "delta_pp": delta,
                }

                for cid in COMP_IDS:
                    d = details.get(cid, {})
                    row[f"{cid}_events"] = d.get("events", 0)
                    row[f"{cid}_pts"] = d.get("pts", 0)

                rows.append(row)

        except Exception as e:
            failed += 1

    summary = {
        "season": season_label,
        "games": total_games,
        "failed": failed,
        "warned": warned,
        "rows": len(rows),
    }
    return rows, summary


def write_pergame_csv(rows, season_label, output_dir):
    """Write pergame CSV."""
    path = os.path.join(output_dir, f"pure_ts_pct_league_pergame_{season_label}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PERGAME_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", help="Process single season (e.g., 1997-98)")
    parser.add_argument("--playoffs", action="store_true",
                        help="Process playoff games instead of regular season")
    args = parser.parse_args()

    output_dir = DATA_DIR
    suffix = "-PO" if args.playoffs else ""

    seasons_to_run = SEASONS
    if args.season:
        seasons_to_run = [(s, p) for s, p in SEASONS if s == args.season]
        if not seasons_to_run:
            print(f"Unknown season: {args.season}")
            sys.exit(1)

    t0 = time.time()
    summaries = []

    for season_label, bbref_prefix in seasons_to_run:
        st = time.time()
        csv_label = season_label + suffix
        print(f"Processing {csv_label}...", end=" ", flush=True)

        rows, summary = process_season_pergame(season_label, bbref_prefix,
                                               playoffs=args.playoffs)

        if rows is None:
            print(f"SKIPPED: {summary.get('error')}")
            summaries.append(summary)
            continue

        path = write_pergame_csv(rows, csv_label, output_dir)
        elapsed = time.time() - st

        print(f"{summary['games']} games, {summary['rows']} rows, "
              f"{summary['failed']} failed ({elapsed:.1f}s)")

        summary["elapsed"] = round(elapsed, 1)
        summaries.append(summary)

    total_elapsed = time.time() - t0
    total_rows = sum(s.get("rows", 0) for s in summaries)
    total_games = sum(s.get("games", 0) for s in summaries)

    print(f"\nBATCH COMPLETE — {len(summaries)} seasons, {total_games} games, "
          f"{total_rows:,} rows in {total_elapsed:.0f}s")
    print(f"{'Season':<10} {'Games':>6} {'Rows':>8} {'Fail':>5} {'Time':>6}")
    print("-" * 40)
    for s in summaries:
        if "error" in s:
            print(f"{s['season']:<10} SKIPPED")
            continue
        print(f"{s['season']:<10} {s['games']:>6} {s['rows']:>8} "
              f"{s['failed']:>5} {s['elapsed']:>5.1f}s")


if __name__ == "__main__":
    main()
