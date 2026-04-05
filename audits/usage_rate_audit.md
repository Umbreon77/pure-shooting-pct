# Adversarial Audit: Usage Rate (USG%)

**Date:** 2026-03-22
**Formula under audit:** USG% = 100 x ((FGA + 0.44 x FTA + TOV) x (Tm MP / 5)) / (MP x (Tm FGA + 0.44 x Tm FTA + Tm TOV))
**Origin:** John Hollinger, _Pro Basketball Forecast_ / Basketball-Reference adoption
**Epistemic status of this audit:** First-principles derivation from the formula, cross-referenced against observed play-by-play data in this project. Player statistics cited are from the project's 2024-25 dataset where available; some box-score figures (TOV, MP, team totals) are from Basketball-Reference and are noted as such.

---

## 1. The Claim

Usage Rate claims to measure the percentage of a team's possessions that a player \"uses\" while on the floor, where \"uses\" means the possession terminates through that player via a field goal attempt, a free throw trip, or a turnover.

The implicit promise: USG% tells you how much of the offense runs through a given player. Higher USG% = bigger offensive role.

---

## 2. The Inputs

| Input | Source | Observed or Derived? | Notes |
|-------|--------|---------------------|-------|
| **FGA** | Box score | Observed | All field goal attempts (2PT + 3PT). Does NOT include shooting fouls that produce 0 FGA. |
| **FTA** | Box score | Observed | All free throw attempts. Includes shooting fouls, And-1s, technical FTs, flagrant FTs, bonus fouls, away-from-play fouls, take fouls -- every FT regardless of cause. |
| **TOV** | Box score | Observed | All turnovers charged to the player. |
| **MP** | Box score | Observed | Minutes played by the individual player. |
| **Tm FGA** | Box score | Observed | Team total field goal attempts. |
| **Tm FTA** | Box score | Observed | Team total free throw attempts. |
| **Tm TOV** | Box score | Observed | Team total turnovers. |
| **Tm MP** | Box score | Observed | Team total minutes played (always 48 x 5 = 240 for regulation, more for OT). |
| **0.44** | Coefficient | **Estimated** | A league-wide approximation of the fraction of FTA that represent possession-consuming events. |

All inputs except 0.44 are directly observed. The 0.44 is the same inherited assumption from TS%, and it is doing real work here.

---

## 3. The Assumptions

### Assumption 1: The 0.44 FTA Coefficient -- Recycled From TS%

The 0.44 multiplier appears in both the numerator and denominator. Its purpose: convert free throw attempts into an estimate of how many possessions those free throws consumed.

The logic: not every FTA is a new possession. And-1 free throws (1 FTA) happen on a possession already counted by the FGA. Technical fouls, flagrant fouls, and away-from-play fouls are \"bonus\" possessions that do not consume a team possession in the normal sense. So the 0.44 tries to estimate: of all FTAs, what fraction represent new possessions?

**Where it fails:**

From the project's 2024-25 data, we can count exactly how many of a player's FTA come from each source. Take SGA (2024-25):

- 669 total FTA
- 209 shooting fouls (2PT): these are NOT FGAs but ARE possession-consuming. Each produces 2 FTA = 418 FTA from 2PT shooting fouls.
- 10 shooting fouls (3PT): each produces 3 FTA = 30 FTA from 3PT shooting fouls.
- 60 And-1 (2PT): each produces 1 FTA = 60 FTA. These are NOT new possessions (FGA already counted).
- 1 And-1 (3PT): 1 FTA. Not a new possession.
- 30 tech FTs: not standard possessions.
- 1 flagrant FT event (3 FTA from the data).
- 1 clear path (2 FTA).
- 3 take fouls (3 FTA).
- 2 away-from-play (2 FTA).
- 59 bonus fouls: each produces 2 FTA = 118 FTA. These ARE possession-consuming.

So of SGA's 669 FTA:
- Possession-consuming FTA (shooting fouls + bonus fouls): 418 + 30 + 118 = 566 FTA from ~268 possession-consuming events
- Non-possession-consuming FTA (And-1s, techs, flagrants, clear path, take, away-from-play): 60 + 1 + 30 + 3 + 2 + 3 + 2 = 101 FTA

To get possession-equivalents: each 2PT shooting foul = 1 possession from 2 FTA, each 3PT shooting foul = 1 possession from 3 FTA, each bonus foul = 1 possession from 2 FTA. So actual possessions consumed = 209 + 10 + 59 = 278 possessions from 669 FTA. The true coefficient for SGA is 278/669 = **0.415**.

For a player like Draymond Green (2024-25): 147 FTA, with 41 shooting foul events (2PT, producing 82 FTA), 0 3PT shooting fouls, 16 and-1s (2PT, 16 FTA), 27 bonus fouls (54 FTA). Possession-consuming events = 41 + 0 + 27 = 68. True coefficient = 68/147 = **0.463**.

The 0.44 is wrong for both players, in opposite directions. For high-volume foul-drawers who take lots of shooting fouls (like SGA), it overestimates possessions consumed. For players with more bonus fouls and And-1s relative to shooting fouls, it underestimates.

**The key point:** Usage Rate inherits the same 0.44 error as TS%, but here it distorts a completely different question -- how much of the offense runs through you. A player whose 0.44 should really be 0.35 gets their \"usage\" inflated; a player whose 0.44 should be 0.50 gets their usage deflated.

### Assumption 2: \"Usage\" = Shots + Free Throw Trips + Turnovers. Nothing Else.

This is the foundational and most consequential assumption. USG% defines \"using\" a possession as one of three terminal events:

1. You shot the ball (FGA)
2. You went to the free throw line (estimated via 0.44 x FTA)
3. You turned it over (TOV)

What does NOT count as \"usage\":

- **Assists.** A player who creates a scoring opportunity for a teammate, resulting in a made basket, has \"used\" zero possessions according to USG%.
- **Hockey assists (secondary assists).** Invisible.
- **Passes that lead to free throws.** If Player A drives and kicks to Player B who gets fouled, Player A used nothing.
- **Screens that create open shots.** Invisible.
- **Offensive rebounds that reset the shot clock.** The rebounder \"uses\" nothing unless they also shoot.
- **Drawing defensive attention / gravity.** A player who warps the defense by standing in the corner, creating an open lane for a teammate, has zero usage.
- **Post-ups that lead to double teams and kick-outs.** Zero usage if the post player passes.

This is not merely an omission -- it is a definitional choice that makes the stat's name a lie. \"Usage\" in plain English means \"how much you used something.\" A player who orchestrates the offense, makes 12 assists, draws double teams that create open looks, and finishes with 10 FGA has much lower USG% than a player who catches and shoots 22 times with 0 assists.

**USG% does not measure how much a player uses possessions. It measures how often a player terminates possessions through individual scoring actions or errors.**

A more honest name would be \"Possession Termination Rate\" or \"Scoring Attempt Share.\"

### Assumption 3: All Possession Terminations Are Equal

In the USG% formula, 1 FGA = 0.44 FTA = 1 TOV. Each counts equally as one \"usage event.\" But these are not equivalent:

- A contested mid-range pullup (1 FGA) is a skilled, intentional offensive action.
- A bonus-situation foul where the player was just holding the ball (0.44 x 2 = 0.88 usage events) may not reflect any offensive initiation at all.
- A live-ball turnover (1 TOV) ended the possession, yes, but treating errors identically to scoring attempts conflates offensive role with offensive mistakes.

A player who turns the ball over 5 times has their USG% inflated by 5 usage events. This creates the perverse result that clumsy ball-handlers who turn it over a lot get HIGHER usage rates, appearing to have bigger offensive roles partly because they make more mistakes.

### Assumption 4: The Prorating Assumption (Tm MP / 5) / MP

The formula normalizes to a per-minute, per-team basis. The (Tm MP / 5) term estimates total minutes available per roster spot (usually 48, or more in OT). Dividing by MP adjusts for playing time.

The denominator (MP x (Tm FGA + 0.44 x Tm FTA + Tm TOV)) represents the total team possessions during the minutes this player was on the floor -- but only approximately. It uses team season totals, not the actual possessions that occurred during this player's minutes. A player who plays exclusively in garbage time faces a denominator based on the team's overall pace, not garbage-time pace.

### Assumption 5: Pace Neutrality

USG% claims to be pace-neutral because it measures a share. But the denominator uses team-level aggregates, not on-court-specific data. A player on a fast-paced team who personally plays at a slower pace (or vice versa) gets a distorted share. This is a minor issue for most players but can matter for bench players whose on-court pace differs substantially from the team average.

### Assumption 6: Technical/Flagrant/Bonus FTs Are \"Usage\"

Technical foul free throws are awarded to a designated shooter, not to a player who created an offensive opportunity. The shooter was chosen to take a freebie. Yet 0.44 x 1 = 0.44 usage events are charged to them. For a player who shoots many tech FTs (like a team's designated FT shooter), this inflates their usage for an action they did not create.

Similarly, bonus/penalty fouls often occur when a player is simply holding the ball or running a play -- they did not attempt to score, but the team foul situation triggered free throws. These inflate USG% for players who happen to get fouled in the bonus.

---

## 4. The Math -- Worked Examples

### Example 1: SGA 2024-25

From Basketball-Reference (2024-25 season, OKC):
- SGA: FGA = 1656, FTA = 669, TOV ~ 230, MP ~ 2536
- OKC team: Tm FGA ~ 7020, Tm FTA ~ 2070, Tm TOV ~ 1050, Tm MP = 240 x 82 = 19680

```
USG% = 100 x ((1656 + 0.44 x 669 + 230) x (19680 / 5)) / (2536 x (7020 + 0.44 x 2070 + 1050))
     = 100 x ((1656 + 294.36 + 230) x 3936) / (2536 x (7020 + 910.8 + 1050))
     = 100 x (2180.36 x 3936) / (2536 x 8980.8)
     = 100 x 8,581,897 / 22,775,309
     ~ 37.7%
```

This is extremely high -- among league leaders. USG% says SGA terminates ~38% of OKC's possessions while he is on the floor. That is plausible for a player who takes 21.8 FGA/game. But note: SGA also averaged ~6 assists per game. Those ~6 possessions per game that he orchestrated and converted into teammate scores count as zero usage. His actual offensive involvement is substantially higher than 38%.

### Example 2: Draymond Green 2024-25

From the project data and Basketball-Reference:
- Green: FGA = 509, FTA = 147, TOV ~ 174, MP ~ 1985
- GSW team: Tm FGA ~ 7200, Tm FTA ~ 1680, Tm TOV ~ 1150, Tm MP = 19680

```
USG% = 100 x ((509 + 0.44 x 147 + 174) x 3936) / (1985 x (7200 + 0.44 x 1680 + 1150))
     = 100 x ((509 + 64.68 + 174) x 3936) / (1985 x (7200 + 739.2 + 1150))
     = 100 x (747.68 x 3936) / (1985 x 9089.2)
     = 100 x 2,942,868 / 18,042,062
     ~ 16.3%
```

USG% says Draymond uses about 16% of GSW's possessions. This is low -- around replacement-level usage. But Draymond averaged ~6 assists per game, was the primary facilitator in many lineups, set screens that generated open shots, and was the decision-maker in GSW's motion offense. His actual offensive involvement is far higher than 16%.

**USG% sees Draymond as a marginal offensive player. Anyone who has watched basketball knows this is wrong.** The stat measures scoring attempt volume, not offensive involvement.

### Example 3: The Jokic Problem

From the project data (2024-25):
- Jokic: FGA = 1325, FTA = 438, TOV ~ 264, MP ~ 2534
- DEN team: Tm FGA ~ 6900, Tm FTA ~ 1800, Tm TOV ~ 1100, Tm MP = 19680

```
USG% = 100 x ((1325 + 0.44 x 438 + 264) x 3936) / (2534 x (6900 + 0.44 x 1800 + 1100))
     = 100 x ((1325 + 192.72 + 264) x 3936) / (2534 x (6900 + 792 + 1100))
     = 100 x (1781.72 x 3936) / (2534 x 8792)
     = 100 x 7,013,010 / 22,279,128
     ~ 31.5%
```

Jokic's USG% is around 31-32%. He also averaged approximately 9-10 assists per game in 2024-25. Those assists represent possessions where Jokic was the primary creator, made the key decision, and delivered the pass that led to a score. None of that registers.

If we naively added assists as \"usage events,\" Jokic's involvement would jump dramatically. His ~700 assists across the season would add 700 events to his numerator, pushing his \"involvement rate\" well above 40%. The gap between his USG% and his actual offensive involvement is enormous.

### Example 4: The Turnover Inflation Problem

Consider two hypothetical players in identical situations:
- Player A: 15 FGA, 4 FTA, 2 TOV per game
- Player B: 15 FGA, 4 FTA, 6 TOV per game

Player B has 4 more turnovers. USG% rewards this with higher usage:
- Player A usage events: 15 + 0.44(4) + 2 = 18.76
- Player B usage events: 15 + 0.44(4) + 6 = 22.76

Player B appears to have a 21% larger offensive role, when in reality they just fumble the ball more. This is not hypothetical -- Russell Westbrook in his peak years had some of the highest USG% in NBA history, and his turnover rate was a meaningful contributor. In 2024-25, Westbrook had 831 FGA, 233 FTA, and an estimated 200+ turnovers in 75 games. His turnovers inflated his USG% by several percentage points.

---

## 5. Systematic Failure Modes

### Failure Mode 1: Playmakers Are Systematically Undercounted (Directional, Large)

Any player whose primary offensive contribution is creating shots for others -- through passing, screening, or drawing defensive attention -- has their offensive role systematically undercounted. This is not a small effect.

Players most harmed:
- **Point guards who pass first:** Chris Paul's USG% was historically around 22-24% despite being the primary offensive engine of multiple top-10 offenses.
- **Big-man facilitators:** Jokic's USG% understates his offensive involvement by at least 10-15 percentage points.
- **Draymond Green types:** USG% codes Draymond as a marginal offensive player. This is laughably wrong for the primary facilitator of one of the greatest offenses in NBA history.

### Failure Mode 2: High-Volume Inefficient Scorers Are Overcounted (Directional, Moderate)

A player who takes bad shots and turns the ball over a lot gets a high USG% -- the stat treats this as a large offensive role rather than poor decision-making. Turnovers are weighted identically to scoring attempts.

### Failure Mode 3: The 0.44 Distortion (Directional, Small to Moderate)

The 0.44 coefficient introduces systematic error that varies by player archetype:
- Players with lots of shooting fouls relative to their total FTA (like SGA) get overcounted, because the 0.44 overestimates their possession consumption from FTs.
- Players with lots of And-1 FTA and tech FTA relative to their total get undercounted.

This error is typically 1-3 percentage points of USG%, smaller than the assist blind spot but still present and systematic.

### Failure Mode 4: Designated FT Shooters Get Phantom Usage

Players chosen to shoot technical foul or transition take foul free throws get usage credit for an event they did not create. For most players this is negligible (a few FTA per season), but it is conceptually wrong.

### Failure Mode 5: Bench Player Pace Distortion (Random, Small)

The formula uses team-level pace aggregates rather than on-court pace. Bench players who play in lineups with substantially different pace than the starters get slightly distorted USG%.

### Failure Mode 6: Cross-Era Comparisons Are Unreliable

USG% is a share metric, so it should theoretically be pace-neutral. But playing style changes across eras (more 3PA, different foul-drawing strategies, different turnover rates) mean the composition of what \"usage\" measures has changed. A 30% USG in 2004 (dominated by mid-range FGA) means something different from a 30% USG in 2025 (dominated by 3PA and foul-drawing).

---

## 6. The Steelman

The strongest defense of USG%:

1. **It answers a narrow but legitimate question.** \"What share of his team's possession-ending events come from this player?\" That question has real value. It tells you who the team's go-to scorers are, who takes the most shots, who handles the ball enough to turn it over. It is a volume-of-scoring metric, and that is useful.

2. **It is pace-neutral by design.** Unlike raw FGA per game, USG% adjusts for pace. A player on a fast team taking 18 FGA/game is not the same as a player on a slow team taking 18 FGA/game. USG% captures this.

3. **It correlates well with what coaches mean by \"scoring load.\"** When a coach says \"we need Tatum to carry more of the load,\" they mean scoring load -- take more shots, get to the line more. USG% measures exactly that.

4. **Simple box-score inputs.** No play-by-play parsing required. Can be computed for any game in NBA history with standard box-score data.

5. **The 0.44 error is small in the context of usage.** While 0.44 is wrong for many individual players (as this project has demonstrated for TS%), in USG% the FTA term is usually a minority of the total usage events. For a player with 20 FGA, 6 FTA, and 3 TOV per game, the FTA term contributes only 0.44 x 6 = 2.64 out of 25.64 total events (10.3%). Even if 0.44 is off by 20% for that player, the USG% error is about 0.5 percentage points. Tolerable for most purposes.

6. **Including turnovers is defensible.** A turnover genuinely ends the possession through that player. If you want to know \"what share of possessions end through Player X,\" turnovers belong in the count. The alternative -- excluding turnovers -- would also be misleading, just in the opposite direction.

---

## 7. The Verdict

### The Name Is a Lie

\"Usage Rate\" implies offensive involvement. It does not measure offensive involvement. It measures **scoring attempt share plus turnover share**. These are related but substantially different concepts.

The stat's name does more damage than its math. If it were called \"Scoring Attempt Rate\" or \"Possession Termination Share,\" nobody would be confused about what it measures, and nobody would use it to argue that Draymond Green has a small offensive role.

### The Math Is Adequate for Its Actual Purpose

If you understand USG% as \"what share of possessions does this player terminate via shot, foul, or turnover,\" the formula is a reasonable approximation. The 0.44 introduces small errors. The prorating is slightly imprecise. But these are minor compared to the definitional problem.

### The Definitional Problem Is Severe

The exclusion of assists, screens, hockey assists, and offensive gravity from \"usage\" is not a minor omission. For facilitators like Jokic, CP3, or Draymond, it understates their offensive role by 10-20 percentage points. For high-volume scorers with few assists, it overstates their share of the offense relative to their actual contribution to possessions.

This creates a systematic bias in how USG% is used in analysis:
- High-USG% players are described as \"carrying the offensive load\"
- Low-USG% players are described as having \"small offensive roles\"

Neither of these is reliably true. A player with 35% USG% and 2 assists per game is probably less central to the offense than a player with 25% USG% and 10 assists per game, but USG% says the opposite.

### Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Mathematical accuracy | B- | The 0.44 introduces small errors; prorating is approximate but reasonable |
| Name accuracy | F | \"Usage\" implies total offensive involvement; stat only measures possession termination |
| Robustness across archetypes | D | Systematically undercounts facilitators, overcounts pure scorers |
| Transparency | B+ | Simple box-score inputs, formula is public, easy to verify |
| Fitness for stated purpose | D+ | If purpose is \"offensive involvement,\" it fails. If purpose is \"scoring load,\" it is adequate. |

### Bottom Line

Usage Rate is a scoring volume metric wearing the disguise of an offensive involvement metric. The formula itself is a tolerable approximation of what it actually calculates -- the share of possessions a player terminates via scoring attempt or error. The real damage is in the name and in how the stat is deployed in analysis. When someone says \"Player X had a 35% usage rate,\" the listener hears \"35% of the offense ran through Player X.\" That is not what the number means. For playmakers, facilitators, and screen-setters, USG% is not just imprecise -- it is actively misleading about their offensive role.

The 0.44 coefficient, while mathematically sloppy (as this project has demonstrated across thousands of player-seasons), is a secondary concern here. Even with a perfect FTA-to-possession conversion, USG% would still systematically undercount anyone whose primary offensive contribution is creation rather than termination.

---

## 8. Comparison to Pure TS% Approach

| Issue | USG% | Pure TS% Response |
|-------|------|-------------------|
| **The 0.44 problem** | Uses 0.44 to estimate possession-consuming FT trips | Eliminates 0.44 entirely by counting actual events from play-by-play |
| **What counts as a \"possession\"** | FGA + 0.44 x FTA + TOV (approximate, excludes non-terminal involvement) | Total scoring possessions: every event type counted separately (12 components) |
| **Tech FTs / designated FTs** | Counted as 0.44 usage events, no distinction from shooting fouls | Counted separately as their own component (C6a), with their own weight and efficiency |
| **And-1 distortion** | And-1 FTA inflate the FTA term even though the possession is already counted via FGA | And-1s are a separate component (C4/C5); no double-counting possible |
| **Bonus fouls** | Buried inside the 0.44 x FTA term, indistinguishable from shooting fouls | Separate component (C6f) with its own weight |

If this project were to build a \"Pure Usage Rate\" analog, the approach would be:

1. **Replace 0.44 x FTA with actual possession-consuming events:** Count shooting fouls (C2 + C3), And-1s (already in FGA, do not double-count), bonus fouls (C6f), and other foul types separately.
2. **Include assists as a form of possession involvement:** An assist is a possession where the player was the primary creator. Whether this should count equally to a scoring attempt is debatable, but excluding it entirely is clearly wrong.
3. **Separate turnovers from scoring attempts:** Report \"Scoring Attempt Rate\" and \"Turnover Rate\" separately rather than conflating them.

The deeper question -- whether a single number can capture \"offensive involvement\" -- is probably unanswerable. Gravity, screen-setting, and decoy actions are real but nearly impossible to quantify from event data alone. USG% does not attempt this, which is defensible. But it should be honest about what it leaves out, starting with its name.

---

## Appendix: Player Data Reference

All player statistics referenced from the project's `data/pure_ts_pct_league_2024-25.csv` unless otherwise noted. Team totals and TOV figures estimated from Basketball-Reference where not available in project data. Minutes played and team aggregates are approximate for worked examples; the mathematical conclusions do not depend on exact values.

---
