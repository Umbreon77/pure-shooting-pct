# Pure Shooting % — Proof of Concept

## Game: Los Angeles Lakers 124, Houston Rockets 116

**Date:** March 18, 2026
**Location:** Toyota Center, Houston, TX
**Data source:** NBA CDN play-by-play JSON (`playbyplay_0022501007.json`)

---

## Player: Luka Doncic

**Box score line:** 40 PTS | 12-25 FG (48.0%) | 7-17 3PT (41.2%) | 9-14 FT (64.3%)

Every scoring event below was extracted from the official NBA play-by-play feed and categorized into PS% components per the definitions in `pure_ts_pct_terms_and_key.md`. The box score totals were reconciled against the play-by-play data — all figures match exactly.

---

## Component Breakdown

### C1a — Clean 2PT Field Goal Attempts

Uncontested by fouls. Each attempt is 1 scoring possession with max = 2 points.

| # | Quarter | Clock | Result | PTS | Description |
|---|---------|-------|--------|-----|-------------|
| 1 | Q1 | 11:13 | MISS | 0 | 10' pullup Shot |
| 2 | Q1 | 5:56 | MISS | 0 | 16' fadeaway Shot |
| 3 | Q1 | 2:55 | MADE | 2 | 9' driving floating Jump Shot |
| 4 | Q2 | 5:10 | MADE | 2 | running finger roll Layup |
| 5 | Q3 | 10:03 | MISS | 0 | 16' step back Shot |
| 6 | Q3 | 0:15 | MADE | 2 | driving finger roll Layup |
| 7 | Q4 | 5:03 | MADE | 2 | 13' turnaround fadeaway Jump Shot |

**FGA₂ = 7 | PTS₂ = 8 | Eff₂ = 8 / (7 x 2) = 8/14 = 0.5714**

Note: The Q2 0:17 layup is excluded from C1a — it was an And-1 (see C4 below). Box score records it as an FGA, but in PS% it belongs to its own component to avoid double-counting.

---

### C1b — Clean 3PT Field Goal Attempts

Uncontested by fouls. Each attempt is 1 scoring possession with max = 3 points.

| # | Quarter | Clock | Result | PTS | Description |
|---|---------|-------|--------|-----|-------------|
| 1 | Q1 | 8:33 | MISS | 0 | 25' step back 3PT |
| 2 | Q1 | 4:57 | MADE | 3 | 28' 3PT |
| 3 | Q1 | 4:15 | MISS | 0 | 24' step back 3PT |
| 4 | Q1 | 1:11 | MADE | 3 | 26' 3PT running pullup |
| 5 | Q1 | 0:30 | MISS | 0 | 24' step back 3PT |
| 6 | Q1 | 0:11 | MADE | 3 | 25' 3PT |
| 7 | Q2 | 3:17 | MISS | 0 | 26' step back 3PT |
| 8 | Q2 | 2:38 | MISS | 0 | 24' step back 3PT |
| 9 | Q2 | 0:29 | MISS | 0 | step back 3PT |
| 10 | Q3 | 9:36 | MADE | 3 | 26' 3PT |
| 11 | Q3 | 8:47 | MISS | 0 | 25' 3PT |
| 12 | Q3 | 2:45 | MISS | 0 | 25' running pullup 3PT |
| 13 | Q3 | 1:45 | MADE | 3 | 25' 3PT pullup |
| 14 | Q3 | 0:01 | MISS | 0 | 26' step back 3PT |
| 15 | Q4 | 3:14 | MADE | 3 | 26' 3PT step back |
| 16 | Q4 | 1:56 | MISS | 0 | 28' step back 3PT |
| 17 | Q4 | 0:58 | MADE | 3 | 24' 3PT step back |

**FGA₃ = 17 | PTS₃ = 21 | Eff₃ = 21 / (17 x 3) = 21/51 = 0.4118**

---

### C2 — 2PT Shooting Fouls

Fouled on a 2PT attempt, shot does not go in, 2 FTAs awarded. Not recorded as an FGA in the box score, but IS a scoring possession. Max = 2 per event.

| # | Quarter | Clock | Fouler | FT Results | PTS |
|---|---------|-------|--------|------------|-----|
| 1 | Q1 | 4:42 | R. Sheppard | MADE, MADE (2/2) | 2 |
| 2 | Q3 | 8:17 | T. Eason | MISS, MADE (1/2) | 1 |

**Amt_SF2 = 2 | PTS_SF2 = 3 | Eff_SF2 = 3 / (2 x 2) = 3/4 = 0.7500**

---

### C3 — 3PT Shooting Fouls

Fouled on a 3PT attempt, shot does not go in, 3 FTAs awarded. Not recorded as an FGA in the box score, but IS a scoring possession. Max = 3 per event.

| # | Quarter | Clock | Fouler | FT Results | PTS |
|---|---------|-------|--------|------------|-----|
| 1 | Q1 | 9:50 | J. Smith Jr. | MISS, MISS, MISS (0/3) | 0 |

**Amt_SF3 = 1 | PTS_SF3 = 0 | Eff_SF3 = 0 / (1 x 3) = 0/3 = 0.0000**

---

### C4 — And-1 (2PT)

Made 2PT field goal plus fouled on the play, 1 bonus FTA awarded. The entire sequence — made basket plus free throw — is 1 scoring possession. Max = 3 per event (2 for the made shot + 1 for the FT).

| # | Quarter | Clock | Fouler | FG | FT Result | PTS |
|---|---------|-------|--------|----|-----------|-----|
| 1 | Q2 | 0:17 | J. Okogie | 2PT MADE (finger roll Layup) | MADE (1/1) | 3 |

**Amt_A1₂ = 1 | PTS_A1₂ = 3 | Eff_A1₂ = 3 / (1 x 3) = 3/3 = 1.0000**

---

### C5 — And-1 (3PT)

None this game.

**Amt_A1₃ = 0**

---

### C6a through C6e — Penalty Free Throws

No technical fouls, flagrant fouls, clear path fouls, transition take fouls, or away-from-play fouls were drawn by Doncic in this game.

**Amt_TF = 0 | Amt_FF = 0 | Amt_CP = 0 | Amt_TK = 0 | Amt_AP = 0**

Note on the Q4 0:30 foul: The play-by-play describes this as a "take personal FOUL" by T. Eason. However, per NBA rules, transition take foul penalties (1 FTA + possession, Component 6d) do not apply in the last 2 minutes of the 4th quarter. With 30.8 seconds remaining, this is a standard personal foul in the bonus — 2 FTAs awarded. Classified under C6f below.

---

### C6f — Bonus (Penalty) Foul Free Throws

Non-shooting personal fouls where the team is in the penalty, resulting in 2 FTAs. The player was not in a shooting motion. Max = 2 per event.

| # | Quarter | Clock | Fouler | FT Results | PTS | Notes |
|---|---------|-------|--------|------------|-----|-------|
| 1 | Q3 | 3:07 | J. Okogie | MADE, MADE (2/2) | 2 | Non-shooting, team in bonus |
| 2 | Q3 | 1:13 | R. Sheppard | MADE, MISS (1/2) | 1 | Non-shooting, team in bonus |
| 3 | Q4 | 0:30 | T. Eason | MADE, MADE (2/2) | 2 | "Take" foul in final 30 sec, bonus rules apply |

**Amt_BF = 3 | PTS_BF = 5 | Eff_BF = 5 / (3 x 2) = 5/6 = 0.8333**

---

## Points Reconciliation

| Source | PTS |
|--------|-----|
| C1a: Clean 2PT FGA | 8 |
| C1b: Clean 3PT FGA | 21 |
| C2: 2PT Shooting Fouls | 3 |
| C3: 3PT Shooting Fouls | 0 |
| C4: And-1 2PT | 3 |
| C6f: Bonus Fouls | 5 |
| **Total** | **40** |

Matches box score: **40 PTS**

---

## FGA Reconciliation

The box score records 25 FGA. In our framework:

- C1a clean 2PT FGA: 7
- C1b clean 3PT FGA: 17
- C4 And-1 2PT: 1 (box score counts this as an FGA and a make)
- **Total: 7 + 17 + 1 = 25 FGA**

The remaining 6 scoring possessions (2 from C2, 1 from C3, 3 from C6f) produced 0 FGA in the box score but consumed real scoring possessions. This is precisely what the standard TS% formula tries to approximate with `0.44 x FTA` and what PS% counts exactly.

---

## FTA Reconciliation

| Source | FTA |
|--------|-----|
| C2: 2PT Shooting Fouls (2 events x 2 FTA) | 4 |
| C3: 3PT Shooting Fouls (1 event x 3 FTA) | 3 |
| C4: And-1 2PT (1 event x 1 FTA) | 1 |
| C6f: Bonus Fouls (3 events x 2 FTA) | 6 |
| **Total** | **14** |

Matches box score: **14 FTA**

---

## PS% Calculation

### The Simple Formula

From the box score line — 40 PTS, 25 FGA, 17 3PA, 14 FTA:

```
PS% = PTS / (2×FGA + 3PA + FTA)
    = 40 / (2×25 + 17 + 14)
         = 40 / (50 + 17 + 14)
         = 40 / 81
         = 0.4938
```

### **PS% = 49.4%**

### Component Verification

The same result derived from the 12-component breakdown, confirming the simple formula is correct:

| Component | Events | PTS | Max PTS | Efficiency |
|-----------|--------|-----|---------|------------|
| C1a: Clean 2PT FGA | 7 | 8 | 14 | 8/14 = 0.5714 |
| C1b: Clean 3PT FGA | 17 | 21 | 51 | 21/51 = 0.4118 |
| C2: 2PT Shooting Foul | 2 | 3 | 4 | 3/4 = 0.7500 |
| C3: 3PT Shooting Foul | 1 | 0 | 3 | 0/3 = 0.0000 |
| C4: And-1 2PT | 1 | 3 | 3 | 3/3 = 1.0000 |
| C6f: Bonus Foul | 3 | 5 | 6 | 5/6 = 0.8333 |
| **Total** | **31** | **40** | **81** | |

Component max (81) = simple formula denominator (2×25 + 17 + 14 = 81). The 12-component PBP derivation proves the box score formula is exact.

---

## Standard TS% Comparison

```
Standard TS% = PTS / (2 x (FGA + 0.44 x FTA))
             = 40 / (2 x (25 + 0.44 x 14))
             = 40 / (2 x (25 + 6.16))
             = 40 / (2 x 31.16)
             = 40 / 62.32
             = 0.6420
```

### **Standard TS% = 64.2%**

### **Delta: -14.8 percentage points**

---

## Why the Gap Exists

Standard TS% overrated Doncic's efficiency in this game by 14.8 percentage points. Three factors drive the gap:

**1. The 0-for-3 from the line on the 3PT shooting foul (C3)**

In Q1 at 9:50, Doncic drew a 3PT shooting foul on J. Smith Jr. and missed all three free throws. This was a real scoring possession where he had a chance at 3 points and scored 0 — a 0.0% efficiency event. Standard TS% buries this inside `0.44 x FTA`, treating those 3 free throw attempts as roughly 1.32 "true shot attempts" worth about 2.64 max points. PS% correctly recognizes this as a single possession worth up to 3 points that yielded 0. The 0.44 coefficient has no mechanism to capture the severity of going 0-for-3 on a single foul event.

**2. Bonus foul possessions that 0.44 underweights (C6f)**

Doncic drew 3 bonus fouls producing 6 FTAs. Standard TS% converts those 6 FTAs into `0.44 x 6 = 2.64` additional "true shot attempts," implying roughly 5.28 max points. PS% correctly counts 3 scoring possessions with a combined max of 6 points. The 0.44 coefficient was designed around a league-wide average mix of foul types — it was never meant to be accurate for a single game where one player's foul distribution deviates from the mean.

**3. Scale difference: what each metric actually measures**

Standard TS% divides points by `2 x TSA`, anchoring the scale so that 50% represents 1 point per "true shot attempt" (roughly league-average efficiency). PS% divides each component's points by that component's max possible points, producing a true 0-to-100% scale where 100% means the player scored every possible point on every scoring possession. These are fundamentally different baselines. PS% asks: "Of all the points this player could have scored given the exact opportunities they had, what fraction did they actually score?" Standard TS% asks a looser question using approximated denominators.

In this game, Doncic had 31 scoring possessions with a combined max of 81 possible points and scored 40. PS% = 40/81 = 49.4%. This is materially lower than the 64.2% that standard TS% assigns.

---

## Key Takeaway

This game proves the formula works end-to-end:

1. **Every scoring event is accounted for.** 31 scoring possessions were extracted from the play-by-play and classified into 6 active components. No events were dropped or double-counted.

2. **Box score totals reconcile perfectly.** FGA (25), 3PT FGA (17), FTA (14), and PTS (40) all match when reconstructed from the component-level data.

3. **All weights sum to 1.** The 6 active components' weights (7/31 + 17/31 + 2/31 + 1/31 + 1/31 + 3/31) equal exactly 31/31 = 1.

4. **The ratio produces a meaningful single percentage.** 49.4% means Doncic scored 49.4% of the maximum possible points across all scoring possessions he had.

5. **The gap from standard TS% is explainable.** Every percentage point of the -14.8 pp difference can be traced to specific events that the 0.44 coefficient mishandles — the 0/3 FT trip, the bonus fouls, and the scale difference between the two metrics.

This is exactly the type of single-game distortion that PS% was built to expose. The 0.44 approximation assumes a "typical" distribution of foul types. Doncic's game featured an atypical mix — a 3PT shooting foul with 0 points scored, a 2PT And-1 with maximum points scored, and 3 bonus foul events — and the approximation broke down. PS% does not approximate. It counts.
