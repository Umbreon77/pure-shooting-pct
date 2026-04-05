# Adversarial Audit: Value Over Replacement Player (VORP)

**Date:** 2026-03-22
**Formula under audit:** VORP = [BPM - (-2.0)] x (% of team minutes played) x (team games / 82)
**Expanded:** VORP = [BPM + 2.0] x (MP / (Team_MP / 5)) x (Team_G / 82)
**Source:** Basketball-Reference, developed by Daniel Myers (BPM 2.0, published ~2014)
**Epistemic note:** Web access was unavailable during this audit. BPM/VORP methodology is drawn from my training data on Daniel Myers' published writeups on Basketball-Reference. All claims about the methodology are flagged as *consensus (auditable)* -- the primary source is https://www.basketball-reference.com/about/bpm2.html and should be verified against it.

---

## 1. The Claim

VORP claims to measure the total value a player contributes to their team above what a \"replacement-level\" player would contribute, expressed in points per 100 possessions accumulated over the season, scaled to an 82-game season.

Put differently: VORP answers \"How many more points of team net rating did this player produce over the course of the season compared to a freely available fill-in?\"

---

## 2. The Inputs

| Input | Source | Type | What It Is |
|-------|--------|------|------------|
| **BPM** | Derived from box score stats via regression | Estimated | A player's estimated contribution to team net rating per 100 possessions while on court. Regressed from box score stats against RAPM-like on/off data. |
| **-2.0 (replacement level)** | Asserted by convention | Assumed constant | The BPM value attributed to a \"replacement-level\" player -- one available at minimal cost (end of bench, G-League callup, minimum contract veteran). |
| **MP (minutes played)** | Box score | Observed | Player's total minutes played during the season. |
| **Team_MP** | Box score | Observed | Total team minutes played (used to compute % of team minutes). Since 5 players are on the court at once, a player's \"share\" is MP / (Team_MP / 5). |
| **Team_G (team games)** | Schedule | Observed | Number of games the player's team has played. Used to prorate to an 82-game season. |
| **82 (season length)** | Asserted by convention | Assumed constant | The standard NBA regular season length. |

### BPM's Own Inputs (the layer underneath)

VORP inherits all of BPM's complexity. BPM 2.0's inputs include *(consensus, auditable)*:

| BPM Input | Notes |
|-----------|-------|
| Points, rebounds, assists, steals, blocks, turnovers | Standard box score, observed |
| Usage rate | Derived from FGA, FTA, TOV, team possessions |
| True shooting percentage | Uses the 0.44 FTA coefficient -- an approximation this project exists to replace |
| Assist percentage, turnover percentage | Derived |
| Offensive/defensive rebound percentage | Derived |
| Steal percentage, block percentage | Derived |
| 3-point attempt rate | Derived |
| Team pace | Derived (possessions per 48 minutes) |
| Position estimate | Estimated from height/position data |
| Team strength (SRS) | Derived from point differential and strength of schedule |
| Regression coefficients | Fitted against multi-year adjusted plus-minus data |

**Critical observation:** VORP is presented as a single formula, but it is actually a three-layer stack: (1) BPM's regression model estimates a rate stat, (2) the -2.0 replacement level subtracts an assumed baseline, (3) the minutes multiplier converts rate to cumulative. Each layer has its own assumptions, and errors compound across layers.

---

## 3. The Assumptions

### Assumption 1: BPM is an accurate estimate of player impact per 100 possessions

This is the foundational assumption, and it is enormous. BPM is a **box-score regression** -- it takes box score statistics and tries to predict what a player's Regularized Adjusted Plus/Minus (RAPM) would be. The regression was fitted on historical data.

**Problems inherited from BPM:**

- **Box score stats are an incomplete representation of basketball.** Defensive positioning, screen-setting, gravity, off-ball movement, help defense quality -- none of these appear in the box score. BPM can only measure what the box score captures. [Epistemic state: established fact]
- **The regression coefficients are fitted, not derived.** The weights on assists, rebounds, steals, etc. are whatever best predicted historical RAPM. They are not first-principles valuations of those actions. If the relationship between, say, steals and true defensive impact changed (or was always noisy), BPM would be wrong by construction. [Epistemic state: first-principles reasoning about regression methodology]
- **BPM uses TS% internally, which uses the 0.44 coefficient.** This means VORP inherits the exact approximation error that Pure TS% was designed to eliminate. Every distortion in TS% flows through BPM's shooting efficiency term and into VORP. [Epistemic state: consensus, auditable]
- **Position adjustment.** BPM adjusts for player position/height. This is an attempt to normalize expectations (a center who gets 5 rebounds is less impressive than a guard who gets 5). But position estimation itself is imprecise, and the adjustment bakes in assumptions about what each position \"should\" produce. [Epistemic state: consensus, auditable]
- **Team adjustment.** BPM adjusts for team strength so that good players on bad teams are not penalized (and vice versa). This adjustment uses SRS (Simple Rating System), which is itself derived. The team adjustment is applied after individual BPM is computed, so that all players on a team sum to the team's point differential. This is a constraint, not a measurement. [Epistemic state: consensus, auditable]

### Assumption 2: -2.0 is the correct replacement level

This is the single most consequential assumption in VORP, and it is the least defended.

**What -2.0 means:** A \"replacement player\" -- the kind of player available at minimal cost to fill a roster spot -- is assumed to produce a team net rating 2.0 points per 100 possessions worse than league average.

**Where did -2.0 come from?** To my knowledge, this was chosen by convention, calibrated to produce \"reasonable-looking\" results -- specifically, so that a team of five replacement-level players would win roughly 20-22% of their games (~16-18 wins in an 82-game season). [Epistemic state: consensus, auditable -- should be verified against Myers' original writeup]

**Problems:**

- **It is a single number applied uniformly across all positions, eras, and contexts.** A replacement-level point guard and a replacement-level center are both assumed to be -2.0 BPM. There is no obvious reason this should be true. The supply and demand for different positions varies; replacement-level center play may be systematically better or worse than replacement-level guard play. [Epistemic state: first-principles reasoning]
- **It does not vary by era.** The talent pool, rule changes, pace, and offensive efficiency have changed substantially over NBA history. A replacement-level player in 2004 (hand-checking era, 90 possessions per game) may be very different from a replacement-level player in 2025 (pace-and-space, 100+ possessions). Holding -2.0 constant across all seasons assumes the distance between replacement and average has not changed. [Epistemic state: first-principles reasoning]
- **The replacement level is self-referential.** \"Replacement level\" is defined as \"what a team would get from a freely available player.\" But which players are \"freely available\" depends on the league's roster and economic structure, which changes with CBA rules, G-League development, two-way contracts, etc. The concept is coherent in theory but operationally slippery. [Epistemic state: first-principles reasoning]
- **-2.0 may be too generous (replacement is better than assumed) or too harsh (replacement is worse).** If true replacement players are actually -3.0 BPM, then VORP systematically overvalues every player. If they are -1.0, it systematically undervalues them. The absolute VORP numbers are entirely dependent on this choice, yet it is rarely examined. [Epistemic state: first-principles reasoning]

### Assumption 3: Value scales linearly with minutes

VORP assumes that a player who plays 36 minutes per game at +5.0 BPM produces exactly twice the value of a player who plays 18 minutes per game at +5.0 BPM. This is the core of the rate-to-cumulative conversion.

**Problems:**

- **Fatigue effects.** A player who plays 40 minutes may be less effective in minutes 35-40 than in minutes 1-10. BPM is an average over all minutes played, so it does not capture within-game degradation. The linear scaling treats minute 40 as equally productive as minute 5. [Epistemic state: first-principles reasoning, supported by empirical research on fatigue effects]
- **Lineup context varies with minutes.** A star playing 36 minutes is on the court with different lineups at different times (starters vs. bench units). Their BPM is an average across all these contexts. The marginal minute may have different value depending on who else is on the court. Linear scaling ignores this. [Epistemic state: first-principles reasoning]
- **Garbage time.** Minutes in blowout wins/losses are treated identically to minutes in close games. A player who pads stats in garbage time gets full VORP credit. [Epistemic state: first-principles reasoning]

### Assumption 4: The 82-game proration is meaningful

The (Team_G / 82) factor scales VORP to an 82-game season. During the season, this simply prorates partial seasons. But it also means:

- **Lockout-shortened seasons** (66 games in 2011-12, 72 in 2019-20) produce lower VORPs for everyone, making cross-season comparisons misleading unless manually adjusted.
- **Mid-season trades** or injuries produce prorated values that assume the player would have maintained their rate for the full season, which may not be true.

### Assumption 5: BPM is additive and context-independent

VORP treats BPM as if a player's impact is portable -- the same regardless of teammates, opponents, or system. A player with +5.0 BPM on a fast-paced team is treated as equally impactful as a +5.0 player on a slow-paced team, even though the fast-paced team has more possessions (and thus more opportunities for the impact to manifest). BPM is per-100-possessions, and the minutes conversion should roughly account for this -- but \"roughly\" is not \"exactly.\"

---

## 4. The Math -- Worked Examples

### Example A: The Healthy Star

**Hypothetical: Nikola Jokic, 2023-24 type season**
- BPM: +12.0 (elite)
- Minutes: 2,476 in 79 games
- Team games: 82
- Team minutes: 82 x 48 x 5 = 19,680 (per-player basis: 19,680 / 5 = 3,936)

```
% of team minutes = 2,476 / 3,936 = 0.6291 (62.9%)
VORP = [12.0 - (-2.0)] x 0.6291 x (82/82)
     = 14.0 x 0.6291 x 1.0
     = 8.81
```

This is a plausible elite-season VORP. No obvious math issues.

### Example B: The Injured Star vs. Healthy Role Player

**Injured star:**
- BPM: +10.0, Minutes: 800 in 25 games, Team games: 82

```
% of team minutes = 800 / 3,936 = 0.2033
VORP = 12.0 x 0.2033 = 2.44
```

**Healthy role player:**
- BPM: +1.0, Minutes: 2,400 in 80 games

```
% of team minutes = 2,400 / 3,936 = 0.6098
VORP = 3.0 x 0.6098 = 1.83
```

The injured +10.0 BPM star (2.44 VORP) edges the healthy +1.0 role player (1.83). Reasonable on its face -- but it illustrates VORP's core tension: a player needs only modest BPM above replacement to accumulate meaningful VORP through durability alone.

### Example C: The Durability Tax

**Ironman, slightly-above-replacement:**
- BPM: -0.5, Minutes: 2,800 in 82 games

```
VORP = 1.5 x 0.7114 = 1.07
```

**Elite player, half season:**
- BPM: +8.0, Minutes: 1,400 in 41 games

```
VORP = 10.0 x 0.3557 = 3.56
```

VORP gets this right -- the elite half-season player dominates. But as rate differences narrow, durability swamps quality.

### Example D: The Tanking Team

**Above-average player sat for tank:**
- BPM: +3.0, Minutes: 2,000 in 65 games, Team games: 82

```
VORP = 5.0 x 0.5081 = 2.54
```

If he played all 82 games at same rate (~2,525 min), VORP would be ~3.21. He is penalized 0.67 VORP for a team decision, not a quality difference.

### Example E: The Noise Cliff at Replacement Level

**Player at exactly -2.0 BPM, 2,500 minutes:** VORP = 0.0
**Player at -2.1 BPM, same minutes:** VORP = -0.064
**Player at -1.9 BPM, same minutes:** VORP = +0.064

A 0.2 BPM difference -- well within BPM's standard error of ~2-3 points -- flips the sign. The replacement level creates an interpretive discontinuity where no actual quality discontinuity exists.

---

## 5. Systematic Failure Modes

### Failure Mode 1: BPM's Errors, Amplified

- **Overvalues high-usage players.** BPM's regression gives substantial weight to usage terms. High-usage players also tend to play heavy minutes. VORP compounds the BPM overestimate with a large minutes multiplier. [Epistemic state: consensus, auditable]
- **Undervalues defensive specialists.** Box scores miss defensive positioning, rotations, help quality. Players whose value is primarily defensive get systematically lower BPM and VORP. [Epistemic state: consensus, auditable]
- **Overvalues rebounding.** Many rebounds are uncontested. BPM gives credit for them. Traditional big men get inflated VORP. [Epistemic state: consensus, auditable]

### Failure Mode 2: Durability Bias

By design, VORP rewards playing time. A player resting 15 games for playoff health has lower regular-season VORP. Bench specialists are structurally capped. This is mathematically correct if \"value\" means \"what happened,\" but misleading if used to evaluate player quality.

### Failure Mode 3: Replacement Level Is a Free Parameter

-2.0 determines the entire absolute scale. It does not vary by position or era. Relative rankings within a season are unaffected, but absolute values, cross-era comparisons, and \"wins above replacement\" conversions all depend on accepting this undefended constant.

### Failure Mode 4: Season-Length Distortion

Shortened seasons mechanically reduce everyone's VORP. Cross-season comparisons require manual adjustment that is rarely performed.

### Failure Mode 5: The Noise Floor

BPM's ~2-3 point standard error means that for the majority of NBA players (those between -4.0 and +2.0 BPM), VORP's sign may be determined by noise rather than signal. VORP is most reliable for the players who need it least (elite players everyone already knows are elite) and least reliable for the players where the question matters most (borderline rotation/replacement players).

---

## 6. The Steelman

1. **It answers a question people actually ask.** \"How valuable was this player over the whole season?\" is natural. Rate stats cannot answer it. VORP's structure -- rate minus baseline times volume -- is the correct shape for the attempt.

2. **Relative rankings are robust to replacement-level choice.** Since -2.0 is a constant subtracted from everyone, ordinal rankings within a season are unaffected by the choice.

3. **Durability IS value.** A player who plays 82 games genuinely provides more cumulative value than an equally talented player who plays 41. For GM decision-making, this matters.

4. **BPM is a reasonable box-score approximation.** It correlates well with more sophisticated measures. Its biases are known and bounded. [Epistemic state: consensus, auditable]

5. **The formula is simple and auditable.** Three operations on four inputs. No black box.

6. **Calibrated to wins.** ~2.7 points of net rating per win allows rough conversion, useful for practical decision-making.

---

## 7. The Verdict

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Conceptual soundness | B | Rate minus baseline times volume is valid |
| Input quality | C | Entirely dependent on BPM's systematic biases |
| Replacement level | D+ | Asserted, not derived. Position-invariant. Era-invariant. |
| Linearity assumption | C+ | Reasonable but demonstrably imperfect |
| Transparency | A- | Simple formula (but BPM itself is a regression) |
| Reliability for elite players | B+ | Signal overwhelms noise |
| Reliability near replacement | D | Noise overwhelms signal; sign flips from error |
| Cross-season comparability | C- | Season-length and era distortions |

### Bottom Line

VORP is a structurally sound framework built on a shaky foundation. The formula is the correct shape for cumulative value measurement. But each layer introduces error: BPM is an imperfect regression with systematic biases, -2.0 is an undefended free parameter, and the minutes multiplier assumes linearity that does not hold exactly.

For identifying the best players in a given season (top 10-15), VORP is adequate because the signal overwhelms the noise. For comparing players near replacement level, for cross-era comparisons, or for any analysis depending on absolute values rather than ordinal rankings, VORP is unreliable.

The most damaging critique: VORP presents itself as a cumulative \"value\" metric, but it cannot be decomposed back into the actual on-court events that produced the value. It is a regression estimate, baselined against an asserted constant, multiplied by playing time. At no point in this chain does anyone count what actually happened on the court with the precision required to justify the implied precision of a number like \"5.32 VORP.\"

---

## 8. Comparison to Pure TS% Approach

| Dimension | VORP | Pure TS% |
|-----------|------|----------|
| **Input source** | Box score stats fed through regression | Play-by-play event data, directly observed |
| **Estimation vs. counting** | Estimates impact via regression coefficients | Counts actual scoring events |
| **Hidden coefficients** | BPM regression weights (many), 0.44 FTA coefficient (inside BPM's TS%), -2.0 replacement level | None |
| **Scope** | Attempts to measure total player value (offense + defense) | Measures only scoring efficiency |
| **Failure mode** | Systematic biases from regression + compounding assumptions | Limited scope (does not claim to measure defense, passing, etc.) |
| **Epistemic honesty** | Presents estimated values as if they were measurements | Presents measurements as measurements |

**The key difference in philosophy:** Pure TS% measures one thing precisely. VORP tries to measure everything approximately. Neither approach is inherently superior -- they answer different questions. But VORP's danger is that its apparent precision (a single number with two decimal places) masks the large uncertainty in its inputs.

**Where VORP uses TS% internally:** BPM includes a shooting efficiency term that uses standard TS% (with the 0.44 coefficient). Every TS% distortion documented in this project flows through BPM's regression and into VORP. The error is laundered through two layers of abstraction, making it harder to detect but not smaller.

**What would a \"Pure VORP\" look like?** Replacing BPM's TS% input with Pure TS% would eliminate one source of systematic error. But the larger problems -- regression coefficients, defensive measurement, replacement level, linearity -- would remain. Fixing TS% inside BPM is necessary but not sufficient for fixing VORP."}],"stop_reason":"end_turn","stop_sequence":null,"usage":{"input_tokens":1,"cache_creation_input_tokens":7615,"cache_read_input_tokens":35388,"output_tokens":5293,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":7615},"inference_geo":"","iterations":[],"speed":"standard"}},"requestId":"req_011CZJoh4FYcqeKPi6jmAnxP","type":"assistant","uuid":"73a40ab1-1734-495c-a3f5-be1304ece6e8","timestamp":"2026-03-22T21:13:02.472Z","userType":"external","entrypoint":"cli","cwd":"/Users/zfreud/NBAstats","sessionId":"ff4f4027-bf9d-40bb-854e-39382c99328e","version":"2.1.81","gitBranch":"HEAD","slug":"replicated-seeking-oasis"}
