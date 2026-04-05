#!/usr/bin/env python3
"""
Pull playoff box scores from NBA API for 1979-80 through 1995-96.

Uses LeagueLeaders endpoint with SeasonType=Playoffs (works for all eras).
Outputs box-score-only CSVs matching existing format.

Usage:
    python3 scripts/pull_historical_playoffs.py
"""

import csv
import os
import sys
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

SEASONS = [
    "1979-80", "1980-81", "1981-82", "1982-83", "1983-84",
    "1984-85", "1985-86", "1986-87", "1987-88", "1988-89",
    "1989-90", "1990-91", "1991-92", "1992-93", "1993-94",
    "1994-95", "1995-96",
]

CSV_COLUMNS = [
    "player_id", "player_name", "team_abbr", "games_played",
    "total_pts", "total_fga", "total_fga2", "total_fga3",
    "total_fta", "total_scoring_poss",
    "pure_ts_pct", "standard_ts_pct", "delta_pp",
    "total_fgm", "total_fg3m", "total_ftm",
]


def fetch_season_playoffs(season):
    """Fetch playoff player stats for one season via LeagueLeaders."""
    from nba_api.stats.endpoints import leagueleaders

    resp = leagueleaders.LeagueLeaders(
        season=season,
        season_type_all_star="Playoffs",
        stat_category_abbreviation="PTS",
        per_mode48="Totals",
        timeout=120,
    )
    data = resp.get_dict()
    rs = data["resultSet"]
    headers = rs["headers"]
    col = {h: i for i, h in enumerate(headers)}

    rows = []
    for r in rs["rowSet"]:
        pid = r[col["PLAYER_ID"]]
        name = r[col["PLAYER"]]
        team = r[col["TEAM"]]
        gp = r[col["GP"]]
        pts = r[col["PTS"]]
        fgm = r[col["FGM"]]
        fga = r[col["FGA"]]
        fg3m = r[col["FG3M"]]
        fg3a = r[col["FG3A"]]
        ftm = r[col["FTM"]]
        fta = r[col["FTA"]]

        fga2 = fga - fg3a
        max_pts = 2 * fga + fg3a + fta
        ps_pct = round(pts / max_pts * 100, 2) if max_pts > 0 else 0
        ts_denom = 2 * (fga + 0.44 * fta)
        ts_pct = round(pts / ts_denom * 100, 2) if ts_denom > 0 else 0
        delta = round(ps_pct - ts_pct, 2)

        rows.append({
            "player_id": pid,
            "player_name": name,
            "team_abbr": team,
            "games_played": gp,
            "total_pts": pts,
            "total_fga": fga,
            "total_fga2": fga2,
            "total_fga3": fg3a,
            "total_fta": fta,
            "total_scoring_poss": 0,
            "pure_ts_pct": ps_pct,
            "standard_ts_pct": ts_pct,
            "delta_pp": delta,
            "total_fgm": fgm,
            "total_fg3m": fg3m,
            "total_ftm": ftm,
        })

    rows.sort(key=lambda r: -r["total_pts"])
    return rows


def main():
    total_seasons = 0
    total_players = 0

    for season in SEASONS:
        csv_label = f"{season}-PO"
        path = os.path.join(DATA_DIR, f"pure_ts_pct_league_{csv_label}.csv")

        # Skip if already exists
        if os.path.exists(path):
            with open(path) as f:
                existing = len(list(csv.DictReader(f)))
            if existing > 0:
                print(f"{season} Playoffs: already exists ({existing} players)")
                total_seasons += 1
                total_players += existing
                continue

        print(f"Fetching {season} Playoffs...", end=" ", flush=True)
        try:
            rows = fetch_season_playoffs(season)
        except Exception as e:
            print(f"FAILED: {e}")
            time.sleep(3)
            continue

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        total_gp = sum(r["games_played"] for r in rows)
        print(f"{len(rows)} players, {total_gp} total GP")
        total_seasons += 1
        total_players += len(rows)
        time.sleep(1.5)

    print(f"\n{total_seasons} seasons, {total_players} total players")


if __name__ == "__main__":
    main()
