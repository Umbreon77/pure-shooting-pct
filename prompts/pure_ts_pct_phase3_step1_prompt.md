# Pure TS% — Phase 3 Step 1: Active Player Roster

## Objective

Build a small utility script that pulls all active NBA players for the current season and outputs a clean roster list. This will serve as the input list for the Phase 3 full-league Pure TS% run.

## Required Reading

- `CLAUDE.md` — Project overview
- `pure_ts_pct_season.py` — Phase 2 script (already uses the `commonallplayers` endpoint for name resolution — reuse that logic)

## Script Specification

**Filename:** `nba_active_roster.py`

### Data Source

Use the NBA stats API endpoint:

```
https://stats.nba.com/stats/commonallplayers?LeagueID=00&Season=2025-26&IsOnlyCurrentSeason=1
```

This is the same endpoint Phase 2 already hits for name resolution. Set appropriate headers (User-Agent, Referer) to avoid 403 blocks — copy whatever headers Phase 2 uses since those already work.

### Output

A clean JSON file: `nba_active_players_2025-26.json`

Each entry should include:

- `player_id` — NBA person ID (used by the PBP and game log APIs)
- `player_name` — Full name (e.g., "Luka Dončić")
- `team_abbr` — Current team abbreviation (e.g., "LAL")
- `team_name` — Full team name (e.g., "Los Angeles Lakers")

### Filters

- Only players who have actually appeared in a game this season (not just on a roster). The game log endpoint will return nothing for players who haven't played, but filtering upfront saves wasted API calls in Phase 3.
- If the API doesn't distinguish between "rostered" and "has played," that's fine — Phase 3 will handle zero-game players gracefully.

### Also Output

- Print total player count to terminal
- Optionally support `--csv` flag to also output as `nba_active_players_2025-26.csv` for easy viewing in Excel/Sheets

### Validation

- Total player count should be in the 450-550 range for a typical NBA season
- Spot check a few known players: Luka Dončić (LAL), Shai Gilgeous-Alexander (OKC), Nikola Jokić (DEN), LeBron James (LAL)
- Verify player IDs match what Phase 2 resolved (e.g., Luka = 1629029)

### Design Notes

- Keep it simple — this is a utility script, not a framework
- The JSON output should be directly consumable by a future Phase 3 script that loops through it
