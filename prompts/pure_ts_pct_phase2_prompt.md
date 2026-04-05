# Pure TS% — Phase 2 Script Prompt

## Objective

Build a Python script that calculates Pure TS% for a single player across an entire NBA season — both per-game breakdowns and a season-level aggregate.

## Required Reading

Read these project files first for full context:

- `pure_ts_pct_terms_and_key.md` — All component definitions, symbols, and the formula
- `pure_ts_pct_proof_of_concept.md` — Validated single-game example
- `pure_ts_pct_single_game.py` — Phase 1 script (reuse its core functions)
- `CLAUDE.md` — Project overview and design principles

## Script Specification

**Filename:** `pure_ts_pct_season.py`

### Inputs

- Player name (e.g., `"Luka Doncic"`)
- Season (e.g., `2025-26` — optional, default to current season)
- Optional flags:
  - `--per-game` — output a row for every game (default: just show season totals)
  - `--save-csv` — export per-game results to a CSV file
  - `--save-json` — export raw component data to JSON for further analysis

### Step 1: Find All Game IDs for the Player's Season

Use the NBA stats API to get the player's game log. Possible endpoints:

- `https://stats.nba.com/stats/playergamelog?PlayerID={id}&Season=2025-26&SeasonType=Regular+Season`
- Or scrape the schedule from `https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json` and filter by team

From the game log, extract every game ID the player appeared in. Handle the game ID format — NBA stats uses `002250XXXX` format, same as the PBP endpoint.

**Important:** Respect rate limits on the NBA API. Add a delay between requests (1-2 seconds between game fetches). Print progress so the user knows it's working (e.g., "Processing game 14/69...").

### Step 2: Run Phase 1 Logic on Each Game

For each game ID, reuse the core functions from `pure_ts_pct_single_game.py`:

- Fetch play-by-play JSON from NBA CDN
- Classify scoring events into components
- Calculate per-game Pure TS% and Standard TS%
- Reconcile against box score totals

If a game fails to fetch or reconcile, log the error and skip it — don't crash the whole run. Track which games succeeded and which failed.

### Step 3: Aggregate Season Totals

**Critical: Do NOT average the per-game percentages.** A 2-point game and a 40-point game should not be weighted equally.

Instead, sum the raw component counts across all games:

```
Season_FGA₂ = sum of FGA₂ from every game
Season_PTS₂ = sum of PTS₂ from every game
Season_Amt_SF2 = sum of Amt_SF2 from every game
... (same for all components)
```

Then calculate season Pure TS% from these aggregated totals using the same weighted average formula. This gives a possession-weighted season number.

Also calculate season Standard TS% from aggregated PTS, FGA, FTA.

### Output

#### Season Summary (always shown)
- Player name, team, season, games played
- Season totals: PTS, FGA, FGA₂, FGA₃, FTA, scoring possessions
- Season component breakdown table (same format as Phase 1 but aggregated)
- Season Pure TS%
- Season Standard TS%
- Delta

#### Per-Game Table (with `--per-game` flag)
One row per game showing:
- Date, opponent, PTS, FGA, FTA
- Scoring possessions
- Pure TS%, Standard TS%, Delta
- Sort by date

Highlight games where the delta exceeds ±10 pp — these are the "distortion games" where the 0.44 coefficient fails hardest.

#### CSV Export (with `--save-csv` flag)
Export the per-game table to `{player_name}_pure_ts_2025-26.csv`

#### JSON Export (with `--save-json` flag)
Export full component-level data for every game to `{player_name}_pure_ts_2025-26.json` — this is the raw dataset for future analysis.

### Design Notes

- **Reuse Phase 1 functions.** Import `classify_scoring_events`, `calculate_pure_ts`, and `box_score_from_components` from `pure_ts_pct_single_game.py`. Do not duplicate this logic.
- **Rate limiting.** 1-2 second delay between NBA CDN fetches. The full season is ~70-82 games, so a run takes ~2-3 minutes. That's fine.
- **Progress output.** Print which game is being processed and running totals so the user knows it's working.
- **Error resilience.** If a single game fails (network error, parsing error, reconciliation mismatch), log it and continue. Report failures at the end.
- **Cache-friendly.** Consider saving fetched PBP JSON files to a local cache directory so re-runs don't re-fetch everything. Optional but nice to have.

### Validation

Run the script for Luka Doncic 2025-26 season. Verify:

1. The LAL @ HOU March 18 game row matches the proof of concept (51.6% Pure TS%, 64.2% Std TS%)
2. Season FGA + FTA + PTS totals are in the right ballpark vs publicly available season stats
3. The season Pure TS% is a plausible number (probably in the 50-60% range for most players)
4. All per-game weights sum to 1.0 when computed from season aggregates

Then run it for one or two other players (LeBron James, Shai Gilgeous-Alexander) to make sure it generalizes.

## Future Phase (not in scope, but keep in mind)

- **Phase 3:** All players, full season — wrap Phase 2 in a loop across every player in the league. That's a separate prompt.
