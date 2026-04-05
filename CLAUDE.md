# CLAUDE.md — Pure Shooting Percentage Project

## Project Overview

**Pure Shooting % (PS%)** is an NBA shooting efficiency metric: `PTS / (2×FGA + 3PA + FTA)`. Points scored divided by max possible points. It replaces standard TS% (`PTS / (2 × (FGA + 0.44 × FTA))`), which uses an arbitrary coefficient and a denominator that breaks on 3-pointers. PS% is simpler, exact, and bounded at 0–100%.

## Why This Exists

The standard TS% formula `PTS / (2 × (FGA + 0.44 × FTA))` has two flaws:

1. **The "2" denominator (fatal):** By treating every attempt as worth max 2 points, TS% breaks on 3-pointers. A perfect 3PT shooter gets 150% TS%; a perfect 2PT shooter gets 100%. The distortion averages ~9-10pp and correlates almost perfectly with 3PT attempt rate — making cross-archetype comparisons meaningless.
2. **The 0.44 coefficient (minor):** A league-wide approximation for possessions consumed by FTs. Actual value is ~0.453; mean error is only +0.19pp. This is what everyone criticizes, but it's the least broken part.

PS% fixes both. See `docs/the_problem.md` for the full analysis.

## Core Architecture

### The Formula

```
PS% = PTS / (2×FGA + 3PA + FTA)
```

Four standard box score numbers. No approximations, no arbitrary coefficients. Every 2PT FGA has a max of 2 points, every 3PT FGA adds 1 more (the extra point a 3 is worth beyond 2), and every FTA has a max of 1 point. The result is a true 0–100% scale where 100% means the player scored every possible point.

Compare to standard TS%: `PTS / (2 × (FGA + 0.44 × FTA))`. Same numerator, but TS% uses a universal "2" that breaks on 3-pointers and an arbitrary 0.44 coefficient. PS% replaces both with exact arithmetic.

### Component Derivation

The formula was derived from first principles by classifying every scoring possession into 12 components (C1a–C6f) via play-by-play data — see `docs/pure_ts_pct_terms_and_key.md`. This derivation proves the formula is correct and powers diagnostic breakdowns (efficiency by foul type, And-1 rates, hidden possessions). The headline number is the simple box score formula above.

### Key Concepts

- **Max Possible Points**: The denominator — the total points a player could have scored. `2×FGA + 3PA + FTA`.
- **Scoring Possession** (diagnostic only): A single scoring event. Broader than FGA — includes shooting fouls, bonus fouls, etc. Used in the PBP component breakdown but not needed for the headline formula.
- See `pure_ts_pct_terms_and_key.md` for component definitions and the full derivation.

## Data Requirements

- NBA play-by-play event data (JSON or similar structured format)
- Must be able to identify event types: field goal attempts, shooting fouls, And-1s, technical fouls, flagrant fouls
- Must distinguish 2PT vs 3PT attempts
- Must link free throw events back to the foul that caused them

## File Structure

```
CLAUDE.md                        — This file (project context for Claude Code)

docs/
  pure_ts_pct_terms_and_key.md   — Formula terms, symbols, component definitions (C1–C6f)
  pure_ts_pct_proof_of_concept.md— Validated single-game example (Luka vs HOU, Mar 18 2026)
  the_problem.md                 — Analysis of TS% flaws (the "2" denominator, the 0.44)
  future_stats_brainstorm.md     — Ideas for metrics beyond PS%

prompts/
  pure_ts_pct_phase1_prompt.md   — Phase 1 spec: single-game calculator
  pure_ts_pct_phase2_prompt.md   — Phase 2 spec: full-season calculator
  pure_ts_pct_phase3_step1_prompt.md — Phase 3 step 1 spec: active player roster

scripts/
  pure_ts_pct_single_game.py     — Phase 1: single player, single game (core CDN PBP parser)
  pure_ts_pct_season.py          — Phase 2: single player, full season (imports Phase 1)
  pure_ts_pct_league.py          — Phase 3: all players, full season
  pure_ts_pct_historical.py      — Multi-season batch pipeline (6 CDN seasons)
  daily_update.py                — Incremental daily update (~30-40 sec)
  nba_active_roster.py           — Active player roster utility
  pull_tracking_data.py          — Fetches tracking data CSVs from stats.nba.com
  scrape_bbref_pbp.py            — BBRef PBP scraper (resumable, rate-limited)
  bbref_pbp_parser.py            — BBRef PBP adapter/classifier (12-component, matches CDN parser output)
  bbref_batch_seasons.py         — Batch runner for BBRef seasons (--playoffs flag for playoff data)
  bbref_batch_pergame.py         — Batch runner for BBRef per-game logs (--playoffs flag)
  pull_historical_playoffs.py    — NBA API playoff box score puller (1979-80 through 1995-96)
  build_one_pager.py             — PDF one-pager generator

viewer/
  template.html                  — HTML/CSS/JS template with /*PLACEHOLDER*/ markers
  build_viewer.py                — Build script: reads CSVs, enriches data, outputs split or monolith
  dist/                          — Split build output (default build target, deploy to Netlify)
    index.html                   — App shell (~4.1 MB gzipped): all player data baked in, no pergame
    data/                        — 59 per-season JSON files loaded on demand (30 RS + 29 PO game logs)
    _headers                     — Netlify cache configuration
  pure_ts_league_viewer.html     — Monolith output (--monolith flag only, ~583 MB, do NOT deploy)

audits/                          — Completed stat audit documents (TS%, PER, etc.)

data/
  pbp_cache/                     — Cached CDN PBP JSON files (one per game, 6 seasons, ~2.9 GB)
  bbref_pbp_cache/               — Cached BBRef PBP JSON files (one per game, 24 seasons + playoffs, ~4.1 GB)
  bbref_game_ids/                — Game ID lists per season (regular season + playoff URL files)
  tracking/                      — 15 NBA tracking data CSVs (passing, drives, shot quality, etc.)
  league_results/                — Per-player result JSONs (CDN pipeline, regenerable)
  backup_csvs/                   — Pre-BBRef-integration CSV backups (name/ID reference)
  *.csv                          — Season + pergame CSVs (93 seasons: 47 RS + 46 PO)
```

## Build & Deploy

### Building the Viewer

```bash
# Default: split build → viewer/dist/ (app shell + per-season JSON files)
python3 viewer/build_viewer.py

# Local testing (split build requires HTTP server for fetch):
cd viewer/dist && python3 -m http.server 8500
# Open http://localhost:8500

# Monolith: single ~583 MB HTML file (local-only, slow to load)
python3 viewer/build_viewer.py --monolith
```

### Split Architecture

The default build produces a split output for Netlify deployment:

- **`viewer/dist/index.html`** (~4.1 MB gzipped): App shell with all 93 seasons of player-level data baked in. All tabs work instantly except All Game Logs.
- **`viewer/dist/data/*.json`** (59 files): Per-season pergame data, fetched on demand when a user opens the All Game Logs tab. Historical seasons are immutable (`Cache-Control: max-age=31536000`); current season refreshes hourly.
- **`viewer/dist/_headers`**: Netlify cache rules.

### Daily Updates

```bash
python3 scripts/daily_update.py          # Update current season (~30-40 sec)
python3 viewer/build_viewer.py           # Rebuild split output
```

## Current Status

### Completed
- All 12 components defined (C1a, C1b, C2, C3, C4, C5, C6a–C6f)
- Formula simplified to `PTS / (2×FGA + 3PA + FTA)` — box score formula, no PBP needed for headline number
- Phase 1: Single-game script — validated against proof of concept
- Phase 2: Full-season script — validated across 163 games (Luka, SGA, LeBron)
- Phase 3: League-wide script — all players, full season
- **93 seasons of data** — 47 regular season (1979-80 through 2025-26) + 46 playoff (1979-80 through 2024-25)
  - 30 RS seasons with full component data (6 CDN + 24 BBRef, 1996-97 through 2025-26)
  - 17 RS seasons box-score-only (1979-80 through 1995-96, NBA API)
  - 29 PO seasons with full components + game logs (1996-97 through 2024-25, BBRef)
  - 17 PO seasons box-score-only (1979-80 through 1995-96, NBA API)
- Daily incremental update script (~30-40 sec) for current season
- Interactive viewer: multi-season support, "All Seasons" cross-era view, column manager, drag-and-drop reorder, filters, CSV export
- **Charts tab**: scatter plot (with headshots toggle), histogram (with mean/median lines), 47-season trends line chart, scoring composition stacked bars
- **Monolith split**: app shell (~4.1 MB gzipped initial load) + 59 on-demand JSON data files (30 RS + 29 PO game logs)
- **BBRef PBP adapter** (`bbref_pbp_parser.py`): classifies BBRef PBP into 12 PS% components. 100% cross-validated against CDN parser on 58 player-games across 3 overlapping games. 0% crash rate across 28,463 regular season + 2,350 playoff games.
- **Playoff integration**: 46 playoff seasons surfaced as separate dropdown entries (e.g., "2023-24 Playoffs"). Excluded from "All Seasons" mode and Trends chart. Slider defaults to min 100 for playoff seasons (vs 500 for RS).
- 2019-20 bubble playoffs recovered: 78 games were already cached, just needed game ID reclassification
- One-pager PDF (`docs/pure_ts_one_pager.pdf`)
- Regression analysis: R²=0.9986 — 3PA rate explains 99.86% of TS% distortion
- 15 tracking data CSVs pulled from stats.nba.com
- 11 stat audits completed (key finding: TS%'s "2" denominator is the fatal flaw, not the 0.44)
- About tab restructured into 4 sub-tabs (The Problem, Methodology, Historical Evidence, Cross-Era Comparison)
- "Last updated" timestamp auto-generated at build time
- `.gitignore` configured: excludes PBP caches (~7 GB), monolith, and regenerable artifacts

### Pending
- Deploy: push to GitHub (Umbreon77), connect to Netlify, launch
- 2025-26 playoffs (waiting for season to progress)
- Viewer enhancements from `docs/outstanding_consolidated.md` (player comparison tool, exportable chart PNGs, position filter)

### Not Started
- Future metrics from brainstorm doc

## Design Principles

1. **No approximations** — points scored divided by max possible points, using exact box score numbers
2. **Max possible points, not possessions** — the denominator is `2×FGA + 3PA + FTA`, the total points that could have been scored
3. **True percentage scale** — output is 0% to 100%, bounded and meaningful. Unlike standard TS%, it cannot exceed 100%
4. **Component diagnostics** — PBP-derived breakdowns (foul profiles, FT by type) provide analytical depth beyond the headline number

## Agent Policy

**NEVER invoke agents (any subagent_type) without explicit user confirmation in the current message.** Default to direct tools (WebSearch, WebFetch, Grep, Glob, Read, Bash, etc.) for all tasks. Only spawn an agent if the user explicitly says to use one.

## Important Notes

- Assisted vs unassisted does not matter for this metric — we measure the shooter's efficiency only
- An offensive rebound leading to a new shot attempt is a new FGA — naturally handled by the formula
- The formula is pure arithmetic — no weighting, no event classification needed for the headline number
- When writing scripts, always reference `docs/pure_ts_pct_terms_and_key.md` for canonical variable names and definitions
- All scripts live in `scripts/` and use relative paths (`../data/`) for cache and output
- Run scripts from the project root: `python3 scripts/pure_ts_pct_season.py "Player Name"`
