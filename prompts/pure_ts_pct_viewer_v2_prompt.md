# Pure TS% Viewer — v2 Feature Additions

## Objective

Add three new views/tabs to the existing `viewer/pure_ts_league_viewer.html`. The data for all of these is already embedded in the HTML from the league CSV — no new data fetching or parsing required.

## Required Reading

- `viewer/pure_ts_league_viewer.html` — Current v1 viewer (understand the existing structure, data format, and styling)
- `viewer/build_viewer.py` — The build script that embeds CSV data into the HTML
- `docs/pure_ts_pct_terms_and_key.md` — Component definitions
- `data/pure_ts_pct_league_2025-26.csv` — Source data (check column names)
- `data/pure_ts_pct_league_pergame_2025-26.csv` — Per-game data (needed for the distortion games tab)

## What To Add

### Tab 1 — Foul Profile

Show how each player's scoring possessions break down by type. This answers: "How does this player score?"

**Display:** A table where each row is a player, and the columns show the percentage of their total scoring possessions that come from each component type. Group the components into readable categories:

| Column | What It Shows |
|--------|---------------|
| Clean 2PT % | FGA₂ / Total SP |
| Clean 3PT % | FGA₃ / Total SP |
| 2PT Shooting Fouls % | Amt_SF2 / Total SP |
| 3PT Shooting Fouls % | Amt_SF3 / Total SP |
| And-1s % | (Amt_A1₂ + Amt_A1₃) / Total SP |
| Penalty FTs % | (Amt_TF + Amt_FF + Amt_CP + Amt_TK + Amt_AP + Amt_BF) / Total SP |

Include a simple horizontal stacked bar for each player showing these proportions visually — so you can see at a glance that SGA is 60% clean 2PT while Luka is 40/40 split between 2PT and 3PT.

- Same search box and min possessions filter as the main table
- Sortable by any column
- Default sort by total scoring possessions descending

### Tab 2 — FT Efficiency by Type

Show each player's free throw make percentage broken out by the foul type that produced the free throws. This data doesn't exist anywhere publicly.

**Columns:**

| Column | Calculation |
|--------|-------------|
| Overall FT% | Total FTM / Total FTA (traditional) |
| Shooting Foul FT% | (PTS_SF2 + PTS_SF3) / (Amt_SF2 × 2 + Amt_SF3 × 3) |
| And-1 FT% | (A1₂ FTM + A1₃ FTM) / (Amt_A1₂ + Amt_A1₃) |
| Bonus Foul FT% | PTS_BF / (Amt_BF × 2) |
| Tech FT% | PTS_TF / Amt_TF |

Note: And-1 FT% needs to isolate just the free throw portion — the made basket is guaranteed, so And-1 FTM = PTS_A1₂ - (Amt_A1₂ × 2) for 2PT and PTS_A1₃ - (Amt_A1₃ × 3) for 3PT. The denominator is just the count of and-1 events since each produces exactly 1 FTA.

- Show N/A or "—" for any foul type where the player has 0 events (can't compute %)
- Same search/filter controls
- Color code cells: green for high FT%, red for low
- Sortable by any column

### Tab 3 — Biggest Distortion Games

Show individual player-games where the gap between Pure TS% and Standard TS% was largest. These are the games where the 0.44 coefficient failed hardest.

**Data source:** This requires the per-game CSV (`data/pure_ts_pct_league_pergame_2025-26.csv`). The build script will need to embed this data too — it's 22,395 rows but that's still manageable in a single HTML file (probably adds 2-3 MB). If that feels too heavy, filter to only games with |delta| >= 8 pp before embedding.

**Columns:** Player, Team, Date, Opponent, PTS, FGA, FTA, Scoring Possessions, Pure TS%, Standard TS%, Delta

- Default sort by |Delta| descending (biggest distortions first)
- Min possessions filter (per game — maybe default to 10 to exclude garbage time appearances)
- Search by player name or team
- Show top 100 or 200 by default with a "show more" button

### Tab Navigation

Add a simple tab bar at the top of the page:

- **Rankings** (current main table — rename from the default view)
- **Foul Profile**
- **FT by Type**
- **Distortion Games**

All tabs share the same search box and min possessions filter where applicable. Switching tabs should feel instant.

### Build Script Update

Update `build_viewer.py` to also embed:
- The per-game CSV data (for the distortion games tab)
- Pre-calculate the foul profile percentages and FT-by-type percentages during the build step so the HTML doesn't need to compute them at runtime

### Styling

- Match the existing dark theme, color coding, and typography from v1
- Stacked bars in the foul profile tab should use distinct but harmonious colors for each component type
- Keep everything feeling like one cohesive tool, not bolted-on additions

### Validation

- Foul Profile: SGA should show ~60% clean 2PT, ~19% clean 3PT. Luka should show ~40% clean 2PT, ~40% clean 3PT.
- FT by Type: Verify a few players' numbers against the Phase 2 season output we already validated
- Distortion Games: The Luka vs HOU March 18 game (-12.6 pp delta) should appear near the top
