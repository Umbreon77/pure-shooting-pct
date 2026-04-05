# Pure TS% Weighting Methodology — Self-Audit

**Date:** 2026-03-22
**Auditor:** Adversarial Auditor (Claude Code)
**Subject:** Whether Pure TS% uses the correct weighting approach
**Status:** FINDING — the current implementation (Approach A) has a structural bias. Approach B is mathematically superior for the stated goal.

---

## 1. The Claim

Pure TS% claims to measure "what fraction of maximum possible scoring did this player achieve?" (from `pure_ts_pct_terms_and_key.md`: "Efficiency = Points scored on a given type of possession divided by the maximum possible points for that type. Always between 0 and 1.")

The metric claims to produce "a true percentage on a 0% to 100% scale."

---

## 2. The Two Approaches Under Examination

### Approach A (current implementation) — Possession-Weighted

```
Pure TS% = sum over all components i of: (events_i / N) * (pts_i / (events_i * max_i))
         = sum over all components i of: pts_i / (N * max_i)
```

Each component's weight = its share of total scoring possessions. Every possession counts equally regardless of how many points were at stake.

### Approach B (alternative) — Max-Points-Weighted

```
Pure TS% = total_pts / total_max_pts
         = sum(pts_i) / sum(events_i * max_i)
```

Each component's weight = its share of total max possible points. A 3PT attempt contributes more weight than a 2PT attempt because more points were at stake.

---

## 3. Boundary Conditions (Question 5)

### Test 1: Perfect efficiency (100% on every component)

If a player makes every shot, every free throw, on every possession:

- **Approach A:** Each component has efficiency = 1.0. Pure TS% = sum(weight_i * 1.0) = sum(weight_i) = 1.0 = 100%. CORRECT.
- **Approach B:** total_pts = total_max_pts. Pure TS% = 1.0 = 100%. CORRECT.

### Test 2: Zero efficiency (0 points on every component)

- **Approach A:** Each component has efficiency = 0.0. Pure TS% = 0.0 = 0%. CORRECT.
- **Approach B:** total_pts = 0. Pure TS% = 0.0 = 0%. CORRECT.

Both approaches pass the boundary conditions.

### Test 3: Can either exceed 100%? (Question 2)

**Approach A** is a convex combination of efficiencies, each bounded [0, 1], with weights summing to 1. A convex combination of values in [0, 1] cannot exceed 1. **Proof:** Pure TS% = sum(w_i * eff_i) where w_i >= 0, sum(w_i) = 1, and 0 <= eff_i <= 1. By the properties of convex combinations, 0 <= sum(w_i * eff_i) <= 1. Maximum is achieved when all eff_i = 1.

**Approach B** is total_pts / total_max_pts. For each component, pts_i <= events_i * max_i (a player cannot score more than max on any event). Therefore sum(pts_i) <= sum(events_i * max_i), so B <= 1.

**Neither approach can exceed 100%.** This is established mathematical fact, not assertion.

---

## 4. The Core Mathematical Difference (Question 1)

The fundamental question: does the stated goal — "what fraction of maximum possible scoring did this player achieve?" — map to Approach A or Approach B?

### The Direct Answer

The question "what fraction of maximum possible scoring did this player achieve?" is literally:

```
total points scored / total maximum possible points
```

**This is Approach B.**

Approach A answers a different question: "what is the average per-possession efficiency, where each possession counts equally regardless of how many points were at stake?"

### Algebraic Proof of the Difference

Consider a player with two component types: 2PT attempts (max=2) and 3PT attempts (max=3).

Let n2 = number of 2PT possessions, n3 = number of 3PT possessions, N = n2 + n3.
Let e2 = efficiency on 2PT, e3 = efficiency on 3PT.
Then pts2 = e2 * n2 * 2, pts3 = e3 * n3 * 3.

**Approach A:**
```
A = (n2/N) * e2 + (n3/N) * e3
  = (e2*n2 + e3*n3) / N
```
This is the arithmetic mean of component efficiencies, weighted by possession count.

**Approach B:**
```
B = (e2*n2*2 + e3*n3*3) / (n2*2 + n3*3)
```
This is the weighted mean of component efficiencies, weighted by max points at stake.

**When are they equal?** Only when all components have the same max points per possession, OR when all components have the same efficiency. In all other cases, they diverge.

**Direction of divergence:** A > B when the component with the LOWER efficiency has the HIGHER max points per possession. Since 3PT efficiency (made 3s / attempts, normalized) is almost always lower than 2PT efficiency across the NBA, **Approach A systematically inflates the Pure TS% for the vast majority of players.**

### Why This Matters Conceptually

Consider a toy example. A player has:
- 5 clean 2PT attempts: made 4 of 5. PTS=8, Max=10, Eff=80%.
- 5 clean 3PT attempts: made 1 of 5. PTS=3, Max=15, Eff=20%.

**Approach A:** (5/10 * 0.80) + (5/10 * 0.20) = 0.40 + 0.10 = **50.0%**

Interpretation: "The player was efficient on half their possessions, inefficient on the other half, so 50%."

**Approach B:** (8 + 3) / (10 + 15) = 11/25 = **44.0%**

Interpretation: "The player had 25 possible points at stake and scored 11. That's 44%."

**Which is correct?** If the claim is "what fraction of maximum possible scoring did this player achieve," the answer is 11/25 = 44%. The player had 25 points available and scored 11. Approach B answers this question directly. Approach A does not.

Approach A treats the 3PT possessions as carrying equal weight to the 2PT possessions, even though each 3PT possession had 50% more scoring potential. This is the exact same structural error that this project was built to fix in standard TS% — standard TS% treats all scoring events as if they have a maximum value of 2 points.

---

## 5. Empirical Evidence (Question 3) — Real Player Data

Analysis covers 794 player-seasons across 2024-25 and 2025-26 data, filtered to 100+ scoring possessions.

### Summary Statistics

| Metric | Value |
|--------|-------|
| Players where A > B | 747 (94.1%) |
| Players where A < B | 47 (5.9%) |
| Mean difference (A - B) | +1.464 pp |
| Median difference (A - B) | +1.496 pp |
| Max difference (A > B) | +4.341 pp |
| Max difference (A < B) | -0.864 pp |
| Players with abs(diff) > 2 pp | 184 (23.2%) |
| Players with abs(diff) > 3 pp | 24 (3.0%) |

### Where the Approaches Diverge Most (A >> B)

These are players with high 3PT share AND low 3PT efficiency relative to 2PT efficiency:

| Player | Season | N | 3PT Share | Approach A | Approach B | Diff |
|--------|--------|---|-----------|------------|------------|------|
| Nae'Qwan Tomlin | 2025-26 | 296 | 33.1% | 49.04% | 45.09% | +3.96 |
| Jay Huff | 2025-26 | 562 | 57.8% | 49.08% | 45.56% | +3.52 |
| Gary Payton II | 2025-26 | 357 | 32.5% | 55.37% | 51.98% | +3.39 |
| Kevin Huerter | 2025-26 | 517 | 52.2% | 46.29% | 43.07% | +3.22 |
| KCP | 2024-25 | 600 | 55.0% | 47.86% | 44.51% | +3.35 |

### Where the Approaches Nearly Agree (A approx B)

These are interior players with almost no 3PT attempts — their possessions are nearly homogeneous in max value:

| Player | N | 3PT Share | Approach A | Approach B | Diff |
|--------|---|-----------|------------|------------|------|
| Luke Kornet | — | 0.9% | 66.82% | 66.82% | +0.003 |
| Neemias Queta | — | 1.2% | 64.52% | 64.53% | -0.016 |
| Giannis | 717 | 5.7% | 61.99% | 61.96% | +0.04 |

### Where A < B (Rare)

These are interior players with high And-1 efficiency (C4, max=3) and lower clean 2PT efficiency (C1a, max=2):

| Player | N | C1a Eff | C4 Eff | Diff |
|--------|---|---------|--------|------|
| Dwight Powell | 120 | 62.7% | 93.9% | -0.86 |
| Mark Williams | 481 | 60.8% | 94.9% | -0.79 |
| Zion Williamson | 880 | 57.0% | 86.9% | -0.66 |

Here, Approach B gives a higher value because it upweights the high-efficiency And-1s (3 max pts each) relative to the lower-efficiency clean 2PTs (2 max pts each).

### Key Star Players

| Player | N | Approach A | Approach B | Diff |
|--------|---|------------|------------|------|
| Luka Doncic | 1605 | 52.22% | 50.36% | +1.86 |
| Jaylen Brown | 1567 | 51.86% | — | ~+1.5 |
| James Harden | 1208 | 50.90% | 49.40% | +1.51 |
| Joel Embiid | 729 | 55.74% | 54.40% | +1.34 |
| Giannis | 717 | 61.99% | 61.96% | +0.04 |

---

## 6. Systematic Bias Analysis (Question 4)

### Approach A's Bias

**Approach A systematically favors players whose worst efficiency is on their highest-max component.** In practice, because nearly every NBA player shoots worse from 3 than from 2 (normalized to max), and because 3PT has max=3 vs max=2, Approach A inflates 94.1% of all players.

The inflation magnitude correlates with:
1. **3PT volume** — more 3PT attempts = more inflation (r is strongly positive)
2. **Efficiency gap** — the larger the gap between 2PT and 3PT efficiency, the more inflation

This is NOT random noise. It is a structural, directional bias that inflates most players and deflates almost none.

**The one player shooting better from 3 than 2 (normalized to max) still saw A > B** (+0.86 pp), because other components (And-1s, shooting fouls) create additional variance between efficiency and max points.

### Approach B's Bias

Approach B has no analogous structural bias. It simply computes total points / total max points. It does not privilege any particular component. A 2PT attempt that scores 2 points contributes the same to both numerator and denominator proportionally as a 3PT attempt that scores 3 points — both are 100% efficiency on their respective max.

**However**, Approach B does give more "influence" to high-max components in a portfolio sense: a single 3PT attempt affects the final number more than a single 2PT attempt because it adds 3 to the denominator instead of 2. This is arguably correct — a 3PT miss costs you more possible points than a 2PT miss.

---

## 7. The Steelman for Approach A (Question 6, Steelman Phase)

The strongest defense of Approach A:

**"Every scoring possession should count equally because the player chose to take that shot. A possession is a possession. If you shoot 10 threes and 10 twos, you used 20 possessions, and each one was equally 'a chance to score.' Weighting by max points double-counts the value of 3PT possessions — they already get credit for being worth more through the higher max in the efficiency denominator."**

This is a coherent position. It says: the weight should reflect opportunity frequency (how often did this type of play happen?), and the efficiency should handle the value normalization (how well did you convert relative to max?). The separation of concerns is clean.

**But it breaks under scrutiny.** The claim of Pure TS% is not "what is your average per-possession efficiency" — it is "what fraction of maximum possible scoring did this player achieve?" These are different questions, and Approach A answers the first while claiming to answer the second.

Moreover, the "each possession counts equally" philosophy has a concrete failure case. Consider two players:

- **Player X:** 100 2PT attempts, made 50. Total: 100 points from 200 max.
- **Player Y:** 50 2PT attempts (made 25, 50 pts) + 50 3PT attempts (made 0, 0 pts). Total: 50 points from 250 max.

Under Approach A:
- Player X: 50/100 * (100/200) = 50.0%
- Player Y: (50/100 * 50/100) + (50/100 * 0/150) = 25.0% + 0% = 25.0%

Under Approach B:
- Player X: 100/200 = 50.0%
- Player Y: 50/250 = 20.0%

Both approaches agree Player X is better. But Approach A says Player Y captured 25% of their potential; Approach B says 20%. Player Y had 250 possible points and scored 50 — that is definitionally 20%, not 25%. Approach A inflates Player Y's number because it gives equal weight to the 50 worthless 3PT possessions as to the 50 2PT possessions, even though the 3PT possessions represented 60% of the max points at stake.

**The steelman does not hold.** The separation of concerns argument is internally consistent but it produces a number that does not match the plain-language claim of the metric.

---

## 8. The Steelman for Approach B

**"Total points scored divided by total max possible points is the most transparent, unambiguous answer to the question 'what fraction of maximum scoring potential did you realize?' It requires no weighting scheme, no averaging methodology, no choices about how to aggregate. It is a single fraction. It cannot be manipulated by the choice of aggregation method because there is no aggregation — just a ratio."**

This steelman holds. The only attack surface is whether "max possible points" is correctly defined per component, and that is a data question (handled by the component definitions), not a weighting question.

---

## 9. Is There a Third Approach? (Question 6)

### Approach C: Points-per-Possession

```
C = total_pts / (N * 2)
```

This is essentially what standard TS% does (points per 2 max). It fails for the same reason TS% fails — it assumes all possessions are worth 2 points.

### Approach D: Harmonic Mean of Component Efficiencies

Weight by the harmonic mean instead of arithmetic mean. This would penalize low-efficiency components more heavily. But it doesn't answer the stated question any better than A, and introduces additional complexity without solving the core problem.

### Approach E: Bayesian / Regression-Based

Apply shrinkage toward league-average by component. Useful for small-sample stability but changes the question from "what did this player achieve?" to "what do we estimate this player's true ability to be?" Out of scope for a deterministic metric.

**Verdict:** No third approach is superior to Approach B for answering the stated question. Approach B is the natural, unique answer to "fraction of max possible points scored."

---

## 10. The Verdict (Combined)

### What is wrong

The current implementation (Approach A) does not answer the question Pure TS% claims to answer. It answers a related but different question — "what is the average per-possession efficiency?" — and the difference is not cosmetic. It introduces a **systematic, directional bias that inflates 94% of players** by a mean of +1.5 pp and up to +4.3 pp.

The bias correlates with 3PT volume, meaning it distorts cross-player comparisons between perimeter and interior players in a predictable direction. This is precisely the kind of bias this project was built to eliminate.

### What should change

**Switch to Approach B: Pure TS% = Total Points Scored / Total Max Possible Points.**

This is:
- Simpler (one fraction, no weighted averaging)
- Unambiguous (directly answers the stated question)
- Free of structural bias between shooting profiles
- Equally bounded [0%, 100%]
- Consistent at boundary conditions

### Severity

**Moderate.** The maximum observed divergence is ~4 pp, and the mean is ~1.5 pp. This is not a catastrophic error — the current metric is still far more accurate than standard TS% — but it is a systematic bias in the wrong direction for a project whose entire thesis is "no approximations, no hidden assumptions."

### The Irony

The proof-of-concept document (`pure_ts_pct_proof_of_concept.md`) actually computes Approach B as a sanity check and notes:

> "Doncic had 31 scoring possessions with a combined max of 81 possible points and scored 40. That is 49.4% of the raw maximum — but because Pure TS% weights by component (not by raw points), the weighted average yields 51.6%."

The document treats 49.4% (Approach B) as a cross-check and 51.6% (Approach A) as the "real" answer. Under this audit's finding, 49.4% is the correct answer to the question the metric claims to answer, and 51.6% is the one with the structural bias.

---

## 11. Implementation Impact

Switching from A to B would:

1. **Simplify the formula.** No need for per-component weight * efficiency terms. Just sum all points, sum all max points, divide.
2. **Change every player's Pure TS% value.** Most would decrease by ~1-2 pp. Interior players with high And-1 rates would see slight increases.
3. **Preserve all existing infrastructure.** The component-level data collection, event classification, and CSV output remain unchanged. Only the final aggregation step changes.
4. **Require updating the terms and key document** to reflect the simpler formula.
5. **Strengthen the project's central argument.** "Total points / total max points" is easier to explain and defend than "possession-weighted average of component efficiencies."

---

## 12. Comparison to Standard TS%

Standard TS% = PTS / (2 * TSA), where TSA = FGA + 0.44 * FTA.

Standard TS% has two problems:
1. The 0.44 coefficient is an approximation.
2. The "2" in the denominator assumes all possessions are worth 2 points.

Pure TS% (Approach A) fixes problem #1 completely (exact event counts) but **partially reintroduces a version of problem #2** through its weighting scheme. By counting every possession equally regardless of max points, it implicitly says "a 3PT possession and a 2PT possession contribute equally to the denominator" — which is a softer version of the same error.

Pure TS% (Approach B) fixes both problems completely. Every possession contributes to the denominator in proportion to its actual max points. No approximation, no flattening.

---

## 13. Epistemic Status of Each Claim

| Claim | Status |
|-------|--------|
| Both approaches are bounded [0, 100%] | First-principles proof |
| Approach A systematically inflates most players | Established fact from data (794 players, 94.1% inflated) |
| Mean inflation is ~1.5 pp | Established fact from data |
| Max inflation is ~4.3 pp | Established fact from data |
| Inflation correlates with 3PT volume and efficiency gap | Established fact from data |
| Approach B directly answers the stated question | First-principles derivation |
| No third approach is superior to B for this question | Reasoned judgment (could be wrong if the stated question is wrong) |
| Switching would not exceed 5 pp change for any player | Established fact from data (max observed: 4.34 pp) |
| The VD framework file (docs/VD_framework.md) does not exist | Observed fact (file not found) |

---

## 14. Note on VD Framework

The file `docs/VD_framework.md` referenced in the auditor's operating instructions does not exist in the repository. This audit was conducted using the principles described in the system prompt (arithmetic over authority, substitution test, steelman-then-kill, epistemic flagging) which appear to be the intended framework content. If the framework document is created later, this audit should be reviewed for compliance.

---

## Appendix A: Algebraic Derivation of When A > B

Let there be k component types. For component i: n_i events, pts_i points scored, max_i points per event.

```
N = sum(n_i)
A = sum(n_i/N * pts_i/(n_i * max_i)) = sum(pts_i/(N * max_i)) = (1/N) * sum(pts_i/max_i)
B = sum(pts_i) / sum(n_i * max_i)
```

Let M = sum(n_i * max_i) (total max points).

```
A - B = (1/N) * sum(pts_i/max_i) - sum(pts_i)/M
```

Rewrite pts_i = eff_i * n_i * max_i:

```
A = (1/N) * sum(eff_i * n_i)
B = sum(eff_i * n_i * max_i) / sum(n_i * max_i)
```

A is the arithmetic mean of efficiencies weighted by possession count.
B is the arithmetic mean of efficiencies weighted by max points (= n_i * max_i).

By the properties of weighted means: if the weight distribution differs and efficiencies are not all equal, A and B will differ. A > B when low-efficiency components have disproportionately high max_i (the max-points weight upweights the low-efficiency terms more than the possession weight does).

Since 3PT efficiency (normalized) < 2PT efficiency (normalized) for nearly all NBA players, and 3PT max (3) > 2PT max (2), this condition holds for the vast majority of the league.

## Appendix B: Proof-of-Concept Recomputed

Luka Doncic vs HOU, March 18, 2026:

| Component | Events | PTS | Max PTS |
|-----------|--------|-----|---------|
| C1a | 7 | 8 | 14 |
| C1b | 17 | 21 | 51 |
| C2 | 2 | 3 | 4 |
| C3 | 1 | 0 | 3 |
| C4 | 1 | 3 | 3 |
| C6f | 3 | 5 | 6 |
| **Total** | **31** | **40** | **81** |

- **Approach A (current):** 51.6% (as documented)
- **Approach B (proposed):** 40/81 = 49.4%
- **Difference:** 2.2 pp
- **Standard TS%:** 64.2%

Under Approach B, the delta from standard TS% would be -14.8 pp instead of -12.6 pp. Both tell the same story (standard TS% massively overrated this game), but Approach B tells it more precisely.
