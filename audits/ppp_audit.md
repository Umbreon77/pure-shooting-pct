# Adversarial Audit: Points Per Possession (PPP)

**Date:** 2026-03-22
**Formula under audit:** PPP = Points / Possessions (multiple implementations)
**Data basis:** Conceptual audit with worked examples from Luka Doncic vs HOU (March 18, 2026) proof of concept data

---

## 1. The Claim

**Team-level PPP** claims to measure how many points a team scores (or allows) per possession, serving as a pace-neutral efficiency metric for comparing teams that play at different speeds.

**Individual-level PPP** claims to measure how many points a player scores per possession they \"use,\" serving as an individual scoring efficiency metric comparable across players regardless of volume or pace.

These are different claims. The team version has a defensible definition. The individual version does not — and that is where this audit spends most of its time.

---

## 2. The Inputs

### 2a. Team-Level Possession Formula (Dean Oliver / Basketball-Reference)

```
Possessions = FGA - OREB + TOV + 0.44 x FTA
```

| Input | Source | Observed or Estimated? | Notes |
|-------|--------|----------------------|-------|
| **FGA** | Box score | Observed | All field goal attempts, including blocked shots. Excludes shooting fouls that don't produce FGAs. |
| **OREB** | Box score | Observed | Offensive rebounds — subtracted because an OREB extends the same possession rather than starting a new one. |
| **TOV** | Box score | Observed | Turnovers — each ends a possession without a shot attempt. |
| **FTA** | Box score | Observed | Free throw attempts — multiplied by 0.44 to estimate how many possessions FTs consumed. |
| **0.44** | League-wide historical average | **Estimated** | Approximates the fraction of FTA that end possessions. Same coefficient used in TS%. |

**Points** is observed from the box score.

### 2b. Synergy Sports (Play-Type PPP)

Synergy defines \"possessions\" differently for each play type (isolation, pick-and-roll ball handler, spot-up, post-up, transition, etc.):

| Input | Source | Observed or Estimated? | Notes |
|-------|--------|----------------------|-------|
| **Play-type possessions** | Proprietary video tagging | Semi-observed | Human taggers classify every half-court play. Relies on subjective judgment for play-type boundaries. |
| **Points** | Linked to tagged possessions | Observed, but attribution is estimated | Points are assigned to the player who \"used\" the possession. Assisted baskets are credited to the scorer, not the passer (for scoring PPP). |

Synergy's possession definition: a play sequence terminates when the ball changes hands, a shot is taken, free throws are awarded, or a turnover occurs. A single team possession can contain multiple Synergy \"possessions\" if, for example, an offensive rebound resets the play type.

### 2c. NBA.com PPP

NBA.com publishes PPP figures that appear to source from Second Spectrum tracking data:

| Input | Source | Observed or Estimated? | Notes |
|-------|--------|----------------------|-------|
| **Possessions** | Tracking-derived | Semi-observed | Definitions vary by page (team stats vs. play-type vs. matchup). Not always documented. |
| **Points** | Tracking-linked | Observed | Same attribution questions as Synergy. |

The exact methodology is not fully published. A metric whose denominator cannot be independently verified cannot be independently audited. [Epistemic state: established fact that methodology is not fully public.]

---

## 3. The Assumptions

### Assumption 1: The 0.44 Coefficient (Team-Level)

Same assumption audited in standard TS%. The 0.44 approximates the share of FTA that end possessions. It handles And-1s (1 FT, no new possession consumed), 2-shot fouls (1 possession consumed by 2 FTs), and 3-shot fouls (1 possession consumed by 3 FTs) by blending them into a single coefficient.

**When it fails:** Same cases as TS% — games or players with atypical foul distributions. At the team level over a full season, errors are small (~0.2pp mean). At the individual level over a single game, errors can be large.

This project's own analysis (docs/the_problem.md) measured the actual league-wide coefficient at approximately 0.453, not 0.44. The 0.44 systematically underestimates possessions consumed by FTs, which inflates PPP slightly (fewer possessions in the denominator = higher PPP).

### Assumption 2: Individual Possessions Are Definable

This is the core philosophical problem with individual PPP, and it is far more serious than the 0.44.

A team possession is reasonably well-defined: it starts when the team gains the ball and ends when they lose it (via score, turnover, defensive rebound, or end of period). An individual possession — \"this player used this possession\" — is not well-defined. Consider:

- **Player A sets a screen, Player B drives and kicks to Player C for a corner three.** Who \"used\" the possession? Synergy credits Player C (the scorer) for a \"spot-up\" possession. Player B gets a \"PnR ball handler\" possession with 0 points (he passed). Player A's screen is invisible. One team possession has been fractured into two or three individual \"possessions,\" only one of which has points attached.

- **Player A drives, draws two defenders, and passes to Player B for an open layup.** Synergy gives Player A a \"drive\" possession with 0 points and Player B a \"cut\" possession with 2 points. Player A's gravity created the 2 points. PPP credits 0 to the creator and 2 to the finisher.

- **Player A posts up, gets doubled, passes out, 3 passes later Player D hits a three.** Synergy gives Player A a \"post-up\" possession with 0 points. Player D gets a \"spot-up\" possession with 3 points. The post-up created the three.

The assumption is: **possession usage is attributable to a single player, and points can be assigned to possession-users in a way that reflects individual efficiency.** This assumption is false on its face for any play involving more than one offensive decision-maker.

[Epistemic state: first-principles derivation from the nature of basketball as a team sport.]

### Assumption 3: \"Using\" a Possession Means Ending It

Most PPP implementations define the possession-user as the player who terminates the action: the shooter, the turnover committer, the foul-drawer. This systematically overcredits finishers and undercredits creators.

A player who receives the ball in a 4-on-3 advantage after a teammate draws a double-team is \"using\" a possession that someone else made valuable. PPP treats the finish as the entire story.

### Assumption 4: All Possessions Are Created Equal

PPP treats every possession in the denominator equally. A contested pull-up three with 3 seconds on the shot clock counts the same as a wide-open dunk off a back-door cut. The numerator (points) captures the outcome, but the denominator (possessions) has no quality adjustment.

This is a defensible simplification — the stat intentionally measures what happened, not what should have happened. But it means PPP conflates shot selection with shot execution.

### Assumption 5: Transition and Putback Attribution

- **Transition:** A player grabs a rebound, outlets to a guard who pushes in transition and scores. Synergy credits the guard with a \"transition\" possession. The rebounder's action is invisible.
- **Putbacks:** An offensive rebounder tips in a missed shot. This may or may not count as a \"new possession\" depending on the implementation. Some systems count it as continuing the prior possession (in which case the original shooter used a possession and got 0 points, and the putback player gets... what?). Others count it as a new possession for the rebounder.

The inconsistency across implementations makes cross-source PPP comparisons unreliable.

### Assumption 6: Points Per Possession, Not Points Per Max Possible Points

PPP uses raw points in the numerator with no normalization for the maximum possible points on each possession type. A possession that yields a made three (3 points) counts 1.5x more than a possession that yields a made two (2 points) in the numerator, but both count as exactly 1 possession in the denominator.

This is the same \"2-point baseline\" problem identified in the TS% and eFG% audits. A player who exclusively shoots (and makes) threes will have a PPP of 3.0. A player who exclusively shoots (and makes) twos will have a PPP of 2.0. Both converted 100% of their scoring opportunities. PPP says the three-point shooter is 50% better.

If the question is \"how many points does this player produce per opportunity?\" then PPP answers correctly. But if the question is \"how efficiently does this player convert their opportunities?\" then PPP gives the wrong answer, because it does not normalize for opportunity value.

---

## 4. The Math — Worked Examples

### 4a. Team-Level PPP (Straightforward Case)

Using a hypothetical team game line:
- FGA = 88, OREB = 12, TOV = 14, FTA = 24, PTS = 110

```
Possessions = 88 - 12 + 14 + 0.44 x 24 = 88 - 12 + 14 + 10.56 = 100.56
PPP = 110 / 100.56 = 1.094
```

If we use the project's corrected coefficient of 0.453:
```
Possessions = 88 - 12 + 14 + 0.453 x 24 = 88 - 12 + 14 + 10.872 = 100.872
PPP = 110 / 100.872 = 1.091
```

Difference: 0.003 PPP. At the team level over a full game, the 0.44 vs 0.453 distinction is negligible.

### 4b. Individual PPP vs. Pure TS% — Luka Doncic vs HOU (March 18, 2026)

From the proof-of-concept data:
- 40 PTS, 25 FGA, 14 FTA, box score line

**Individual PPP (team-formula approach):**
```
\"Possessions\" = FGA + 0.44 x FTA = 25 + 0.44 x 14 = 25 + 6.16 = 31.16
PPP = 40 / 31.16 = 1.284
```

**Pure TS% approach:**
- Total Scoring Possessions = 31 (exact count from play-by-play)
- Pure TS% = 51.6% (weighted average of component efficiencies)

Now compute what PPP would be with exact possessions:
```
PPP (exact possessions) = 40 / 31 = 1.290
```

And standard TS%:
```
TS% = 40 / (2 x 31.16) = 40 / 62.32 = 0.642 = 64.2%
```

Observe: **PPP = 1.284 and TS% = 0.642. TS% is exactly PPP divided by 2.** This is not a coincidence. When individual possessions are estimated via `FGA + 0.44 x FTA`:

```
TS% = PTS / (2 x (FGA + 0.44 x FTA))
PPP = PTS / (FGA + 0.44 x FTA)

Therefore: PPP = 2 x TS%
```

At the individual level with the team-formula possession estimate, PPP and TS% are the same metric on different scales. Every flaw in TS% is a flaw in PPP, and vice versa.

**Now compare PPP to Pure TS%:**

PPP says Doncic produced 1.284 points per possession. That sounds good — league average is roughly 1.10-1.15. But Pure TS% says he captured only 51.6% of his maximum possible points. These paint very different pictures.

The divergence comes from the normalization. PPP values a 3PT make at 3 points in the numerator and 1 possession in the denominator. Pure TS% values a 3PT make at 3 points scored out of 3 possible (100% efficiency on that possession, weight = 1/N).

### 4c. Edge Case — The Designated Free Throw Shooter

A player shoots 4 technical foul free throws in a game, makes 3, and takes no other shots.

```
PPP (team formula) = 3 / (0 + 0.44 x 4) = 3 / 1.76 = 1.705
```

But the player had 4 scoring possessions (each tech FT is 1 possession, max = 1).

```
PPP (exact) = 3 / 4 = 0.750
Pure TS% = 3 / (4 x 1) = 75%
```

The team formula says 1.705 PPP — an elite efficiency score — for a player who made 75% of their free throws. The 0.44 coefficient collapses 4 FTA into 1.76 \"possessions\" when there were actually 4 independent scoring events. The error is a factor of 2.27x in the denominator.

### 4d. Edge Case — The Putback Player With a Shooting Foul

A player: 4 putback makes (8 pts, 4 FGA), plus 1 shooting foul (1-for-2 FT, 0 FGA, 2 FTA).

```
PPP (team formula) = 9 / (4 + 0.44 x 2) = 9 / 4.88 = 1.844
```

The shooting foul produced 0 FGA. The player had 5 actual scoring possessions. PPP with exact possessions:
```
PPP (exact) = 9 / 5 = 1.800
```

Pure TS%:
```
= (4/5 x 8/8) + (1/5 x 1/2) = 0.8 + 0.1 = 90%
```

The 0.44 overcounts here — 0.88 \"possessions\" for what was 1 possession — deflating the denominator and inflating PPP.

---

## 5. Systematic Failure Modes

### Failure Mode 1: PPP = 2 x TS% (Individual Team-Formula Version)

When individual PPP is computed via `PTS / (FGA + 0.44 x FTA)`, it is algebraically identical to `2 x TS%`. This means PPP inherits every flaw of standard TS%: the 0.44 coefficient error, the 2-point baseline distortion, the inability to function as a true percentage. Any criticism of TS% applies with equal force. They are the same metric.

### Failure Mode 2: Possession Attribution (Synergy/Play-Type Version)

A team that runs 100 half-court possessions might generate 130-150 individual Synergy possessions across all players and play types. A pick-and-roll counts as one PnR ball-handler possession AND one PnR roll-man possession. A drive-and-kick counts as one drive possession AND one spot-up possession. Individual PPP figures are not additive and cannot be aggregated to produce team PPP.

### Failure Mode 3: Creator-Finisher Problem

PPP credits the terminator of the possession. Creators (playmakers who drive and kick, post players who draw doubles and pass out) are penalized — they \"use\" possessions but produce 0 points because they passed. Finishers (spot-up shooters, cutters, roll men) are rewarded — they receive the ball in advantageous positions created by others.

A player who goes 6-for-6 on wide-open corner threes off drive-and-kicks has a PPP of 3.0. The playmaker who created all six looks might have a PPP of 0.6. PPP says the corner shooter was 5x more efficient.

### Failure Mode 4: No Normalization for Possession Value

League-average PPP has risen as 3PA rates have risen — not because teams are more efficient at converting opportunities, but because the opportunities themselves have higher point values. PPP conflates these two phenomena.

### Failure Mode 5: Non-Shooting Possessions Mixed In (Synergy) or Excluded (Team Formula)

Synergy PPP includes turnovers. The team-formula individual version (`FGA + 0.44 x FTA`) excludes them entirely. Neither approach is fully satisfactory. Synergy blends shooting with ball security. The team formula ignores a real cost.

### Failure Mode 6: Transition Inflation

Transition possessions are inherently higher-value. A player who gets a disproportionate share of transition opportunities will have an inflated PPP that reflects their role, not their skill.

---

## 6. The Steelman

### Team-Level PPP

1. **Pace neutrality.** Points per game is meaningless for comparing teams at different speeds. PPP solves this. A team scoring 115 in 105 possessions (1.095 PPP) is less efficient than one scoring 105 in 92 possessions (1.141 PPP). This is genuinely useful.

2. **Includes turnovers.** Unlike TS% or eFG%, team PPP counts turnovers as possessions used with 0 points scored.

3. **The 0.44 error is small at the team level.** Over a full season, the coefficient error averages out to fractions of a point.

4. **Simple, interpretable, widely available.** It has been the standard team efficiency metric for two decades for good reason.

### Individual PPP (Synergy Play-Type)

1. **Play-by-play grounding.** Synergy possessions are derived from actual video, not box-score approximation.

2. **Play-type filtering.** \"This player scores 1.15 PPP on isolations\" is more actionable than aggregate efficiency numbers.

3. **Includes turnovers within play types.** A player who turns it over on 20% of their isolations has a lower isolation PPP.

4. **Widely used by NBA teams.** Synergy data is part of the analytical infrastructure of every NBA front office.

### The Strongest Single Defense

At the team level, PPP is the best widely-available measure of team offensive/defensive efficiency. Nothing else is as simple, as interpretable, and as pace-neutral.

At the individual level, Synergy play-type PPP is the best widely-available measure of play-type-specific finishing efficiency. It is not a measure of overall individual offensive value — but it was never designed to be.

---

## 7. The Verdict

### Team-Level PPP

**Does it do what it claims?** Mostly yes. The 0.44 introduces small systematic error. The lack of normalization for shot-type value means cross-era comparisons are somewhat distorted. Within a single season, team PPP rankings are robust.

**Grade: B+.**

### Individual PPP (Team-Formula Version)

**Does it do what it claims?** No. It is algebraically identical to 2 x TS%, inheriting every flaw. It adds no information that TS% does not already provide. It should not be presented as a distinct metric.

**Grade: D.**

### Individual PPP (Synergy Play-Type Version)

**Does it do what it claims?** Partially. Within a specific play type, reasonable measure of finishing efficiency. In aggregate, unreliable due to possession attribution ambiguity, creator-finisher bias, non-additivity, and no normalization for shot-type value.

**Grade: C+.**

### Summary Table

| Version | Question It Answers Well | Question It Fails At |
|---------|------------------------|---------------------|
| Team PPP | \"How efficiently does this team score relative to pace?\" | \"How efficiently does this team convert opportunities, normalized for shot type?\" |
| Individual PPP (team formula) | None that TS% doesn't already answer | Everything — it is 2 x TS% |
| Individual PPP (Synergy) | \"How well does this player finish isolation possessions?\" | \"How efficient is this player overall?\" |

---

## 8. Comparison to Pure TS% Approach

| Feature | Team PPP | Individual PPP (team formula) | Individual PPP (Synergy) | Pure TS% |
|---------|----------|------------------------------|-------------------------|----------|
| Includes turnovers | Yes | No | Yes | No |
| Includes all FT types | Via 0.44 estimate | Via 0.44 estimate | Partially | Yes (exact, by foul type) |
| Correct 3PT scaling | No (raw points) | No (raw points) | No (raw points) | Yes (max = 3 for 3PT) |
| Bounded 0-100% | No (0 to ~3.0) | No (0 to ~3.0) | No (0 to ~3.0) | Yes |
| Possession count | Estimated (0.44) | Estimated (0.44) | Video-derived | Exact (play-by-play) |
| Play-type granularity | No | No | Yes (major advantage) | No |
| Creator vs finisher | N/A (team level) | No | No (credits finisher) | No (credits scorer) |
| Cross-archetype validity | Moderate | Poor | Poor to Moderate | Good |

### Where PPP Has an Advantage Over Pure TS%

1. **Turnovers.** Team PPP and Synergy PPP count turnovers. Pure TS% does not. A player who scores efficiently but turns it over frequently looks better in Pure TS% than they should.

2. **Play-type context.** Synergy PPP provides play-type breakdowns (isolation, PnR, spot-up, etc.). Pure TS% gives a single aggregate number. For coaching decisions and game-planning, play-type PPP is more actionable.

3. **Pace neutrality at team level.** Pure TS% is a player-level metric and does not address team-level pace normalization.

### Where Pure TS% Has an Advantage Over PPP

1. **Exact possession counting.** No 0.44. No estimation.

2. **Correct normalization.** Each component measured against its own maximum. Eliminates structural inflation of high-3PA players.

3. **True percentage scale.** Bounded 0-100%. A PPP of 2.0 could mean a player made every 2PT attempt, or made 2/3 of their 3PT attempts — the number has no interpretable ceiling.

4. **Component decomposition.** 12 components. You can see efficiency by foul type, shot type, and play outcome.

### The Conceptual Divide

PPP and Pure TS% answer fundamentally different questions:

- **PPP asks: \"How many points did this player/team produce per possession?\"** This is a production metric. Three-point attempts are inherently worth more because they produce more points when successful.

- **Pure TS% asks: \"What fraction of the maximum possible points did this player score across their scoring possessions?\"** This is a conversion efficiency metric. 100% means perfection regardless of shot type.

Neither question is wrong. They serve different purposes. The danger is in conflating the two — using a production metric as if it were a conversion efficiency metric. That conflation systematically overvalues three-point shooting volume relative to three-point shooting skill, and it is the most common misuse of PPP in NBA analytics discourse.

---

### Appendix: Self-Correction on 0.44 Amplification

An initial hypothesis was that the 0.44 coefficient error is amplified in PPP relative to TS% because PPP lacks the \"2\" in the denominator. On inspection, this is wrong. Since PPP = 2 x TS% algebraically, the proportional error from the 0.44 coefficient is identical in both metrics. The \"2\" scales both numerator and denominator proportionally. [Epistemic state: self-corrected during derivation.]

---

*Audit conducted under the project's adversarial audit protocol. All claims marked with epistemic state. No files were modified.*

---
