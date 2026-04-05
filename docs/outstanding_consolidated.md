# Outstanding Items — Consolidated

## Before Deploy

### About Tab Reorganization (in progress)
- Reorganize into 4 sub-tabs: The Problem, Methodology, Historical Evidence, Cross-Era Comparison
- Review The Problem tab for redundancy between "Example Box Scores" section and "Same Efficiency, Different TS%" section after content is moved in
- Review The Problem tab opening flow now that structural/same efficiency/exceeds 100% sections are added

### Methodology Tab Fixes
- Update data source section from "six seasons (2020-21 through 2025-26)" to reflect all 47 seasons (1979-80 through 2025-26) with note that PBP data covers 6 most recent
- Add Charts tab instructions/help text (collapsible "?" toggle with descriptions of Scatter Plot, Histogram, Trends, Composition)

### CLAUDE.md Update
- Update for PS% rename (was Pure TS%)
- Update status sections for new tabs (Historical Evidence, Cross-Era Comparison)
- Update for BBRef scraping architecture decisions
- Update outstanding items reference

### Deploy Prep
- Split 108MB monolith HTML into app shell + per-season JSON data files loaded on demand
- Push to GitHub under Umbreon77
- Connect GitHub repo to Netlify
- Pick subdomain name (or use default netlify.app)
- Add "Last updated: [date]" somewhere visible on the site

### One-Pager PDF
- Update for PS% rename (currently says Pure TS%)

---

## Soon After Deploy

### BBRef PBP Scraping
- 1997-98 season scraped and cached (1,189 games). 23 more seasons to run (1996-97, 1999-2000 through 2019-20)
- Run in 4 batches of ~6 seasons each on local terminal
- Build BBRef adapter/classifier for PS% components (equivalent of pure_ts_pct_single_game.py for BBRef event format)
- Fix BBRef parser issues: player name spacing bug, truncated shot types, technical FT classification
- 2019-20 bubble: playoff games show 0 due to BBRef page structure difference, needs manual fix
- Collect playoff game IDs for 6 recent seasons (2020-21 through 2025-26) from NBA CDN

### Viewer Enhancements
- Player comparison tool (side-by-side component breakdowns)
- Exportable PNG/SVG from charts for sharing/publishing
- Position filter (needs position data added to pipeline)
- Excel-style column filters

### Data Viz Additions
- Correlation plots (PS% vs PPG, vs usage, vs FT rate)
- Hidden possessions visualization
- Foul drawing profile comparisons

---

## Future

### New Metrics
- Offensive impact stat (playmaking formula designed but blocked by Second Spectrum data access)
- Foul geography Phase 1 (shot distance on FT-resulting fouls)
- Foul geography Phase 2 (all fouls including non-FT)
- Defensive impact metric (separate project)

### Research
- Review BBall Index LEBRON methodology
- Investigate NBA Gravity API accessibility
- Map tracking data fields to offensive impact tiers

### Infrastructure
- Web app / backend migration (solves file size long-term)
- Historical PBP integration into viewer (game logs, foul profiles for pre-2021 seasons once BBRef data is processed)
- Playoff data integration into viewer once collected
- Custom domain purchase (optional, cosmetic)
