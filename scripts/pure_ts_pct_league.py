#!/usr/bin/env python3
"""
Pure TS% — League-Wide Season Calculator

Runs Pure TS% for every active NBA player across a full NBA season,
producing per-player result files and consolidated league CSVs.

Usage:
    python scripts/pure_ts_pct_league.py
    python scripts/pure_ts_pct_league.py --resume
    python scripts/pure_ts_pct_league.py --min-games 20 --min-possessions 100

Requires: scripts/pure_ts_pct_single_game.py, scripts/pure_ts_pct_season.py
"""

import argparse
import csv
import datetime
import json
import os
import shutil
import statistics
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
PBP_CACHE = os.path.join(DATA_DIR, "pbp_cache")
RESULTS_DIR = os.path.join(DATA_DIR, "league_results")

from pure_ts_pct_single_game import (
    COMPONENTS,
    classify_scoring_events,
    calculate_pure_ts,
    box_score_from_components,
)

from pure_ts_pct_season import (
    NBA_HEADERS,
    FETCH_DELAY,
    get_game_log,
    fetch_pbp_cached,
)

COMP_IDS = list(COMPONENTS.keys())

# ---------------------------------------------------------------------------
# Player result file I/O
# ---------------------------------------------------------------------------

def _result_path(player_id):
    return os.path.join(RESULTS_DIR, f"{player_id}.json")


def is_player_done(player_id):
    return os.path.exists(_result_path(player_id))


def save_player_result(player_id, summary, per_game_rows):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = _result_path(player_id)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"summary": summary, "per_game": per_game_rows}, f)
    os.replace(tmp, path)


def load_player_result(player_id):
    with open(_result_path(player_id)) as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_player_list(season):
    path = os.path.join(DATA_DIR, f"nba_active_players_{season}.json")
    with open(path) as f:
        return json.load(f)


def _game_log_cache_path(season):
    return os.path.join(DATA_DIR, f"league_game_logs_{season}.json")


def fetch_all_game_logs(players, season):
    """
    Fetch game logs for all players, using a cache file.

    Returns dict: str(player_id) -> list of game dicts.
    """
    cache_path = _game_log_cache_path(season)
    cached = {}

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cached = json.load(f)

    missing = [p for p in players if str(p["player_id"]) not in cached]

    if not missing:
        print(f"  Game logs loaded from cache ({len(cached)} players)")
        return cached

    if cached:
        print(f"  Game logs: {len(cached)} cached, {len(missing)} to fetch")
    else:
        print(f"  Fetching game logs for {len(missing)} players...")

    for i, p in enumerate(missing):
        pid = str(p["player_id"])
        try:
            games = get_game_log(int(pid), season)
            cached[pid] = games
        except Exception as e:
            cached[pid] = []

        if (i + 1) % 20 == 0 or i == len(missing) - 1:
            print(f"\r  Game logs: {i + 1}/{len(missing)} fetched", end="",
                  flush=True)
        time.sleep(1.0)

    print()

    with open(cache_path, "w") as f:
        json.dump(cached, f)
    print(f"  Game log cache saved ({len(cached)} players)")
    return cached

# ---------------------------------------------------------------------------
# PBP fetching
# ---------------------------------------------------------------------------

def collect_unique_game_ids(game_logs):
    ids = set()
    for games in game_logs.values():
        for g in games:
            ids.add(g["game_id"])
    return sorted(ids)


def fetch_missing_pbp(game_ids):
    """Fetch any PBP files not already in the cache. Returns error count."""
    os.makedirs(PBP_CACHE, exist_ok=True)

    cached = 0
    to_fetch = []
    for gid in game_ids:
        if os.path.exists(os.path.join(PBP_CACHE, f"{gid}.json")):
            cached += 1
        else:
            to_fetch.append(gid)

    print(f"  PBP cache: {cached}/{len(game_ids)} games cached, "
          f"{len(to_fetch)} to fetch")

    if not to_fetch:
        return 0

    errors = 0
    for i, gid in enumerate(to_fetch):
        try:
            fetch_pbp_cached(gid)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"\n  PBP error ({gid}): {e}")

        if (i + 1) % 20 == 0 or i == len(to_fetch) - 1:
            print(f"\r  PBP fetch: {i + 1}/{len(to_fetch)}", end="",
                  flush=True)
        time.sleep(FETCH_DELAY)

    print()
    print(f"  PBP fetch complete. {cached + len(to_fetch) - errors} games "
          f"cached" + (f", {errors} errors" if errors else ""))
    return errors

# ---------------------------------------------------------------------------
# Player processing
# ---------------------------------------------------------------------------

def extract_opponent(matchup):
    """'LAL @ HOU' -> 'HOU', 'LAL vs. HOU' -> 'HOU'."""
    for sep in (" @ ", " vs. "):
        if sep in matchup:
            return matchup.split(sep)[1].strip()
    return matchup


def process_player_season(player, games, game_logs_raw):
    """
    Run Pure TS% for one player across all their games.

    Returns (summary_dict, per_game_rows_list).
    summary_dict is None if the player had zero scoring possessions.
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

            # Quarter-level computation (Q4 absorbs all OT periods)
            quarter_data = {}
            for q in range(1, 5):
                if q < 4:
                    q_actions = [a for a in actions if a.get("period") == q]
                else:
                    q_actions = [a for a in actions if a.get("period", 0) >= 4]
                q_comps = classify_scoring_events(q_actions, player_id)
                q_pure_ts, q_poss, _q_det = calculate_pure_ts(q_comps)
                q_box = box_score_from_components(q_comps)
                if q_poss == 0:
                    quarter_data[q] = {
                        "pure_ts": None,
                        "sp": 0,
                        "std_ts": None,
                        "delta": None,
                    }
                else:
                    q_tsa = q_box["fga"] + 0.44 * q_box["fta"]
                    q_std_ts = q_box["pts"] / (2 * q_tsa) if q_tsa > 0 else 0.0
                    quarter_data[q] = {
                        "pure_ts": q_pure_ts,
                        "sp": q_poss,
                        "std_ts": q_std_ts,
                        "delta": (q_pure_ts - q_std_ts) * 100,
                    }

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

            # Build component data for this game
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
                pure_ts_val = None
                std_ts_val = None
                delta_val = None
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
                "quarters": quarter_data,
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
    for q in range(1, 5):
        hdrs.extend([
            f"q{q}_pure_ts", f"q{q}_sp", f"q{q}_std_ts", f"q{q}_delta",
        ])
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
    quarters = g.get("quarters", {})
    for q in range(1, 5):
        qd = quarters.get(q) or quarters.get(str(q)) or {}
        qpts = qd.get("pure_ts")
        qstd = qd.get("std_ts")
        qdelta = qd.get("delta")
        row.extend([
            round(qpts * 100, 2) if qpts is not None else "",
            qd.get("sp") or 0,
            round(qstd * 100, 2) if qstd is not None else "",
            round(qdelta, 2) if qdelta is not None else "",
        ])
    return row


def generate_csvs(players, season, min_games, min_poss):
    """
    Read all per-player result files and generate the two league CSVs.

    Returns (summary_path, summary_count, pergame_path, pergame_count).
    """
    summaries = []
    pergame_count = 0

    # -- Per-game CSV (stream from result files) ----------------------------
    pergame_path = os.path.join(
        DATA_DIR, f"pure_ts_pct_league_pergame_{season}.csv"
    )
    pergame_tmp = pergame_path + ".tmp"

    with open(pergame_tmp, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(pergame_csv_headers())

        for p in players:
            pid = p["player_id"]
            if not is_player_done(pid):
                continue
            result = load_player_result(pid)
            summary = result.get("summary")
            per_game = result.get("per_game", [])

            if summary:
                summaries.append(summary)

            for g in per_game:
                writer.writerow(pergame_to_row(p, g))
                pergame_count += 1

    os.replace(pergame_tmp, pergame_path)

    # -- Summary CSV --------------------------------------------------------
    filtered = [
        s for s in summaries
        if s["games_played"] >= min_games
        and s["total_scoring_poss"] >= min_poss
    ]
    filtered.sort(key=lambda s: s["total_scoring_poss"], reverse=True)

    summary_path = os.path.join(
        DATA_DIR, f"pure_ts_pct_league_{season}.csv"
    )
    summary_tmp = summary_path + ".tmp"
    with open(summary_tmp, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(summary_csv_headers())
        for s in filtered:
            writer.writerow(summary_to_row(s))
    os.replace(summary_tmp, summary_path)

    return summary_path, len(filtered), pergame_path, pergame_count, summaries

# ---------------------------------------------------------------------------
# Log file
# ---------------------------------------------------------------------------

def write_log(season, start_time, end_time, total_players, total_games,
              players_ok, players_failed, players_skipped, all_failures,
              summaries, summary_path, summary_count, pergame_path,
              pergame_count):
    """Write the run log. Returns path."""
    log_path = os.path.join(DATA_DIR, f"league_run_log_{season}.txt")

    valid = [s for s in summaries
             if s.get("total_scoring_poss", 0) > 0 and s.get("pure_ts_pct", 0) > 0]

    # Aggregate ratio: sum all pts / sum all max pts
    league_pts = sum(s["total_pts"] for s in valid) if valid else 0
    league_max_pts = sum(s["total_pts"] / (s["pure_ts_pct"] / 100)
                         for s in valid) if valid else 0
    league_fga = sum(s["total_fga"] for s in valid) if valid else 0
    league_fta = sum(s["total_fta"] for s in valid) if valid else 0
    league_tsa = league_fga + 0.44 * league_fta
    agg_pure = (league_pts / league_max_pts * 100) if league_max_pts > 0 else 0
    agg_std = (league_pts / (2 * league_tsa) * 100) if league_tsa > 0 else 0
    agg_delta = agg_pure - agg_std

    runtime = (end_time - start_time).total_seconds() / 60

    with open(log_path, "w") as f:
        f.write("--- Pure TS% League Run ---\n\n")
        f.write(f"Season:   {season}\n")
        f.write(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Runtime:  {runtime:.1f} minutes\n\n")

        f.write(f"Players in roster: {total_players}\n")
        f.write(f"  Processed successfully: {players_ok}\n")
        f.write(f"  Skipped (0 games/possessions): {players_skipped}\n")
        if players_failed:
            f.write(f"  Failed: {players_failed}\n")
        f.write(f"\nTotal unique games: {total_games}\n\n")

        f.write(f"Summary Statistics ({len(valid)} players with "
                f">0 scoring possessions):\n")
        f.write(f"  League Pure TS%:     {agg_pure:.1f}%\n")
        f.write(f"  League Standard TS%: {agg_std:.1f}%\n")
        f.write(f"  League Delta:        {agg_delta:+.1f} pp\n\n")

        f.write(f"Output Files:\n")
        f.write(f"  {summary_path} ({summary_count} rows)\n")
        f.write(f"  {pergame_path} ({pergame_count} rows)\n\n")

        if all_failures:
            f.write(f"Game-Level Failures ({len(all_failures)} players "
                    f"with errors):\n")
            for pid, name, errors in all_failures:
                f.write(f"  {name} (ID {pid}): "
                        f"{len(errors)} game error(s)\n")
                for err in errors[:5]:
                    f.write(f"    {err}\n")
                if len(errors) > 5:
                    f.write(f"    ... and {len(errors) - 5} more\n")

    return log_path

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run Pure TS%% for every active NBA player "
                    "across a full season."
    )
    parser.add_argument("--season", default="2025-26")
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last interrupted run (skip already-processed "
             "players)",
    )
    parser.add_argument("--min-games", type=int, default=0,
                        help="Min games for summary CSV inclusion")
    parser.add_argument("--min-possessions", type=int, default=0,
                        help="Min scoring possessions for summary CSV "
                             "inclusion")
    args = parser.parse_args()

    start_time = datetime.datetime.now()
    season = args.season

    print(f"\n{'=' * 60}")
    print(f"  PURE TS% — LEAGUE-WIDE SEASON RUN")
    print(f"  Season: {season}")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    # Load player list
    players = load_player_list(season)
    print(f"Players: {len(players)} in roster\n")

    # Fresh run vs resume
    if args.resume:
        already = sum(1 for p in players if is_player_done(p["player_id"]))
        if already:
            print(f"Resuming: {already} players already processed\n")
    else:
        if os.path.exists(RESULTS_DIR):
            shutil.rmtree(RESULTS_DIR)
            print("Fresh run: cleared previous results\n")

    # === Phase 0: Fetch all game logs =====================================
    print("=== PHASE 0: Game Logs ===")
    game_logs = fetch_all_game_logs(players, season)

    # === Pass 1: Fetch missing PBP ========================================
    print("\n=== PASS 1: Fetching PBP Data ===")
    all_game_ids = collect_unique_game_ids(game_logs)
    print(f"  {len(all_game_ids)} unique games across all players")
    fetch_missing_pbp(all_game_ids)

    # === Pass 2: Process players ==========================================
    print(f"\n=== PASS 2: Processing Players ===\n")

    players_ok = 0
    players_skipped = 0
    players_failed = 0
    all_failures = []
    processed_this_run = 0

    for i, player in enumerate(players):
        pid = player["player_id"]
        pid_str = str(pid)
        name = player["player_name"]
        team = player["team_abbr"] or "—"
        idx = i + 1

        # Skip if already done
        if is_player_done(pid):
            result = load_player_result(pid)
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
            # Save empty result so we don't retry
            save_player_result(pid, None, [])
            players_skipped += 1
            print(f"  [{idx}/{len(players)}] {name} ({team}) — "
                  f"0 games — skipped")
            continue

        # Process
        summary, per_game_rows = process_player_season(
            player, games, game_logs
        )

        # Save result
        save_player_result(pid, summary, per_game_rows)
        processed_this_run += 1

        if summary is None:
            players_skipped += 1
            print(f"  [{idx}/{len(players)}] {name} ({team}) — "
                  f"0 scoring possessions — skipped")
            continue

        players_ok += 1
        fail_count = summary.get("games_failed", 0)
        fail_str = f" ({fail_count} game errors)" if fail_count else ""
        if summary.get("fail_ids"):
            all_failures.append((pid, name, summary["fail_ids"]))

        print(f"  [{idx}/{len(players)}] {name} ({team}) — "
              f"{summary['games_played']} games — "
              f"Pure TS%: {summary['pure_ts_pct']:.1f}%{fail_str}")

    # === Generate CSVs ====================================================
    print(f"\n=== Generating Output Files ===\n")

    summary_path, summary_count, pergame_path, pergame_count, summaries = \
        generate_csvs(players, season, args.min_games, args.min_possessions)

    # === Write log ========================================================
    end_time = datetime.datetime.now()
    log_path = write_log(
        season, start_time, end_time, len(players), len(all_game_ids),
        players_ok, players_failed, players_skipped, all_failures,
        summaries, summary_path, summary_count, pergame_path, pergame_count,
    )

    # === Print summary ====================================================
    runtime = (end_time - start_time).total_seconds() / 60
    valid = [s for s in summaries if s.get("total_scoring_poss", 0) > 0]

    print(f"{'=' * 60}")
    print(f"  COMPLETE")
    print(f"  Runtime: {runtime:.1f} minutes "
          f"({processed_this_run} players processed this run)")
    print(f"  Players with data: {players_ok}")
    if players_skipped:
        print(f"  Players skipped (0 games/possessions): {players_skipped}")
    if all_failures:
        print(f"  Players with game-level errors: {len(all_failures)}")

    print(f"\n  Output:")
    print(f"    {summary_path} ({summary_count} rows)")
    print(f"    {pergame_path} ({pergame_count} rows)")
    print(f"    {log_path}")

    if valid:
        print(f"\n  League Averages ({len(valid)} players, aggregate ratio):")
        print(f"    League Pure TS%:     {agg_pure:.1f}%")
        print(f"    League Standard TS%: {agg_std:.1f}%")
        print(f"    League Delta:        {agg_delta:+.1f} pp")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
