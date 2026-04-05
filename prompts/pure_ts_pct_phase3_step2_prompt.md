# Pure TS% — Phase 3 Step 2: Full League Season Run

## Objective

Build a script that runs Pure TS% for every active player in the NBA across the full 2025-26 season, producing a single consolidated dataset.

## Required Reading

- `CLAUDE.md` — Project overview and current file structure
- `docs/pure_ts_pct_terms_and_key.md` — Formula definitions
- `scripts/pure_ts_pct_season.py` — Phase 2 script (the core logic to reuse)
- `scripts/nba_active_roster.py` — Phase 3 Step 1 (produced the player list)
- `data/nba_active_players_2025-26.json` — The 576-player input list

## Script Specification

**Filename:** `scripts/pure_ts_pct_league.py`

### Inputs

- Player list: read from `data/nba_active_players_2025-26.json`
- Optional flags:
  - `--resume` — pick up where the last run left off (critical for a 500+ player job)
  - `--min-games N` — only include players with at least N games in the output (default: 0, include everyone)
  - `--min-possessions N` — only include players with at least N scoring possessions (useful for filtering out garbage time guys)

### Architecture: Two-Pass Approach

#### Pass 1 — Fetch All PBP Data

Before processing any players, pre-fetch all PBP JSON files needed for the season. This is smarter than fetching per-player because many players share games.

1. Collect all unique game IDs across all 576 players' game logs
2. Check which ones are already in `data/pbp_cache/`
3. Fetch only the missing ones, with 1-1.5 second delay between fetches
4. Log progress: "Fetching PBP data: 847/1031 cached, 184 to download..."

This turns a 40,000-fetch problem into a ~1,200-fetch problem (minus what's already cached). After Pass 1, everything runs from local cache.

**Resumability for Pass 1:** If interrupted, the next run with `--resume` just checks the cache again and picks up where it left off. Already-downloaded files don't need re-fetching.

#### Pass 2 — Process All Players

Loop through each player in the roster list:

1. Fetch their game log (same API call Phase 2 uses)
2. For each game, load PBP from local cache (already downloaded in Pass 1)
3. Run the Phase 2 classification and calculation logic
4. Store per-game and season-aggregate results
5. Log progress: "Processing player 214/576: Nikola Jokić (DEN)..."

**Resumability for Pass 2:** Save a progress file (`data/league_run_progress.json`) after each player completes. On `--resume`, skip already-processed players. This way a 6-hour run that crashes at player 400 doesn't have to restart from scratch.

**Error handling:** If a player fails (bad game log, PBP parse error, reconciliation mismatch), log the error with details, skip them, and continue. Report all failures at the end.

### Output Files

#### 1. League Summary CSV — `data/pure_ts_pct_league_2025-26.csv`

One row per player, columns:

- player_id, player_name, team_abbr, games_played
- total_pts, total_fga, total_fga2, total_fga3, total_fta, total_scoring_possessions
- pure_ts_pct, standard_ts_pct, delta
- Component counts: events and efficiency for each component (C1a, C1b, C2, C3, C4, C5, C6a-f)

Sort by total scoring possessions descending (highest volume players first).

#### 2. Per-Game Detail CSV — `data/pure_ts_pct_league_pergame_2025-26.csv`

One row per player-game, columns:

- player_id, player_name, team_abbr, game_id, game_date, opponent
- pts, fga, fta, scoring_possessions
- pure_ts_pct, standard_ts_pct, delta
- Component counts for that game

This is the full granular dataset — every scoring possession for every player in every game.

#### 3. League Run Log — `data/league_run_log.txt`

- Start/end timestamps
- Total players processed, total games processed
- Any failures with details
- Summary stats: mean/median Pure TS%, mean/median delta, etc.

### Rate Limiting and Performance

- Pass 1 (PBP fetches): 1-1.5 second delay between uncached fetches
- Pass 2 (game log fetches): 1 second delay between players for the game log API call
- Estimated total runtime for a cold run: 30-45 minutes for Pass 1 (fetching ~1000 PBP files), 15-20 minutes for Pass 2 (576 game log fetches + local processing)
- Re-runs with full cache: 15-20 minutes (Pass 2 only, no network for PBP)

### Progress Output

This is a long-running job. The user needs to see it's alive:

```
=== PASS 1: Fetching PBP Data ===
PBP cache: 169/1189 games cached, 1020 to fetch
Fetching game 0022500001... done (1/1020)
Fetching game 0022500002... done (2/1020)
...
PBP fetch complete. 1189 games cached.

=== PASS 2: Processing Players ===
[1/576] Shai Gilgeous-Alexander (OKC) — 58 games — Pure TS%: 61.0% — ✓
[2/576] Luka Dončić (LAL) — 57 games — Pure TS%: 52.1% — ✓
[3/576] Nikola Jokić (DEN) — 53 games — Pure TS%: 61.1% — ✓
...
[576/576] Complete.

=== SUMMARY ===
576 players processed, 0 failures
Output: data/pure_ts_pct_league_2025-26.csv (576 rows)
Output: data/pure_ts_pct_league_pergame_2025-26.csv (38,412 rows)
```

### Validation

After the run completes:

1. Spot check Luka, SGA, Jokic, LeBron season numbers against Phase 2 output — must match exactly
2. Verify league-wide totals are plausible:
   - Mean Pure TS% should be in the 48-55% range
   - Mean Standard TS% should be in the 55-60% range
   - Delta should be consistently negative (Standard > Pure for most players)
3. Check that total league PTS reconciles with publicly available season totals (ballpark check)

### Design Notes

- **Import, don't duplicate.** Reuse the core functions from `pure_ts_pct_single_game.py` and the season aggregation logic from `pure_ts_pct_season.py`.
- **Memory management.** Don't hold all 576 players' per-game data in memory at once. Process each player, write their rows to the output files, then move on.
- **Atomic writes.** Write to temporary files and rename on completion so a crash doesn't corrupt partial output.
- **The per-game CSV will be large** (~40,000 rows). That's fine for CSV — it'll open in Excel/Sheets without issues.
