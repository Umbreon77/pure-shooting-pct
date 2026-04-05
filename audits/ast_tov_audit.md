# Adversarial Audit: Assist-to-Turnover Ratio (AST/TOV)

**Date:** 2026-03-22
**Formula under audit:** AST/TOV = Assists / Turnovers

---

## 1. The Claim

AST/TOV claims to measure a player's ball-handling reliability and playmaking quality -- specifically, how well a player takes care of the ball while creating scoring opportunities for teammates. A higher ratio is taken to mean \"better playmaker\" or \"more trustworthy with the ball.\"

---

## 2. The Inputs

| Input | Source | Type | What It Includes | What It Excludes |
|-------|--------|------|------------------|------------------|
| **Assists (AST)** | Box score (observed) | Counted event | A pass that directly leads to a made field goal, credited at the scorer's discretion. The passer must be judged to have contributed meaningfully to the basket. | Passes that lead to fouls drawn (no FG = no assist). Passes that create wide-open looks that are missed. \"Hockey assists\" (secondary passes in a chain). Gravity-based creation where the passer's threat warps the defense but someone else delivers the final pass. Screen assists. |
| **Turnovers (TOV)** | Box score (observed) | Counted event | Any loss of possession charged to the player: bad passes, offensive fouls, travels, backcourt violations, stepping out of bounds, shot clock violations (sometimes split among players), stolen-ball turnovers. | Team turnovers not charged to individuals. \"Near-turnovers\" (loose balls recovered by own team). Turnovers that would have occurred if the passer hadn't pulled back the pass (risk avoided = invisible). |

Both inputs are directly observed but subjectively counted. Assists in particular involve scorer discretion -- the same play might be credited as an assist in one arena and not in another. The NBA's official scoring guidelines leave meaningful room for interpretation on what constitutes a pass that \"directly led to\" a basket.

---

## 3. The Assumptions

### Assumption 1: All Assists Are Equal

The formula treats every assist identically. A lob to a rolling center for an uncontested dunk counts the same as a cross-court skip pass that threads two defenders and creates a contested three. A \"drive-and-kick to a wide-open shooter\" assist counts the same as a \"full-court outlet to a streaking wing\" assist.

**Reality:** Assists vary enormously in difficulty, value, and the degree to which the passer -- rather than the shooter -- created the opportunity. A player who racks up 8 assists per game by executing simple pick-and-roll passes to a dominant big man is performing a fundamentally different task than a player who gets 8 assists per game by creating out of isolation.

### Assumption 2: All Turnovers Are Equal

A live-ball turnover (steal leading to a fast break, typically worth ~1.1 points for the opponent) is treated identically to a dead-ball turnover (stepping out of bounds, which merely ends the possession). The expected-point cost of these events differs by roughly 0.5-0.6 points, yet AST/TOV treats them as interchangeable.

### Assumption 3: The Relationship Between Creation and Turnovers Is Ratio-Based

The formula assumes that dividing assists by turnovers produces a meaningful measure of quality. This is a ratio, not a rate. It contains no information about volume or opportunity. A player who touches the ball 3 times per game and a player who handles it 90 times per game can produce the same AST/TOV. The formula implicitly assumes that what matters is the proportion between good outcomes (assists) and bad outcomes (turnovers), regardless of how many total ball-handling events occurred.

### Assumption 4: Non-Assist Creation Does Not Exist

A player who consistently draws two defenders and passes to the open man -- but the open man swings it to an even more open man who scores -- gets zero credit. The first passer created the advantage; the second passer delivered the final pass. AST/TOV only sees the second pass. Similarly, a player who drives and draws a foul on the shooter (or themselves) creates a scoring opportunity that produces no assist.

### Assumption 5: Non-Turnover Ball Misuse Does Not Exist

The only \"bad\" ball-handling outcome counted is a turnover. A player who dribbles for 18 seconds and then jacks a contested mid-range jumper has technically committed zero turnovers. A player who makes an ill-advised pass that happens to result in a missed shot rather than a steal has committed zero turnovers. Poor possessions that are not technically turnovers are invisible to this metric.

### Assumption 6: Higher Ratio = Better

This is the deepest and most pernicious assumption. It presumes that increasing AST/TOV always indicates improvement. But a player can increase their ratio two ways: (a) create more assists, or (b) commit fewer turnovers. Method (b) can be achieved by simply passing less aggressively -- deferring to safe passes, avoiding the skip pass that might get tipped, declining to thread the needle. A risk-averse player can achieve a high AST/TOV by never attempting the passes that generate the most valuable scoring opportunities.

### Assumption 7: Division by Zero is Somebody Else's Problem

If a player records zero turnovers in a game (or stretch of games), the formula is undefined. This is not a rare edge case -- it happens regularly in individual games, especially for low-usage players.

---

## 4. The Math -- Worked Examples

### Example 1: The Conservative Point Guard vs. The Aggressive Creator

**Player A -- The Conservative PG**
- 4 AST, 1 TOV
- AST/TOV = 4.00

**Player B -- The Aggressive Creator**
- 10 AST, 3 TOV
- AST/TOV = 3.33

AST/TOV says Player A is the better playmaker. But examine what actually happened:

Player A contributed 4 made baskets for teammates (roughly 8-10 points created) and lost 1 possession. Net: ~8-10 points created minus ~1 point lost = ~7-9 net points.

Player B contributed 10 made baskets for teammates (roughly 20-24 points created) and lost 3 possessions. Net: ~20-24 points created minus ~3 points lost = ~17-21 net points.

Player B created roughly 2.5x the net value, but AST/TOV ranks Player A higher. The ratio punishes volume creators who accept marginal increases in turnover risk in exchange for massive increases in creation output.

### Example 2: The Ratio King vs. The Engine

**Player C -- Off-Ball Wing**
- Handles the ball rarely, primarily catches and shoots
- 3 AST, 0.5 TOV per game
- AST/TOV = 6.00

**Player D -- Primary Ball-Handler**
- Initiates the offense on 60% of possessions, runs pick-and-roll, drives and kicks
- 8 AST, 3.5 TOV per game
- AST/TOV = 2.29

AST/TOV says Player C is a vastly better playmaker. Player C barely handles the ball. His 3 assists come from simple drive-and-kick passes and transition outlets. Player D runs the entire offense. His 3.5 turnovers are the cost of 8 assists and dozens of additional plays that resulted in good shots but no official assist credit.

### Example 3: The Division-by-Zero Game

**Player E in a single game:**
- 5 AST, 0 TOV
- AST/TOV = undefined (division by zero)

This player had a genuinely excellent game, but the metric literally cannot produce a value. Common workarounds -- adding 0.5 to the denominator, reporting \"infinity,\" or simply omitting the data point -- are all ad hoc patches to a formula that was not designed for this case.

### Example 4: Equal Ratios, Wildly Different Players

**Player F:** 2 AST, 1 TOV --> AST/TOV = 2.00
**Player G:** 12 AST, 6 TOV --> AST/TOV = 2.00

These players have identical AST/TOV ratios. Player F is a center who barely touches the ball in the half-court. Player G is an All-NBA point guard running a top-5 offense. The metric cannot distinguish them.

---

## 5. Systematic Failure Modes

### Failure Mode 1: Volume Blindness (Systematic, Pervasive)

AST/TOV is a ratio with no volume floor. It structurally favors low-usage players over high-usage players. A player who handles the ball 5 times per game can trivially achieve a better AST/TOV than a player who handles it 80 times per game, because the low-volume player faces almost no opportunities to commit turnovers.

**Who gets overcredited:** Low-usage wings, catch-and-shoot players, off-ball movers who occasionally make a simple pass that leads to a basket.

**Who gets undercredited:** Primary ball-handlers, high-usage creators, players who run the offense. The players who generate the most total value from their passing almost always look worse in AST/TOV than players who generate far less.

### Failure Mode 2: Risk Aversion Bias (Systematic)

AST/TOV rewards avoiding turnovers at least as much as it rewards creating assists. A player can dramatically improve their AST/TOV by eliminating high-risk, high-reward passes from their game. The cross-court skip pass that creates an open three 60% of the time but gets intercepted 15% of the time is a positive expected-value play. AST/TOV penalizes the player for the 15% interceptions and only partially credits the 60% successes (only if the open three goes in AND the assist is credited).

The rational response to being evaluated by AST/TOV is to play more conservatively -- which is the opposite of what produces good offense.

### Failure Mode 3: Assist Credit Is Subjective and Contextual

Arena scorers have measurably different assist-crediting tendencies. Home teams tend to receive slightly more assists. A player's AST/TOV can be influenced by factors completely unrelated to their actual playmaking quality.

### Failure Mode 4: Turnover Types Are Not Differentiated

Turnovers range from catastrophic (live-ball turnover in transition leading to an easy layup, ~1.1 expected points for the opponent) to benign (offensive three-second violation, dead ball, ~0.0 transition points). AST/TOV treats these identically.

### Failure Mode 5: Offensive System Effects

A player in a motion offense with constant ball movement will naturally accumulate more assists on simple passes than a player in an isolation-heavy system. Conversely, a player asked to hold the ball and create in late-clock situations will accumulate more turnovers relative to their assists. AST/TOV is measuring system fit as much as individual skill.

### Failure Mode 6: The Denominator Problem -- Turnovers Are Not Only a Playmaking Outcome

Turnovers include offensive fouls (charges), travels, backcourt violations, and other events that have nothing to do with passing or playmaking. A player who takes 3 charges called against them while driving has 3 turnovers on their record that have nothing to do with their ability to distribute the ball.

---

## 6. The Steelman

The strongest defense of AST/TOV:

1. **Simplicity and availability.** Two box-score inputs, universally available for every player in every game across every era. Anyone can compute it with a basic box score.

2. **It captures a real signal at the extremes.** Players who are genuinely elite playmakers tend to post high AST/TOV ratios. Players who are genuinely reckless tend to post low ones. At the tails of the distribution, the signal is real: a player with 11 AST and 2 TOV per game is almost certainly a better playmaker than a player with 3 AST and 5 TOV per game.

3. **Quick filter for ball security.** For a narrow use case -- \"among players with similar usage and assist volume, who takes better care of the ball?\" -- AST/TOV provides a reasonable first-pass answer. If two starting point guards both average 8 assists, comparing their turnovers tells you something real about their decision-making efficiency.

4. **Contextual use is reasonable.** When combined with assist volume, usage rate, and team offensive rating, AST/TOV adds a genuine piece of information. It is not meant to be the whole picture.

5. **Intuitive interpretation.** \"For every turnover, this player creates X scoring opportunities for teammates\" is immediately understandable to any basketball viewer.

**Does the steelman hold?**

Partially. Points 1, 4, and 5 are solid. Point 2 is true but weak: most stats work at the extremes; the question is whether a stat works in the messy middle where the interesting comparisons live. Point 3 is the strongest defense: when you control for volume and role, AST/TOV adds real information. But the stat itself does not control for volume and role -- the analyst has to do that work externally, which means the stat is incomplete without context it does not provide.

---

## 7. The Verdict

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Accuracy | D | Volume blindness and risk-aversion bias produce systematically wrong rankings |
| Transparency | A | Two directly observed inputs, no hidden coefficients |
| Robustness | D- | Division by zero, no volume floor, system-dependent, scorer-discretion variance |
| Interpretability | B+ | Intuitive meaning, but the intuition misleads (higher is not always better) |

### What AST/TOV Actually Measures

AST/TOV does not measure playmaking quality. It measures the ratio of officially credited scoring passes to officially charged possession losses. These are related to playmaking the way FG% is related to scoring efficiency -- correlated, but with systematic distortions that make cross-player comparisons unreliable.

### Fitness for Purpose

- **\"Measure playmaking quality\":** Unfit. Structurally rewards risk aversion and penalizes volume creation.
- **\"Compare playmaking among players with similar roles and usage\":** Adequate. When volume and role are held roughly constant, AST/TOV provides a real signal about decision-making efficiency.
- **\"Identify reckless ball-handlers\":** Adequate as a floor check. Very low AST/TOV (below ~1.5 for guards) reliably indicates a turnover problem. But the converse is not true: very high AST/TOV does not reliably indicate elite playmaking.
- **\"Evaluate playmaking across positions/roles/eras\":** Unfit. A center's AST/TOV and a point guard's AST/TOV are not comparable.

### The Core Problem

AST/TOV confuses efficiency with production. It answers \"what is the ratio of your good outcomes to your bad outcomes?\" when the question that matters is \"how much total value did your passing create?\" A player who generates 20 points of value for teammates while losing 3 possessions is more valuable than a player who generates 8 points of value while losing 1. The ratio says otherwise.

This is not fixable by adjusting the formula. The conceptual frame -- dividing a count of successes by a count of failures, with no volume weighting -- is the problem. The fix requires moving to rate-based or net-value-based frameworks: assists per 100 possessions, potential assists (tracking data), points created per turnover, or expected-value models that weight assists by the difficulty and value of the pass.

### Bottom Line

AST/TOV is the FG% of playmaking metrics: simple, available, intuitive, and wrong in the ways that matter most. It rewards the exact behavior (risk aversion, low volume, safe passes) that produces worse offenses, and it penalizes the exact behavior (aggressive creation, high volume, difficult passes) that produces better ones. Use it as a quick sanity check for ball security, never as a measure of playmaking quality.

---

## 8. Comparison to Pure TS% Approach

AST/TOV is a passing/playmaking metric, not a scoring efficiency metric, so a direct formula comparison to Pure TS% is not applicable. However, the audit reveals structural parallels:

| Structural Problem | AST/TOV | Standard TS% | Pure TS% Response |
|-------------------|---------|--------------|-------------------|
| Treats unlike events as identical | All assists equal, all turnovers equal | All FTs approximated at 0.44 | Each scoring event typed and measured separately |
| Missing inputs | No volume, no difficulty, no pass type | No foul-type differentiation | All foul types counted from play-by-play |
| Ratio vs. rate confusion | Ratio with no volume context | Rate-based (better) | Rate-based with exact denominators |
| Denominator problem | TOV includes non-playmaking events | FTA includes non-shooting FTs | Only scoring possessions, correctly typed |

The design philosophy behind Pure TS% -- disaggregate events by type, count exactly, avoid approximation -- represents the direction any playmaking metric would need to go to fix AST/TOV's problems. A \"Pure Playmaking\" metric would need to:

1. Classify passes by type (drive-and-kick, PnR, transition, post entry, etc.)
2. Weight assists by the value and difficulty of the created shot
3. Credit non-assist creation (passes that lead to fouls drawn, secondary assists, gravity effects)
4. Differentiate turnovers by type and cost (live-ball vs. dead-ball)
5. Normalize by opportunity (touches, time of possession, potential assists)

This requires tracking data, not box scores -- exactly the shift that Pure TS% makes from standard TS%.

---

**Epistemic notes:** The approximate point values for live-ball vs. dead-ball turnovers (~1.1 vs ~0.5 expected points) are consensus estimates from publicly available NBA analytics research, not first-principles derivations from this project's data. The scorer-discretion variance claim for assists is an established finding in sports analytics literature. All worked examples use hypothetical but archetype-representative numbers; no specific player data was queried for this audit.

---
