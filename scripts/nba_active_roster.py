#!/usr/bin/env python3
"""
NBA Active Roster — Utility Script

Pulls all active NBA players for the current season and outputs a clean
roster list as JSON (and optionally CSV).

Usage:
    python scripts/nba_active_roster.py
    python scripts/nba_active_roster.py --season 2025-26 --csv
"""

import argparse
import csv
import json
import os
import sys
import urllib.request

NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nba.com/",
    "Accept": "application/json",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_all_players(season="2025-26"):
    """
    Fetch all active players for the season from commonallplayers endpoint.

    Returns a list of dicts: [{player_id, player_name, team_abbr, team_name}, ...]
    """
    url = (
        "https://stats.nba.com/stats/commonallplayers"
        f"?LeagueID=00&Season={season}&IsOnlyCurrentSeason=1"
    )
    req = urllib.request.Request(url, headers=NBA_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    rs = data["resultSets"][0]
    headers = rs["headers"]
    col = {h: i for i, h in enumerate(headers)}

    players = []
    for row in rs["rowSet"]:
        # Filter: only players flagged as having played
        if row[col["GAMES_PLAYED_FLAG"]] != "Y":
            continue

        team_city = row[col["TEAM_CITY"]] or ""
        team_name_short = row[col["TEAM_NAME"]] or ""
        full_team = f"{team_city} {team_name_short}".strip()

        players.append({
            "player_id": row[col["PERSON_ID"]],
            "player_name": row[col["DISPLAY_FIRST_LAST"]],
            "team_abbr": row[col["TEAM_ABBREVIATION"]] or "",
            "team_name": full_team,
        })

    # Sort by team, then name
    players.sort(key=lambda p: (p["team_abbr"], p["player_name"]))
    return players


def save_json(players, season):
    """Save player list as JSON."""
    filename = os.path.join(DATA_DIR, f"nba_active_players_{season}.json")
    with open(filename, "w") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    print(f"  JSON saved: {filename}")
    return filename


def save_csv_file(players, season):
    """Save player list as CSV."""
    filename = os.path.join(DATA_DIR, f"nba_active_players_{season}.csv")
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "player_name", "team_abbr", "team_name"])
        for p in players:
            writer.writerow([
                p["player_id"], p["player_name"],
                p["team_abbr"], p["team_name"],
            ])
    print(f"  CSV saved:  {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(
        description="Pull active NBA player roster for a season."
    )
    parser.add_argument(
        "--season", default="2025-26",
        help="NBA season (e.g. 2025-26). Default: 2025-26",
    )
    parser.add_argument(
        "--csv", action="store_true",
        help="Also export as CSV",
    )
    args = parser.parse_args()

    print(f"Fetching active players for {args.season}...")
    players = fetch_all_players(args.season)
    print(f"  {len(players)} active players found.\n")

    # Spot checks
    spot_checks = {
        1629029: ("Luka Dončić", "LAL"),
        1628983: ("Shai Gilgeous-Alexander", "OKC"),
        203999: ("Nikola Jokić", "DEN"),
        2544: ("LeBron James", "LAL"),
    }
    print("  Spot checks:")
    for pid, (expected_name, expected_team) in spot_checks.items():
        match = next((p for p in players if p["player_id"] == pid), None)
        if match:
            ok = expected_team == match["team_abbr"]
            print(f"    {match['player_name']:<30} {match['team_abbr']:<5} "
                  f"ID={pid}  {'OK' if ok else 'TEAM MISMATCH'}")
        else:
            print(f"    {expected_name:<30} NOT FOUND (expected ID {pid})")
    print()

    # Team summary
    teams = {}
    for p in players:
        teams[p["team_abbr"]] = teams.get(p["team_abbr"], 0) + 1
    print(f"  {len(teams)} teams, "
          f"avg {len(players) / len(teams):.1f} players per team\n")

    # Save
    os.makedirs(DATA_DIR, exist_ok=True)
    save_json(players, args.season)
    if args.csv:
        save_csv_file(players, args.season)

    print()


if __name__ == "__main__":
    main()
