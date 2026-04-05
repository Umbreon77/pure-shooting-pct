# Future Stats — Brainstorming Doc

## Purpose

This is a running list of ideas for custom-built advanced stats that extend beyond Pure TS%. The goal is to eventually build a suite of precise, play-by-play-derived metrics that replace approximation-based stats with deterministic calculations.

---

## Offensive Impact Stat (working concept)

Pure TS% measures individual scoring efficiency. But scoring is only one part of offensive impact. A true offensive impact metric would need to incorporate:

### Scoring (covered by Pure TS%)
- Already built — per-possession scoring efficiency across all event types

### Playmaking / Passing
- Assists: not just counting them, but weighting by the value of the shot created
  - An assist on a corner 3 vs an assist on a contested midrange are not equal
  - Could derive "assist efficiency" from PBP: what % of assisted shots were made?
  - Points generated via assists (simple: sum of points on assisted baskets)
  - Potential assists (passes that lead to a shot attempt, made or missed)
- Hockey assists / secondary assists — available in PBP data?
- Passes that draw fouls / lead to FTAs for teammates

### Shot Creation
- Unassisted scoring rate — what % of a player's makes are self-created?
- Gravity / attention — harder to measure, but could proxy via:
  - How often the player is doubled
  - Teammate shooting % when the player is on vs off court (on/off splits)
  - Shot quality of teammate attempts when this player is the passer

### Possession Value
- Turnovers as negative possessions (discussed and excluded from Pure TS%, but relevant here)
- Usage rate (what % of team possessions does this player use?)
- Points per possession used (incorporates turnovers as wasted possessions)
- Net possession value: points generated (scoring + assists) minus points lost (turnovers leading to opponent scores)

### Free Throw Drawing
- Fouls drawn per possession used
- Quality of foul drawn (shooting foul vs bonus foul vs and-1 — different values)
- Already captured in Pure TS% component data — could extract and weight

---

## Other Potential Metrics

### Defensive Impact (separate project)
- Opponent shooting % when guarded by this player
- Contests per game
- Forced turnovers
- PBP-derived defensive possessions

### Rebounding Impact
- Offensive rebound rate → new possession creation
- Contested vs uncontested rebounds

### Clutch Efficiency
- Pure TS% filtered to last 5 minutes of games within 5 points
- Component breakdown in clutch vs non-clutch

### Shot Quality Adjustment
- Adjust Pure TS% for shot difficulty (distance, defender proximity, shot clock)
- Would require tracking data (Second Spectrum / NBA.com tracking stats)

---

## Design Principles (carry forward from Pure TS%)

1. **No approximations** — derive from actual PBP events
2. **Component-based** — break complex metrics into discrete, verifiable pieces
3. **Reconcilable** — output must tie back to box score totals
4. **Weighted properly** — don't average percentages, aggregate raw counts first

---

## Notes

- Expected value is already embedded in Pure TS% — the component-level efficiency (PTS / max possible) naturally captures the value of 3s vs 2s without needing a separate adjustment
- Turnovers excluded from Pure TS% by design — they belong in a broader offensive impact metric that measures total possession value
- The PBP JSON from NBA CDN contains assist data, turnover data, and foul detail — much of what's needed for the offensive impact stat is already in our data pipeline

---

## Foul Geography / Where Players Get Fouled

### Phase 1 — FT-Resulting Fouls (data already captured)
- Shooting fouls (C2/C3) and And-1s (C4/C5) are tied to shot attempts, which include distance from basket in the PBP data (e.g., "16' fadeaway", "driving layup from 2 ft")
- Extract the distance for each of these events and map where on the court a player gets fouled when shooting
- This is a more specific category than "all fouls" — it tells you where a player draws fouls that actually produce free throws
- Nobody has this data visualized publicly

### Phase 2 — All Fouls Including Non-FT Fouls
- The first 4 team fouls per quarter before the bonus result in a sideline inbound — no FTs, no scoring possession
- These fouls ARE in the PBP data but our current parser skips them (they don't produce scoring possessions)
- Would require updating the PBP parser to also capture fouls that didn't produce free throws
- Gives the complete picture: where does this player draw contact regardless of whether it produces FTs
- Build Phase 2 on top of Phase 1 since the model/visualization will already exist

---

## Viewer Roadmap (pure_ts_league_viewer.html)

### Already Built (v1)
- Interactive sortable/filterable table with all 563 players
- Search by player name or team
- Min possessions slider
- Click-to-expand component breakdown per player
- Color-coded Pure TS% and Delta columns

### Next Up (v2)
- **Foul Profile tab** — breakdown of each player's scoring possessions by type (what % are clean FGAs vs shooting fouls vs bonus fouls vs and-1s). Shows *how* a player scores, not just efficiency.
- **FT Efficiency by Type tab** — per-foul-type FT make rates (shooting foul FT%, and-1 FT%, bonus FT%, tech FT%). This data doesn't exist anywhere else publicly.
- **Biggest Distortion Games tab** — individual games with the largest Pure TS% vs Standard TS% gaps. Pull from the 22,395 per-game rows.

### Future (v3+)
- Foul geography visualization (where on the court players get fouled)
- Player comparison tool (side-by-side component breakdowns)
- Distribution charts / histograms for league-wide Pure TS%
- Offensive impact stat integration once that metric is built

---

## Data Visualization / Graphics Toolkit

### Why
- Tables are great for lookup but bad for showing patterns, distributions, and relationships across 563 players
- Visualizations make the case for Pure TS% far more compelling than numbers alone — a scatter plot showing systematic overrating by standard TS% is instantly persuasive
- Needed for any eventual publishing, presentation, or public-facing version of the project

### What to Build

#### Tier 1 — Core Pure TS% Visuals (build first)
- **Pure TS% vs Standard TS% scatter plot** — every qualified player as a dot, 45-degree reference line showing where they'd be if the metrics agreed. The systematic offset above the line IS the argument for the metric. Color by position or team optionally.
- **Delta distribution histogram** — how much does standard TS% overrate/underrate each player? Shows the spread and central tendency of the distortion. Highlight outliers.
- **Pure TS% distribution histogram** — league-wide spread with mean/median/std markers. What does "average" efficiency actually look like on the true scale?

#### Tier 2 — Component & Profile Visuals
- **Scoring possession breakdown stacked bars** — for a given player or set of players, show what % of their scoring possessions are clean FGA vs shooting fouls vs and-1s vs bonus fouls vs etc. Reveals HOW players score, not just how well.
- **Hidden possessions bar chart** — how many scoring possessions per player does the box score miss entirely? (shooting fouls + bonus fouls + other non-FGA events). Shows the size of the problem that 0.44 tries to paper over.
- **FT efficiency by foul type grouped bars** — do players shoot differently on shooting fouls vs and-1s vs bonus situations? Novel data nobody else has.

#### Tier 3 — Relationship / Correlation Visuals
- **Pure TS% vs PPG scatter** — efficiency vs volume. Who is efficient AND high-volume?
- **Pure TS% vs usage rate scatter** — does efficiency drop with higher usage? (expected, but by how much?)
- **Delta vs foul drawing rate scatter** — do players who draw more fouls see bigger distortions from standard TS%? (hypothesis: yes)
- **And-1 rate vs Delta scatter** — and-1s are the most underweighted event in standard TS%. Do players with more and-1s show bigger gaps?

#### Tier 4 — Team-Level & Game-Level Visuals
- **Team average Pure TS% bar chart** — which teams are actually the most efficient on the true scale?
- **Biggest distortion games scatter or strip plot** — from the 22,395 game rows, show the distribution of per-game deltas. Highlight the extreme cases.

### Implementation Options
- **Python (matplotlib / seaborn)** — best for static, publication-quality graphics. Exportable as PNG/SVG. Good for one-off analysis plots. CC can build these as standalone scripts.
- **Interactive in-viewer (Chart.js / D3.js)** — best for exploration. Users can hover, filter, click. Could add as new tabs in the existing viewer HTML.
- **Both** — build Python scripts for static/export versions, add interactive versions to the viewer later. The Python versions are faster to ship and can inform what's worth making interactive.

### Priority
Build Tier 1 first — these three plots alone tell the whole story of why Pure TS% matters. They're the visuals you'd put in a blog post or presentation to make the case.

---

## Historical Seasons Data

### Why
- More seasons = stronger statistical case for Pure TS% vs standard TS%
- Can show how the 0.44 coefficient's distortion varies across eras (3PT revolution, pace changes, rule changes like take foul)
- Enables historical player comparisons on the Pure TS% scale

### How
- NBA CDN PBP JSON endpoint uses the same format across seasons — just different game IDs
- Need to identify how far back the PBP JSON data is available (likely 2015-16 onward, possibly earlier)
- The existing Phase 3 pipeline (fetch PBP → classify → aggregate) works for any season — just swap the season parameter
- Can run historical scrapes overnight with longer delays between fetches to avoid rate limits
- Each season is ~1,200 games, same as current season

### TODO
- [ ] Test the NBA CDN PBP endpoint for older seasons (try 2024-25, 2023-24, etc.) to find how far back data exists
- [ ] Once confirmed, run the Phase 3 pipeline for each available historical season
- [ ] Build a multi-season viewer or add a season selector to the existing viewer

---

## Offensive Impact Stat — Deep Dive

### The Problem With Current "Impact" Metrics

**Net Rating / On-Off splits** — the most commonly cited "impact" metric is deeply flawed:
- Extremely noisy in small samples. A player's 5-man lineup might have 200 minutes together — that's not enough to draw conclusions.
- No control for opponent quality, game state, or garbage time. A guy who plays his bench minutes against the other team's bench in blowouts looks great on net rating.
- Lineup context is everything. A player's on-off numbers change dramatically depending on who else is on the court. It's measuring the lineup, not the player.
- Treated with way more authority than the data supports. Analysts cite net rating as if it's a precise measurement when it's really a rough directional signal at best.

**Box score-based metrics (PER, Win Shares, BPM):**
- Built on box score aggregations, which we've already shown are lossy (hidden possessions, the 0.44 problem)
- PER in particular is widely criticized — it overvalues volume scoring and doesn't properly account for efficiency or defensive impact
- These metrics try to smoosh everything into one number, which inevitably means arbitrary weighting choices

**The opportunity:** Build an offensive impact stat from play-by-play events — same philosophy as Pure TS% (deterministic, component-based, reconcilable) — but measuring total offensive contribution, not just scoring efficiency.

### What Should Go Into Offensive Impact?

#### Tier 1 — Scoring Efficiency (DONE)
- Pure TS% — already built
- This is the foundation: how efficiently does this player convert when they get a scoring opportunity?

#### Tier 2 — Scoring Volume
- Scoring possessions consumed / total team possessions (usage concept but derived from PBP, not estimated)
- Points generated per minute or per game
- This layer asks: how MUCH does this player score, not just how well?

#### Tier 3 — Playmaking / Assist Value
- Not all assists are equal. An assist on an open corner 3 is worth more expected points than an assist on a contested midrange 2.
- **Assist points generated:** sum of actual points scored on assisted baskets. Simple and available in PBP.
- **Potential assists:** passes that led to a shot attempt (made or missed). PBP may or may not have this — need to check.
- **Assist-to-turnover ratio:** but derived from actual PBP events, not box score
- **Free throw assists:** passes that led directly to a teammate being fouled and going to the line. Does the PBP data capture the passer on these?

#### Tier 4 — Shot Creation
- Unassisted scoring rate: what % of this player's makes were self-created?
- This separates "catch and shoot" guys from "create your own shot" guys
- Available in PBP since assisted baskets are tagged

#### Tier 5 — Possession Preservation (Turnovers)
- Turnovers as negative events — each TO is a wasted possession
- But not all TOs are equal: a live-ball TO leading to a fast break is worse than a dead-ball TO
- PBP has turnover type data (steal vs out of bounds vs offensive foul etc.)
- Could weight turnovers by their actual cost (opponent points scored off that specific TO)

#### Tier 6 — Foul Drawing Value
- Already captured in Pure TS% component data
- Could extract: fouls drawn per possession, quality of foul drawn
- A player who draws shooting fouls is more valuable than one who draws bonus fouls (shooting fouls = higher max points per possession)

### What Should NOT Go Into Offensive Impact?
- Defense (separate metric entirely)
- Rebounding (debatable — offensive rebounds create possessions, but that's more of a "possession creation" stat)
- "Gravity" or "attention" — actually NBA does have gravity data at nba.com/inside-the-game/player/gravity. Worth investigating if we can access this via API.
- Anything that requires lineup context or on-off splits — we're measuring the individual, not the lineup

### External Resources
- **BBall Index LEBRON metric** — https://www.bball-index.com/lebron-introduction/ — a composite impact stat. Review their methodology to understand what they're doing and where our approach differs.
- **NBA Gravity data** — https://www.nba.com/inside-the-game/player/gravity — NBA's own gravity metric. Investigate if accessible via API.

### Design Principles (same as Pure TS%)
1. Every input derived from actual PBP events or official NBA tracking data — no estimates
2. Component-based — each dimension of offensive impact is measured separately and can be examined independently
3. Reconcilable — outputs should tie back to verifiable totals
4. Combine via weighted average or additive model — not a black box regression
5. The single-number output should be interpretable: "this player generated X points of offensive value per Y possessions"

---

## NBA Stats Data Inventory

Full taxonomy of data available on nba.com/stats. Each top-level category has sub-categories (Level 3) accessible via dropdown menus on the site. All backed by stats.nba.com API endpoints.

### General (Traditional box score derived)
Sub-categories: Traditional, Advanced, Misc, Scoring, Opponent, Defense, Four Factors
- Available back to: all NBA history for traditional, varies for advanced

### Clutch
- Same sub-types as General but filtered to clutch situations (last 5 min, score within 5)

### Playtype (Synergy data — play classification)
Sub-categories:
- Isolation
- Transition
- Pick & Roll Ball Handler
- Pick & Roll Roll Man
- Post Up
- Spot Up
- Handoff
- Cut
- Off Screen
- Putbacks
- Misc
- Available back to: 2015-16
- **Relevance to OI:** High — play type efficiency tells you HOW a player scores, not just that they scored

### Tracking (Second Spectrum camera data)
Sub-categories:
- Drives
- Defensive Impact
- Catch & Shoot
- Passing (PASSES MADE, PASSES RECEIVED, AST, SECONDARY AST, POTENTIAL AST, AST PTS CREATED, AST ADJ, FT AST)
- Touches (TOUCHES, FRONT CT TOUCHES, TIME OF POSS, AVG SEC PER TOUCH, AVG DRIB PER TOUCH, PTS PER TOUCH)
- Pull Up Shooting
- Rebounding / Offensive Rebounding / Defensive Rebounding
- Shooting Efficiency
- Speed & Distance
- Elbow Touches
- Post Ups (tracking version)
- Paint Touches
- Available back to: 2013-14
- **Relevance to OI:** Critical — Passing sub-category has potential assists, hockey assists, FT assists. Touches has time of possession and points per touch.

### Defense Dashboard
Sub-categories: Overall, 3PT, 2PT, <6ft, <10ft, >15ft
- **Relevance to OI:** None (defensive metric)

### Shot Dashboard
Sub-categories: General, Closest Defender, Closest Defender +10, Dribbles, Touch Time
- **Relevance to OI:** Moderate — shot difficulty context for scoring efficiency

### Shooting
Sub-categories: by distance zones, by area
- **Relevance to OI:** Moderate — shot selection profile

### Inside the Game (separate section from main stats)
- Gravity — https://www.nba.com/inside-the-game/player/gravity
- **Relevance to OI:** High if accessible — measures how much defensive attention a player draws

### Hustle Stats
- Contested shots, charges drawn, screen assists, deflections, loose balls recovered
- **Relevance to OI:** Low-moderate — screen assists could factor into playmaking

### Other Available
- Dunk Scores, Box Outs, Opponent Shooting, Advanced Box Scores, Bios

### Key Data for Offensive Impact (priority order)
1. **Our PBP data** — scoring events, foul events (already have)
2. **Tracking > Passing** — potential assists, hockey assists, AST points created, FT assists
3. **Tracking > Touches** — possessions touched, time of possession, points per touch
4. **Tracking > Drives** — drives per game, drive efficiency
5. **Playtype data** — efficiency by play type (iso, PnR, spot up, etc.)
6. **Shot Dashboard** — shot quality context (contested vs open)
7. **Gravity** — if API accessible

### TODO
- [ ] Identify the stats.nba.com API endpoints for each of these data categories
- [ ] Test if historical seasons are available via the same endpoints
- [ ] Determine if gravity data has an API or is only available through the Inside the Game UI
- [ ] Pull a sample of the Tracking > Passing data and examine what fields are available
