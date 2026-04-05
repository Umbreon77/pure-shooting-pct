# Adversarial Audit: Player Efficiency Rating (PER)

**Date:** 2026-03-22
**Formula under audit:** Hollinger's Player Efficiency Rating
**Creator:** John Hollinger (introduced circa 2003, refined through ESPN tenure)
**Data basis:** 2024-25 and 2025-26 Pure TS% league data; structural analysis of the PER formula itself

---

## 1. The Claim

PER claims to be \"a per-minute rating of a player's performance\" that boils all box-score production into a single number, where 15.0 equals league average, and higher is better.

The implied claim is stronger: PER positions itself as a measure of **overall player value** -- not just offensive box-score production. By presenting one number on a common scale, it implies commensurability: that a 25 PER center is \"more efficient\" than a 20 PER wing, full stop.

---

## 2. The Inputs

### 2.1 Direct Box-Score Inputs

| Input | Source | Observed or Derived? | Notes |
|-------|--------|---------------------|-------|
| FGM | Box score | Observed | Made field goals |
| FGA | Box score | Observed | Field goal attempts |
| FTM | Box score | Observed | Made free throws |
| FTA | Box score | Observed | Free throw attempts |
| 3PM | Box score | Observed | Made three-pointers |
| AST | Box score | Observed | Assists |
| ORB | Box score | Observed | Offensive rebounds |
| DRB | Box score | Observed | Defensive rebounds |
| STL | Box score | Observed | Steals |
| BLK | Box score | Observed | Blocks |
| TO | Box score | Observed | Turnovers |
| PF | Box score | Observed | Personal fouls |
| MIN | Box score | Observed | Minutes played |

### 2.2 Team and League Inputs

| Input | Source | Notes |
|-------|--------|-------|
| Team pace (Tm_Pace) | Derived | Possessions per 48 minutes |
| League pace (Lg_Pace) | Derived | League-average possessions per 48 minutes |
| League FT rate | Derived | League FTM/FTA |
| League ORB% | Derived | Fraction of available offensive rebounds grabbed league-wide |
| League averages for AST, FG, FT, TO, etc. | Derived | Used in normalization |

### 2.3 Formula Structure

PER is calculated in three stages:

**Stage 1: Raw unadjusted PER (uPER)** -- the core formula per minute, combining 13 box-score inputs with league-derived coefficients including `factor`, `VOP` (value of a possession), and `DRB%`.

**Stage 2: Pace Adjustment** -- `aPER = uPER * (Lg_Pace / Tm_Pace)`

**Stage 3: League Normalization** -- `PER = aPER * (15 / Lg_aPER)` -- forces league-average PER to exactly 15.0 every season.

---

## 3. The Assumptions

### Assumption 1: The Coefficient Weights Are Defensible

This is the central weakness. An assist is worth (2/3). A steal is worth +1. A block is worth VOP * DRB% (~0.7). **Where do these come from?** They are Hollinger's judgment calls. There is no published derivation that starts from first principles and arrives at these specific coefficients. No regression model. No theoretical framework. These are calibrated guesses dressed in mathematical notation.

The (2/3) assist coefficient: why not 0.5? Why not 0.75? The number could reasonably be 0.4 to 0.8 depending on counterfactual beliefs. Hollinger's argument is plausible assertion, not derivation.

**Epistemic status:** Established fact that the coefficients are Hollinger's choices. I cannot prove an alternative set is correct, but the burden of proof is on the formula, and PER does not meet it.

### Assumption 2: The 0.44 Free Throw Coefficient (Again)

PER inherits the 0.44 from TS%. It appears in the missed-FT penalty term and VOP calculation. Our Pure TS% data shows gaps of 5-13+pp between standard TS% and Pure TS% for individual players. PER inherits and compounds this error.

### Assumption 3: Pace Adjustment Is Sufficient Context

Pace adjustment controls for one dimension only. It does not control for quality of teammates, role in the offense (starter vs. bench against second units), or garbage time.

### Assumption 4: Normalizing to 15.0 Creates Meaningful Cross-Era Comparisons

Forces league-average PER = 15.0 every season, creating the illusion of cross-era comparability. But underlying distributions may differ. The multiplicative scaling preserves rankings but alters distances between players in non-uniform ways.

### Assumption 5: Defense Can Be Captured by Steals and Blocks

**The most devastating assumption.** PER's defensive model is: steals (+1), blocks (+VOP * DRB%), personal fouls (penalty). That is it. No rim protection beyond blocks. No perimeter defense. No help defense. No positioning. No contest rates. No deflections. No charges drawn.

A player who contests 15 shots per game and holds opponents to 5% below expected FG% gets zero credit. A player who gambles for steals (2/game but allows blow-by drives) gets +2 PER credit.

### Assumption 6: Volume Is Not Penalized Proportionally

High-usage players tend to have higher PERs than equally efficient low-usage players. PER does not distinguish between \"taking 25 shots because you're SGA\" and \"taking 25 shots because nobody else on your bad team will.\"

### Assumption 7: Offensive Rebounds Are ~3x More Valuable Than Defensive Rebounds

Directionally correct, but the specific ratio is derived from league averages without justification for why 3x (rather than 2x or 5x) is correct.

---

## 4. The Math -- Worked Examples with Real Data

### 4.1 Nikola Jokic (2024-25)
- 69 GP, 2015 PTS, 1325 FGA, 438 FTA
- Pure TS%: 60.27% | Standard TS%: 66.38% | Delta: -6.11pp

PER loves Jokic (historically 30+) because he accumulates every box-score stat. But PER double-counts: his assists create points also credited to scorers' FGM. The (2/3) coefficient reduces but does not eliminate this. And his standard TS% overstates efficiency by 6.11pp, which PER inherits through its 0.44-dependent terms.

### 4.2 Evan Mobley (2024-25) -- Defensive Anchor Blind Spot
- 70 GP, 1294 PTS, 891 FGA, 295 FTA
- Pure TS%: 57.61% | Standard TS%: 63.38%

Elite rim protector anchoring Cleveland's top defense. PER sees blocks and steals only. Cannot see contest rate, help rotations, switching ability, or deterrent effect. His PER (~18-20) understates total impact by 5-8+ points.

### 4.3 James Harden (2024-25) -- Free-Throw-Drawing Machine
- 79 GP, 1802 PTS, 1295 FGA, 578 FTA
- Pure TS%: 48.44% | Standard TS%: 58.15% | Delta: -9.72pp

The 9.72pp TS% gap means PER systematically misprices Harden's efficiency. His unusual foul-drawing profile (non-shooting fouls, bonus fouls, 3PT shooting fouls) breaks the 0.44 assumption badly.

### 4.4 Derrick White (2024-25) -- 3-and-D Player Gets Crushed
- 76 GP, 1248 PTS, 959 FGA, 161 FTA
- Pure TS%: 46.85% | Standard TS%: 60.59% | Delta: -13.74pp

Elite defender. PER (~13-14) says below-average player. Every serious defensive metric and coaching consensus says otherwise. His perimeter defense, pass denial, and switching versatility are worth zero in PER.

### 4.5 Stephen Curry (2024-25) -- Gravity Is Invisible
- 70 GP, 1718 PTS, 1258 FGA, 299 FTA
- Pure TS%: 49.57% | Standard TS%: 61.82% | Delta: -12.25pp

PER inherits the 12.25pp TS% inflation. And PER cannot capture gravity -- Curry's mere presence distorts defenses, creating points that appear in *other players'* PER scores.

---

## 5. Systematic Failure Modes

### Failure Mode 1: Offense Over Defense (Structural, Unfixable)
PER is ~80-85% offensive by weight. **Overcredited:** high-usage scorers (Westbrook career PER ~21 despite stretches of below-average efficiency), stat-stuffing big men, steal gamblers. **Undercredited:** elite perimeter defenders (White, Holiday, Caruso), rim protectors whose impact is in contest rates (Adebayo), help defenders.

Not fixable within the framework. The box score does not contain enough defensive information.

### Failure Mode 2: High-Usage Inefficiency Trap
Jordan Poole (2024-25): 48.07% Pure TS% (below average) but 20+ PPG volume gives PER ~15-17. Christian Braun: 60.14% Pure TS% (elite) but lower usage means lower PER. PER does not adequately penalize inefficient volume.

### Failure Mode 3: Rebound Inflation for Big Men
Uncontested rebounds get nearly the same PER credit as contested ones. Our tracking data shows contested/uncontested breakdowns that PER ignores entirely. Systematically inflates big men relative to guards.

### Failure Mode 4: Per-Minute Distortion
Bench sparkplugs vs. second units get inflated per-minute stats. Starters facing best defenders for 36 minutes are comparatively penalized. Minimum-minute games produce extreme outliers.

### Failure Mode 5: Assists Double-Count Problem
Player A assists Player B: A gets +(2/3), B gets full FGM credit. Combined PER credit exceeds actual points scored. Teams with high assist rates (Denver, Boston) get inflated total PER. Creates team-context bias that pace adjustment does not fix.

---

## 6. The Steelman

1. **Groundbreaking for its era** -- moved discourse beyond PPG/RPG/APG. Holds.
2. **All-observed inputs** -- replicable and verifiable from box scores. Holds.
3. **Pace adjustment directionally correct** -- better than nothing. Holds.
4. **15.0 = average is intuitive and communicable.** Holds.
5. **Correlates with team wins.** Weaker -- driven almost entirely by offensive component.
6. **Coefficients not obviously wrong.** Weakest form of justification -- \"we cannot prove wrong\" is not \"shown to be right.\"
7. **Provides rough rankings most people want.** Undermined by systematic bias against defensive specialists and across positions.

**The steelman holds for historical importance and communicability. It does not hold for accuracy.**

---

## 7. The Verdict

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| **Accuracy** | D+ | ~80-85% offensive, barely captures defense. Inherits 0.44 error. Coefficient weights are unjustified assertions. |
| **Transparency** | B- | Formula public, inputs observed. But complexity obscures that coefficients are judgment calls, not derivations. |
| **Robustness** | D | Fails systematically across archetypes. Error is directional, not random. |
| **Interpretability** | B | 15.0 = average scale is genuinely useful for communication. |

### Fitness for Purpose

| Use Case | Fitness |
|----------|---------|
| \"Measure overall player value\" | **Unfit** |
| \"Rank offensive box-score production per minute\" | **Adequate** |
| \"Compare players across positions\" | **Unfit** |
| \"Compare players across eras\" | **Marginal** |
| \"Quick shorthand for who's playing well\" | **Adequate** (if you already know its biases) |

### The Kill Shot

PER's fatal flaw is the combination of: (1) unjustified coefficient weights presented as derivations, (2) near-total defensive blindness in a stat claiming to measure overall player performance, and (3) inherited 0.44 error compounding efficiency mismeasurement. It measures \"offensive box-score accumulation, pace-adjusted, per minute, with a light garnish of steals and blocks.\"

**PER was an important stat in 2003. It is an obsolete one in 2026.**

---

## 8. Comparison to Pure TS% Approach

| Feature | PER | Pure TS% |
|---------|-----|----------|
| What it measures | Offensive box-score accumulation (mostly) | Scoring efficiency per scoring possession |
| Honest about scope? | No -- \"Player Efficiency Rating\" implies totality | Yes -- explicitly about scoring possessions |
| Coefficients | Hollinger's judgment calls | None -- all directly observed |
| Defense | Steals + blocks only | Not in scope (correctly excluded) |
| Free throw handling | Inherits 0.44 approximation | Exact, by foul type (12 components) |
| Scale | 15.0 = average, unbounded | 0% to 100%, true percentage |
| Positional bias | Heavy | Minimal |

PER's inclusion of steals and blocks as a defensive proxy actually makes it *worse* than ignoring defense. By including a bad defensive signal, PER gives the false impression that defense is accounted for. A metric that openly says \"I don't measure defense\" (like Pure TS%) is more honest and less misleading than one that pretends to measure defense through steals and blocks alone.

---

**File intended for:** `/Users/zfreud/NBAstats/audits/per_audit.md`
