# Adversarial Audit: Effective Field Goal Percentage (eFG%)

**Date:** 2026-03-22
**Formula under audit:** eFG% = (FGM + 0.5 × 3PM) / FGA
**Data basis:** 2,841 player-seasons across six NBA seasons (2020-21 through 2025-26)

---

## 1. The Claim

eFG% claims to measure a player's shooting efficiency from the field, adjusted for the fact that three-point field goals are worth more than two-point field goals. It purports to answer: "Given a player's field goal attempts, how efficiently did they convert those attempts into points, accounting for the extra value of threes?"

---

## 2. The Inputs

| Input | Source | What It Includes | What It Excludes |
|-------|--------|------------------|------------------|
| **FGM** | Box score | All made field goals (2PT + 3PT), including And-1 makes | Free throws, missed shots that drew fouls |
| **3PM** | Box score | All made three-point field goals | Two-point makes |
| **FGA** | Box score | All field goal attempts (2PT + 3PT) | Shooting foul trips (0 FGA), bonus fouls, tech FTs, flagrant FTs, all non-shooting FT events |

Every input is directly observed. No estimation, no derivation. This is a genuine strength.

---

## 3. The Assumptions

### Assumption 1: The 0.5 Multiplier on 3PM

A made three-pointer scores 3 points; a made two-pointer scores 2. The 0.5 bonus converts three-point makes into "two-point-equivalent makes." If you make a three, that is worth 1.5 two-pointers in scoring value (3/2 = 1.5), so you get credit for 1 FGM (already counted) plus an additional 0.5.

**What this assumes:** That the appropriate baseline for measuring shooting efficiency is the two-point field goal. Every shot is evaluated against a 2-point maximum. A perfect 3PT shooter who goes 10-for-10 from three:

```
eFG% = (10 + 0.5 × 10) / 10 = 15/10 = 150%
```

This is not a percentage in any meaningful sense. The 0.5 in eFG% and the "2" in TS% are the same assumption expressed differently — all shooting measured against a 2-point maximum.

### Assumption 2: Free Throws Do Not Exist

eFG% contains zero information about free throws. It does not account for:

- **Shooting fouls (missed shot + FTs):** Produces 0 FGA in the box score. Completely invisible.
- **And-1 FTs:** The made FG is counted, but the bonus free throw is ignored.
- **Bonus/penalty fouls, technical FTs, flagrant FTs, clear path fouls, take fouls, away-from-play fouls:** All invisible.

This is a stated design choice, not a hidden flaw. But ~20-30% of a typical player's scoring possessions are entirely excluded.

### Assumption 3: Denominator Deflation

Players who draw shooting fouls get their denominator reduced relative to the number of scoring opportunities they actually consumed. Two players who each take 20 scoring actions:
- Player A: 20 clean FGAs, no fouls drawn. eFG% denominates over 20.
- Player B: 15 clean FGAs + 5 shooting fouls. eFG% denominates over 15.

Player B had 20 scoring attempts but eFG% only sees 15.

---

## 4. Real Examples

### SGA vs Derrick White (2024-25) — The Comparison eFG% Gets Wrong

| Metric | Derrick White | SGA |
|--------|--------------|-----|
| eFG% | 58.03% | 56.86% |
| Standard TS% | 60.59% | 63.68% |
| Pure TS% | 46.85% | 58.08% |

**eFG% says White was more efficient than SGA.** Pure TS% shows SGA was 11.23pp better. White's high 3PA rate (72.1%) inflates his eFG% through the 0.5 multiplier. SGA's massive free-throw production (669 FTA from 209 shooting fouls, 60 And-1s) is invisible.

### Jarrett Allen (2024-25) — Where eFG% Accidentally Works

```
eFG% = 452/640 = 70.63%
Pure TS% = 70.46%
Gap: +0.17 pp
```

Allen takes almost exclusively 2PT shots (5 three-point attempts all season), so the 0.5 multiplier does nothing. His moderate FT rate means the FT blind spot has minimal impact. For near-exclusive 2PT rim scorers, eFG% happens to give an answer close to truth.

### Duncan Robinson (2024-25) — Maximum 3PT Inflation

```
eFG% = 58.07%
Pure TS% = 45.32%
Gap: +12.75 pp
```

Robinson's 3PA rate is 72.9%. eFG% gives him a 0.5 bonus for every made three. His 3PT efficiency (C1b_eff = 39.21%) is mediocre, but eFG% makes him look solidly above-average.

### Giannis Antetokounmpo (2024-25) — And-1 Blind Spot

```
eFG% = 60.65%
Pure TS% = 59.66%
Gap: +0.99 pp
```

92 And-1s in a season. eFG% counts the made FG but ignores the bonus FT. It cannot distinguish "made 2PT shot" from "made 2PT shot + missed bonus FT." For prolific And-1 players, this is a systematic blind spot.

---

## 5. Systematic Failure Modes

### Failure Mode 1: 3PT Inflation (Systematic)

Every player who takes 3PT shots gets overcredited. Players with 3PA rates above 60% routinely show eFG% values 10-15pp higher than Pure TS%. Players with 3PA rates below 10% show virtually no gap.

### Failure Mode 2: Free Throw Blindness (Systematic)

~20-30% of a typical player's scoring possessions are invisible. Direction of distortion depends on FT skill:
- Good FT shooter + lots of FT trips → eFG% **underrates** them
- Poor FT shooter + lots of FT trips → eFG% can **accidentally overrate** them

### Failure Mode 3: And-1 Distortion

Cannot distinguish "made shot" from "made shot + missed bonus FT." For prolific And-1 players (Giannis, Zion), systematic blind spot.

### Failure Mode 4: Cross-Archetype Comparison Breakdown

- 3PT specialists: inflated by 0.5 multiplier, barely affected by FT blind spot (draw few fouls)
- Rim scorers: minimal 3PT inflation, moderately affected by FT blind spot
- Foul-drawing guards: moderate 3PT inflation AND heavily affected by FT blind spot

eFG% cannot make meaningful cross-archetype comparisons.

---

## 6. The Steelman

1. **Transparency:** Three directly observed box-score inputs. No hidden coefficients. Anyone can compute and verify it.
2. **Answers a specific question well:** "How many points per FGA from field goals?" The formula is exactly half the points-per-FGA from field goals only.
3. **Isolates shooting from foul-drawing:** If you want to evaluate pure FG shooting ability independent of foul-drawing skill, eFG% is the right tool.
4. **Within-archetype comparisons are reasonable:** When two players have similar 3PA rates and FT rates, eFG% gives directionally correct rankings.
5. **Strictly better than FG%:** FG% ignores 3PT value entirely. eFG% is the better version.

---

## 7. Verdict

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Accuracy | C- | Ignores ~25% of scoring opportunities. 3PT inflation distorts by up to 15+pp |
| Transparency | A | Three directly observed inputs, no hidden coefficients |
| Robustness | D+ | Fails systematically for high-3PA and high-FT-rate players |
| Interpretability | C | Exceeds 100% for efficient 3PT shooters |

### Fitness for Purpose

- **"Measure overall scoring efficiency":** Unfit. Ignores 20-30% of scoring possessions.
- **"Measure FG shooting efficiency, adjusted for 3PT value":** Adequate but misleading scale (exceeds 100%).
- **"Compare shooters within similar archetypes":** Adequate. Distortions approximately cancel.
- **"Compare shooters across archetypes or eras":** Unfit. 10-15pp systematic bias.

### Bottom Line

eFG% is an honest, transparent stat that answers a narrow question well: "How many points per FGA from the field?" It is strictly better than FG%. But it is frequently misused as a measure of overall shooting efficiency, where it produces systematic errors that are large, predictable, and directional. The 0.5 in eFG% and the 2 in TS% are the same assumption — all shooting measured against a 2-point max. Pure TS% rejects this assumption entirely.

---

## 8. Comparison

| Feature | eFG% | Standard TS% | Pure TS% |
|---------|------|--------------|----------|
| Includes free throws | No | Yes (via 0.44 × FTA) | Yes (exact, by foul type) |
| Correct 3PT scaling | No (2PT baseline) | No (2PT baseline) | Yes (3PT max = 3) |
| Bounded 0-100% | No | No | Yes |
| Coefficients/estimates | None | 0.44 (estimated) | None |
| Inputs required | 3 (box score) | 4 (box score) | 12 components (play-by-play) |
| Data availability | Universal | Universal | Requires PBP parsing |
| Cross-archetype validity | Poor | Moderate | Good |
