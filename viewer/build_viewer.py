#!/usr/bin/env python3
"""
Build the PS% League Viewer.

Default: split build (app shell + per-season JSON) → viewer/dist/
  python3 viewer/build_viewer.py

Monolith: single 495MB HTML file (slow to load, use split instead)
  python3 viewer/build_viewer.py --monolith

Local testing (split build):
  cd viewer/dist && python3 -m http.server 8500
  Open http://localhost:8500
"""

import argparse
import csv
import json
import os
import sys
from statistics import mean

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "pure_ts_league_viewer.html")

def discover_seasons(data_dir):
    """Auto-discover seasons from pure_ts_pct_league_*.csv files.

    Returns seasons sorted: newest RS first, then playoff entries grouped
    after their corresponding RS season (e.g., 2024-25, 2024-25-PO, ...).
    """
    import glob
    pattern = os.path.join(data_dir, "pure_ts_pct_league_*.csv")
    seasons = set()
    for path in glob.glob(pattern):
        fname = os.path.basename(path)
        if "pergame" in fname:
            continue
        season = fname.replace("pure_ts_pct_league_", "").replace(".csv", "")
        seasons.add(season)

    def sort_key(s):
        # Extract base year for sorting; PO sorts after RS for same year
        base = s.replace("-PO", "")
        is_po = s.endswith("-PO")
        return (base, is_po)

    # Sort by year descending, RS before PO within same year
    return sorted(seasons, key=sort_key, reverse=True)

COMPONENTS = [
    ("C1a", "Clean 2PT FGA", 2),
    ("C1b", "Clean 3PT FGA", 3),
    ("C2", "2PT Shooting Foul", 2),
    ("C3", "3PT Shooting Foul", 3),
    ("C4", "And-1 2PT", 3),
    ("C5", "And-1 3PT", 4),
    ("C6a", "Tech FT", 1),
    ("C6b", "Flagrant FT", 2),
    ("C6c", "Clear Path FT", 2),
    ("C6d", "Take Foul FT", 1),
    ("C6e", "Away-From-Play FT", 1),
    ("C6f", "Bonus Foul FT", 2),
]

NUMERIC_FIELDS = {
    "games_played", "total_pts", "total_fga", "total_fga2", "total_fga3",
    "total_fta", "total_scoring_poss", "pure_ts_pct", "standard_ts_pct",
    "delta_pp", "total_fgm", "total_fg3m", "total_ftm",
}

PERGAME_NUMERIC = {
    "pts", "fga", "fta", "scoring_poss", "pure_ts_pct",
    "standard_ts_pct", "delta_pp",
}


def _num(val):
    """Convert string to int or float, or None."""
    if val == "" or val is None:
        return None
    try:
        return float(val) if "." in str(val) else int(val)
    except (ValueError, TypeError):
        return None


def read_league_csv(path):
    players = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            p = {}
            for k, v in row.items():
                if k in NUMERIC_FIELDS or k.startswith("C"):
                    p[k] = _num(v)
                else:
                    p[k] = v if v != "" else None
            players.append(p)
    return players


def read_pergame_csv(path, delta_threshold=0.0):
    """Read per-game CSV, loading all rows."""
    games = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            d = _num(row.get("delta_pp", ""))
            if delta_threshold > 0.0 and (d is None or abs(d) < delta_threshold):
                continue
            g = {}
            for k, v in row.items():
                if k in PERGAME_NUMERIC or k.startswith("q"):
                    g[k] = _num(v)
                elif k.startswith("C"):
                    g[k] = _num(v)
                else:
                    g[k] = v if v != "" else None
            # Pre-calculate per-game FGM and FTM from component data
            def _gev(cid):
                return g.get(f"{cid}_events") or 0
            def _gpts(cid):
                return g.get(f"{cid}_pts") or 0
            g_a1_ftm = max(0, _gpts("C4") - _gev("C4") * 2) + max(0, _gpts("C5") - _gev("C5") * 3)
            g["fgm"] = int((_gpts("C1a") / 2 if _gpts("C1a") else 0) +
                           (_gpts("C1b") / 3 if _gpts("C1b") else 0) +
                           _gev("C4") + _gev("C5"))
            g["ftm"] = int(_gpts("C2") + _gpts("C3") + g_a1_ftm +
                           _gpts("C6a") + _gpts("C6b") + _gpts("C6c") +
                           _gpts("C6d") + _gpts("C6e") + _gpts("C6f"))
            games.append(g)
    return games


def _safe_div(a, b):
    """Safe division returning None on zero denominator."""
    if b is None or b == 0:
        return None
    return round(a / b * 100, 1)


def enrich_player(p, has_components=True):
    """Add derived fields to a player dict.

    For seasons with component data (PBP-era): derives FGM/3PM/FTM from
    components, computes foul profiles and FT-by-type breakdowns.
    For box-score-only seasons: uses FGM/3PM/FTM directly from CSV, skips
    component-derived fields.
    """
    total_fga = p.get("total_fga") or 0
    total_fga3 = p.get("total_fga3") or 0
    total_fta_val = p.get("total_fta") or 0

    # --- Max Possible Points (always computable) ---
    p["max_possible_pts"] = 2 * total_fga + total_fga3 + total_fta_val

    if not has_components:
        # Box-score-only: FGM, FG3M, FTM already in CSV
        total_fgm = p.get("total_fgm") or 0
        total_fg3m = p.get("total_fg3m") or 0
        total_ftm = p.get("total_ftm") or 0

        p["total_fgm"] = int(total_fgm)
        p["fg_pct"] = round(total_fgm / total_fga * 100, 1) if total_fga else None

        p["total_3pm"] = int(total_fg3m)
        p["total_3pa"] = int(total_fga3)
        p["three_pct"] = round(total_fg3m / total_fga3 * 100, 1) if total_fga3 else None

        p["total_2pm"] = int(total_fgm - total_fg3m)
        p["total_2pa"] = int(total_fga - total_fga3)
        p["two_pct"] = round(p["total_2pm"] / p["total_2pa"] * 100, 1) if p["total_2pa"] else None

        p["ft_overall_ftm"] = int(total_ftm)
        p["ft_overall_fta"] = int(total_fta_val)
        p["ft_overall_pct"] = round(total_ftm / total_fta_val * 100, 1) if total_fta_val else None

        return p

    # --- Component data available: derive everything from components ---
    sp = p.get("total_scoring_poss") or 0

    def ev(cid):
        return p.get(f"{cid}_events") or 0

    def pts(cid):
        return p.get(f"{cid}_pts") or 0

    c6_penalty = ev("C6a") + ev("C6b") + ev("C6c") + ev("C6d") + ev("C6e") + ev("C6f")

    # Foul profile percentages
    p["fp_clean2"] = _safe_div(ev("C1a"), sp) if sp else None
    p["fp_clean3"] = _safe_div(ev("C1b"), sp) if sp else None
    p["fp_sf2"] = _safe_div(ev("C2"), sp) if sp else None
    p["fp_sf3"] = _safe_div(ev("C3"), sp) if sp else None
    p["fp_and1"] = _safe_div(ev("C4") + ev("C5"), sp) if sp else None
    p["fp_penalty"] = _safe_div(c6_penalty, sp) if sp else None

    # FT by type
    sf_ftm = pts("C2") + pts("C3")
    sf_fta = ev("C2") * 2 + ev("C3") * 3
    p["ft_shooting_pct"] = round(sf_ftm / sf_fta * 100, 1) if sf_fta else None

    a1_ftm = max(0, pts("C4") - ev("C4") * 2) + max(0, pts("C5") - ev("C5") * 3)
    a1_fta = ev("C4") + ev("C5")
    p["ft_and1_pct"] = round(a1_ftm / a1_fta * 100, 1) if a1_fta else None

    bf_fta = ev("C6f") * 2
    p["ft_bonus_pct"] = round(pts("C6f") / bf_fta * 100, 1) if bf_fta else None

    p["ft_tech_pct"] = round(pts("C6a") / ev("C6a") * 100, 1) if ev("C6a") else None

    total_ftm = (
        pts("C2") + pts("C3") + a1_ftm +
        pts("C6a") + pts("C6b") + pts("C6c") +
        pts("C6d") + pts("C6e") + pts("C6f")
    )
    total_fta = (
        ev("C2") * 2 + ev("C3") * 3 + a1_fta +
        ev("C6a") + ev("C6b") * 2 + ev("C6c") * 2 +
        ev("C6d") + ev("C6e") + ev("C6f") * 2
    )
    p["ft_overall_pct"] = round(total_ftm / total_fta * 100, 1) if total_fta else None

    # FGM / shooting splits
    clean_2pt_fgm = pts("C1a") / 2 if pts("C1a") else 0
    clean_3pt_fgm = pts("C1b") / 3 if pts("C1b") else 0
    total_fgm = clean_2pt_fgm + clean_3pt_fgm + ev("C4") + ev("C5")
    p["total_fgm"] = int(total_fgm)
    p["fg_pct"] = round(total_fgm / total_fga * 100, 1) if total_fga else None

    p["total_3pm"] = int(clean_3pt_fgm + ev("C5"))
    p["total_3pa"] = int(total_fga3)
    p["three_pct"] = round(p["total_3pm"] / p["total_3pa"] * 100, 1) if p["total_3pa"] else None

    p["total_2pm"] = int(clean_2pt_fgm + ev("C4"))
    p["total_2pa"] = int(total_fga - total_fga3)
    p["two_pct"] = round(p["total_2pm"] / p["total_2pa"] * 100, 1) if p["total_2pa"] else None

    and1_total = ev("C4") + ev("C5")
    p["and1_rate"] = round(and1_total / total_fgm * 100, 1) if total_fgm else None

    foul_events = (ev("C2") + ev("C3") + ev("C4") + ev("C5") +
                   ev("C6a") + ev("C6b") + ev("C6c") + ev("C6d") +
                   ev("C6e") + ev("C6f"))
    p["foul_draw_rate"] = round(foul_events / sp * 100, 1) if sp else None

    hidden = (ev("C2") + ev("C3") +
              ev("C6a") + ev("C6b") + ev("C6c") + ev("C6d") +
              ev("C6e") + ev("C6f"))
    p["hidden_poss"] = hidden
    p["hidden_poss_pct"] = round(hidden / sp * 100, 1) if sp else None

    # Raw counts for Foul Profile tab
    p["fp_clean2_n"] = ev("C1a")
    p["fp_clean3_n"] = ev("C1b")
    p["fp_sf2_n"] = ev("C2")
    p["fp_sf3_n"] = ev("C3")
    p["fp_and1_n"] = ev("C4") + ev("C5")
    p["fp_penalty_n"] = c6_penalty

    # FTM/FTA for FT by Type tab
    p["ft_shooting_ftm"] = sf_ftm
    p["ft_shooting_fta"] = sf_fta
    p["ft_and1_ftm"] = int(a1_ftm)
    p["ft_and1_fta"] = a1_fta
    p["ft_bonus_ftm"] = pts("C6f")
    p["ft_bonus_fta"] = bf_fta
    p["ft_tech_ftm"] = pts("C6a")
    p["ft_tech_fta"] = ev("C6a")
    p["ft_overall_ftm"] = int(total_ftm)
    p["ft_overall_fta"] = int(total_fta)

    return p


def compute_season_meta(players):
    """Compute league-level metadata for a season's player list."""
    # Use aggregate ratio for avg delta: sum pts / sum max pts
    valid = [p for p in players
             if (p.get("total_pts") or 0) > 0
             and (p.get("pure_ts_pct") or 0) > 0]
    if valid:
        league_pts = sum(p.get("total_pts") or 0 for p in valid)
        league_fga = sum(p.get("total_fga") or 0 for p in valid)
        league_fga3 = sum(p.get("total_fga3") or 0 for p in valid)
        league_fta = sum(p.get("total_fta") or 0 for p in valid)
        league_max = 2 * league_fga + league_fga3 + league_fta
        league_tsa = league_fga + 0.44 * league_fta
        agg_pure = (league_pts / league_max * 100) if league_max > 0 else 0
        agg_std = (league_pts / (2 * league_tsa) * 100) if league_tsa > 0 else 0
        avg_delta = round(agg_pure - agg_std, 1)
        tpa_rate = round(league_fga3 / league_fga * 100, 1) if league_fga > 0 else 0
    else:
        avg_delta = None
        agg_pure = agg_std = tpa_rate = 0
    return {
        "avg_delta": avg_delta,
        "player_count": len(players),
        "league_pure_ts": round(agg_pure, 1),
        "league_std_ts": round(agg_std, 1),
        "league_3pa_rate": tpa_rate,
    }


ERA_COMPARISON_PLAYERS = [
    ("Kareem Abdul-Jabbar", "1979-80"),
    ("Larry Bird", "1985-86"),
    ("Magic Johnson", "1986-87"),
    ("Danny Ainge", "1987-88"),
    ("Michael Jordan", "1990-91"),
    ("Reggie Miller", "1992-93"),
    ("Hakeem Olajuwon", "1993-94"),
    ("Shaquille O'Neal", "1999-00"),
    ("Allen Iverson", "2000-01"),
    ("Ray Allen", "2001-02"),
    ("Tim Duncan", "2002-03"),
    ("Tracy McGrady", "2002-03"),
    ("Steve Nash", "2005-06"),
    ("Kobe Bryant", "2005-06"),
    ("Dwyane Wade", "2008-09"),
    ("Dirk Nowitzki", "2010-11"),
    ("Dwight Howard", "2010-11"),
    ("LeBron James", "2012-13"),
    ("Carmelo Anthony", "2012-13"),
    ("Kevin Durant", "2013-14"),
    ("Stephen Curry", "2015-16"),
    ("Russell Westbrook", "2016-17"),
    ("James Harden", "2018-19"),
    ("Kawhi Leonard", "2018-19"),
    ("Giannis Antetokounmpo", "2019-20"),
    ("Damian Lillard", "2019-20"),
    ("Nikola Jokić", "2023-24"),
    ("Luka Dončić", "2023-24"),
    ("Jayson Tatum", "2024-25"),
    ("Anthony Edwards", "2024-25"),
    ("Shai Gilgeous-Alexander", "2025-26"),
]


def _strip_accents(s):
    """Remove diacritics for accent-insensitive matching."""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _load_nba_id_lookup():
    """Build a lookup from (player_name_lower, season) → numeric NBA player_id
    using the backup CSVs that contain original NBA API player IDs."""
    backup_dir = os.path.join(DATA_DIR, "backup_csvs")
    lookup = {}
    if not os.path.isdir(backup_dir):
        return lookup
    import glob
    for path in glob.glob(os.path.join(backup_dir, "pure_ts_pct_league_*.csv")):
        season = os.path.basename(path).replace("pure_ts_pct_league_", "").replace(".csv", "")
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                name = _strip_accents(row.get("player_name") or "").lower()
                pid = row.get("player_id", "")
                if name and pid and pid.isdigit():
                    lookup[(name, season)] = pid
    return lookup


def compute_era_comparison(all_players):
    """Build the era comparison data for the Evidence tab."""
    nba_ids = _load_nba_id_lookup()
    results = []
    for player_name, season in ERA_COMPARISON_PLAYERS:
        players = all_players.get(season, [])
        target = _strip_accents(player_name).lower()
        match = None
        for p in players:
            candidate = _strip_accents(p.get("player_name") or "").lower()
            if candidate == target:
                match = p
                break
        if not match:
            continue
        fga = match.get("total_fga") or 0
        fga3 = match.get("total_fga3") or 0
        tpa_rate = round(fga3 / fga * 100, 1) if fga > 0 else None

        # Resolve player_id: prefer numeric NBA ID from backup lookup
        pid = match.get("player_id")
        if pid and not str(pid).replace(".", "").isdigit():
            nba_pid = nba_ids.get((target, season))
            if nba_pid:
                pid = nba_pid

        results.append({
            "player_name": match.get("player_name", player_name),
            "player_id": pid,
            "season": season,
            "tpa_rate": tpa_rate,
            "pure_ts_pct": match.get("pure_ts_pct"),
            "standard_ts_pct": match.get("standard_ts_pct"),
            "delta_pp": match.get("delta_pp"),
        })
    return results


def build_html(all_players, all_pergame, season_meta, seasons_list, comps,
               split_mode=False):
    """Generate the HTML by reading template and injecting data.

    When split_mode is True, pergame data is replaced with an empty dict
    and the template's PERGAME placeholder is set to {}.  The async
    loader injected into the template handles fetching per-season JSON
    files on demand.
    """
    era_comp = compute_era_comparison(all_players)

    template_path = os.path.join(SCRIPT_DIR, "template.html")
    with open(template_path) as f:
        html = f.read()
    html = html.replace("/*PLAYERS_DATA*/", json.dumps(all_players, ensure_ascii=False))

    if split_mode:
        # Empty pergame — loaded on demand via fetch
        html = html.replace("/*PERGAME_DATA*/", "{}")
    else:
        html = html.replace("/*PERGAME_DATA*/", json.dumps(all_pergame, ensure_ascii=False))

    html = html.replace("/*COMPS_DATA*/", json.dumps(comps))
    html = html.replace("/*SEASON_META*/", json.dumps(season_meta))
    html = html.replace("/*SEASONS_LIST*/", json.dumps(seasons_list))
    html = html.replace("/*ERA_COMPARISON*/", json.dumps(era_comp))

    from datetime import datetime
    build_date = datetime.now().strftime("%B %-d, %Y")
    html = html.replace("/*BUILD_DATE*/", build_date)

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DIST_DIR = os.path.join(SCRIPT_DIR, "dist")


def _load_all_seasons(data_dir):
    """Load all season data. Returns (all_players, all_pergame, season_meta, loaded_seasons)."""
    all_players = {}
    all_pergame = {}
    season_meta = {}
    loaded_seasons = []

    seasons = discover_seasons(data_dir)
    print(f"Discovered {len(seasons)} seasons\n")

    for season in seasons:
        csv_path = os.path.join(data_dir, f"pure_ts_pct_league_{season}.csv")
        pergame_path = os.path.join(data_dir, f"pure_ts_pct_league_pergame_{season}.csv")

        if not os.path.exists(csv_path):
            continue

        has_game_logs = os.path.exists(pergame_path)

        print(f"Loading {season}...", end=" ", flush=True)

        players = read_league_csv(csv_path)

        has_components = any(
            (p.get("C1a_events") or 0) > 0 for p in players
        )

        for p in players:
            enrich_player(p, has_components=has_components)

        pergame = read_pergame_csv(pergame_path) if has_game_logs else []

        is_playoffs = season.endswith("-PO")
        meta = compute_season_meta(players)
        meta["has_pbp"] = has_game_logs
        meta["has_components"] = has_components
        meta["is_playoffs"] = is_playoffs

        delta_str = f"{meta['avg_delta']:+.1f}pp" if meta['avg_delta'] is not None else "N/A"
        if has_components and has_game_logs:
            print(f"{len(players)} players, {len(pergame)} per-game rows loaded "
                  f"(avg delta: {delta_str})")
        elif has_components:
            print(f"{len(players)} players, components (no game logs) "
                  f"(avg delta: {delta_str})")
        else:
            print(f"{len(players)} players, box-score only "
                  f"(avg delta: {delta_str})")

        all_players[season] = players
        all_pergame[season] = pergame
        season_meta[season] = meta
        loaded_seasons.append(season)

    if not loaded_seasons:
        sys.exit("Error: No season data found. Check data/ directory.")

    print(f"\n{len(loaded_seasons)} seasons loaded: {', '.join(loaded_seasons)}")
    return all_players, all_pergame, season_meta, loaded_seasons


def main():
    parser = argparse.ArgumentParser(
        description="Build the PS%% League Viewer HTML (v2)."
    )
    parser.add_argument("--monolith", action="store_true",
                        help="Build single monolith HTML instead of split (slow, 495MB+)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help="Output HTML path (monolith mode only)")
    args = parser.parse_args()

    all_players, all_pergame, season_meta, loaded_seasons = _load_all_seasons(DATA_DIR)

    if not args.monolith:
        print("Building split output...")
        os.makedirs(os.path.join(DIST_DIR, "data"), exist_ok=True)

        # 1. Write per-season pergame JSON files (CDN seasons only)
        pergame_seasons = []
        for season in loaded_seasons:
            if not all_pergame.get(season):
                continue
            data_path = os.path.join(DIST_DIR, "data", f"{season}.json")
            with open(data_path, "w") as f:
                json.dump(all_pergame[season], f, ensure_ascii=False)
            size_kb = os.path.getsize(data_path) / 1024
            print(f"  {season}.json: {size_kb:.0f} KB ({len(all_pergame[season])} rows)")
            pergame_seasons.append(season)

        # 2. Build app shell HTML (no pergame data baked in)
        html = build_html(all_players, all_pergame, season_meta,
                          loaded_seasons, COMPONENTS, split_mode=True)

        index_path = os.path.join(DIST_DIR, "index.html")
        with open(index_path, "w") as f:
            f.write(html)
        size_kb = os.path.getsize(index_path) / 1024
        print(f"  index.html: {size_kb:.0f} KB ({size_kb/1024:.1f} MB)")

        # 3. Write Netlify _headers file
        current_season = loaded_seasons[0]  # newest season
        headers_lines = [
            "# Cache-Control for per-season game log JSON files",
            "/data/*.json",
            "  Access-Control-Allow-Origin: *",
            "",
        ]
        for season in pergame_seasons:
            if season == current_season:
                headers_lines.extend([
                    f"/data/{season}.json",
                    "  Cache-Control: public, max-age=3600",
                    "",
                ])
            else:
                headers_lines.extend([
                    f"/data/{season}.json",
                    "  Cache-Control: public, max-age=31536000, immutable",
                    "",
                ])
        headers_path = os.path.join(DIST_DIR, "_headers")
        with open(headers_path, "w") as f:
            f.write("\n".join(headers_lines) + "\n")
        print(f"  _headers: {len(pergame_seasons)} season rules")

        print(f"\nSplit output: {DIST_DIR}/")
        print(f"  index.html + {len(pergame_seasons)} JSON files + _headers")
        print(f"\nLocal testing: cd viewer/dist && python3 -m http.server 8500")
        print(f"  Then open http://localhost:8500")
    else:
        print("Building monolith HTML...")

        html = build_html(all_players, all_pergame, season_meta,
                          loaded_seasons, COMPONENTS)

        with open(args.output, "w") as f:
            f.write(html)

        size_kb = os.path.getsize(args.output) / 1024
        print(f"  Written: {args.output} ({size_kb:.0f} KB)")
        print(f"\nOpen in browser: file://{os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
