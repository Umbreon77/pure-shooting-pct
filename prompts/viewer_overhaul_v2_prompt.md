# Prompt: Viewer Overhaul v2 — Table Infrastructure & Column Improvements

## Context

The file `viewer/pure_ts_league_viewer.html` is a single-file static HTML viewer (all data embedded, built by `viewer/build_viewer.py`) with 5 tabs: Rankings, Foul Profile, FT by Type, Distortion Games, and About. It currently displays Pure TS% data for 563 NBA players (2025-26 season) and 22,395 per-game rows.

This prompt is a structural overhaul of the table infrastructure across all tabs. Read the existing viewer HTML carefully before making changes — preserve all existing functionality, data, styling, and tab structure. The changes below are additive or modify existing behavior.

---

## Part 1 — Universal Changes (apply to ALL table tabs)

### 1A. Draggable / Reorderable Columns

Users should be able to drag column headers to reorder them. Implement drag-and-drop on the `<th>` elements. When a column is dragged to a new position, the entire column (header + all data cells) moves. Column order should persist within the session (doesn't need to survive page reload).

### 1B. Column Manager (replaces the current "Columns" toggle button)

Replace the current "Columns" button (which toggles 3 specific columns) with a proper column manager:

- Button still labeled "Columns" in the same position
- Clicking it opens a dropdown/popover listing ALL columns for the current tab
- Each column has a checkbox to show/hide it
- A few columns are **locked and cannot be hidden**: # (rank number), PLAYER, TEAM
- All other columns are togglable
- All columns should be **visible by default** (no hidden-by-default columns)
- The column manager should have a "Reset" option that restores default column visibility and order

### 1C. Separate Columns for Every Sortable Value

**This is the most important structural change.** Currently, some columns combine two values in one cell (e.g., "343/512" for FGM/FGA, or "60.6% (934)" for percentage + raw count). This makes it impossible to sort by both values independently.

**New rule:** Every distinct numeric value gets its own column. Users can hide columns they don't want via the column manager. Examples:
- Old: `FG` column showing "343/512" → New: `FGM` column (343), `FGA` column (512), `FG%` column (67.0%)
- Old: `CLEAN 2PT` column showing "60.6% (934)" → New: `CLEAN 2PT %` column (60.6%), `CLEAN 2PT` column (934)

Every column must be independently sortable by clicking its header.

### 1D. Filter by Team

Add a team filter dropdown (or multi-select) near the existing search bar. Options should include all 30 NBA teams plus an "All Teams" default. Selecting a team filters the table to only show players from that team. Should work alongside the existing search bar and min possessions slider.

### 1E. Filter by Position

Add a position filter near the team filter. Options: All Positions, Guard, Forward, Center. Player positions should be derived from the data (the player roster JSON includes position data — `nba_active_players_2025-26.json`). If position data isn't currently embedded in the viewer, it will need to be added to the `build_viewer.py` data pipeline.

### 1F. Download Data Button

Add a "Download" button (near the Columns button) that exports the **currently visible and filtered** table data:
- Offer CSV format (primary)
- The export should respect all active filters (team, position, min possessions, search) and only include visible columns
- Filename should include the tab name and date, e.g., `pure_ts_rankings_2025-26.csv`

---

## Part 2 — Rankings Tab Changes

### 2A. Shooting Breakdown Columns

Replace the current `FG` and `FT` combined columns with separate, sortable columns. The full column order after PTS should be:

| Column | Content | Notes |
|--------|---------|-------|
| FGM | Field goals made | Integer |
| FGA | Field goal attempts | Integer |
| FG% | Field goal percentage | e.g., 48.0% |
| 3PM | 3-pointers made | Integer |
| 3PA | 3-point attempts | Integer |
| 3P% | 3-point percentage | e.g., 41.2% |
| 2PM | 2-pointers made | Integer, derived: FGM - 3PM |
| 2PA | 2-point attempts | Integer, derived: FGA - 3PA |
| 2P% | 2-point percentage | Derived: 2PM / 2PA |
| FTM | Free throws made | Integer |
| FTA | Free throw attempts | Integer |
| FT% | Free throw percentage | e.g., 64.3% |

**Data source:** FGM, FGA, 3PM, 3PA data should already be available in the component breakdown (Clean 2PT + Clean 3PT + And-1 events reconstruct the box score FG totals). FTM/FTA are already shown. 2PM/2PA are derived from the others.

### 2B. And-1 Rate, Foul Draw Rate, Hidden Possessions

These 3 columns are currently behind the "Columns" toggle. Changes:
- **Show all 3 by default** (no longer hidden)
- **Rename** "Foul Drawing Rate" → "Foul Draw Rate" (shorter header)
- **Hidden Possessions**: Currently shows raw count and percentage in one cell. Split into two columns:
  - `Hidden Poss` — raw count (integer, sortable)
  - `Hidden Poss %` — percentage of total scoring possessions (sortable)

### 2C. Full Default Column Order for Rankings Tab

```
#, PLAYER, TEAM, GP, PTS, FGM, FGA, FG%, 3PM, 3PA, 3P%, 2PM, 2PA, 2P%, FTM, FTA, FT%, SP, PURE TS%, STD TS%, DELTA, And-1 Rate, Foul Draw Rate, Hidden Poss, Hidden Poss %
```

All visible by default. User can hide any column except #, PLAYER, TEAM via the column manager.

---

## Part 3 — Foul Profile Tab Changes

### 3A. Split Combined Columns

Each foul type column currently shows "percentage (raw count)" in one cell. Split each into two columns:

| Current | New Column 1 | New Column 2 |
|---------|-------------|-------------|
| CLEAN 2PT showing "60.6% (934)" | CLEAN 2PT % (60.6%) | CLEAN 2PT (934) |
| CLEAN 3PT showing "22.7% (350)" | CLEAN 3PT % (22.7%) | CLEAN 3PT (350) |
| 2PT SF showing "10.5% (161)" | 2PT SF % (10.5%) | 2PT SF (161) |
| 3PT SF showing "0.4% (6)" | 3PT SF % (0.4%) | 3PT SF (6) |
| AND-1S showing "3.6% (56)" | AND-1S % (3.6%) | AND-1S (56) |
| PENALTY FTS showing "2.1% (33)" | PENALTY FTS % (2.1%) | PENALTY FTS (33) |

Each column independently sortable. The DISTRIBUTION stacked bar column remains as-is.

### 3B. Default Column Order for Foul Profile Tab

```
#, PLAYER, TEAM, SP, CLEAN 2PT %, CLEAN 2PT, CLEAN 3PT %, CLEAN 3PT, 2PT SF %, 2PT SF, 3PT SF %, 3PT SF, AND-1S %, AND-1S, PENALTY FTS %, PENALTY FTS, DISTRIBUTION
```

---

## Part 4 — FT by Type Tab Changes

### 4A. Split Combined Columns

Same principle. Each FT% column currently shows "percentage (made/attempted)". Split into three columns each:

| Current | New Columns |
|---------|------------|
| OVERALL FT% showing "79.6% (360/452)" | OVERALL FT% (79.6%), OVERALL FTM (360), OVERALL FTA (452) |
| SHOOTING FOUL showing "80.0% (272/340)" | SHOOTING FOUL % (80.0%), SF FTM (272), SF FTA (340) |
| AND-1 showing "78.6% (44/56)" | AND-1 % (78.6%), A1 FTM (44), A1 FTA (56) |
| BONUS showing "78.3% (36/46)" | BONUS % (78.3%), BONUS FTM (36), BONUS FTA (46) |
| TECH showing "85.7% (6/7)" | TECH % (85.7%), TECH FTM (6), TECH FTA (7) |

Each column independently sortable.

---

## Part 5 — Distortion Games Tab Changes

### 5A. Delta Threshold Slider

Replace the hardcoded 8pp delta filter with an adjustable slider:
- Label: "Min |delta|:"
- Range: 0pp to 30pp (step: 1pp)
- Default value: 5pp (lowered from 8pp to show more games by default)
- The "Showing X of Y games" counter should update dynamically as the slider moves
- Include the threshold note in the counter, e.g., "Showing 412 of 4140 games (|delta| ≥ 5pp)"

### 5B. Split FG and FT Columns

Same as Rankings — if FG currently shows "11/12", split into FGM (11) and FGA (12). Same for FT.

---

## Part 6 — build_viewer.py Updates

The `build_viewer.py` script embeds data into the HTML. It may need updates to:

1. **Include position data** for each player (needed for position filter). Source this from `data/nba_active_players_2025-26.json` which should have position info. If it only has a raw position string, map to Guard/Forward/Center categories.

2. **Include 3PM/3PA data** per player if not already embedded. This should be derivable from the component data (Clean 3PT FGA = 3PA minus And-1 3PT events; Clean 3PT makes + And-1 3PT makes = 3PM). Verify the math reconciles with box score 3P totals.

3. **Include 2PM/2PA data** — derived from FGM - 3PM and FGA - 3PA respectively.

4. Ensure all raw counts that were previously only shown inline (e.g., "(934)" next to a percentage) are available as separate data fields for the new split columns.

---

## Implementation Notes

- This is a single static HTML file. All JavaScript is inline. Keep it that way.
- Preserve the existing dark theme, color coding logic, tab structure, search functionality, and min possessions slider.
- The column drag-and-drop can use native HTML5 drag-and-drop API or a lightweight inline implementation. No external dependencies that require CDN loads (the viewer should work offline).
- Test that all sorting works correctly after the column split — especially percentage columns (sort as numbers, not strings) and derived columns (2P%, etc.).
- The "Showing X of Y" counter must update correctly when team filter, position filter, search, and min possessions slider are all active simultaneously.
- Column manager state (which columns are visible) should be independent per tab.
