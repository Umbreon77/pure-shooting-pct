# Pure Shooting Percentage — Terms & Key

## What This Is

A shooting efficiency metric that replaces the NBA's standard True Shooting Percentage (TS%) with a mathematically exact calculation. No approximations, no arbitrary coefficients.

---

## The Formula

```
PS% = PTS / (2×FGA + 3PA + FTA)
```

Four standard box score numbers. The denominator is the maximum possible points a player could have scored:

- Every FGA is worth at most 2 points → `2×FGA`
- Every 3-point attempt is worth 1 more point beyond that → `+ 3PA`
- Every free throw attempt is worth at most 1 point → `+ FTA`

The result is a true 0–100% scale where 100% means the player scored every possible point. Compare to standard TS%: `PTS / (2 × (FGA + 0.44 × FTA))` — same numerator, but TS% uses a universal "2" that breaks on 3-pointers and an arbitrary 0.44 coefficient.

---

## Component Derivation

The formula above was derived by classifying every scoring possession into 12 components (C1a–C6f) from play-by-play data. This derivation proves the formula is correct and also powers diagnostic breakdowns — efficiency by foul type, And-1 rates, hidden possessions — that don't exist in box score data alone. The component definitions below document the full derivation.

---

## General Terms

| Term | Meaning |
|------|---------|
| **Max Possible Points** | The denominator of the formula: `2×FGA + 3PA + FTA`. The total points a player could have scored given every attempt they took. This is the core concept — not possessions, not attempts, but points that could have been scored. |
| **Scoring Possession** | A single scoring event (diagnostic term). Broader than FGA — includes shooting fouls, bonus fouls, and other events that produce FTAs but no FGA. Used in the component breakdown but not needed for the headline formula. |
| **Efficiency (Eff)** | Points scored on a given type of event divided by the maximum possible points for that type. Always between 0 and 1. Used in per-component diagnostics. |
| **Weight (w)** | The proportion of a player's total scoring possessions that a given type represents. All weights sum to 1. Used in per-component diagnostics. |

---

## Component 1 — Clean Field Goal Attempts (no foul on the play)

A player takes a 2PT or 3PT shot and no foul occurs on the play. Assisted or unassisted does not matter.

| Symbol | What It Means |
|--------|---------------|
| **PTS₂** | Total points scored on clean 2PT field goals |
| **PTS₃** | Total points scored on clean 3PT field goals |
| **FGA₂** | Number of clean 2PT field goal attempts (no foul on the play) |
| **FGA₃** | Number of clean 3PT field goal attempts (no foul on the play) |
| **Eff₂** | Efficiency on clean 2PT attempts = PTS₂ / (FGA₂ × 2) |
| **Eff₃** | Efficiency on clean 3PT attempts = PTS₃ / (FGA₃ × 3) |
| **w₂** | Weight = FGA₂ / Total Scoring Possessions |
| **w₃** | Weight = FGA₃ / Total Scoring Possessions |

**Why multiply by 2 or 3 in the denominator?** Because that's the max points possible on that type of attempt. A 2PT shot can yield at most 2 points. A 3PT shot can yield at most 3. Dividing actual points by max points gives us a clean 0-to-1 efficiency.

---

## Component 2 — 2PT Shooting Fouls (no made field goal)

A player gets fouled on a 2PT shot attempt, the shot does NOT go in, and the player goes to the free throw line for 2 attempts. This is NOT recorded as an FGA in the box score, but it IS a scoring possession in our formula.

| Symbol | What It Means |
|--------|---------------|
| **PTS_SF2** | Total points scored on free throws from 2PT shooting fouls |
| **Amt_SF2** | Number of 2PT shooting foul events (each event = 1 scoring possession, regardless of FTs made or missed) |
| **Eff_SF2** | Efficiency on 2PT shooting fouls = PTS_SF2 / (Amt_SF2 × 2) |
| **w_SF2** | Weight = Amt_SF2 / Total Scoring Possessions |

**Why multiply by 2?** Each 2PT shooting foul event sends the player to the line for 2 free throws, each worth 1 point. Max possible = 2.

---

## Component 3 — 3PT Shooting Fouls (no made field goal)

A player gets fouled on a 3PT shot attempt, the shot does NOT go in, and the player goes to the free throw line for 3 attempts. Like Component 2, this is NOT recorded as an FGA in the box score, but it IS a scoring possession in our formula.

| Symbol | What It Means |
|--------|---------------|
| **PTS_SF3** | Total points scored on free throws from 3PT shooting fouls |
| **Amt_SF3** | Number of 3PT shooting foul events (each event = 1 scoring possession, regardless of FTs made or missed) |
| **Eff_SF3** | Efficiency on 3PT shooting fouls = PTS_SF3 / (Amt_SF3 × 3) |
| **w_SF3** | Weight = Amt_SF3 / Total Scoring Possessions |

**Why multiply by 3?** Each 3PT shooting foul event sends the player to the line for 3 free throws, each worth 1 point. Max possible = 3.

---

## Component 4 — And-1s (2PT)

A player makes a 2PT field goal AND is fouled on the play, earning 1 bonus free throw attempt. The made basket is always 2 points (if the shot doesn't go in, it's a shooting foul — Component 2, not an And-1). The free throw adds 0 or 1 point. This entire sequence is 1 scoring possession. Note: the box score records this as an FGA and a make — so And-1 2PT makes must be **excluded** from Component 1's FGA₂ count to avoid double-counting.

| Symbol | What It Means |
|--------|---------------|
| **PTS_A1₂** | Total points scored on 2PT And-1 plays (made FG + FT result combined) |
| **Amt_A1₂** | Number of 2PT And-1 events (each event = 1 scoring possession) |
| **Eff_A1₂** | Efficiency on 2PT And-1s = PTS_A1₂ / (Amt_A1₂ × 3) |
| **w_A1₂** | Weight = Amt_A1₂ / Total Scoring Possessions |

**Why multiply by 3?** The made 2PT shot is worth 2, plus the bonus free throw is worth up to 1. Max possible = 3 per event.

---

## Component 5 — And-1s (3PT)

A player makes a 3PT field goal AND is fouled on the play, earning 1 bonus free throw attempt. The made basket is always 3 points. The free throw adds 0 or 1 point. This entire sequence is 1 scoring possession. Like Component 4, the box score records this as an FGA and a make — so And-1 3PT makes must be **excluded** from Component 1's FGA₃ count to avoid double-counting.

| Symbol | What It Means |
|--------|---------------|
| **PTS_A1₃** | Total points scored on 3PT And-1 plays (made FG + FT result combined) |
| **Amt_A1₃** | Number of 3PT And-1 events (each event = 1 scoring possession) |
| **Eff_A1₃** | Efficiency on 3PT And-1s = PTS_A1₃ / (Amt_A1₃ × 4) |
| **w_A1₃** | Weight = Amt_A1₃ / Total Scoring Possessions |

**Why multiply by 4?** The made 3PT shot is worth 3, plus the bonus free throw is worth up to 1. Max possible = 4 per event.

---

## Component 6a — Technical Foul Free Throws

Free throws awarded from technical fouls, including defensive 3-second violations. The player at the line did not create this scoring opportunity through their own offensive action — they were chosen to shoot. Regardless, it is a discrete scoring event: 1 free throw worth 1 point that requires skill to convert and counts on the scoreboard. Any player in the game can be selected to shoot. The team that had possession retains it after the FTA — no possession changes hands. Each tech FT is treated as its own scoring event with max = 1.

| Symbol | What It Means |
|--------|---------------|
| **PTS_TF** | Total points scored on technical foul free throws |
| **Amt_TF** | Number of technical foul FT events (each event = 1 scoring possession) |
| **Eff_TF** | Efficiency on tech FTs = PTS_TF / (Amt_TF × 1), which simplifies to PTS_TF / Amt_TF |
| **w_TF** | Weight = Amt_TF / Total Scoring Possessions |

**Why multiply by 1?** Each technical foul event awards 1 free throw worth 1 point. Max possible = 1. The efficiency here is simply: did you make it or not.

---

## Component 6b — Flagrant Foul Free Throws (non-shooting)

Free throws awarded from flagrant fouls (penalty 1 or 2) that occur **away from a shot attempt** — the player was not in a shooting motion when fouled. The fouled player gets 2 FTAs and the team gets possession afterward. Important: flagrant fouls that occur **during a shot attempt** are NOT counted here — those fold into existing components (C2/C3 for missed shots, C4/C5 for made shots). Only the non-shooting flagrant events belong in this component.

Note on possession: the "plus possession" after a flagrant is a future, separate event. It does not affect the scoring efficiency calculation of the current play. If the player scores on that next possession, it gets captured naturally as whatever component type it ends up being.

| Symbol | What It Means |
|--------|---------------|
| **PTS_FF** | Total points scored on free throws from non-shooting flagrant fouls |
| **Amt_FF** | Number of non-shooting flagrant foul events (each event = 1 scoring possession) |
| **Eff_FF** | Efficiency on flagrant FTs = PTS_FF / (Amt_FF × 2) |
| **w_FF** | Weight = Amt_FF / Total Scoring Possessions |

**Why multiply by 2?** Each non-shooting flagrant foul awards 2 free throws, each worth 1 point. Max possible = 2.

---

## Component 6c — Clear Path Foul Free Throws

Free throws awarded when a defender commits a clear-path-to-the-basket foul — a personal foul on an offensive player during a transition scoring opportunity where no defender is ahead of the ball. The fouled player shoots 2 FTAs and the team gets possession afterward. Per NBA rules, a clear path foul **cannot** occur if the offensive player is fouled in the act of shooting (that would be a standard shooting foul under C2/C3). This component only covers non-shooting clear path fouls.

**Formula note:** This component uses the same efficiency calculation as C6b (max = 2). In the formula, clear path events can be combined with non-shooting flagrant events into a single "2 FTA penalty events" bucket. They are separated here for data categorization clarity when parsing play-by-play logs.

| Symbol | What It Means |
|--------|---------------|
| **PTS_CP** | Total points scored on free throws from clear path fouls |
| **Amt_CP** | Number of clear path foul events (each event = 1 scoring possession) |
| **Eff_CP** | Efficiency on clear path FTs = PTS_CP / (Amt_CP × 2) |
| **w_CP** | Weight = Amt_CP / Total Scoring Possessions |

**Why multiply by 2?** Each clear path foul awards 2 free throws, each worth 1 point. Max possible = 2.

---

## Component 6d — Transition Take Foul Free Throws

Free throws awarded when a defender commits a transition take foul — an intentional foul where the defender does not make a play on the ball, committed to stop a fast-break scoring opportunity. Per the NBA rulebook (Section XI—Transition Take Foul, confirmed in the 2025-26 official rules PDF), the penalty is 1 FTA (any player on the offensive team may shoot) and the offensive team retains possession. Does not apply in the last 2 minutes of the 4th quarter or overtime. Note: if a take foul is also flagrant, it escalates to 2 FTAs and falls under C6b instead.

**Formula note:** This component uses the same efficiency calculation as C6a (max = 1). In the formula, take foul FT events can be combined with tech FT events into a single "1 FTA penalty events" bucket. They are separated here for data categorization clarity.

| Symbol | What It Means |
|--------|---------------|
| **PTS_TK** | Total points scored on free throws from transition take fouls |
| **Amt_TK** | Number of transition take foul events (each event = 1 scoring possession) |
| **Eff_TK** | Efficiency on take foul FTs = PTS_TK / (Amt_TK × 1), which simplifies to PTS_TK / Amt_TK |
| **w_TK** | Weight = Amt_TK / Total Scoring Possessions |

**Why multiply by 1?** Each transition take foul awards 1 free throw worth 1 point. Max possible = 1.

---

## Component 6e — Away-From-Play Foul Free Throws

Free throws awarded when a defender fouls an offensive player away from the ball. Per NBA rules (Section X—Away-From-The-Play Foul), the penalty is 1 FTA (any player in the game may shoot) and the offensive team gets possession. These typically occur in late-game situations when a team is intentionally fouling off-ball. Note: if the away-from-play foul is also flagrant, it escalates to 2 FTAs and falls under C6b instead.

**Formula note:** This component uses the same efficiency calculation as C6a (max = 1). In the formula, away-from-play FT events can be combined with tech FT and take foul events into a single "1 FTA penalty events" bucket. They are separated here for data categorization clarity.

| Symbol | What It Means |
|--------|---------------|
| **PTS_AP** | Total points scored on free throws from away-from-play fouls |
| **Amt_AP** | Number of away-from-play foul events (each event = 1 scoring possession) |
| **Eff_AP** | Efficiency on away-from-play FTs = PTS_AP / (Amt_AP × 1), which simplifies to PTS_AP / Amt_AP |
| **w_AP** | Weight = Amt_AP / Total Scoring Possessions |

**Why multiply by 1?** Each away-from-play foul awards 1 free throw worth 1 point. Max possible = 1.

---

## Component 6f — Bonus (Penalty) Foul Free Throws

Free throws awarded when a defender commits a common personal foul (non-shooting) while the team is in the penalty/bonus. The fouled player goes to the line for 2 FTAs even though they were not in a shooting motion. This is one of the most common foul types in any NBA game — it happens multiple times per game whenever a team exceeds its foul limit in a quarter. These events are NOT shooting fouls, NOT flagrant, NOT technical, and NOT any other special foul category — just regular personal fouls that result in free throws because of the team foul situation.

| Symbol | What It Means |
|--------|---------------|
| **PTS_BF** | Total points scored on free throws from bonus (penalty) fouls |
| **Amt_BF** | Number of bonus foul events (each event = 1 scoring possession) |
| **Eff_BF** | Efficiency on bonus FTs = PTS_BF / (Amt_BF × 2) |
| **w_BF** | Weight = Amt_BF / Total Scoring Possessions |

**Why multiply by 2?** Each bonus foul event awards 2 free throws, each worth 1 point. Max possible = 2.

---

## The Simple Formula

The 12-component derivation above reduces to:

```
PS% = PTS / (2×FGA + 3PA + FTA)
```

Four standard box score numbers. This works because every component's max possible points maps exactly to a combination of FGA, 3PA, and FTA entries in the box score:

- A clean 2PT FGA → 1 FGA (max 2) → contributes 2 to denominator ✓
- A clean 3PT FGA → 1 FGA (max 2) + 1 3PA (max 1 more) → contributes 3 ✓
- A 2PT shooting foul (miss) → 0 FGA + 2 FTA → contributes 2 ✓
- A 3PT shooting foul (miss) → 0 FGA + 3 FTA → contributes 3 ✓
- A 2PT And-1 → 1 FGA (max 2) + 1 FTA (max 1) → contributes 3 ✓
- A 3PT And-1 → 1 FGA (max 2) + 1 3PA (max 1) + 1 FTA (max 1) → contributes 4 ✓
- Any non-shooting FT event → FTA only → contributes 1 per FTA ✓

The headline number should be computed from box score data (the official record). The 12-component PBP derivation is the proof of why the formula is correct, and it powers diagnostic breakdowns that don't exist in box score data alone.

---

## Component-Level Formula (Expanded)

For diagnostic purposes, the formula can be expanded to show each component's contribution:

```
              PTS₂ + PTS₃ + PTS_SF2 + PTS_SF3 + PTS_A1₂ + PTS_A1₃
            + PTS_TF + PTS_FF + PTS_CP + PTS_TK + PTS_AP + PTS_BF
PS%     = ─────────────────────────────────────────────────────────────
            (FGA₂×2) + (FGA₃×3) + (Amt_SF2×2) + (Amt_SF3×3)
          + (Amt_A1₂×3) + (Amt_A1₃×4) + (Amt_TF×1) + (Amt_FF×2)
          + (Amt_CP×2) + (Amt_TK×1) + (Amt_AP×1) + (Amt_BF×2)
```

This is mathematically equivalent to `PTS / (2×FGA + 3PA + FTA)`. The expanded form exists for component-level analysis — breaking down where a player's efficiency comes from.

---

## Key Principle

The denominator in this formula is the **maximum possible points** across all scoring opportunities. This naturally accounts for scoring possessions that the box score hides — a shooting foul that doesn't result in a made basket produces 0 FGAs but the FTAs still appear in the denominator. Standard TS% tries to approximate this with `0.44 × FTA`. PS% doesn't approximate — the box score arithmetic is exact.
