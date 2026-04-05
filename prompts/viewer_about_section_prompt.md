# Pure TS% Viewer — About / Methodology Section

## Objective

Add a text-based "About" tab to the viewer that explains what Pure TS% is, how it's derived, why it exists, and how to interpret every stat shown in the tool. This is the documentation that makes the tool self-explanatory — if someone opens this viewer with zero context, this tab should get them up to speed.

## Required Reading

- `docs/pure_ts_pct_terms_and_key.md` — The canonical source for all definitions and formulas
- `docs/pure_ts_pct_proof_of_concept.md` — The Luka Doncic worked example
- `viewer/pure_ts_league_viewer.html` — Current viewer (understand existing tabs and stats)

## What To Build

Add an **"About"** tab to the viewer tab bar. Place it as the last tab (after Distortion Games). This tab is pure content — no data table, no interactivity. Just well-written, well-structured text.

### Section 1 — What Is Pure TS%?

Brief, plain-language explanation:

- Pure TS% is a shooting efficiency metric that measures what percentage of maximum possible points a player captured across all their scoring possessions
- It replaces the standard True Shooting Percentage (TS%) which uses an approximation (the 0.44 free throw coefficient) with an exact calculation derived from play-by-play data
- The result is a true 0-to-100% scale — unlike standard TS%, it can never exceed 100%
- It's a weighted average: each type of scoring event (2PT shots, 3PT shots, shooting fouls, and-1s, bonus fouls, etc.) is measured against its own maximum possible points, then combined based on how often each type occurred

### Section 2 — Why Does This Exist?

Explain the problem with standard TS%:

- The standard formula `PTS / (2 × (FGA + 0.44 × FTA))` uses 0.44 as a league-wide estimate of how many possessions free throws consume
- This 0.44 is an average — it assumes a "typical" distribution of foul types (and-1s, 2-shot fouls, 3-shot fouls, techs, etc.)
- For any individual player or game where the foul distribution deviates from typical, the estimate breaks down
- The standard formula can produce values over 100%, which is nonsensical for a percentage
- Example: Sam Merrill scored 32 points on 12 FGA and 1 FTA on Feb 11, 2026 — standard TS% = 128.6%, Pure TS% = 91.7%
- On average across the entire 2025-26 NBA season, standard TS% overrates player efficiency by approximately 7.6 percentage points

### Section 3 — How It Works (The Components)

List each component with a one-line description. Keep it scannable — this isn't a textbook, it's a reference:

- **C1a — Clean 2PT FGA:** Player takes a 2-point shot, no foul. Max = 2 pts.
- **C1b — Clean 3PT FGA:** Player takes a 3-point shot, no foul. Max = 3 pts.
- **C2 — 2PT Shooting Foul:** Fouled on a 2-point shot (miss), 2 free throws. Max = 2 pts.
- **C3 — 3PT Shooting Foul:** Fouled on a 3-point shot (miss), 3 free throws. Max = 3 pts.
- **C4 — And-1 (2PT):** Makes a 2-point shot AND is fouled, 1 bonus free throw. Max = 3 pts.
- **C5 — And-1 (3PT):** Makes a 3-point shot AND is fouled, 1 bonus free throw. Max = 4 pts.
- **C6a — Tech FT:** Technical foul free throw. Max = 1 pt.
- **C6b — Flagrant FT:** Non-shooting flagrant foul, 2 free throws. Max = 2 pts.
- **C6c — Clear Path FT:** Clear path foul, 2 free throws. Max = 2 pts.
- **C6d — Take Foul FT:** Transition take foul, 1 free throw. Max = 1 pt.
- **C6e — Away-From-Play FT:** Away-from-play foul, 1 free throw. Max = 1 pt.
- **C6f — Bonus Foul FT:** Non-shooting foul in the penalty, 2 free throws. Max = 2 pts.

### Section 4 — The Formula

Show the formula itself, cleanly formatted:

```
Pure TS% = Σ (weight × efficiency) for each component

Where:
  Efficiency = Points scored / Max possible points for that component type
  Weight = Component's scoring possessions / Total scoring possessions
  All weights sum to 1
```

Emphasize the key concept: **scoring possessions, not field goal attempts.** A shooting foul that doesn't result in a made basket produces 0 FGAs in the box score but still consumes 1 scoring possession. Pure TS% counts these. Standard TS% approximates them.

### Section 5 — How To Read The Stats

Brief guide to each stat shown in the viewer:

- **Pure TS%** — The metric. What % of maximum possible points did the player capture across all scoring possessions.
- **Standard TS%** — Traditional True Shooting %. Shown for comparison.
- **Delta** — Pure TS% minus Standard TS%. Negative means standard TS% overrated the player. The bigger the negative number, the more the 0.44 approximation distorted their true efficiency.
- **Scoring Possessions (SP)** — Total scoring events consumed by the player. Broader than FGA — includes shooting fouls, bonus fouls, and other events that don't register as FGAs.
- **And-1 Rate** — % of made field goals that resulted in an and-1.
- **Foul Drawing Rate** — % of scoring possessions that involved any foul.
- **Hidden Possessions** — Scoring possessions that produced zero FGAs in the box score. The number + percentage shown represents how much of a player's scoring activity is invisible to traditional stats.

### Section 6 — How To Read The Tabs

One-liner for each tab:

- **Rankings** — Season-level Pure TS% for every player, sortable and filterable.
- **Foul Profile** — How each player's scoring possessions break down by type. Shows the composition of a player's scoring, not just the efficiency.
- **FT by Type** — Free throw make rate broken out by the type of foul that produced the free throws. This data is not available from any other public source.
- **Distortion Games** — Individual game performances where the gap between Pure TS% and Standard TS% was largest, revealing where the 0.44 approximation fails hardest.

### Section 7 — Data Source & Methodology Notes

- Data source: NBA official play-by-play event data (2025-26 regular season)
- Every scoring event categorized from play-by-play logs — no approximations, no estimates
- Box score totals (FGA, FTA, PTS) reconciled against play-by-play data for every game
- Season-level stats are aggregated from raw component totals, not averaged from per-game percentages

## Styling

- Match the dark theme of the rest of the viewer
- Use clear section headers with some visual separation between sections
- Keep paragraphs short — this is reference material, not an essay
- Use the monospace/code styling for the formula display
- Readable line length — don't let text stretch the full width of the screen on wide monitors. Max width around 800px for the text content, centered.

## Validation

- Read through the entire About tab and verify all component descriptions match `pure_ts_pct_terms_and_key.md`
- Verify the Sam Merrill example numbers (32 pts, 12 FGA, 1 FTA, 128.6% Std TS%, 91.7% Pure TS%)
- Verify the league-wide average delta (~7.6 pp) matches what the data shows
