# Pure TS% — Front End Data Viewer

## Objective

Build a local HTML page that lets us explore the Pure TS% league data visually — interactive table with search, sort, filter, and clean presentation. Open it in a browser, no server required.

## Required Reading

- `CLAUDE.md` — Project overview
- `data/pure_ts_pct_league_2025-26.csv` — The 563-player league dataset (this is the data source)

## What To Build

**Filename:** `viewer/pure_ts_league_viewer.html` (single self-contained HTML file)

### Core Features

#### Interactive Table
- Display all players from the league CSV
- Columns to show: Rank, Player Name, Team, Games Played, PTS, FGA, FTA, Scoring Possessions, Pure TS%, Standard TS%, Delta
- Click any column header to sort ascending/descending
- Default sort: Pure TS% descending

#### Search
- Text search box that filters by player name or team abbreviation in real time as you type

#### Minimum Possessions Filter
- A slider or input field that sets a minimum scoring possessions threshold
- Default to something reasonable like 500
- Updating the slider instantly filters the table
- Show the current count of players displayed (e.g., "Showing 127 of 563 players")

#### Visual Touches
- Color code the Delta column: deeper red for larger negative deltas, lighter for smaller
- Highlight Pure TS% with a subtle color scale (green = high, red = low)
- Clean typography, readable at a glance — this is a data tool not a marketing page
- Sticky header row so column names stay visible when scrolling

### Data Loading

The CSV file lives at `../data/pure_ts_pct_league_2025-26.csv` relative to the viewer folder. Since this is a local file, browsers may block fetch requests to local CSVs. Two options:

1. **Embed the data directly** — read the CSV at build time and embed it as a JavaScript array in the HTML file. This is the simplest approach and avoids CORS issues entirely. Preferred.
2. Or provide a one-line Python server command in the file header for people who want to keep data separate.

Go with option 1 — read the CSV and bake the data into the HTML file as a JS const. Write a small Python build script (`viewer/build_viewer.py`) that reads the CSV and generates the HTML with embedded data.

### Nice To Have (not required for v1, but design with these in mind)

- Click a player row to expand and show their component breakdown (C1a, C1b, C2, etc.)
- A toggle to show/hide advanced columns (component-level efficiencies and weights)
- A small histogram or distribution chart showing where the selected minimum-possessions cohort falls on Pure TS%

### Design Notes

- Single HTML file, no external dependencies except maybe a CDN link to a lightweight CSS framework or table library if it helps
- Must work by just double-clicking the HTML file in Finder — no server, no build step (the build script generates the final HTML, but the output is standalone)
- Keep it fast — 563 rows is trivial, everything should feel instant
- Mobile-friendly is not a priority — this is a desktop data exploration tool

### Validation

- Open the HTML file in Chrome/Safari
- Search "Doncic" — should show Luka with Pure TS% 52.1%, Standard TS% 61.4%
- Set minimum possessions to 1000 — should filter down to the high-volume players
- Sort by Delta — players with the biggest standard TS% overrating should be at top
- Verify player count matches the CSV (563 total, fewer with possession filter applied)
