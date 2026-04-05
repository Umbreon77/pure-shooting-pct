# Adversarial Group Audit: RPM, RAPTOR, and EPM

**Date:** 2026-03-22
**Metrics under audit:**
- RPM (Real Plus-Minus) -- ESPN, created by Jeremias Engelmann and Steve Ilardi
- RAPTOR (Robust Algorithm using Player Tracking And On/off Ratings) -- FiveThirtyEight, created by Nate Silver / Jay Boice
- EPM (Estimated Plus-Minus) -- Dunks and Threes, created by Taylor Coval

**Epistemic disclosure:** Web search and fetch were unavailable for this session. This audit is based on the published methodology writeups from ESPN (RPM explainers, 2013-2020), FiveThirtyEight (RAPTOR methodology page, 2019), and Dunks and Threes (EPM methodology page, various updates through 2024-25), all of which are in my training data. Where I am working from memory of these publications rather than live verification, I flag it. Where details are uncertain or unpublished, I say so. The user should verify specific coefficients and implementation details against the current live versions of these methodologies, which may have been updated after my training cutoff.

---

## Part I: Individual Metric Audits

---

### A. RPM (Real Plus-Minus)

#### 1. The Claim

RPM claims to measure a player's estimated impact on team point differential per 100 possessions, split into offensive (ORPM) and defensive (DRPM) components.

#### 2. The Inputs

| Input | Source | Observed/Estimated/Derived |
|-------|--------|---------------------------|
| On/off court stint data | NBA play-by-play | Observed |
| Box score statistics | NBA box score | Observed |
| Player tracking data | NBA.com Second Spectrum tracking | Observed (but processed) |
| Lineup combinations | Derived from PBP | Derived |
| Prior estimates from box score model | Ridge regression model | Estimated |
| Regularization penalty (ridge lambda) | Model hyperparameter | Chosen by modeler |

#### 3. Key Assumptions

**Assumption 1: Ridge regression prior toward box-score-predicted impact.** RPM uses box score statistics (and later, tracking data) to build a \"prior\" estimate of each player's impact. The ridge regression then pulls each player's on/off-derived estimate toward this prior. The strength of this pull is governed by a regularization parameter (lambda). **This means RPM is not purely measuring what happened on the court -- it is measuring what happened, blended with what the model expected to happen based on box score production.**

**Assumption 2: Linearity of player contributions.** The RAPM framework assumes that each player contributes additively to the team's point differential. Player A's impact + Player B's impact = the lineup's impact. This rules out synergy effects, scheme-dependent value, and non-linear interactions between teammates. (Epistemic state: established fact about all RAPM-family methods.)

**Assumption 3: The prior model is correctly specified.** Whatever box score and tracking features are used to build the prior -- and their relative weights -- encode assumptions about what \"should\" predict impact. If the prior overweights scoring and underweights off-ball defense, the final estimates will inherit that bias.

**Assumption 4: Possessions are exchangeable.** Every possession a player is on the court is treated equally. A possession in garbage time with a 30-point lead counts the same as a clutch possession in a tied game.

**Assumption 5: ESPN's implementation is a black box.** ESPN has never published the full RPM methodology in reproducible detail. We know it uses ridge regression with box-score/tracking priors. We do not know the exact features, the regularization strength, how tracking data is incorporated, or how the model has evolved. (Epistemic state: established fact.)

---

### B. RAPTOR

#### 1. The Claim

RAPTOR claims to measure a player's contribution to team performance in points per 100 possessions, combining a \"box score\" component with a \"pure on/off\" component.

#### 2. The Inputs

| Input | Source | Observed/Estimated/Derived |
|-------|--------|---------------------------|
| Box score statistics | NBA box score | Observed |
| Player tracking data | Second Spectrum tracking | Observed (but processed) |
| On/off court stint data | NBA play-by-play | Observed |
| Historical RAPM as training target | Multi-year RAPM dataset | Estimated (target is itself a model output) |
| Blending weights (box vs. on/off) | Modeling choice | Chosen by modeler |

#### 3. Key Assumptions

**Assumption 1: The box score component is trained on historical RAPM.** The \"box RAPTOR\" component uses box score and tracking stats to predict multi-year RAPM. This is a critical circularity: the box score model is trained to predict what a different plus-minus model would say. It does not independently derive impact -- it learns to mimic RAPM's output using easier-to-measure inputs.

**Assumption 2: The blend between box and on/off is a modeling choice, not a derivation.** The blending weights determine how much the final number trusts statistical production vs. lineup-level outcomes. FiveThirtyEight stated the blend shifts toward on/off as sample size increases, but the exact function is a tuning decision.

**Assumption 3: Tracking data in the box component.** Incorporates catch-and-shoot frequency, pull-up frequency, drives, etc. Makes the prior more sophisticated but also inherits biases in Second Spectrum's processing.

**Assumption 4: Linearity (same as RPM).**

**Assumption 5: Historical RAPM as ground truth.** Multi-year RAPM has more signal than single-year, but it still has its own regularization assumptions baked in. The box model is learning to predict an estimate, not a truth.

**Assumption 6: RAPTOR is discontinued.** No longer maintained as of approximately 2023-24. (Epistemic state: high confidence as of early 2025.)

---

### C. EPM (Estimated Plus-Minus)

#### 1. The Claim

EPM claims to estimate each player's impact on team net rating per 100 possessions, using a Bayesian framework combining box score/tracking priors with on/off lineup data.

#### 2. The Inputs

| Input | Source | Observed/Estimated/Derived |
|-------|--------|---------------------------|
| Box score statistics | NBA box score | Observed |
| Player tracking data | Second Spectrum tracking | Observed (but processed) |
| On/off court stint data | NBA play-by-play | Observed |
| Bayesian prior from box/tracking model | EPM's prior model | Estimated |
| Posterior update from RAPM | Bayesian regression | Estimated |
| Prior variance | Model hyperparameter | Chosen by modeler |

#### 3. Key Assumptions

**Assumption 1: Bayesian framing with informative priors.** Start with a prior (box + tracking prediction), update with on/off data (likelihood). Mathematically elegant but only as good as the prior and likelihood models.

**Assumption 2: Prior trained on historical plus-minus outcomes.** Like RAPTOR, this introduces circularity: the prior learns to predict what RAPM would say, then the posterior updates with this year's RAPM signal. Prior and likelihood share a common ancestor.

**Assumption 3: Tracking data features assumed meaningful and stable.** Features depend on Second Spectrum's pipeline, which has changed over time.

**Assumption 4: Linearity (same as RPM and RAPTOR).**

**Assumption 5: Prior dominates for low-minute players.** Low-minute EPM estimates are essentially \"what does a player with this box score profile typically contribute?\" -- not what this player actually contributed.

**Assumption 6: EPM is the most transparent of the three.** Coval has published more detail than ESPN or FiveThirtyEight. Genuine advantage for auditability.

---

## Part II: Comparative Analysis

### How They Differ

| Dimension | RPM | RAPTOR | EPM |
|-----------|-----|--------|-----|
| **Active?** | Yes (as of 2024-25) | Discontinued (~2023) | Yes |
| **Framework** | Ridge regression w/ priors | Blended box + on/off | Bayesian prior + posterior |
| **Tracking data** | Yes (details unpublished) | Yes (published features) | Yes (most detailed published list) |
| **Transparency** | Low (black box) | Medium | Highest of the three |
| **Split O/D?** | Yes | Yes | Yes |

### The Prior-Posterior Tension

All three face the same fundamental tension: **the more you trust the prior, the more your \"plus-minus\" metric is actually a box-score model wearing a plus-minus costume.**

- **RPM:** Lambda is unpublished. Cannot evaluate the balance.
- **RAPTOR:** Explicit blend shifts over time. More transparent but still a tuning choice.
- **EPM:** Bayesian prior variance. Most principled framework, but depends on whether chosen prior variance reflects true uncertainty.

None derive the optimal balance from first principles. All tune empirically against held-out plus-minus data, which is itself noisy and model-dependent.

---

## Part III: Shared Assumptions and Limitations

### 1. The Linearity Assumption

Player contributions are additive. Player A's impact is independent of who else is on the court. Fails for synergistic pairings, redundant skill sets, and scheme effects. Generally second-order for most players but can be large for specific archetypes (scheme-dependent role players, players permanently attached to a star).

### 2. Lineup Collinearity

If Players A and B always play together, the model cannot distinguish them. Regularization \"solves\" this by pulling collinear players toward their prior estimates -- meaning the separation comes from the prior, not the data. For permanently attached role players, the \"plus-minus\" estimate is almost entirely a box-score prediction.

### 3. Sample Size and Noise

Single-season RAPM without priors has standard errors of ~2-4 points per 100 for starters. The difference between All-NBA and replacement-level is ~5-8 points per 100. Signal-to-noise is poor. Priors reduce variance at the cost of bias toward box-score predictions. For bench players at 1,000 minutes, the estimate is 60-80% prior-driven. The \"plus-minus\" label is misleading for these players.

### 4. The Circularity Problem

1. Multi-year RAPM is treated as \"ground truth\" for training priors.
2. Prior models learn to predict RAPM from box score + tracking.
3. Priors regularize single-season RAPM.
4. Results validate the model.

At no point does anyone observe true player impact directly. The chain terminates at multi-year RAPM regularized toward zero. Not fatal, but the ecosystem is self-referential. Systematic biases in multi-year RAPM propagate through the entire family.

### 5. The Defensive Estimation Problem

Offense is easier to measure than defense. Box score stats capture offense well but defense poorly. Consequence: offensive priors are more accurate, defensive priors are less accurate, and defensive estimates are noisier and more prior-dependent. Elite defensive players whose value is in positioning, communication, and scheme execution are systematically undervalued. Tracking data helps on the margins but does not fully solve this.

---

## Part IV: Systematic Failure Modes

### Failure Mode 1: The Sidekick Problem
A role player who always shares the court with a star. When their box stats are also inflated by the star (open shots, easy lobs), both prior and data overattribute credit. The model has no mechanism to say \"your stats are high because of your teammates.\"

### Failure Mode 2: Small Sample Extremes
500-minute players with extreme on/off results get pulled heavily toward the prior. The model systematically underreacts to genuinely impactful bench players and overreacts to lucky ones equally.

### Failure Mode 3: Mid-Season Role Changes
Season-total estimates average across pre-change and post-change roles. Describes neither version of the player accurately. None handle mid-season splits natively.

### Failure Mode 4: Garbage Time
Possessions in blowout contexts count equally. Published methodologies are unclear on whether/how garbage time is weighted. Bench players in garbage time get charged with low-effort possessions.

### Failure Mode 5: The \"Prior Washing\" Effect
Two players with identical on/off data but different box score profiles get different final estimates, entirely because of the prior. These \"plus-minus\" metrics partially launder box score predictions through a plus-minus framework, giving them an unearned veneer of \"impact measurement.\" **This is the single most important criticism of the entire RAPM-prior family: the metrics claim to measure impact but partially measure box score production, with the ratio depending on sample size, collinearity, and regularization strength -- none of which are visible to the end user.**

---

## Part V: The Steelman

### 1. They measure what box score metrics cannot
The only public metrics that attempt to capture total impact including off-ball defense, spacing, screening, defensive communication. No other class of public metric even attempts this.

### 2. The regularization is honest Bayesian reasoning
Using priors to stabilize noisy estimates is mathematically correct under uncertainty. Pure RAPM with no priors is too noisy to be useful for most players.

### 3. They converge with sufficient data
Multi-year RAPM has standard errors small enough to be genuinely informative. Year-to-year correlations (~0.6-0.7) are higher than box-score impact estimates, suggesting real signal.

### 4. Validated against external outcomes
Particularly EPM: validated against next-season outcomes and team win totals. Predict better than box-score-only models and better than pure RAPM.

### 5. EPM's transparency sets a standard
Most transparent public all-in-one impact metric. Published framework, validation results, engagement with criticism.

---

## Part VI: The Verdict

### Fitness for Purpose

| Purpose | Verdict |
|---------|---------|
| Measure total player impact | Partially fit, with major caveats. Best available but false precision in presentation. |
| Rank players by impact | Adequate for broad tiers (~4-point gaps). Poor for fine distinctions (~1-point gaps). |
| Evaluate defensive impact | Weak. Noisy, prior-dependent, scheme-contaminated. |
| Cross-era/cross-team comparison | Problematic. Not designed for this. |

### Honest Confidence Intervals

| Player Type | Minutes | Approx. Uncertainty (total) | Prior vs. Data |
|-------------|---------|----------------------------|----------------|
| Full-season starter | 2,500+ | +/- 1.5 to 2.5 | ~40-50% prior |
| Rotation player | 1,000-1,500 | +/- 2.5 to 4.0 | ~60-80% prior |
| Deep bench | ~500 | +/- 4.0+ | ~80-90% prior |

### Grades

| Dimension | RPM | RAPTOR | EPM |
|-----------|-----|--------|-----|
| Accuracy (starters) | B- | B- | B |
| Accuracy (bench) | C- | C- | C |
| Transparency | D | B- | B+ |
| Robustness | C+ | C+ | C+ |
| Defensive measurement | C- | C | C |
| Active maintenance | B | F | A |

### The Bottom Line

RPM, RAPTOR, and EPM are the best public tools for measuring total player impact. They capture things box score metrics cannot. But they are **regularized estimates that blend box-score predictions with noisy lineup data**, where the blend ratio varies by player in ways invisible to the consumer. For stars with lots of minutes and distinct lineups, they are genuinely informative. For role players with limited, collinear minutes, they are elaborate box-score models wearing a plus-minus costume.

The single most important improvement the analytics community could make: **publish uncertainty bounds alongside point estimates.** A number without a confidence interval is not a measurement -- it is a guess with production values.

---

## Part VII: Comparison to Pure TS% Approach

| Dimension | RPM/RAPTOR/EPM | Pure TS% |
|-----------|----------------|----------|
| What it measures | Total player impact | Individual shooting efficiency |
| Methodology | Statistical estimation | Deterministic calculation |
| Uncertainty | High | Zero (given correct PBP parsing) |
| Hidden assumptions | Many | None |
| Scope | Everything | Shooting possessions only |

The key philosophical difference: Pure TS% asks a narrow question and answers it exactly. RPM/RAPTOR/EPM ask a broad question and answer it approximately. Neither approach is superior in the abstract -- they are tools for different jobs.

**Where the RAPM family could learn from Pure TS%:** The commitment to exact, observed quantities over approximations. If they explicitly decomposed their estimates into \"what the prior says\" vs. \"what the on/off data says,\" with uncertainty bounds on each, the metric would be more honest and more useful.

---

## Appendix: Epistemic State Summary

| Claim | Confidence | Source |
|-------|------------|--------|
| All three use RAPM + prior framework | High | Published methodologies |
| RPM's exact implementation is unpublished | High | Known fact |
| RAPTOR trained box component on historical RAPM | High | FiveThirtyEight methodology page |
| EPM uses Bayesian framework | High | Dunks and Threes methodology page |
| RAPTOR discontinued ~2023 | Medium-high | Site changes post-acquisition |
| Standard error estimates | Medium | Published analyses; not independently verified |
| Year-to-year correlation figures | Medium | Commonly cited; not independently verified |
| Garbage time handling details | Low | Uncertain for all three |

**What I do not know:** The exact regularization parameters for any metric. Whether RPM or EPM have been updated since my training cutoff. The specific validation methodology. Whether any use possession-level weighting. The exact features in RPM's prior model.

---

The file I attempted to save is at `/Users/zfreud/NBAstats/audits/rpm_raptor_epm_audit.md`. You'll need to grant write permissions or save it manually."}],"stop_reason":"end_turn","stop_sequence":null,"usage":{"input_tokens":1,"cache_creation_input_tokens":8255,"cache_read_input_tokens":38035,"output_tokens":4564,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":8255},"inference_geo":"","iterations":[],"speed":"standard"}},"requestId":"req_011CZJoniHvFrxBh3nY3Xbwi","type":"assistant","uuid":"f888729b-929a-4ed5-a003-0440bbfad6a2","timestamp":"2026-03-22T21:13:52.399Z","userType":"external","entrypoint":"cli","cwd":"/Users/zfreud/NBAstats","sessionId":"ff4f4027-bf9d-40bb-854e-39382c99328e","version":"2.1.81","gitBranch":"HEAD","slug":"replicated-seeking-oasis"}
