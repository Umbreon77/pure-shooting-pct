# Methodology

## The Formula

```
PS% = PTS / (2×FGA + 3PA + FTA)
```

Pure Shooting % (PS%) measures shooting efficiency using four standard box score numbers:

- Points (PTS)
- Field goal attempts (FGA)
- Three-point attempts (3PA)
- Free throw attempts (FTA)

The numerator is total points scored. The denominator is the maximum points that could have been scored across all of a player's attempts. The result is a true 0-100% scale with no approximations or arbitrary coefficients. This captures a player's precise shooting efficiency over a given game, season, or career.

This is not a model or an approximation. If the question is "what percentage of available points did a player score," there is only one calculation that answers it: total points divided by total possible points. The data to compute this has always been on every standard box score. No play-by-play parsing, no estimated coefficients, no arbitrary weights required.

For reference, TS% uses: `PTS / (2 × (FGA + 0.44 × FTA))`. PS% is simpler, more precise, and a true percentage.

## Where The Formula Comes From

There are only three ways to score in basketball. Each has a known maximum value per attempt:

| Attempt Type | Max Points | Existing Stat |
|---|---|---|
| 2-point field goal | 2 | 2P% = 2PM / 2PA |
| 3-point field goal | 3 | 3P% = 3PM / 3PA |
| Free throw | 1 | FT% = FTM / FTA |

To combine all three into one overall shooting percentage, sum all points scored for the numerator and sum all possible points that could have been scored for the denominator. Divide the numerator by the denominator for PS%.

```
Numerator (points scored)          = 2×2PM + 3×3PM + FTM  (which is just PTS)
Denominator (max possible points)  = 2×2PA + 3×3PA + FTA

Unsimplified formula: PS% = (2×2PM + 3×3PM + FTM) / (2×2PA + 3×3PA + FTA)
```

Standard box scores show FGA (all field goal attempts) rather than 2PA separately. Since 2PA = FGA − 3PA, we replace the 2PA term in the denominator with FGA − 3PA. Here is the denominator simplified:

```
2×2PA + 3×3PA + FTA
= 2×(FGA − 3PA) + 3×3PA + FTA
= 2×FGA − 2×3PA + 3×3PA + FTA
= 2×FGA + 3PA + FTA
```

2×FGA + 3PA + FTA is the denominator simplified. So again, the formula is points scored divided by max possible points, expressed using four numbers on every box score:

```
PS% = PTS / (2×FGA + 3PA + FTA)
```

## What About Free Throw Types?

A natural follow-up: does the formula need to account for whether a player shoots 1, 2, or 3 free throws on a given trip to the line?

No. Every free throw attempt has a max value of 1 point regardless of how many are awarded on the play. The box score records all FTAs. The formula counts them all — each one adds 1 to the denominator.

The formula was originally derived by classifying every scoring event into 12 play-by-play components (shooting fouls, And-1s, technicals, flagrants, bonus fouls, etc.) and proving that the max possible points across all 12 components sum to exactly `2×FGA + 3PA + FTA`. That derivation confirmed the formula is correct. The component-level breakdown also powers the diagnostic tabs on this site — foul profiles, FT efficiency by type, And-1 rates — but it doesn't change the headline number.

## How To Read The Stats

| Stat | What It Means |
|---|---|
| **PS%** | Points scored as a percentage of maximum possible points. The core metric. |
| **TS%** | Traditional True Shooting %. Shown for comparison. |
| **Delta** | PS% minus TS%. Negative means TS% overrated the player. The gap is driven primarily by the "2" denominator in TS% which inflates 3-point shooters. |
| **Scoring Possessions (SP)** | Total scoring events: FGA + non-shooting foul events. Broader than FGA because it includes events that produce FTAs but no FGA (shooting fouls, bonus fouls, etc.). |
| **And-1 Rate** | % of made field goals that resulted in an And-1. |
| **Foul Draw Rate** | % of scoring possessions that involved any foul. |
| **Hidden Possessions** | Scoring events that produced zero FGAs in the box score (shooting fouls, bonus fouls, etc.). Shows how much of a player's scoring activity is invisible to FGA-based stats. |

Use the **Columns** button on any tab to show or hide columns. Drag column headers to reorder them. Use the **Download** button to export the currently visible, filtered data as CSV or Excel.

## How To Read The Tabs

| Tab | What It Shows |
|---|---|
| **Rankings** | Season-level PS% for every player, with full shooting splits (FG, 3P, 2P, FT), sortable and filterable. |
| **Foul Profile** | How each player's scoring events break down by type. Shows the composition of a player's scoring, not just the efficiency. |
| **FT by Type** | Free throw make rate broken out by the type of foul that produced the free throws. This data is not available from any other public source. |
| **All Game Logs** | Individual game performances with per-game PS%, TS%, and Delta. Use the delta slider to filter to high-distortion games, and the quarter filter to view quarter-level efficiency breakdowns. |

## Data Source & Methodology

**Data source:** PS% is calculated across all 47 seasons (1979-80 through 2025-26) using box score data (PTS, FGA, 3PA, FTA). Play-by-play component data (foul profiles, And-1 rates, hidden possessions) is available for 30 seasons: 6 via NBA CDN (2020-21 through 2025-26) and 24 via Basketball Reference (1996-97 through 2019-20). The remaining 17 seasons (1979-80 through 1995-96) have headline PS% but no PBP component breakdowns.

Season-level stats are aggregated from raw totals across all games, not averaged from per-game percentages. A 40-point game and a 2-point game contribute proportionally to the season number.
