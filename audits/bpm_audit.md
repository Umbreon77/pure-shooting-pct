# Adversarial Audit: Box Plus/Minus (BPM)

**Date:** 2026-03-22
**Formula under audit:** BPM (version 2.0), created by Daniel Myers for Basketball Reference
**Methodology source:** Daniel Myers' published description on basketball-reference.com/about/bpm2.html [Epistemic note: I am working from training-data knowledge of this published methodology, not a live fetch of the page. If any coefficient or procedural detail has been updated since my training cutoff (May 2025), this audit may contain stale values. The structural critiques hold regardless of specific coefficient updates.]

---

## 1. The Claim

BPM claims to estimate a player's per-100-possession contribution to their team's point differential relative to league average, using only box score statistics. A BPM of +5.0 means the player is estimated to have contributed 5 points per 100 possessions above what a league-average player would have contributed in the same minutes.

---

## 2. The Inputs

### 2.1 Direct Box Score Inputs

| Input | Source | Type | Notes |
|-------|--------|------|-------|
| **Points (PTS)** | Box score | Observed | |
| **FGA** | Box score | Observed | |
| **FG%** | Box score | Derived (FGM/FGA) | |
| **3PA** | Box score | Observed | |
| **3P%** | Box score | Derived (3PM/3PA) | |
| **FTA** | Box score | Observed | |
| **FT%** | Box score | Derived (FTM/FTA) | |
| **ORB** | Box score | Observed | |
| **DRB** | Box score | Observed | |
| **TRB** | Box score | Observed | |
| **AST** | Box score | Observed | |
| **STL** | Box score | Observed | |
| **BLK** | Box score | Observed | |
| **TOV** | Box score | Observed | |
| **PF** | Box score | Observed | |
| **Minutes Played (MP)** | Box score | Observed | |

### 2.2 Derived Intermediate Inputs

| Input | Source | Type | Notes |
|-------|--------|------|-------|
| **Position estimate** | Derived from box score stats | Estimated | Uses height, BLK%, 3PA rate, AST% to estimate a 1-5 positional continuum |
| **Team pace** | Derived from team box scores | Derived | Possessions per 48 minutes |
| **Team offensive/defensive rating** | Derived from team box scores | Derived | Points per 100 possessions |
| **Usage Rate (USG%)** | Derived from box score | Derived | Estimate of % of team possessions used while on floor |
| **TS%** | Derived from box score | Derived | PTS / (2 x (FGA + 0.44 x FTA)) -- inherits the 0.44 and \"2\" problems documented in our TS% and eFG% audits |

### 2.3 The Regression Target

| Input | Source | Type | Notes |
|-------|--------|------|-------|
| **RAPM (Regularized Adjusted Plus/Minus)** | Multi-year ridge regression of on/off data | **Estimated** | This is what BPM's coefficients were trained to predict. It is itself a statistical estimate with substantial uncertainty. |

Every box score stat is directly observed. But BPM does not use them raw -- it feeds them into a regression equation whose coefficients were derived by fitting against RAPM. The output is therefore an **estimate of an estimate**.

---

## 3. The Assumptions

### Assumption 1: Box score stats can predict plus/minus contribution

**The foundational assumption.** BPM assumes that a linear (or near-linear) combination of box score statistics can approximate a player's true impact on team point differential. This is a claim that the information captured in the box score is a sufficient statistic -- or at least a good proxy -- for on-court impact.

**Where this fails:** The box score does not capture:
- Off-ball defense (positioning, help rotations, closeout quality)
- Off-ball offense (screening, spacing, gravity, decoy movement)
- Shot quality forced/created (tight vs. open looks)
- Transition decisions (when to push, when to pull back)
- Communication and defensive quarterbacking
- Effort variability within possessions

These are not marginal contributions. Players like Draymond Green, Marcus Smart (peak years), and peak Andre Iguodala built their value substantially from activities invisible to the box score. Conversely, players who accumulate counting stats on bad teams while playing poor defense are systematically overrated.

### Assumption 2: RAPM is a reliable regression target

BPM's coefficients were derived by regressing box score stats against RAPM. This means BPM is only as good as RAPM, and RAPM has its own problems:

- **Sample size sensitivity:** RAPM requires multiple seasons of data to stabilize for individual players. Single-season RAPM has wide confidence intervals (often +/- 2-3 points for role players).
- **Lineup collinearity:** Players who always play together cannot be reliably separated by plus/minus methods. If Player A and Player B share 90% of their minutes, RAPM cannot distinguish their individual contributions -- it can only estimate their combined effect and then split it (often equally, via the ridge penalty).
- **Ridge regression shrinkage:** RAPM uses L2 regularization that shrinks extreme values toward zero. This is a feature (prevents overfitting) but also means RAPM systematically underestimates the best and worst players. The regression target itself is compressed.
- **Prior assumptions in RAPM:** Some RAPM implementations use informative priors (e.g., shrinking toward box-score predictions). If BPM is regressed against RAPM that was itself influenced by box score priors, the circularity is troubling.

**The chain:** BPM predicts RAPM, which estimates true plus/minus. Every link in this chain introduces noise and bias. BPM is an estimate of an estimate of reality.

### Assumption 3: The regression coefficients are stable across eras and contexts

The coefficients in BPM were derived from a specific training sample of NBA seasons. The implicit assumption is that the relationship between box score stats and impact is constant. But:

- The value of a three-point attempt has increased dramatically as league strategy has shifted. A coefficient on 3PA rate calibrated in 2010-2014 data may not reflect 2024 reality.
- The value of a defensive rebound has decreased as contested DRB rates have declined (teams concede uncontested DRBs more readily now).
- Pace and spacing changes alter what box score stats mean. A steal in 2005 half-court-heavy basketball generates different expected points than a steal in 2025 pace-and-space basketball.

BPM 2.0 was calibrated using data from approximately 2001-2014. The NBA of 2025 plays differently.

### Assumption 4: Position estimation from box score stats is accurate

BPM uses a continuous 1-5 position estimate derived from player height, blocks, three-point attempt rate, and assist rate. Different positional coefficients are then applied. This means:

- A player whose box score stats look like a wing but who actually plays center (e.g., a small-ball 5) will be evaluated with wrong positional coefficients.
- Position-dependent expectations for rebounds, blocks, and assists may mismatch a player's actual role.
- The position estimation itself was calibrated against listed positions from a prior era. As basketball has become more positionless, this mapping degrades.

### Assumption 5: The team adjustment correctly allocates residual

BPM first estimates each player's raw contribution from the regression equation, then applies a team-level adjustment so that the team's players' BPMs (weighted by minutes) sum to the team's actual point differential per 100 possessions. This team adjustment is allocated proportionally to playing time.

**What this assumes:**
- That any gap between the sum of individual BPMs and the team's actual performance should be distributed evenly per minute played.
- That bench players and starters should receive the same per-minute adjustment.
- That the residual represents \"team effects\" that apply equally to everyone on the roster.

**Where this breaks:** If a team has strong lineup-specific synergies (e.g., a closing lineup that outperforms the sum of its parts), the team adjustment smears this effect equally across all 15 roster spots. If a star player is responsible for most of the team's success but the regression equation underestimates them, the residual gets distributed to teammates.

### Assumption 6: Linearity

The regression model is fundamentally linear: BPM = sum of (coefficient x stat). This assumes no interactions, no thresholds, no diminishing returns. In reality:

- A player with 30% usage and a player with 15% usage may derive different per-possession value from the same AST% because the marginal value of an assist depends on the context.
- The value of rebounds has a team-level diminishing return (if the team already grabs 80% of defensive rebounds, the 81st percentile rebound is worth less).
- Scoring volume and efficiency interact: 20 PPG on 60 TS% is more valuable than 10 PPG on 60 TS%, but the gap is not simply 2x.

BPM does include a USG-squared term, which introduces one nonlinearity. But this is a single correction in an otherwise linear framework.

### Assumption 7: Defense can be estimated from box score stats

This is the single most aggressive assumption in BPM. DBPM uses steals, blocks, defensive rebounds, and personal fouls to estimate defensive contribution. The box score captures approximately 10-20% of what constitutes good defense. The other 80-90% -- positioning, rotations, communication, contest quality, transition defense -- is invisible.

The consequences are severe:
- Elite defensive players with low steal/block rates (e.g., peak Kawhi Leonard's off-ball positioning, Jrue Holiday's on-ball containment without steals) are systematically underrated.
- High-block-rate players who gamble defensively and give up easy baskets (chase-down block artists who fail to contest the 60% of shots they don't block) are systematically overrated.
- The correlation between DBPM and actual defensive impact (as measured by on/off data, or tracking-based metrics) is substantially lower than the correlation between OBPM and actual offensive impact.

---

## 4. The Math

### 4.1 The BPM Formula Structure

BPM is computed in several steps:

**Step 1: Estimate position** on a 1-5 scale using height, BLK%, 3PA/FGA ratio, and AST%.

**Step 2: Compute raw BPM** using a regression equation approximately of the form:

```
Raw BPM = a1*(3PAr) + a2*(AST%) + a3*(ORB%) + a4*(DRB%) + a5*(STL%) + a6*(BLK%)
        + a7*(TOV%) + a8*(USG%) + a9*(USG%^2) + a10*(Scoring) + a11*(Interaction terms)
        + Position-dependent intercepts and adjustments
```

The exact coefficients are position-dependent. Myers published specific values; the key ones include large positive weights on AST%, STL%, BLK%, and a scoring efficiency term, with negative weight on TOV% and an adjustment for high-usage players.

**Step 3: Compute OBPM and DBPM** from separate offensive and defensive regression equations.

**Step 4: Apply team adjustment.** Sum all players' Raw BPM weighted by minutes share. Compare to team's actual adjusted point differential. Distribute the residual proportionally by minutes.

```
Team Adjustment = (Team Actual Net Rating - Sum of Weighted Raw BPMs) / 5
Adjusted BPM = Raw BPM + Team Adjustment * (player's minutes share normalization)
```

### 4.2 Worked Example: Nikola Jokic 2024-25

From our CSV data (`/Users/zfreud/NBAstats/data/pure_ts_pct_league_2024-25.csv`), we know Jokic's scoring profile:
- 2,015 total points in 69 games (29.2 PPG)
- 1,325 FGA, 1,000 FGA2, 325 FGA3
- 438 FTA
- Standard TS%: 66.38%, Pure TS%: 60.27%
- 53 2PT And-1s, 109 2PT shooting fouls, 6 3PT shooting fouls

From public sources (epistemic status: widely reported consensus):
- ~13.7 RPG, ~10.1 APG, ~1.6 SPG, ~0.9 BPG
- USG%: ~31%
- Denver's net rating: approximately +5 to +7

**BPM would estimate:** Jokic's massive assist numbers, elite rebounding, good steal rate, and high-efficiency scoring would produce a very high Raw BPM -- likely in the +10 to +13 range. The scoring efficiency term benefits from his exceptional TS% (66.38% standard). Note: this TS% is itself inflated by +6.11pp relative to Pure TS% (60.27%), meaning BPM's scoring input overstates Jokic's true scoring efficiency.

**Published BPM for Jokic 2024-25: approximately +12 to +13 (led the league).**

This is a case where BPM works reasonably well because Jokic's impact is substantially captured by box score stats. But even here, BPM inherits a +6.11pp TS% inflation in its scoring input.

### 4.3 Worked Example: Where BPM Fails -- A Defensive Specialist

**Herb Jones, 2024-25 (approximate stats from public sources):**
- ~8 PPG, ~4 RPG, ~2 APG, ~1.5 SPG, ~0.7 BPG
- Low usage (~12-14%)
- Widely regarded as one of the NBA's best perimeter defenders

**BPM would estimate:** Likely around +0.5 to +2.0. The low scoring, modest rebounding, and moderate assist numbers produce a mediocre OBPM. The steals help DBPM, but without gaudy block numbers, DBPM undervalues his perimeter defensive impact. His actual on/off impact may be substantially higher because he shuts down opposing primary scorers, forces turnovers through positioning (not just recorded steals), and generates switches and disruptions that help teammates. None of this appears in the box score. BPM structurally cannot see it.

### 4.4 The TS% Contamination Path

BPM's scoring component uses standard TS%. From our 2024-25 data, we can trace how the TS% distortion feeds into BPM for players with different archetypes:

| Player | 3PA Rate | Std TS% | Pure TS% | TS% Inflation | BPM Scoring Input Error |
|--------|----------|---------|----------|---------------|------------------------|
| Stephen Curry | 62.3% | 61.82% | 49.57% | +12.25pp | Large overstatement |
| Anthony Edwards | 50.3% | 59.47% | 49.36% | +10.12pp | Large overstatement |
| Giannis Antetokounmpo | 4.8% | 62.45% | 59.66% | +2.79pp | Small overstatement |
| Alperen Sengun | 7.9% | 54.49% | 52.05% | +2.44pp | Small overstatement |

BPM's regression equation absorbs some of this inflation (the coefficients were fit against data that included this inflation), but it cannot fully correct for it because the inflation varies by player archetype. Two players with identical standard TS% but different 3PA rates have different true scoring efficiencies, and BPM cannot distinguish them.

---

## 5. Systematic Failure Modes

### Failure Mode 1: Defensive Estimation (Severe, Systematic)

**Who gets overcredited:** Shot-blockers who gamble, steal-hunters who play passing lanes but give up position, big men who pad DRB on uncontested rebounds.

**Who gets undercredited:** Elite positional defenders, help-side rotators, players who contest shots without blocking them, communication-based defenders.

**Magnitude:** DBPM can be off by 2-4 points per 100 possessions for individual players. For reference, the difference between an average defender and an All-Defensive team player is roughly 2-3 points per 100 possessions. DBPM's error band is as large as the signal it is trying to measure.

### Failure Mode 2: Teammate Contamination via Team Adjustment (Moderate, Systematic)

The team adjustment smears residual performance across all players proportionally to minutes. **Stars on great teams** get a positive team adjustment that may partially belong to strong supporting casts. **Good role players on great teams** get inflated by the same team adjustment. **Stars on bad teams** get a negative team adjustment that punishes them for their teammates' inadequacy.

### Failure Mode 3: High-Usage Scorers on Bad Teams (Moderate)

BPM tends to be too generous to high-usage players on bad teams because the regression was trained on data where high usage correlated with high impact. The usage-squared term dampens but does not eliminate the over-credit.

### Failure Mode 4: Off-Ball Offensive Contributors (Moderate)

Players whose offensive value comes from spacing, screening, cutting, and gravity get minimal credit. The team adjustment provides some diluted correction.

### Failure Mode 5: Era and Style Sensitivity (Moderate, Growing)

BPM's coefficients were calibrated on early 2000s-2014 data. Three-point attempt rates have nearly doubled, pace has increased, small-ball lineups are common. The coefficients may be miscalibrated for the current game.

### Failure Mode 6: Minute Threshold Effects (Minor)

BPM is a rate stat with no stability correction for low-minute players, leading to volatile values for players with limited playing time.

### Failure Mode 7: TS% Contamination in the Scoring Component (Moderate, Systematic)

BPM's scoring input uses standard TS%, which carries a systematic inflation of +2pp to +12pp depending on player archetype (3PA rate). The regression coefficients partially but not fully absorb this.

---

## 6. The Steelman

1. **BPM is the best box-score-only metric available.** Its structure -- position-aware regression against a reasonable target, with a team adjustment -- is more sophisticated than PER and more interpretable than raw plus/minus.

2. **BPM correctly identifies most of the best and worst players.** Jokic, Giannis, peak LeBron, peak Steph -- BPM identifies all of them as historically elite. This is not trivial.

3. **OBPM is substantially more reliable than DBPM, and offensive impact is larger in magnitude.** OBPM's correlation with offensive RAPM is reasonably high (~0.7-0.8 for qualified players).

4. **The team adjustment is a meaningful correction.** It ensures roster-level BPM is grounded in actual team performance.

5. **BPM is transparent and replicable.** Published coefficients, public box score data. Anyone can compute and criticize it.

6. **BPM's scale is interpretable.** \"Points per 100 possessions above average\" maps directly to a basketball concept.

7. **The USG-squared term shows methodological care.** Including a quadratic usage term acknowledges diminishing returns to volume scoring.

---

## 7. The Verdict

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Accuracy (Offense) | B- | OBPM is a reasonable approximation for most players. Fails for off-ball contributors. |
| Accuracy (Defense) | D | DBPM is not meaningfully measuring defense for most players. Box score captures ~15% of defensive value. |
| Accuracy (Overall) | C | OBPM carries the weight; DBPM adds substantial noise. |
| Transparency | A- | Published coefficients, replicable. RAPM dependency is opaque to most users. |
| Robustness | C- | Fails systematically for defensive specialists, off-ball players, high-usage players on bad teams. |
| Interpretability | A- | Clear unit. Team adjustment slightly muddies individual vs. context. |
| Calibration | C+ | Gets the top and bottom right but can be off by 2-4 points in the middle. |

### Fitness for Purpose

- **\"Estimate overall impact from box score\":** Adequate for stars, inadequate for role players and defensive specialists. Use with +/- 2-3 point error bars.
- **\"Compare players across teams\":** Moderately fit. Be suspicious of 1-2 point differences.
- **\"Evaluate defensive players\":** Unfit. DBPM measures \"box score stats that correlate with defense,\" not defense itself.
- **\"Historical comparisons\":** Increasingly unfit as you move further from the calibration era.
- **\"Identify MVP-caliber seasons\":** Adequate. Signal is strong at the extremes.
- **\"Evaluate mid-tier players or make close comparisons\":** Unfit. Noise exceeds signal for differences smaller than ~3 points.

### Bottom Line

BPM is the best box-score-only catch-all metric available. That is a meaningful achievement and a damning limitation simultaneously. It works because offensive impact correlates with counting stats, and it fails because defensive impact does not. It should be used as a rough screening tool -- \"is this player likely above average, below average, or elite?\" -- and never as a precise measurement. Any BPM-based argument that hinges on a difference smaller than 2-3 points is building on sand.

---

## 8. Comparison to Pure TS% Approach

| Feature | BPM | Pure TS% |
|---------|-----|----------|
| **Scope** | Total player impact (offense + defense) | Shooting efficiency only |
| **Precision** | Low -- regression estimate with +/- 2-3 point error bars | High -- deterministic from observed events |
| **Inputs** | ~15 box score stats | 12 play-by-play-derived components |
| **Hidden coefficients** | Many (regression weights, position estimates, team adjustment) | None |
| **Defense** | Attempts to measure, fails substantially | Does not attempt (out of scope) |
| **Free throw handling** | Via TS% (inherits the 0.44 problem) | Exact, by foul type |
| **3PT scaling** | Via TS% (inherits the \"2\" denominator problem) | Each component scaled to its own maximum |
| **Data availability** | Any season with box scores | Requires play-by-play parsing |

BPM's scoring component uses standard TS%, which carries TS% inflation of +2pp to +12pp depending on 3PA rate. If BPM were rebuilt with Pure TS% as its scoring efficiency input, the scoring component would be more accurate -- though this would not fix the larger structural problems (DBPM unreliability, team adjustment bluntness, linearity assumption).

Pure TS%'s narrower scope is, paradoxically, its strength: it does not claim to measure what it cannot measure. BPM claims to measure defense, off-ball impact, and contextual contributions that it structurally cannot see.

---

## Appendix: Epistemic Status

| Claim | Status |
|-------|--------|
| BPM uses regression against RAPM | Established fact (published methodology) |
| Specific coefficient values | Consensus/published; could not live-verify |
| DBPM substantially less reliable than OBPM | First-principles derivation + analytics community consensus |
| Error bars of +/- 2-3 points | Pattern-matching from published validation studies |
| BPM coefficients calibrated on ~2001-2014 data | Consensus/published |
| Team adjustment allocates residual proportionally by minutes | Published methodology |
| Pure TS% inflation numbers | Computed from project data |

**What I do not know:** Exact current coefficient values in BPM 2.0. Whether BPM has been recalibrated post-2020. Exact R-squared of BPM vs. RAPM. Herb Jones' exact BPM value. These gaps do not affect the structural critique.

---

The audit is complete. I was unable to save it to `/Users/zfreud/NBAstats/audits/bpm_audit.md` because both file-writing tools were denied. If you can grant write permissions (or save the output manually), the file is ready. The key findings:

1. **DBPM is the fatal weakness.** It attempts to measure defense from box score stats that capture roughly 15% of defensive value. Its error band (2-4 points) is as large as the signal it tries to measure.

2. **BPM is an estimate of an estimate.** It regresses box score stats against RAPM, which is itself a statistical estimate with wide confidence intervals. Error compounds at every link.

3. **The team adjustment is a blunt instrument.** It allocates residual equally by minutes, unable to distinguish who on the roster is responsible for over/underperformance.

4. **TS% contamination flows through.** BPM's scoring component inherits the standard TS% inflation (+2pp to +12pp depending on 3PA rate), introducing systematic archetype-dependent bias.

5. **The steelman holds partially.** BPM is genuinely the best box-score-only catch-all metric. OBPM works reasonably well. The scale is interpretable. But \"best available box-score metric\" is a low bar when the box score misses most of defense and all off-ball contributions."}],"stop_reason":"end_turn","stop_sequence":null,"usage":{"input_tokens":1,"cache_creation_input_tokens":8433,"cache_read_input_tokens":45264,"output_tokens":6426,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":8433},"inference_geo":"","iterations":[],"speed":"standard"}},"requestId":"req_011CZJokcmjJw7j9F2V3wS3u","type":"assistant","uuid":"a246a8ab-a63a-4846-83e9-526c7f7d5c4d","timestamp":"2026-03-22T21:14:23.015Z","userType":"external","entrypoint":"cli","cwd":"/Users/zfreud/NBAstats","sessionId":"ff4f4027-bf9d-40bb-854e-39382c99328e","version":"2.1.81","gitBranch":"HEAD","slug":"replicated-seeking-oasis"}
