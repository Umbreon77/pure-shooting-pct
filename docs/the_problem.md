# The Problem with True Shooting % (TS%)

True Shooting Percentage (TS%) is the most widely used measure of shooting efficiency in basketball. It attempts to capture a player's total scoring efficiency by accounting for 2-point field goals, 3-point field goals, and free throws in a single number. The intention is sound. The execution has two mathematical flaws, one minor and one fundamental.

Shooting efficiency, at its core, answers a simple question: of all the points a player could have scored given the attempts they took, how many did they actually score? This is already how we measure efficiency for individual shot types. A player who goes 4 for 10 on 3-pointers shot 40%. Said another way, they scored 12 points out of a possible 30 points on their 3-point attempts. A player who goes 7 for 10 on free throws shot 70%, scoring 7 points out of a possible 10. This works cleanly because both the numerator and denominator deal in the same unit: 3-point shots divided by 3-point shots, free throws divided by free throws.

Standard NBA box scores provide 3-point and free throw attempts, makes, and the subsequent efficiency expressed as a percentage. 3P% simply equals 3PM / 3PA. This is a true percentage and an accurate calculation of 3-point efficiency. A player's 3-point shooting efficiency is how many threes they made out of all the threes they took. That makes sense intuitively, and it should.

However, standard box scores do not separate 2-point and 3-point field goal attempts. All shot attempts from the field are combined into a single number: FGA. This is where the problem begins.

Because a 2-point field goal is worth 2 points and a 3-point field goal is worth 3, a single FGA figure blends two different scoring values together. Dividing total field goals made by total field goal attempts does not produce a meaningful efficiency number, because making a 3-pointer generates more points than making a 2-pointer from the same number of attempts. Despite this structural limitation, the resulting FG% is a stat often referenced for both players and teams. This also belies that it does not consider free throws at all.

The methodology behind 3P% and FT% is sound, both logically and mathematically: points scored divided by points possible. TS% strays from this methodology in an attempt to reconcile the difference in point values, and account for free throws, introducing approximations and a denominator structure that distorts the answer, particularly for players who shoot 3-pointers. PS% restores the sound methodology to what shooting efficiency was always intended to measure: points scored divided by points possible. It applies this across all three ways a player can score (2-point field goals, 3-point field goals, and free throws), producing a single figure.

True Shooting Percentage uses this formula:

```
TS% = PTS / (2 × (FGA + 0.44 × FTA))
```

A common criticism of TS% is that the 0.44 coefficient is an approximation. But the 0.44 is actually the least broken part of this formula. The more significant flaw is the **2** in the denominator.

## Problem 1 (Minor): The 0.44 Coefficient

The 0.44 exists to estimate how many possessions free throws consumed. Not every trip to the free throw line is the same:

- An And-1 earns one free throw
- A shooting foul earns two
- A three-point shooting foul earns three

The 0.44 is a league-wide average designed to collapse all of these into a single approximation.

Across 1,104 qualified player-seasons in our play-by-play dataset (2020-21 through 2025-26), the actual league-wide coefficient is approximately **0.453**. Using 0.44 instead produces a mean error of **+0.19 percentage points**. About 90% of players fall within 0.05 of the true coefficient.

That is a small error. Within a single game, the 0.44 can produce noticeable distortions, particularly when a player's foul mix deviates from the league average. But across a full season, the coefficient's inaccuracy is real and worth fixing, not the catastrophic distortion people think it is.

**The 0.44 is a problem. It is not the problem.**

The 0.44 contributes +0.19pp of error on average. The "2" contributes approximately 9-10pp. The part people criticize is roughly 50 times smaller than the less discussed structural flaw. Both figures are derived from the play-by-play and box score data on this site.

## Problem 2 (Fatal): The "2" in the Denominator

The standard formula divides everything by `2 × (FGA + 0.44 × FTA)`. This means every attempt is treated as if its maximum value is 2 points. A player who scores 20 points on 20 attempts gets 20/40 = 50%. That works fine for 2-pointers, but a 3-pointer is worth more than 2.

### Example Box Scores

Pure Shooting % uses a different formula: `PTS / (2×FGA + 3PA + FTA)`. The full derivation is on the Methodology tab. Here is how the two formulas compare on simple examples.

**Perfect shooting: every player converts 100% of their attempts.**

| Scenario | Line | PTS | TS% | PS% |
|---|---|---|---|---|
| 10/10 on 2-pointers | 20 pts, 10 FGA, 0 FTA | 20 | 100.0% | 100.0% |
| 10/10 on 3-pointers | 30 pts, 10 FGA, 0 FTA | 30 | 150.0% | 100.0% |
| 10/10 on free throws | 10 pts, 0 FGA, 10 FTA | 10 | 113.6% | 100.0% |
| 5/5 on 3s + 5/5 on 2s | 25 pts, 10 FGA, 0 FTA | 25 | 125.0% | 100.0% |

All four players scored every possible point on every attempt. PS% gives all four the same score: 100%. TS% ranges from 100% to 150% depending on shot type.

**50% shooting: same accuracy, different shot types.**

| Scenario | Line | PTS | TS% | PS% |
|---|---|---|---|---|
| 5/10 all 2-pointers | 10 pts, 10 FGA, 0 FTA | 10 | 50.0% | 50.0% |
| 5/10 all 3-pointers | 15 pts, 10 FGA, 0 FTA | 15 | 75.0% | 50.0% |
| 3/5 on 3s + 2/5 on 2s | 13 pts, 10 FGA, 0 FTA | 13 | 65.0% | 52.0% |
| 2/5 on 3s + 3/5 on 2s | 12 pts, 10 FGA, 0 FTA | 12 | 60.0% | 48.0% |

Two players shoot 50% from the field on the same number of attempts. PS% correctly gives both 50%. TS% says the 3-point shooter was 25 percentage points more efficient, for shooting the exact same percentage from a different spot on the floor.

This is not a rounding error. It is a structural flaw baked into the formula's design.

## What This Looks Like in Practice

| Player | Season | 3PT Attempt Rate | TS% | PS% | Distortion |
|---|---|---|---|---|---|
| AJ Green | 2025-26 | 85.8% | 60.94% | 43.37% | +17.0 pp |
| Steph Curry | 2020-21 | 51.8% | 65.47% | 53.03% | +12.8 pp |
| Shai Gilgeous-Alexander | 2025-26 | 22.3% | 66.30% | 59.50% | +6.9 pp |
| Deandre Ayton | 2023-24 | 6.6% | 58.48% | 57.96% | +0.5 pp |

The distortion is not random noise. It is almost perfectly correlated with 3PT attempt rate. Players who live behind the arc are systematically overrated by TS%. Players who live at the rim are barely affected. The average distortion across the league is **~9-10 percentage points**, ranging from about 0.5pp to 17.5pp at the individual player level.

## What This Means for Comparisons

**Cross-archetype comparisons (3PT shooter vs. rim scorer):** Unfit for purpose. A 15+ percentage point structural bias between player archetypes means TS% cannot answer the question "who was more efficient?" when the players operate in different parts of the floor.

**Within-archetype comparisons (guard vs. guard, center vs. center):** Adequate. When two players have similar 3PT attempt rates, the distortion is similar and largely cancels out. TS% rankings within a position group tend to hold.

**Historical and era comparisons:** Increasingly unfit. The NBA has shifted dramatically toward 3PT attempts over the past decade. Comparing a 2010 player at 20% 3PT rate against a 2025 player at 50% 3PT rate using TS% conflates efficiency improvement with shot-type inflation.

## When A "Percentage" Exceeds 100%

A percentage that exceeds 100% is not a percentage. Across six NBA seasons (2020-21 through 2025-26), **283 individual games** produced a TS% above 100%, in games with at least 10 scoring possessions. These are not obscure bench performances. They include All-Stars and playoff starters:

| Player | Date | Line | TS% | PS% |
|---|---|---|---|---|
| Luke Kennard | Mar 24, 2023 | 30 pts, 11 FGA, 0 FTA | 136.4% | 90.9% |
| Sam Merrill | Feb 11, 2026 | 32 pts, 12 FGA, 1 FTA | 128.6% | 91.7% |
| Michael Porter Jr. | Mar 2, 2024 | 25 pts, 10 FGA, 0 FTA | 125.0% | 100.0% |
| Davis Bertans | Feb 17, 2021 | 35 pts, 11 FGA, 8 FTA | 120.5% | 85.7% |
| Tyrese Haliburton | Apr 1, 2022 | 30 pts, 11 FGA, 4 FTA | 117.5% | 92.3% |
| Paul George | Mar 14, 2024 | 28 pts, 12 FGA, 0 FTA | 116.7% | 91.7% |

The pattern: 3-point-heavy games with few free throws. The "2" denominator gives these players credit for scoring 3 points on an attempt calibrated for 2, and the formula has no mechanism to prevent the result from exceeding 100%. PS% measures each of these games on a true 0-100% scale.

## The Name Is a Misnomer

TS% is not bounded at 100%. It is not a true percentage. And it does not measure shooting efficiency in a way that holds across player archetypes or eras. The "True" in "True Shooting Percentage" was meant to signal that it accounts for free throws and three-pointers, an improvement over raw field goal percentage. That was the right instinct. The execution is broken.

**Pure Shooting % fixes both problems** with a simpler formula: `PTS / (2×FGA + 3PA + FTA)`. Four standard box score numbers, no arbitrary coefficients. The result is a true 0-100% scale where 100% means a player scored every possible point on every scoring opportunity they had.

## Same Efficiency, Different TS%

The following pairs of hypothetical box scores demonstrate the distortion. In each pair, both players scored the same number of points out of the same maximum possible points, giving them identical PS%. TS% gives the 3-point shooter a higher score every time.

| Pair | Player | Line | PTS | Max PTS | PS% | TS% |
|---|---|---|---|---|---|---|
| Small gap | Mid-range scorer | 8/16 2PT, 1/2 3PT, 3/4 FT | 22 | 42 | 52.4% | 55.7% |
| | Perimeter scorer | 8/13 2PT, 1/4 3PT, 3/4 FT | 22 | 42 | 52.4% | 58.6% |
| Medium gap | Interior scorer | 10/18 2PT, 1/2 3PT, 5/8 FT | 28 | 50 | 56.0% | 59.5% |
| | Perimeter scorer | 7/12 2PT, 3/6 3PT, 5/8 FT | 28 | 50 | 56.0% | 65.1% |
| Large gap | Rim scorer | 11/21 2PT, 0/0 3PT, 8/10 FT | 30 | 52 | 57.7% | 59.1% |
| | 3PT shooter | 7/12 2PT, 3/6 3PT, 7/10 FT | 30 | 52 | 57.7% | 67.0% |

## The Relationship Is Structural

Across all 47 seasons, 3-point attempt rate explains 99.86% of the variance in the distortion between TS% and PS% (R² = 0.9986). The relationship follows: Delta = -0.91 + (-0.208 × 3PA Rate). Every 1 percentage point increase in league 3PA rate widens the gap by approximately 0.21 percentage points.

At the current league 3PA rate of ~42%, the average distortion is approximately 9.7 percentage points. If the league reaches 50% 3PA rate, the distortion would exceed 11 percentage points. The gap is not stabilizing. It is growing.

This means TS% systematically overrates players who shoot more 3-pointers and underrates those who don't. Two players with identical actual shooting efficiency will receive different TS% scores if one takes more 3-pointers than the other. PS% eliminates this bias entirely: a player's score depends only on how many of their available points they actually scored, regardless of where they shot from.
