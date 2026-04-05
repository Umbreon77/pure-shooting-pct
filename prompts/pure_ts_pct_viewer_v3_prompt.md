# Pure TS% Viewer — v3 Feature Additions

## Objective

Add new stat columns/views to the existing viewer, plus fix the tooltip delay issue from v2.

## Required Reading

- `viewer/pure_ts_league_viewer.html` — Current v2 viewer
- `viewer/build_viewer.py` — Build script
- `docs/pure_ts_pct_terms_and_key.md` — Component definitions
- `docs/future_stats_brainstorm.md` — Feature ideas and roadmap

## Fix: Instant Tooltips

The current column header tooltips use native `title` attributes which have a built-in browser delay before appearing. Replace ALL `title` attribute tooltips across all four tabs with CSS-powered tooltips:

- Use a `data-tooltip` attribute on each element
- Display via CSS `::after` pseudo-element triggered by `:hover`
- No JS needed — pure CSS
- Appears instantly on hover, no delay
- Styled to match the dark theme (dark background, light text, slight rounded corners, small font)
- Positioned above or below the element so it doesn't overlap other headers
- Apply this globally so any future tooltips also get the instant behavior

## New Columns / Stats to Add

These should be added as new columns on the **Rankings** tab (the main table). They use data already embedded — no new data sources needed.

### 1. And-1 Rate

What percentage of a player's made field goals resulted in an and-1?

```
And-1 Rate = (Amt_A1₂ + Amt_A1₃) / Total FGM
```

Where Total FGM = FGM from C1a + FGM from C1b + Amt_A1₂ + Amt_A1₃ (since every and-1 is a make).

FGM from C1a = PTS₂ / 2 (each clean 2PT make = 2 pts).
FGM from C1b = PTS₃ / 3 (each clean 3PT make = 3 pts).

Display as a percentage. Tooltip: "Percentage of made field goals that resulted in an And-1 (made basket + bonus free throw)."

### 2. Foul Drawing Rate

How often does this player draw a foul per scoring possession?

```
Foul Drawing Rate = Total Foul Events / Total Scoring Possessions
```

Where Total Foul Events = Amt_SF2 + Amt_SF3 + Amt_A1₂ + Amt_A1₃ + Amt_TF + Amt_FF + Amt_CP + Amt_TK + Amt_AP + Amt_BF

(Every component except C1a and C1b involves a foul.)

Display as a percentage. Tooltip: "Percentage of scoring possessions that involved a foul (shooting fouls, and-1s, bonus fouls, techs, etc.)."

### 3. Hidden Possessions

The number (and percentage) of a player's scoring possessions that produced ZERO field goal attempts in the box score. These are the possessions that are invisible to traditional stats — the exact gap that Pure TS% exists to measure.

```
Hidden Possessions = Amt_SF2 + Amt_SF3 + Amt_TF + Amt_FF + Amt_CP + Amt_TK + Amt_AP + Amt_BF
Hidden Poss % = Hidden Possessions / Total Scoring Possessions
```

Note: And-1s are NOT hidden — they produce an FGA in the box score. Only shooting fouls (where the shot didn't go in) and all C6 penalty events are truly hidden from the box score.

Display as: "47 (14.2%)" — raw count plus percentage in the same cell.

Tooltip: "Scoring possessions that produced zero FGAs in the box score. These are invisible to traditional stats — shooting fouls where the shot didn't go in, plus bonus fouls, tech FTs, and other penalty free throws."

### 4. Columns Visibility

Adding these three columns makes the Rankings tab wider. Add a small "Columns" dropdown or toggle button that lets the user show/hide columns. Default visible columns:

- Rank, Player, Team, GP, PTS, FGA, FTA, SP, Pure TS%, Std TS%, Delta

Toggle-able (hidden by default, user can turn on):

- And-1 Rate, Foul Drawing Rate, Hidden Possessions
- Plus any component-level columns if desired

This keeps the default view clean while making the extra stats available.

### Pre-calculate in Build Script

Update `build_viewer.py` to pre-calculate And-1 Rate, Foul Drawing Rate, and Hidden Possessions during the build step. Embed them as additional fields in the player data so the HTML doesn't compute them at runtime.

## Validation

- **And-1 Rate:** SGA had 52 and-1s. His total FGM from the season data should be checkable. The rate should be a reasonable single-digit percentage for most players.
- **Foul Drawing Rate:** Luka should be higher than SGA since he had more foul-only possessions proportionally.
- **Hidden Possessions:** Luka had 185 + 15 + 10 + 45 = 255 hidden possessions out of 1532 total = ~16.6%. SGA had 171 + 9 + 18 + 1 + 1 + 2 + 40 = 242 out of 1383 = ~17.5%. Verify these against the embedded data.
- **Tooltips:** Hover over any column header on any tab — tooltip should appear instantly with no delay.
