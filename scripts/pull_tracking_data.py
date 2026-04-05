#!/usr/bin/env python3
"""
Pull all NBA Tracking data from stats.nba.com via nba_api.

Uses the LeagueDashPtStats endpoint with each PtMeasureType to pull
full-league season totals for every tracking category. Saves each
as a separate CSV in data/tracking/.

Usage:
    python scripts/pull_tracking_data.py
"""

import csv
import os
import sys
import time

from nba_api.stats.endpoints import leaguedashptstats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "tracking")

SEASON = "2025-26"
SEASON_TYPE = "Regular Season"
DELAY = 3  # seconds between API calls

# All available PtMeasureType values
MEASURE_TYPES = [
    "Passing",
    "Possessions",
    "CatchShoot",
    "Defense",
    "Drives",
    "Efficiency",
    "ElbowTouch",
    "PaintTouch",
    "PostTouch",
    "PullUpShot",
    "Rebounding",
    "SpeedDistance",
]


def pull_measure(measure_type):
    """Pull one tracking measure type, return (headers, rows)."""
    resp = leaguedashptstats.LeagueDashPtStats(
        pt_measure_type=measure_type,
        player_or_team="Player",
        per_mode_simple="Totals",
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
    )
    data = resp.get_dict()
    rs = data["resultSets"][0]
    return rs["headers"], rs["rowSet"]


def save_csv(headers, rows, filename):
    """Save headers + rows to CSV."""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Pulling NBA Tracking data for {SEASON}")
    print(f"  {len(MEASURE_TYPES)} measure types, {DELAY}s delay between calls\n")

    results = {}

    for i, mt in enumerate(MEASURE_TYPES):
        if i > 0:
            print(f"  (waiting {DELAY}s...)")
            time.sleep(DELAY)

        filename = mt.lower() + f"_{SEASON}.csv"
        print(f"[{i+1}/{len(MEASURE_TYPES)}] {mt}...", end=" ", flush=True)

        try:
            headers, rows = pull_measure(mt)
            path = save_csv(headers, rows, filename)
            results[mt] = {"headers": headers, "rows": len(rows), "path": path}
            print(f"{len(rows)} players")
            print(f"    Columns: {headers}")
        except Exception as e:
            print(f"FAILED: {e}")
            results[mt] = {"error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for mt, info in results.items():
        if "error" in info:
            print(f"  {mt}: FAILED — {info['error']}")
        else:
            print(f"  {mt}: {info['rows']} players, {len(info['headers'])} columns")
    print(f"\nFiles saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
