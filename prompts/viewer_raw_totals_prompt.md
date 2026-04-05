# Pure TS% Viewer — Raw Totals on FT by Type & Foul Profile

## Objective

The FT by Type and Foul Profile tabs currently show only percentages. Add raw counts alongside the percentages so users have full context. A percentage without knowing the sample size can be misleading — 100% on 1 attempt is very different from 90% on 100 attempts.

## What To Change

### Foul Profile Tab

Currently shows the percentage breakdown of scoring possessions by type. Add the raw event count next to each percentage.

**Current format:** `60.2%`
**New format:** `832 (60.2%)`

This applies to every column in the foul profile table:
- Clean 2PT %: show `FGA₂ (FGA₂ / Total SP %)`
- Clean 3PT %: show `FGA₃ (FGA₃ / Total SP %)`
- 2PT Shooting Fouls %: show `Amt_SF2 (Amt_SF2 / Total SP %)`
- 3PT Shooting Fouls %: show `Amt_SF3 (Amt_SF3 / Total SP %)`
- And-1s %: show `Amt_A1 combined (Amt_A1 / Total SP %)`
- Penalty FTs %: show `Amt_penalty combined (Amt_penalty / Total SP %)`

The stacked bar visualization should remain as-is (driven by percentages). The raw counts appear in the table cells.

### FT by Type Tab

Currently shows only the FT make percentage for each foul type. Add a FTM/FTA fraction alongside each percentage.

**Current format:** `83.6%`
**New format:** `83.6% (184/220)`

This applies to every FT% column:
- Shooting Foul FT%: show `pct% (FTM/FTA)` where FTM = PTS_SF2 + PTS_SF3 and FTA = Amt_SF2 × 2 + Amt_SF3 × 3
- And-1 FT%: show `pct% (FTM/FTA)` where FTM and FTA are the and-1 free throw makes and attempts
- Bonus Foul FT%: show `pct% (FTM/FTA)` where FTM = PTS_BF and FTA = Amt_BF × 2
- Tech FT%: show `pct% (FTM/FTA)` where FTM = PTS_TF and FTA = Amt_TF
- Overall FT%: show `pct% (total FTM / total FTA)`

For types with 0 events, keep showing "—" as before.

### Styling

- The raw counts / fractions should be slightly de-emphasized visually so the percentage remains the primary number. Use a smaller font size or a muted color (e.g., lighter gray) for the counts/fractions.
- Make sure the columns are wide enough to accommodate the longer content without wrapping awkwardly.
- The color coding should still be driven by the percentage value, not affected by the raw counts.

### Pre-calculate in Build Script

Update `build_viewer.py` to pre-calculate and embed:
- FTM and FTA for each foul type per player (for the FT by Type tab fractions)
- These values should already be derivable from the existing embedded component data, but pre-calculating them keeps the HTML clean.

### Validation

- SGA: Shooting Foul FT% should show something like `90.1% (308/342)` — verify the fraction matches the percentage
- Luka: Foul Profile Clean 3PT should show something like `609 (39.8%)` — verify count matches
- Jokic: Bonus Foul FT% should show something like `82.1% (110/134)` — verify against Phase 2 output
