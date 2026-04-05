#!/usr/bin/env python3
"""
Collect PBP game IDs from Basketball Reference for seasons 1996-97 through 2019-20.
Splits each season into regular season and playoff files.
Skips NBA_1998 (already done).
"""

import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "bbref_game_ids")
os.makedirs(OUT_DIR, exist_ok=True)

# Standard months for most seasons
STANDARD_MONTHS = ["october", "november", "december", "january", "february",
                   "march", "april", "may", "june"]

# Special month lists for unusual seasons
SEASON_MONTHS = {
    1999: ["february", "march", "april", "may", "june"],  # lockout, started Feb
    2012: ["december", "january", "february", "march", "april", "may", "june"],  # lockout, started Dec 2011
    2020: ["october", "november", "december", "january", "february", "march",
           "july", "august", "september", "october"],  # COVID bubble
}

BASE_URL = "https://www.basketball-reference.com/leagues/NBA_{}_games-{}.html"
DELAY = 4  # seconds between requests


def to_pbp_url(boxscore_href):
    return "https://www.basketball-reference.com" + boxscore_href.replace(
        "/boxscores/", "/boxscores/pbp/"
    )


def fetch_season(yyyy):
    """Fetch all monthly schedule pages for a season, return (reg, playoff) URL lists."""
    months = SEASON_MONTHS.get(yyyy, STANDARD_MONTHS)
    all_reg = []
    all_playoff = []
    playoffs_started = False  # persists across months

    for month in months:
        url = BASE_URL.format(yyyy, month)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
        except Exception as e:
            print(f"    {month}: ERROR ({e})")
            time.sleep(DELAY)
            continue

        if resp.status_code == 404:
            # Skip months with no games
            time.sleep(DELAY)
            continue

        if resp.status_code != 200:
            print(f"    {month}: HTTP {resp.status_code}")
            time.sleep(DELAY)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        sched_table = soup.find("table", id="schedule")

        if not sched_table:
            time.sleep(DELAY)
            continue

        month_reg = []
        month_playoff = []
        seen = set()

        for row in sched_table.find_all("tr"):
            # Check for Playoffs header
            th = row.find("th", colspan=True)
            if th and "Playoffs" in th.get_text():
                playoffs_started = True
                continue

            # Extract box score link
            for a in row.find_all("a", href=True):
                href = a["href"]
                if re.match(r"/boxscores/\d{9}\w+\.html$", href) and href not in seen:
                    seen.add(href)
                    if playoffs_started:
                        month_playoff.append(href)
                    else:
                        month_reg.append(href)

        all_reg.extend(month_reg)
        all_playoff.extend(month_playoff)

        reg_str = f"{len(month_reg)}r" if month_reg else ""
        po_str = f"{len(month_playoff)}p" if month_playoff else ""
        count_str = "+".join(filter(None, [reg_str, po_str])) or "0"
        print(f"    {month:12s} {count_str}", flush=True)

        time.sleep(DELAY)

    return all_reg, all_playoff


def main():
    seasons = list(range(1997, 2021))  # NBA_1997 through NBA_2020

    results = []

    for yyyy in seasons:
        season_label = f"NBA_{yyyy}"
        display = f"{yyyy-1}-{str(yyyy)[2:]}"
        print(f"\n{season_label} ({display}):", flush=True)

        reg_links, po_links = fetch_season(yyyy)

        reg_urls = [to_pbp_url(l) for l in reg_links]
        po_urls = [to_pbp_url(l) for l in po_links]

        # Save
        reg_path = os.path.join(OUT_DIR, f"{season_label}_regular_season_pbp_urls.txt")
        po_path = os.path.join(OUT_DIR, f"{season_label}_playoffs_pbp_urls.txt")

        with open(reg_path, "w") as f:
            for u in reg_urls:
                f.write(u + "\n")
        with open(po_path, "w") as f:
            for u in po_urls:
                f.write(u + "\n")

        print(f"  => {len(reg_urls)} regular season, {len(po_urls)} playoffs", flush=True)
        results.append((yyyy, len(reg_urls), len(po_urls)))

    # Sort results by year
    results.sort()

    # Grand total table
    print(f"\n{'='*60}")
    print(f"{'Season':<12} {'Reg Season':>12} {'Playoffs':>10} {'Total':>8}")
    print(f"{'-'*12} {'-'*12} {'-'*10} {'-'*8}")
    total_reg = 0
    total_po = 0
    for yyyy, reg, po in results:
        display = f"{yyyy-1}-{str(yyyy)[2:]}"
        print(f"{display:<12} {reg:>12} {po:>10} {reg+po:>8}")
        total_reg += reg
        total_po += po
    print(f"{'-'*12} {'-'*12} {'-'*10} {'-'*8}")
    print(f"{'TOTAL':<12} {total_reg:>12} {total_po:>10} {total_reg+total_po:>8}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
