#!/usr/bin/env python3
"""
Pure TS% — Historical Multi-Season Pipeline

Runs the Pure TS% league pipeline across multiple historical NBA seasons.
Uses the same core logic as pure_ts_pct_league.py but parameterized for
any season where CDN PBP data is available (2019-20 through 2024-25).

Usage:
    python scripts/pure_ts_pct_historical.py
    python scripts/pure_ts_pct_historical.py --seasons 2024-25 2023-24
    python scripts/pure_ts_pct_historical.py --dry-run 5

Resumable: uses pbp_cache/ and per-season league_results/{season}/ dirs.
Restarting picks up where it left off.
"""

import argparse
import csv
import datetime
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
PBP_CACHE = os.path.join(DATA_DIR, "pbp_cache")

# Import core classification and computation logic
from pure_ts_pct_single_game import (
    COMPONENTS,
    classify_scoring_events,
    calculate_pure_ts,
    box_score_from_components,
)

from pure_ts_pct_season import (
    NBA_HEADERS,
    fetch_pbp_cached,
)

COMP_IDS = list(COMPONENTS.keys())

ALL_SEASONS = [
    "2024-25", "2023-24", "2022-23", "2021-22", "2020-21", "2019-20",
]

# ---------------------------------------------------------------------------
# Roster fetching (works for historical seasons)
# ---------------------------------------------------------------------------

def fetch_roster(season):
    """
    Fetch all players who played in a given season.

    Uses nba_api's commonallplayers with IsOnlyCurrentSeason=0,
    then filters by TO_YEAR to get players active in that season.
    Returns list of dicts: [{player_id, player_name, team_abbr, team_name}]
    """
    from nba_api.stats.endpoints import commonallplayers

    resp = commonallplayers.CommonAllPlayers(
        league_id='00', season=season, is_only_current_season=0, timeout=120,
    )
    data = resp.get_dict()
    rs = data['resultSets'][0]
    headers = rs['headers']
    col = {h: i for i, h in enumerate(headers)}

    # The end year of the season (e.g., "2024-25" -> 2025)
    end_year = int(season.split("-")[0]) + 1

    players = []
    for row in rs['rowSet']:
        to_year = int(row[col['TO_YEAR']]) if row[col['TO_YEAR']] else 0
        if to_year < end_year:
            continue
        if row[col['GAMES_PLAYED_FLAG']] != 'Y':
            continue

        team_city = row[col['TEAM_CITY']] or ""
        team_name = row[col['TEAM_NAME']] or ""

        players.append({
            "player_id": row[col['PERSON_ID']],
            "player_name": row[col['DISPLAY_FIRST_LAST']],
            "team_abbr": row[col['TEAM_ABBREVIATION']] or "",
            "team_name": f"{team_city} {team_name}".strip(),
        })

    return players


def save_roster(players, season):
    """Save roster JSON for a season (so it can be reused on resume)."""
    path = os.path.join(DATA_DIR, f"nba_active_players_{season}.json")
    with open(path, "w") as f:
        json.dump(players, f, ensure_ascii=False)
    return path


def load_roster(season):
    """Load cached roster JSON if it exists."""
    path = os.path.join(DATA_DIR, f"nba_active_players_{season}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


# ---------------------------------------------------------------------------
# Game log fetching via nba_api
# ---------------------------------------------------------------------------

def fetch_game_log(player_id, season):
    """Fetch a player's game log for a season. Returns list of game dicts."""
    from nba_api.stats.endpoints import playergamelog

    resp = playergamelog.PlayerGameLog(
        player_id=str(player_id),
        season=season,
        season_type_all_star='Regular Season',
        timeout=120,
    )
    data = resp.get_dict()
    rs = data['resultSets'][0]
    headers = rs['headers']
    col = {h: i for i, h in enumerate(headers)}
    rows = rs['rowSet']

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

    games.reverse()  # chronological order
    return games


def fetch_all_game_logs(players, season):
    """
    Fetch game logs for all players, using a cache file.
    Returns dict: str(player_id) -> list of game dicts.
    """
    cache_path = os.path.join(DATA_DIR, f"league_game_logs_{season}.json")

    cached = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cached = json.load(f)

    missing = [p for p in players if str(p["player_id"]) not in cached]

    if not missing:
        print(f"    Game logs loaded from cache ({len(cached)} players)")
        return cached

    if cached:
        print(f"    Game logs: {len(cached)} cached, {len(missing)} to fetch")
    else:
        print(f"    Fetching game logs for {len(missing)} players...")

    for i, p in enumerate(missing):
        pid = str(p["player_id"])
        try:
            games = fetch_game_log(int(pid), season)
            cached[pid] = games
        except Exception as e:
            cached[pid] = []

        if (i + 1) % 20 == 0 or i == len(missing) - 1:
            print(f"\r    Game logs: {i + 1}/{len(missing)} fetched", end="",
                  flush=True)
        time.sleep(1.0)

    print()

    with open(cache_path, "w") as f:
        json.dump(cached, f)
    print(f"    Game log cache saved ({len(cached)} players)")
    return cached


# ---------------------------------------------------------------------------
# PBP fetching with retry
# ---------------------------------------------------------------------------

def fetch_pbp_with_retry(game_id, max_retries=3, retry_delay=30):
    """
    Fetch PBP for a game with retry logic.
    Returns True on success, False on permanent failure.
    """
    cache_path = os.path.join(PBP_CACHE, f"{game_id}.json")
    if os.path.exists(cache_path):
        return True

    for attempt in range(max_retries):
        try:
            fetch_pbp_cached(game_id)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False  # game doesn't exist, don't retry
            if attempt < max_retries - 1:
                print(f"\n    Retry {attempt+1}/{max_retries} for {game_id} "
                      f"(HTTP {e.code}), waiting {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                return False
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"\n    Retry {attempt+1}/{max_retries} for {game_id} "
                      f"({e}), waiting {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                return False
    return False


def fetch_missing_pbp(game_ids):
    """Fetch any PBP files not already in the cache. Returns (ok, errors, skipped)."""
    os.makedirs(PBP_CACHE, exist_ok=True)

    cached = 0
    to_fetch = []
    for gid in game_ids:
        if os.path.exists(os.path.join(PBP_CACHE, f"{gid}.json")):
            cached += 1
        else:
            to_fetch.append(gid)

    print(f"    PBP: {cached}/{len(game_ids)} cached, {len(to_fetch)} to fetch")

    if not to_fetch:
        return cached, 0, []

    errors = 0
    skipped = []
    t0 = time.time()

    for i, gid in enumerate(to_fetch):
        ok = fetch_pbp_with_retry(gid)
        if not ok:
            errors += 1
            skipped.append(gid)
            if errors <= 5:
                print(f"\n    PBP skip: {gid}")

        if (i + 1) % 50 == 0 or i == len(to_fetch) - 1:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(to_fetch) - i - 1) / rate if rate > 0 else 0
            print(f"\r    PBP: {i+1}/{len(to_fetch)} "
                  f"({cached+i+1-errors}/{len(game_ids)} total) "
                  f"~{remaining/60:.0f}m remaining", end="", flush=True)

        time.sleep(2)  # polite delay

    print()
    return cached + len(to_fetch) - errors, errors, skipped


# ---------------------------------------------------------------------------
# Player processing (reused from league script)
# ---------------------------------------------------------------------------

def extract_opponent(matchup):
    for sep in (" @ ", " vs. "):
        if sep in matchup:
            return matchup.split(sep)[1].strip()
    return matchup


def process_player_season(player, games):
    """
    Run Pure TS% for one player across all their games.
    Returns (summary_dict, per_game_rows_list).
    """
    player_id = player["player_id"]
    per_game_rows = []
    all_components = []
    games_ok = 0
    games_failed = 0
    fail_ids = []

    for game in games:
        gid = game["game_id"]
        pbp_path = os.path.join(PBP_CACHE, f"{gid}.json")

        if not os.path.exists(pbp_path):
            games_failed += 1
            fail_ids.append(f"{gid}: PBP not cached")
            continue

        try:
            with open(pbp_path) as f:
                data = json.load(f)
            actions = data["game"]["actions"]

            comps = classify_scoring_events(actions, player_id)
            pure_ts, total_poss, details = calculate_pure_ts(comps)
            box = box_score_from_components(comps)

            # Reconciliation check
            if (box["pts"] != game["pts"] or box["fga"] != game["fga"]
                    or box["fta"] != game["fta"]):
                games_failed += 1
                fail_ids.append(
                    f"{gid}: recon (pbp {box['pts']}p/{box['fga']}fga/"
                    f"{box['fta']}fta vs log {game['pts']}p/{game['fga']}fga/"
                    f"{game['fta']}fta)"
                )
                continue

            comp_row = {}
            for cid in COMP_IDS:
                if cid in details:
                    comp_row[cid] = {
                        "events": details[cid]["events"],
                        "pts": details[cid]["pts"],
                    }
                else:
                    comp_row[cid] = {"events": 0, "pts": 0}

            if total_poss == 0:
                pure_ts_val = std_ts_val = delta_val = None
            else:
                tsa = box["fga"] + 0.44 * box["fta"]
                std_ts_val = box["pts"] / (2 * tsa) if tsa > 0 else 0.0
                pure_ts_val = pure_ts
                delta_val = (pure_ts - std_ts_val) * 100

            per_game_rows.append({
                "game_id": gid,
                "date": game["date"],
                "matchup": game["matchup"],
                "opponent": extract_opponent(game["matchup"]),
                "pts": box["pts"],
                "fga": box["fga"],
                "fta": box["fta"],
                "scoring_poss": total_poss,
                "pure_ts": pure_ts_val,
                "std_ts": std_ts_val,
                "delta": delta_val,
                "components": comp_row,
            })

            if total_poss > 0:
                all_components.append(comps)
                games_ok += 1

        except Exception as e:
            games_failed += 1
            fail_ids.append(f"{gid}: {e}")

    # Season aggregate
    if not all_components:
        return None, per_game_rows

    season_comps = {k: [] for k in COMPONENTS}
    for game_comps in all_components:
        for cid, events in game_comps.items():
            season_comps[cid].extend(events)

    pure_ts, total_poss, details = calculate_pure_ts(season_comps)
    box = box_score_from_components(season_comps)

    tsa = box["fga"] + 0.44 * box["fta"]
    std_ts = box["pts"] / (2 * tsa) if tsa > 0 else 0.0
    delta = (pure_ts - std_ts) * 100

    summary = {
        "player_id": player["player_id"],
        "player_name": player["player_name"],
        "team_abbr": player["team_abbr"],
        "games_played": games_ok,
        "games_failed": games_failed,
        "total_pts": box["pts"],
        "total_fga": box["fga"],
        "total_fga2": box["fga"] - box["fg3a"],
        "total_fga3": box["fg3a"],
        "total_fta": box["fta"],
        "total_scoring_poss": total_poss,
        "pure_ts_pct": round(pure_ts * 100, 2),
        "standard_ts_pct": round(std_ts * 100, 2),
        "delta_pp": round(delta, 2),
        "fail_ids": fail_ids,
    }

    for cid in COMP_IDS:
        if cid in details:
            d = details[cid]
            summary[f"{cid}_events"] = d["events"]
            summary[f"{cid}_pts"] = d["pts"]
            summary[f"{cid}_eff"] = round(d["eff"] * 100, 2)
        else:
            summary[f"{cid}_events"] = 0
            summary[f"{cid}_pts"] = 0
            summary[f"{cid}_eff"] = ""

    return summary, per_game_rows


# ---------------------------------------------------------------------------
# Per-season result storage (isolated per season)
# ---------------------------------------------------------------------------

def _results_dir(season):
    return os.path.join(DATA_DIR, "league_results", season)


def _result_path(season, player_id):
    return os.path.join(_results_dir(season), f"{player_id}.json")


def is_player_done(season, player_id):
    return os.path.exists(_result_path(season, player_id))


def save_player_result(season, player_id, summary, per_game_rows):
    d = _results_dir(season)
    os.makedirs(d, exist_ok=True)
    path = _result_path(season, player_id)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"summary": summary, "per_game": per_game_rows}, f)
    os.replace(tmp, path)


def load_player_result(season, player_id):
    with open(_result_path(season, player_id)) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# CSV generation
# ---------------------------------------------------------------------------

def summary_csv_headers():
    hdrs = [
        "player_id", "player_name", "team_abbr", "games_played",
        "total_pts", "total_fga", "total_fga2", "total_fga3",
        "total_fta", "total_scoring_poss",
        "pure_ts_pct", "standard_ts_pct", "delta_pp",
    ]
    for cid in COMP_IDS:
        hdrs.extend([f"{cid}_events", f"{cid}_pts", f"{cid}_eff"])
    return hdrs


def summary_to_row(s):
    row = [
        s["player_id"], s["player_name"], s["team_abbr"], s["games_played"],
        s["total_pts"], s["total_fga"], s["total_fga2"], s["total_fga3"],
        s["total_fta"], s["total_scoring_poss"],
        s["pure_ts_pct"], s["standard_ts_pct"], s["delta_pp"],
    ]
    for cid in COMP_IDS:
        row.extend([
            s.get(f"{cid}_events", 0),
            s.get(f"{cid}_pts", 0),
            s.get(f"{cid}_eff", ""),
        ])
    return row


def pergame_csv_headers():
    hdrs = [
        "player_id", "player_name", "team_abbr",
        "game_id", "game_date", "opponent",
        "pts", "fga", "fta", "scoring_poss",
        "pure_ts_pct", "standard_ts_pct", "delta_pp",
    ]
    for cid in COMP_IDS:
        hdrs.extend([f"{cid}_events", f"{cid}_pts"])
    return hdrs


def pergame_to_row(player, g):
    row = [
        player["player_id"], player["player_name"],
        player.get("team_abbr", ""),
        g["game_id"], g["date"], g["opponent"],
        g["pts"], g["fga"], g["fta"], g["scoring_poss"],
        round(g["pure_ts"] * 100, 2) if g["pure_ts"] is not None else "",
        round(g["std_ts"] * 100, 2) if g["std_ts"] is not None else "",
        round(g["delta"], 2) if g["delta"] is not None else "",
    ]
    for cid in COMP_IDS:
        comp = g.get("components", {}).get(cid, {"events": 0, "pts": 0})
        row.extend([comp["events"], comp["pts"]])
    return row


def generate_csvs(players, season):
    """Generate the two league CSVs for a season. Returns summary stats."""
    summaries = []
    pergame_count = 0

    pergame_path = os.path.join(
        DATA_DIR, f"pure_ts_pct_league_pergame_{season}.csv"
    )
    pergame_tmp = pergame_path + ".tmp"

    with open(pergame_tmp, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(pergame_csv_headers())
        for p in players:
            pid = p["player_id"]
            if not is_player_done(season, pid):
                continue
            result = load_player_result(season, pid)
            summary = result.get("summary")
            per_game = result.get("per_game", [])
            if summary:
                summaries.append(summary)
            for g in per_game:
                writer.writerow(pergame_to_row(p, g))
                pergame_count += 1

    os.replace(pergame_tmp, pergame_path)

    # Summary CSV — all players (no min filter for historical)
    filtered = sorted(summaries, key=lambda s: s["total_scoring_poss"],
                      reverse=True)

    summary_path = os.path.join(DATA_DIR, f"pure_ts_pct_league_{season}.csv")
    summary_tmp = summary_path + ".tmp"
    with open(summary_tmp, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(summary_csv_headers())
        for s in filtered:
            writer.writerow(summary_to_row(s))
    os.replace(summary_tmp, summary_path)

    return {
        "summary_path": summary_path,
        "summary_count": len(filtered),
        "pergame_path": pergame_path,
        "pergame_count": pergame_count,
        "summaries": summaries,
    }


# ---------------------------------------------------------------------------
# Process one full season
# ---------------------------------------------------------------------------

def run_season(season, dry_run_games=0):
    """
    Run the full Pure TS% pipeline for one season.
    If dry_run_games > 0, only process the first N games worth of players.
    Returns a season result dict.
    """
    t0 = datetime.datetime.now()
    print(f"\n{'='*60}")
    print(f"  SEASON: {season}")
    print(f"  Started: {t0.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # --- Roster ---
    players = load_roster(season)
    if players:
        print(f"\n  Roster: {len(players)} players (cached)")
    else:
        print(f"\n  Fetching roster for {season}...")
        players = fetch_roster(season)
        save_roster(players, season)
        print(f"  Roster: {len(players)} players saved")

    # --- Game logs ---
    print(f"\n  === Game Logs ===")
    game_logs = fetch_all_game_logs(players, season)

    # If dry run, select player subset first so we only fetch their PBP
    player_list = players
    if dry_run_games > 0:
        with_games = [p for p in players
                      if game_logs.get(str(p["player_id"]), [])]
        player_list = with_games[:dry_run_games]
        print(f"\n    DRY RUN: processing {len(player_list)} players only")

    # Collect unique game IDs (only for selected players)
    all_game_ids = set()
    for p in player_list:
        for g in game_logs.get(str(p["player_id"]), []):
            all_game_ids.add(g["game_id"])
    all_game_ids = sorted(all_game_ids)
    print(f"    {len(all_game_ids)} unique games across "
          f"{'selected' if dry_run_games else 'all'} players")

    # --- PBP fetch ---
    print(f"\n  === PBP Fetch ===")
    ok_count, error_count, skipped_games = fetch_missing_pbp(all_game_ids)
    if skipped_games:
        print(f"    Skipped {len(skipped_games)} games (logged)")

    # --- Process players ---
    print(f"\n  === Processing Players ===")

    players_ok = 0
    players_skipped = 0
    all_failures = []
    processed = 0

    for i, player in enumerate(player_list):
        pid = player["player_id"]
        pid_str = str(pid)
        name = player["player_name"]
        team = player["team_abbr"] or "—"
        idx = i + 1

        # Skip if already done (resume support)
        if is_player_done(season, pid):
            result = load_player_result(season, pid)
            s = result.get("summary")
            if s:
                players_ok += 1
                if s.get("fail_ids"):
                    all_failures.append((pid, name, s["fail_ids"]))
            else:
                players_skipped += 1
            continue

        # Get game log
        games = game_logs.get(pid_str, [])
        if not games:
            save_player_result(season, pid, None, [])
            players_skipped += 1
            continue

        # Process
        summary, per_game_rows = process_player_season(player, games)
        save_player_result(season, pid, summary, per_game_rows)
        processed += 1

        if summary is None:
            players_skipped += 1
            continue

        players_ok += 1
        fail_count = summary.get("games_failed", 0)
        if summary.get("fail_ids"):
            all_failures.append((pid, name, summary["fail_ids"]))

        if processed % 25 == 0 or idx == len(player_list):
            print(f"    [{idx}/{len(player_list)}] {name} ({team}) — "
                  f"{summary['games_played']}g — "
                  f"Pure TS%: {summary['pure_ts_pct']:.1f}%")

    # --- Generate CSVs ---
    print(f"\n  === Generating CSVs ===")
    csv_result = generate_csvs(
        player_list if dry_run_games > 0 else players, season
    )

    t1 = datetime.datetime.now()
    runtime_min = (t1 - t0).total_seconds() / 60

    # Compute league averages (aggregate ratio: sum pts / sum max pts)
    valid = [s for s in csv_result["summaries"]
             if s.get("total_scoring_poss", 0) > 0 and s.get("pure_ts_pct", 0) > 0]
    league_pts = sum(s["total_pts"] for s in valid)
    league_max_pts = sum(s["total_pts"] / (s["pure_ts_pct"] / 100) for s in valid)
    league_fga = sum(s["total_fga"] for s in valid)
    league_fta = sum(s["total_fta"] for s in valid)
    league_tsa = league_fga + 0.44 * league_fta
    avg_pure = (league_pts / league_max_pts * 100) if league_max_pts > 0 else 0
    avg_std = (league_pts / (2 * league_tsa) * 100) if league_tsa > 0 else 0
    avg_delta = avg_pure - avg_std

    print(f"\n  --- {season} Complete ---")
    print(f"  Runtime: {runtime_min:.1f} min")
    print(f"  Players: {players_ok} with data, {players_skipped} skipped")
    print(f"  Games: {len(all_game_ids)} unique")
    print(f"  CSVs: {csv_result['summary_count']} player rows, "
          f"{csv_result['pergame_count']} per-game rows")
    print(f"  League avg Pure TS%: {avg_pure:.1f}%")
    print(f"  League avg Std TS%:  {avg_std:.1f}%")
    print(f"  League avg Delta:    {avg_delta:+.1f}pp")

    if all_failures:
        print(f"  Players with game errors: {len(all_failures)}")

    return {
        "season": season,
        "runtime_min": runtime_min,
        "players_ok": players_ok,
        "players_skipped": players_skipped,
        "games": len(all_game_ids),
        "summary_count": csv_result["summary_count"],
        "pergame_count": csv_result["pergame_count"],
        "avg_pure": avg_pure,
        "avg_std": avg_std,
        "avg_delta": avg_delta,
        "errors": len(all_failures),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run Pure TS%% across multiple historical NBA seasons."
    )
    parser.add_argument(
        "--seasons", nargs="+", default=ALL_SEASONS,
        help="Seasons to process (default: all 6 historical seasons)",
    )
    parser.add_argument(
        "--dry-run", type=int, default=0, metavar="N",
        help="Only process first N players per season (for testing)",
    )
    args = parser.parse_args()

    seasons = args.seasons
    dry_run = args.dry_run

    print(f"\n{'#'*60}")
    print(f"  PURE TS% — HISTORICAL MULTI-SEASON PIPELINE")
    print(f"  Seasons: {', '.join(seasons)}")
    if dry_run:
        print(f"  DRY RUN: {dry_run} players per season")
    print(f"  Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = []
    for season in seasons:
        result = run_season(season, dry_run_games=dry_run)
        results.append(result)

    # Final summary
    print(f"\n{'#'*60}")
    print(f"  FINAL SUMMARY")
    print(f"{'#'*60}")
    print(f"\n{'Season':<12} {'Runtime':>8} {'Players':>8} {'Games':>7} "
          f"{'Pure TS%':>9} {'Std TS%':>9} {'Delta':>8}")
    print("-" * 70)
    for r in results:
        print(f"{r['season']:<12} {r['runtime_min']:>7.1f}m {r['players_ok']:>8} "
              f"{r['games']:>7} {r['avg_pure']:>8.1f}% {r['avg_std']:>8.1f}% "
              f"{r['avg_delta']:>+7.1f}pp")

    total_runtime = sum(r["runtime_min"] for r in results)
    print(f"\nTotal runtime: {total_runtime:.1f} minutes")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
