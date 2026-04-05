# Adversarial Audit: Assist Percentage (AST%)

**Date:** 2026-03-22
**Formula under audit:** AST% = 100 * AST / (((MP / (Tm MP / 5)) * Tm FGM) - FGM)
**Origin:** Dean Oliver, adapted by Basketball Reference. Part of the \"Four Factors\" family of basketball analytics.

---

## 1. The Claim

AST% claims to estimate the percentage of teammate field goals a player assisted while that player was on the floor.

---

## 2. The Inputs

| Input | Source | Type | What It Is | What It Is Not |
|-------|--------|------|------------|----------------|
| **AST** | Box score | Observed | Player's total assists in the game/season | Does not distinguish assist type, quality, or context |
| **MP** | Box score | Observed | Player's minutes played | Not \"time on floor with specific lineups\" |
| **Tm MP** | Box score | Observed | Team total minutes played (always 240 for a regulation game, 265 for OT, etc.) | Not adjusted for garbage time or blowouts |
| **Tm FGM** | Box score | Observed | Team total field goals made | Includes player's own FGM |
| **FGM** | Box score | Observed | Player's own field goals made | Does not include FGM on plays where the player was fouled (shooting fouls with no make) |

All five inputs are directly observed from box scores. No estimation in the inputs themselves.

The estimation lives entirely in how these inputs are combined.

---

## 3. The Assumptions

### Assumption 1: Minutes-Based Prorating of Teammate FGM

The denominator is the core assumption of this entire formula. Let me unpack it.

**What the denominator tries to do:** Estimate how many teammate field goals were made while the player was on the floor.

**How it does it:** The term `(MP / (Tm MP / 5))` is a ratio. `Tm MP / 5` equals the total game minutes (e.g., 240 / 5 = 48 for a regulation game). So `MP / (Tm MP / 5)` is the fraction of the game the player was on the court. Multiply that by `Tm FGM` to get the estimated number of team FGM while the player was on the floor. Then subtract the player's own `FGM` to get estimated teammate FGM while on floor.

**What this assumes:** That field goals are scored at a uniform rate throughout the game, and the player's on-court minutes are a representative sample of the team's scoring distribution. In other words: if a player plays 36 of 48 minutes, the formula assumes 75% of the team's FGM happened while that player was on the floor.

**When this breaks:**

- **Starters who sit during bench runs.** A starter who plays 32 minutes but sits during a 15-0 run by the bench gets credited as if 67% of team FGM happened with them on court. The actual number could be much lower.
- **Bench players in high-scoring lineups.** A bench guard who plays 22 minutes but exclusively in lineups that outscore opponents will have more teammate FGM in his minutes than the formula estimates, deflating his denominator and inflating his AST%.
- **Blowouts.** A star who plays 28 minutes in a blowout (sits the 4th quarter) while the team scores heavily in garbage time. The formula credits them with 58% of team FGM; the reality could be 40%.
- **Overtime games.** The formula handles this mechanically (Tm MP grows), but scoring rates in OT can differ sharply from regulation.

**Epistemic status:** First-principles critique. The assumption of uniform scoring rate across a player's minutes is verifiable and routinely violated. NBA on/off data shows that scoring rates vary substantially by lineup. This is not a minor approximation; it is the entire structural weakness of the formula.

### Assumption 2: Assists Are a Complete Measure of Playmaking

The numerator counts assists. An assist in the NBA is defined as a pass to a teammate who immediately scores, provided the pass is deemed to have contributed directly to the basket. This definition is subjective and applied by the scorekeeper.

**What this misses:**

- **Hockey assists.** A player makes the pass that creates the pass that creates the score. Zero credit.
- **Screen assists.** Setting a screen that frees the shooter. Zero credit.
- **Gravity-based creation.** Drawing two defenders, which opens a teammate's shot on the weak side. Zero credit.
- **Passes that create advantage but not immediate scores.** A player drives, draws help, kicks to a teammate who pump-fakes and drives for a layup. Often no assist because the scorer \"created their own shot\" after the pass.

**What this overcounts:**

- **Dribble handoffs to a player who does everything.** PG hands the ball to a wing who takes three dribbles into a step-back three. Scorekeeper often awards an assist. The \"creation\" was minimal.
- **Swing passes.** Ball moves from guard to wing to corner for a three. Last passer gets the assist, but the first pass may have been the one that broke the defense.
- **Post entry passes.** Guard dumps it to a center who backs down the defender for 4 seconds and scores. Assist recorded. Playmaking value: debatable.

**Epistemic status:** Established fact. The NBA's assist definition is well-documented and its inconsistencies are widely acknowledged. Scorekeeper variance across arenas is a measured phenomenon — home teams historically receive more assists per game on identical plays.

### Assumption 3: FGM Is the Right Denominator Unit

AST% denominates over teammate FGM. This means it asks: \"Of teammate shots that went in, how many did this player assist?\"

**What this ignores:**

- **Teammate FGA.** A player who passes to teammates who miss is not penalized. If you pass to bad shooters who brick everything, your AST% is calculated only over the makes.
- **Free throw generation.** If a player's pass leads to a teammate drawing a shooting foul rather than making a basket, no assist is recorded, and the event is invisible to AST%.
- **Turnovers.** Attempting to create but turning the ball over is invisible.

**The perverse incentive:** AST% is higher when teammate FGM is lower (smaller denominator), all else equal. A playmaker on a team of poor shooters can post a higher AST% than an equally skilled playmaker on a team of great shooters, because the denominator shrinks. This is backwards — the playmaker on the good shooting team may be creating better looks.

### Assumption 4: All Assists Are Equal

AST% counts every assist as 1. An assist on an open corner three (worth approximately 1.2 expected points) counts the same as an assist on a contested mid-range two (worth approximately 0.8 expected points). A no-look cross-court pass that creates a wide-open dunk counts the same as a swing pass to a shooter who makes a contested pull-up.

This is a design choice, not an error. But it means AST% is a volume-and-opportunity stat, not an impact stat.

---

## 4. The Math -- Worked Examples

### Example 1: High-Usage Point Guard (Trae Young archetype)

Suppose in a single game:
- AST = 11, MP = 36, Tm MP = 240, Tm FGM = 42, FGM = 8

```
AST% = 100 * 11 / (((36 / (240 / 5)) * 42) - 8)
     = 100 * 11 / (((36 / 48) * 42) - 8)
     = 100 * 11 / ((0.75 * 42) - 8)
     = 100 * 11 / (31.5 - 8)
     = 100 * 11 / 23.5
     = 46.8%
```

**Interpretation:** Trae assisted on approximately 47% of teammate made baskets while on floor. Sounds plausible for a high-usage PG.

**But what if Trae sat for 12 minutes while the bench lineup went on a 24-8 run?** The team made 42 FGM total, but maybe only 28 happened while Trae was on court (not 31.5). Then teammate FGM with Trae on court = 28 - 8 = 20. Real AST% = 11/20 = 55%. The formula underestimates his AST% because it overcredits his minutes with too many team FGM.

**Or what if the bench was terrible?** Only 6 team FGM in Trae's 12 minutes off. Then 36 FGM happened while Trae was on court. Teammate FGM = 36 - 8 = 28. Real AST% = 11/28 = 39.3%. The formula at 46.8% overcredits him.

**The error range in this single game: 39.3% to 55%.** The formula gives 46.8%. That is a 16-point uncertainty band from one game.

### Example 2: Low-Minutes Role Player

- AST = 3, MP = 18, Tm MP = 240, Tm FGM = 42, FGM = 4

```
AST% = 100 * 3 / (((18 / 48) * 42) - 4)
     = 100 * 3 / ((0.375 * 42) - 4)
     = 100 * 3 / (15.75 - 4)
     = 100 * 3 / 11.75
     = 25.5%
```

For a low-minutes player, the prorating is even more volatile. If this player only plays during blowout garbage time when the opposing defense has disengaged, the 15.75 estimated team FGM during their minutes could easily be 20 (inflated scoring rate). Real AST% might be 3/16 = 18.8%. The formula overestimates by 6.7pp.

### Example 3: The High-Scoring Center

- AST = 2, MP = 34, Tm MP = 240, Tm FGM = 40, FGM = 14

```
AST% = 100 * 2 / (((34 / 48) * 40) - 14)
     = 100 * 2 / ((0.708 * 40) - 14)
     = 100 * 2 / (28.33 - 14)
     = 100 * 2 / 14.33
     = 14.0%
```

High-FGM players have a mechanically deflated denominator (subtracting their own large FGM), which means their AST% is calculated over a smaller pool. This is directionally correct — they leave fewer teammate makes to assist — but it also means AST% can increase if a player scores more himself, even with zero change in passing.

### Edge Case: Player Plays Every Minute

If MP = 48 (or MP = Tm MP / 5):

```
MP / (Tm MP / 5) = 1.0
Denominator = (1.0 * Tm FGM) - FGM = Tm FGM - FGM = actual teammate FGM
```

When a player plays every minute, the prorating is exact. AST% = AST / (Tm FGM - FGM), which is the true percentage of teammate FGM assisted. This is the one scenario where the formula is mathematically precise.

**Implication:** AST% accuracy degrades as minutes played decreases below the full game. The further from full-game minutes, the worse the estimate.

---

## 5. Systematic Failure Modes

### Failure Mode 1: Pace and Scoring Rate Variance (Systematic)

Teams that score in bursts (runs) violate the uniform-rate assumption. Virtually all NBA teams score in bursts. The question is how correlated the player's on-court time is with those bursts.

**Who gets overcredited:** Bench players who play exclusively in high-scoring lineups. Their minutes coincide with above-average scoring rates, so the formula underestimates teammate FGM in their minutes, producing an inflated AST%.

**Who gets undercredited:** Starters on teams with potent bench units. If the bench outscores the starters per-minute, the formula overcredits the starter's minutes with FGM, producing a deflated AST%.

### Failure Mode 2: Team Quality / Teammate Shooting (Systematic)

AST% denominates over teammate FGM, not teammate FGA. A playmaker on a team of poor shooters has a smaller denominator (fewer teammate FGM) than an identical playmaker on a team of good shooters. This inflates AST% for playmakers on bad teams.

**Concrete scenario:** Two point guards each average 8 assists per game in 36 minutes. PG-A's teammates shoot 48% from the field; PG-B's teammates shoot 42%. PG-A has more teammate FGM in the denominator, so his AST% is lower, despite identical assist production. The formula implies PG-B is the better playmaker.

### Failure Mode 3: Scorekeeper Bias (Systematic, Arena-Specific)

NBA assists are recorded by arena scorekeepers who apply subjective judgment. Studies have documented home-team assist inflation of 1-3 assists per game at certain arenas. This is a systematic bias that AST% inherits directly and cannot correct for.

A player who plays 41 home games and 41 away games gets a season AST% that blends two different assist-counting standards. Comparing AST% across players on different teams partially compares scorekeeper generosity.

### Failure Mode 4: Usage-AST% Interaction (Structural)

High-usage players take more shots themselves, which mechanically reduces teammate FGA and FGM. This reduces the denominator of AST%. If a player's usage increases (more FGM), the denominator shrinks, and AST% can increase even without any change in passing behavior.

**Example:** A player goes from 6 FGM to 10 FGM per game while assists stay at 7. Team FGM stays at 40. Minutes stay at 36.

```
Before: AST% = 100 * 7 / ((0.75 * 40) - 6) = 700 / 24 = 29.2%
After:  AST% = 100 * 7 / ((0.75 * 40) - 10) = 700 / 20 = 35.0%
```

AST% increased by 5.8pp with zero change in playmaking. The player just scored more himself.

### Failure Mode 5: The Assist Definition Itself (Fundamental)

This is not a failure of the AST% formula per se, but of the input it depends on. The NBA's assist definition is:

- Subjective (scorekeeper discretion on \"directly contributed\")
- Binary (1 or 0, no partial credit for passes that created advantage but not immediate scores)
- Inconsistently applied (varies by arena, scorekeeper, era)
- Systematically biased toward certain play types (catch-and-shoot gets assists; plays requiring additional dribbles often don't)

Any metric built on assists inherits all of these problems.

### Failure Mode 6: No Quality Adjustment

Ten assists leading to ten open corner threes is drastically more valuable than ten assists leading to ten contested long twos. AST% treats them identically. A player who consistently creates high-value shots (open threes, shots at the rim) shows the same AST% as one who feeds teammates for inefficient attempts, as long as both assists result in makes.

---

## 6. The Steelman

The strongest defense of AST%:

1. **It uses only observed data.** Five box-score inputs, all directly measured. No regression models, no tracking data dependencies, no coefficients estimated from league averages. This makes it universally computable for any game in NBA history back to when assists were recorded.

2. **The minutes prorating, while imperfect, is unbiased in expectation over large samples.** Over an 82-game season, a starter's minutes will include both high-scoring and low-scoring stretches. The uniform-rate assumption's errors should partially cancel out over many games, even if they are large for any single game. This is the central argument for AST% at season scale.

3. **It answers a question nobody else answers simply.** \"What fraction of his teammates' makes did this player assist?\" There is no simpler formula that answers this question. Raw assists don't account for opportunity (a player on a high-FGM team needs more assists to be equally impactful). AST% normalizes for opportunity.

4. **Ordinal rankings are largely stable.** The top of the AST% leaderboard — point guards who genuinely create the most shots for teammates — is generally correct in its ordering. Trae Young, Tyrese Haliburton, and other high-assist PGs rank at the top. Low-creation bigs rank at the bottom. The middle may be noisy, but the extremes are informative.

5. **The full-game edge case is exact.** For players who play every minute (increasingly common for stars in playoff games), AST% is mathematically precise. No estimation needed.

---

## 7. The Verdict

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Accuracy (single game) | D | Minutes prorating introduces 10-20pp error bands in individual games |
| Accuracy (season) | C+ | Errors partially cancel over 82 games, but team-quality and usage biases persist |
| Transparency | A- | Simple formula, all observed inputs; the prorating logic is non-obvious but derivable |
| Robustness | C- | Sensitive to team quality, scorekeeper variance, usage rate, and lineup scoring variance |
| Interpretability | B+ | \"% of teammate FGM you assisted\" is intuitive and easy to explain |

### What AST% Actually Measures

AST% does not measure playmaking ability. It does not measure shot creation. It does not measure passing impact.

AST% measures, approximately, the fraction of teammate made field goals that a player was credited with assisting, prorated by a uniform-rate minutes assumption. It is a volume-normalized counting stat with a noisy denominator.

### Fitness for Purpose

- **\"How much of his team's offense does this player create?\"** Unfit. Misses hockey assists, gravity, screen assists, FT-generating passes. Only captures direct-to-score passes that the scorekeeper chose to credit.
- **\"What percentage of teammate makes did this player assist?\"** Adequate at season scale for high-minutes players. Poor at game scale. Systematically biased by team quality and usage rate.
- **\"Rank players by playmaking ability\":** Adequate for extremes (top 10 vs bottom 10). Poor for distinguishing players in the middle third. Conflates opportunity, usage, and team context with skill.
- **\"Compare playmakers across eras or teams\":** Unfit. Scorekeeper standards, pace, and team construction differ too much.

### Bottom Line

AST% is a reasonable first-pass normalization of raw assists. Its core contribution — adjusting assist counts for playing time and teammate scoring — is a real improvement over raw assist totals. But the minutes-based prorating is a substantial approximation that introduces systematic biases, and the metric inherits every limitation of the NBA's subjective assist definition. It should be understood as \"approximately what fraction of teammate makes were assisted, assuming scoring happened uniformly across the game.\" That is a much weaker claim than \"percentage of teammate FGM assisted while on floor,\" which is what the stat purports to measure. The gap between those two statements is the gap between what AST% claims and what it delivers.

---

## 8. Comparison to Pure TS% Approach

AST% and Pure TS% operate in different domains (playmaking vs. scoring efficiency), so a direct methodological comparison is limited. However, the philosophical contrast is instructive:

| Feature | AST% | Pure TS% |
|---------|------|----------|
| **Core input quality** | Assists (subjective, scorekeeper-dependent) | Play-by-play events (objective, machine-parsed) |
| **Estimation vs. observation** | Estimates teammate FGM via minutes prorating | Observes every scoring event directly |
| **Hidden assumptions** | Uniform scoring rate across minutes | None (deterministic) |
| **Denominator construction** | Estimated teammate FGM (noisy) | Total scoring possessions (exact) |
| **Data requirements** | Box score (universally available) | Play-by-play (requires parsing infrastructure) |

If one were to build a \"Pure AST%\" in the spirit of this project, the path is clear: use play-by-play data (or on/off splits) to count actual teammate FGM while the player was on the court, rather than estimating it via minutes prorating. NBA tracking data already provides this. The formula would become:

```
Pure AST% = AST / (On-Court Teammate FGM)
```

This eliminates Assumption 1 entirely. Assumptions 2 through 4 (assist definition quality, FGM-only denominator, no quality adjustment) would remain. A further refinement could weight assists by the expected points added of each assisted shot, but that moves beyond AST% into a different metric altogether.

The fundamental lesson is the same one that motivated Pure TS%: when you can observe the actual quantity, do not estimate it. AST% estimates teammate FGM on court. The data to observe it directly exists. The estimation is the unnecessary weakness.

---

The complete audit is above. I was unable to write it to `/Users/zfreud/NBAstats/audits/ast_pct_audit.md` because my auditor role is read-only. You can copy this content into that file, or grant Write permission and I will save it directly."}],"stop_reason":"end_turn","stop_sequence":null,"usage":{"input_tokens":1,"cache_creation_input_tokens":5524,"cache_read_input_tokens":29074,"output_tokens":5372,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":5524},"inference_geo":"","iterations":[],"speed":"standard"}},"requestId":"req_011CZJoTn6b3fsCev4pBTZuk","type":"assistant","uuid":"972ee042-6373-4d67-9f45-47cbbbf611d3","timestamp":"2026-03-22T21:10:07.071Z","userType":"external","entrypoint":"cli","cwd":"/Users/zfreud/NBAstats","sessionId":"ff4f4027-bf9d-40bb-854e-39382c99328e","version":"2.1.81","gitBranch":"HEAD","slug":"replicated-seeking-oasis"}
