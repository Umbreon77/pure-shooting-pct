# Pure TS% Viewer — UI Cleanup & Consistency Pass

## Objective

Fix several inconsistencies and improve usability across all tabs. This is a polish pass — no new data or stats, just making what's already there more consistent and useful.

## Fixes

### 1. Foul Profile — Flip the Format

Currently showing `500 (89.3%)` — raw count first, percentage in parentheses. This is backwards compared to the FT by Type tab which correctly shows `80.0% (272/340)`.

**Fix:** Flip to `89.3% (500)` — percentage first (primary number), raw count in parentheses (context). Match the FT by Type convention. The percentage should remain the full-size number; the raw count in parentheses should be slightly de-emphasized (smaller font or muted color).

### 2. Rankings Tab — FGA and FTA as Fractions

Currently FGA shows just attempts (e.g., `512`) and FTA shows just attempts (e.g., `108`). Attempts without makes gives incomplete context.

**Fix:** Show as fractions:
- FGA column → FGM/FGA (e.g., `233/512`)
- FTA column → FTM/FTA (e.g., `89/108`)

The data needed to compute FGM is already embedded:
- FGM = (PTS₂ / 2) + (PTS₃ / 3) + Amt_A1₂ + Amt_A1₃ (clean makes + and-1 makes)
- FTM = total FTM from all component FT data

Pre-calculate these in the build script and embed them.

### 3. Distortion Games Tab — Same FGA/FTA Fix

Same issue as Rankings — FGA and FTA are just raw attempts.

**Fix:** Show as FGM/FGA and FTM/FTA fractions, same format as Rankings.

The per-game CSV should have the data needed, or derive from the per-game component data.

### 4. Foul Profile — Add Stacked Bar Legend

The stacked bar visualization has colored segments but no legend explaining which color is which component. First-time users can't interpret the bars.

**Fix:** Add a small legend row above or below the table (or as a fixed element near the header) showing:
- Color swatch + "Clean 2PT"
- Color swatch + "Clean 3PT"
- Color swatch + "2PT SF"
- Color swatch + "3PT SF"
- Color swatch + "And-1s"
- Color swatch + "Penalty FTs"

Keep it compact — one horizontal row of small swatches with labels.

### 5. Column Toggle on All Data Tabs

Currently only the Rankings tab has a "Columns" button. Add column toggle capability to:

- **Foul Profile tab** — let users hide/show any of the component columns
- **FT by Type tab** — let users hide/show any of the FT type columns
- **Distortion Games tab** — let users hide/show columns (e.g., hide FGA/FTA if they just want to see Pure TS% vs Std TS%)

Use the same "Columns" dropdown button UI pattern from the Rankings tab. Each tab has its own independent column visibility state. The button should only appear on tabs that have a data table (hide it on the About tab, same as the search/filter controls).

### 6. About Tab — Mention Hidden Columns

Add a brief note in the "How To Read The Stats" section of the About tab mentioning that additional columns (And-1 Rate, Foul Drawing Rate, Hidden Possessions) are available via the "Columns" button on the Rankings tab. Users might not discover these on their own.

## Build Script

Update `build_viewer.py` to pre-calculate:
- FGM for each player (for Rankings FGM/FGA fractions)
- FTM for each player (for Rankings FTM/FTA fractions)
- Per-game FGM and FTM (for Distortion Games fractions)

## Validation

- Foul Profile: verify format is now `89.3% (500)` not `500 (89.3%)`
- Rankings: verify FGA column shows fractions like `233/512`
- Rankings: verify FTA column shows fractions like `89/108`
- Distortion Games: verify same fraction format
- Foul Profile: verify legend is visible and colors match the bars
- All data tabs: verify Columns button appears and works independently per tab
- About tab: verify hidden columns are mentioned
- Cross-check a few FGM values: e.g., Luka's FGM should be ~606 (from 606-1277 FG box score line)
