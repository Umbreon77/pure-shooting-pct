#!/usr/bin/env python3
"""
BBRef Batch Season Runner — Generate per-season league CSVs from BBRef PBP cache.

Processes all 24 BBRef seasons (1996-97 through 2019-20) and outputs CSV files
matching the format of existing pure_ts_pct_league_YYYY-YY.csv files, with
full component columns (C1a–C6f).

Usage:
    python3 scripts/bbref_batch_seasons.py
    python3 scripts/bbref_batch_seasons.py --season 1997-98
"""

import csv
import json
import os
import re
import sys
import time
import warnings
from collections import defaultdict

import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
from bbref_pbp_parser import classify_bbref_game, classify_all_players, COMPONENTS, normalize_name
from pure_ts_pct_single_game import calculate_pure_ts, box_score_from_components

# ---------------------------------------------------------------------------
# Season / game-ID mapping
# ---------------------------------------------------------------------------

# BBRef names seasons by end year. Map display season to file patterns.
SEASONS = [
    ("1996-97", "NBA_1997"),
    ("1997-98", "NBA_1998"),
    ("1998-99", "NBA_1999"),
    ("1999-00", "NBA_2000"),
    ("2000-01", "NBA_2001"),
    ("2001-02", "NBA_2002"),
    ("2002-03", "NBA_2003"),
    ("2003-04", "NBA_2004"),
    ("2004-05", "NBA_2005"),
    ("2005-06", "NBA_2006"),
    ("2006-07", "NBA_2007"),
    ("2007-08", "NBA_2008"),
    ("2008-09", "NBA_2009"),
    ("2009-10", "NBA_2010"),
    ("2010-11", "NBA_2011"),
    ("2011-12", "NBA_2012"),
    ("2012-13", "NBA_2013"),
    ("2013-14", "NBA_2014"),
    ("2014-15", "NBA_2015"),
    ("2015-16", "NBA_2016"),
    ("2016-17", "NBA_2017"),
    ("2017-18", "NBA_2018"),
    ("2018-19", "NBA_2019"),
    ("2019-20", "NBA_2020"),
    ("2020-21", "NBA_2021"),
    ("2021-22", "NBA_2022"),
    ("2022-23", "NBA_2023"),
    ("2023-24", "NBA_2024"),
    ("2024-25", "NBA_2025"),
]

# Team name → abbreviation mapping
TEAM_ABBR = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "L.A. Clippers": "LAC", "LA Clippers": "LAC", "Los Angeles Clippers": "LAC",
    "L.A. Lakers": "LAL", "LA Lakers": "LAL", "Los Angeles Lakers": "LAL",
    "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN",
    "New Jersey": "NJN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI",
    "Phoenix": "PHX", "Portland": "POR", "Sacramento": "SAC",
    "San Antonio": "SAS", "Seattle": "SEA", "Toronto": "TOR", "Utah": "UTA",
    "Vancouver": "VAN", "Washington": "WAS",
    # Alternate names
    "New Orleans/Oklahoma City": "NOK", "New Orleans Hornets": "NOH",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backup_csvs")
GAME_IDS_DIR = os.path.join(DATA_DIR, "bbref_game_ids")
CACHE_DIR = os.path.join(DATA_DIR, "bbref_pbp_cache")


def _last_first(name):
    """Extract (last_name, first_initial) from a player name, stripping
    diacritics and suffixes."""
    norm = normalize_name(name)
    parts = norm.replace(".", " ").split()
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    while parts and parts[-1] in suffixes:
        parts = parts[:-1]
    last = parts[-1] if parts else ""
    first_i = parts[0][0] if len(parts) > 1 else ""
    return last, first_i


def build_nba_api_lookup(season_label):
    """Build a lookup from BBRef names to full NBA API names and numeric
    player IDs using the backup CSV or main data CSV for this season."""
    backup_path = os.path.join(BACKUP_DIR, f"pure_ts_pct_league_{season_label}.csv")
    if not os.path.exists(backup_path):
        # Fall back to main data CSV (for CDN-era seasons with numeric IDs)
        backup_path = os.path.join(DATA_DIR, f"pure_ts_pct_league_{season_label}.csv")
    if not os.path.exists(backup_path):
        return {}

    by_team = {}   # (last, first_i, team) -> {name, player_id}
    by_name = {}   # (last, first_i) -> [{name, player_id}, ...]
    with open(backup_path, newline="") as f:
        for row in csv.DictReader(f):
            full = row["player_name"]
            pid = row["player_id"]
            last, fi = _last_first(full)
            entry = {"name": full, "player_id": pid}
            by_team[(last, fi, row["team_abbr"])] = entry
            by_name.setdefault((last, fi), []).append(entry)

    return {"by_team": by_team, "by_name": by_name}


def resolve_nba_api(abbrev_name, team_abbr, lookup):
    """Resolve a BBRef abbreviated name to full NBA API name and numeric ID.

    Returns (full_name, nba_player_id). Falls back to (abbrev_name, None)."""
    if not lookup:
        return abbrev_name, None
    last, fi = _last_first(abbrev_name)
    entry = lookup["by_team"].get((last, fi, team_abbr))
    if not entry:
        candidates = lookup["by_name"].get((last, fi), [])
        entry = candidates[0] if candidates else None
    if entry:
        return entry["name"], entry["player_id"]
    return abbrev_name, None


def load_game_ids(bbref_prefix, playoffs=False):
    """Load game IDs from regular season or playoff URL files."""
    game_ids = []
    for suffix in (("playoffs",) if playoffs else ("regular_season",)):
        path = os.path.join(GAME_IDS_DIR, f"{bbref_prefix}_{suffix}_pbp_urls.txt")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m = re.search(r'/pbp/(\d+[A-Z]+)\.html', line)
                if m:
                    game_ids.append(m.group(1))
    return game_ids


def get_player_team(events, player_id):
    """Determine primary team for a player from their events."""
    team_counts = defaultdict(int)
    for e in events:
        if e.get("player_id") == player_id and e.get("team"):
            team_counts[e["team"]] += 1
    if not team_counts:
        return ""
    return max(team_counts, key=team_counts.get)


def process_season(season_label, bbref_prefix, playoffs=False):
    """Process all games in a season. Returns (per-player stats, season summary)."""
    game_ids = load_game_ids(bbref_prefix, playoffs=playoffs)
    if not game_ids:
        return None, {"error": f"No game IDs found for {bbref_prefix}"}

    # Build lookup from NBA API backup CSV (full names + numeric IDs)
    api_lookup = build_nba_api_lookup(season_label)

    # Per-player accumulators
    players = {}  # player_id → {name, team, games, comps_list}

    total_games = 0
    failed = 0
    warned = 0
    warn_count = 0

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
                    warn_count += len(w)

            total_games += 1

            events = game["events"]
            for pname, comps in results.items():
                # Find player_id
                pid = None
                for e in events:
                    if e.get("player") == pname and e.get("player_id"):
                        pid = e["player_id"]
                        break
                if not pid:
                    continue

                # Extract slug from BBRef path
                slug = pid.split("/")[-1].replace(".html", "")

                if slug not in players:
                    team_name = get_player_team(events, pid)
                    team_abbr = TEAM_ABBR.get(team_name, team_name[:3].upper())
                    players[slug] = {
                        "name": pname,
                        "team": team_abbr,
                        "games": 0,
                        "all_comps": {k: [] for k in COMPONENTS},
                    }

                p = players[slug]
                p["games"] += 1
                for cid, evts in comps.items():
                    p["all_comps"][cid].extend(evts)

        except Exception as e:
            failed += 1

    # Compute season stats per player
    rows = []
    league_pts = league_fga = league_fg3a = league_fta = 0

    for slug, p in players.items():
        comps = p["all_comps"]
        pure_ts, total_poss, details = calculate_pure_ts(comps)
        box = box_score_from_components(comps)

        if box["pts"] == 0 and box["fga"] == 0:
            continue

        max_pts = 2 * box["fga"] + box["fg3a"] + box["fta"]
        ps_pct = (box["pts"] / max_pts * 100) if max_pts > 0 else 0
        ts_denom = 2 * (box["fga"] + 0.44 * box["fta"])
        ts_pct = (box["pts"] / ts_denom * 100) if ts_denom > 0 else 0
        delta = ps_pct - ts_pct

        league_pts += box["pts"]
        league_fga += box["fga"]
        league_fg3a += box["fg3a"]
        league_fta += box["fta"]

        full_name, nba_pid = resolve_nba_api(p["name"], p["team"], api_lookup)
        row = {
            "player_id": nba_pid or slug,
            "player_name": full_name,
            "team_abbr": p["team"],
            "games_played": p["games"],
            "total_pts": box["pts"],
            "total_fga": box["fga"],
            "total_fga2": box["fga"] - box["fg3a"],
            "total_fga3": box["fg3a"],
            "total_fta": box["fta"],
            "total_scoring_poss": total_poss,
            "pure_ts_pct": round(ps_pct, 2),
            "standard_ts_pct": round(ts_pct, 2),
            "delta_pp": round(delta, 2),
        }

        # FGM / FG3M / FTM from box_score_from_components
        row["total_fgm"] = box["fg_made"]
        row["total_fg3m"] = box["fg3_made"]
        row["total_ftm"] = box["ft_made"]

        # Component columns
        for cid in COMPONENTS:
            d = details.get(cid, {})
            row[f"{cid}_events"] = d.get("events", 0)
            row[f"{cid}_pts"] = d.get("pts", 0)
            eff = d.get("eff")
            row[f"{cid}_eff"] = round(eff * 100, 2) if eff is not None else ""

        rows.append(row)

    # Sort by total_pts descending
    rows.sort(key=lambda r: -r["total_pts"])

    # League summary
    league_max = 2 * league_fga + league_fg3a + league_fta
    league_ps = (league_pts / league_max * 100) if league_max > 0 else 0
    league_ts_denom = 2 * (league_fga + 0.44 * league_fta)
    league_ts = (league_pts / league_ts_denom * 100) if league_ts_denom > 0 else 0
    tpa_rate = (league_fg3a / league_fga * 100) if league_fga > 0 else 0

    summary = {
        "season": season_label,
        "games": total_games,
        "failed": failed,
        "warned": warned,
        "warnings": warn_count,
        "players": len(rows),
        "league_ps": round(league_ps, 1),
        "league_ts": round(league_ts, 1),
        "delta": round(league_ps - league_ts, 1),
        "tpa_rate": round(tpa_rate, 1),
    }

    return rows, summary


def write_csv(rows, season_label, output_dir):
    """Write season CSV in the same format as existing league CSVs."""
    # Build column list
    base_cols = [
        "player_id", "player_name", "team_abbr", "games_played",
        "total_pts", "total_fga", "total_fga2", "total_fga3", "total_fta",
        "total_scoring_poss", "pure_ts_pct", "standard_ts_pct", "delta_pp",
    ]
    comp_cols = []
    for cid in COMPONENTS:
        comp_cols.extend([f"{cid}_events", f"{cid}_pts", f"{cid}_eff"])

    all_cols = base_cols + comp_cols + ["total_fgm", "total_fg3m", "total_ftm"]

    path = os.path.join(output_dir, f"pure_ts_pct_league_{season_label}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols, extrasaction="ignore")
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
    os.makedirs(output_dir, exist_ok=True)

    seasons_to_run = SEASONS
    if args.season:
        seasons_to_run = [(s, p) for s, p in SEASONS if s == args.season]
        if not seasons_to_run:
            print(f"Unknown season: {args.season}")
            sys.exit(1)

    suffix = "-PO" if args.playoffs else ""
    mode_label = "PLAYOFFS" if args.playoffs else "REGULAR SEASON"

    t0 = time.time()
    summaries = []

    for season_label, bbref_prefix in seasons_to_run:
        st = time.time()
        csv_label = season_label + suffix
        print(f"\n{'='*60}")
        print(f"Processing {csv_label} ({bbref_prefix} {mode_label})...")

        rows, summary = process_season(season_label, bbref_prefix,
                                       playoffs=args.playoffs)

        if rows is None:
            print(f"  SKIPPED: {summary.get('error', 'unknown')}")
            summaries.append(summary)
            continue

        # Write CSV
        path = write_csv(rows, csv_label, output_dir)
        elapsed = time.time() - st

        print(f"  Games: {summary['games']}  Failed: {summary['failed']}  "
              f"Warned: {summary['warned']} ({summary['warnings']} warnings)")
        print(f"  Players: {summary['players']}  "
              f"PS%: {summary['league_ps']}  TS%: {summary['league_ts']}  "
              f"Delta: {summary['delta']}pp  3PA%: {summary['tpa_rate']}%")
        print(f"  Wrote: {os.path.basename(path)}  ({elapsed:.1f}s)")

        summary["elapsed"] = round(elapsed, 1)
        summaries.append(summary)

    total_elapsed = time.time() - t0

    # Final report
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE — {len(summaries)} seasons in {total_elapsed:.0f}s")
    print(f"{'='*60}")
    print(f"{'Season':<10} {'Games':>6} {'Fail':>5} {'Warn%':>6} "
          f"{'PS%':>6} {'TS%':>6} {'Delta':>7} {'3PA%':>6} {'Time':>6}")
    print("-" * 65)
    for s in summaries:
        if "error" in s:
            print(f"{s['season']:<10} SKIPPED: {s['error']}")
            continue
        warn_pct = (s["warnings"] / max(s["games"], 1) * 100)
        print(f"{s['season']:<10} {s['games']:>6} {s['failed']:>5} "
              f"{warn_pct:>5.1f}% {s['league_ps']:>5.1f} {s['league_ts']:>5.1f} "
              f"{s['delta']:>+6.1f}pp {s['tpa_rate']:>5.1f} {s['elapsed']:>5.1f}s")

    # Flag anomalies
    anomalies = []
    for s in summaries:
        if "error" in s:
            continue
        if s["failed"] > 0 and s["failed"] / (s["games"] + s["failed"]) > 0.01:
            anomalies.append(f"{s['season']}: {s['failed']} failed games ({s['failed']/(s['games']+s['failed'])*100:.1f}%)")
        if s["games"] > 0 and s["warnings"] / s["games"] > 0.01:
            pass  # warning rate per game, not per player-game
        if not (47.0 <= s["league_ps"] <= 51.0):
            anomalies.append(f"{s['season']}: league PS% = {s['league_ps']}% (outside 47-51 range)")

    if anomalies:
        print(f"\n=== ANOMALIES ===")
        for a in anomalies:
            print(f"  {a}")
    else:
        print(f"\nNo anomalies detected.")


if __name__ == "__main__":
    main()
