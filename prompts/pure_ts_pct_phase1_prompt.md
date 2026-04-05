# Pure TS% — Phase 1 Script Prompt

## Objective

Build a Python script that calculates Pure TS% for a single player in a single game using NBA play-by-play data.

## Required Reading

Read these project files first for full context:

- `pure_ts_pct_terms_and_key.md` — All component definitions, symbols, and the formula
- `pure_ts_pct_proof_of_concept.md` — Validated example with known-good output
- `CLAUDE.md` — Project overview and design principles

## Script Specification

**Filename:** `pure_ts_pct_single_game.py`

### Inputs

- Game ID (e.g., `0022501007` for LAL vs HOU March 18, 2026)
- Player name (e.g., `Luka Doncic`)

### Data Source

Fetch play-by-play JSON from:

```
https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json
```

Study the response structure from `playbyplay_0022501007.json` to understand how events, action types, fouls, FTs, and shots are linked.

### Event Classification

Parse every event for the specified player and categorize into Pure TS% components per the definitions in `pure_ts_pct_terms_and_key.md`:

| Component | Type | Key Logic |
|-----------|------|-----------|
| C1a | Clean 2PT FGA | 2PT shot attempt, no foul on the play |
| C1b | Clean 3PT FGA | 3PT shot attempt, no foul on the play |
| C2 | 2PT Shooting Foul | Fouled on 2PT shot, shot does NOT go in, 2 FTAs |
| C3 | 3PT Shooting Foul | Fouled on 3PT shot, shot does NOT go in, 3 FTAs |
| C4 | And-1 2PT | Made 2PT FG + fouled, 1 bonus FTA |
| C5 | And-1 3PT | Made 3PT FG + fouled, 1 bonus FTA |
| C6a | Tech FTs | Technical foul FTs (including defensive 3-sec) |
| C6b | Non-shooting Flagrant FTs | Flagrant foul away from shot attempt, 2 FTAs |
| C6c | Clear Path FTs | Clear path foul, 2 FTAs |
| C6d | Transition Take Foul FTs | Take foul, 1 FTA |
| C6e | Away-from-Play FTs | Away-from-play foul, 1 FTA |
| C6f | Bonus Foul FTs | Non-shooting personal foul in the penalty, 2 FTAs |

### Critical Parsing Requirements

- **Link FTs to parent fouls:** Free throw events must be traced back to the foul that caused them to determine the correct component
- **No double-counting:** And-1 FGAs (C4/C5) must be excluded from C1a/C1b clean FGA counts
- **Shooting foul vs bonus foul:** A shooting foul means the player was in the act of shooting. A bonus foul means they were NOT shooting but the team is in the penalty. These are different components (C2/C3 vs C6f)
- **Flagrant on shot attempt:** If a flagrant foul occurs during a shot attempt, classify under C2/C3/C4/C5 as appropriate, NOT under C6b

### Calculation

Compute Pure TS% using the weighted average formula:

```
Pure TS% = Σ (wᵢ × Effᵢ) for all active components

Where:
  Effᵢ = PTS / (Events × Max Points Per Event)
  wᵢ = Events / Total Scoring Possessions
  Total Scoring Possessions = sum of all component event counts
```

Also compute standard TS% for comparison:

```
Standard TS% = PTS / (2 × (FGA + 0.44 × FTA))
```

### Output

1. **Component breakdown table** showing: Component, Type, Events, PTS, Max PTS, Efficiency
2. **Box score reconciliation** — verify FGA, 3PT FGA, FTA, and PTS match
3. **Pure TS% result** with full calculation walkthrough
4. **Standard TS% result** for comparison
5. **Delta** between the two metrics

### Validation Target

The script output MUST match the proof of concept exactly:

- **Player:** Luka Dončić
- **Game:** 0022501007 (LAL 124, HOU 116, March 18, 2026)
- **Box score:** 40 PTS, 12-25 FG, 7-17 3PT, 9-14 FT
- **Total scoring possessions:** 31
- **Pure TS%:** 51.6%
- **Standard TS%:** 64.2%
- **Component breakdown must match proof of concept doc exactly**

If the numbers don't match, debug until they do. The proof of concept was manually validated play-by-play — it is the source of truth.

## Future Phases (not in scope for this script, but design with them in mind)

- **Phase 2:** Single player, full season — loop this script across all games for a player
- **Phase 3:** All players, full season — loop Phase 2 across every player

Design the core parsing and calculation logic as reusable functions so they can be called by Phase 2/3 wrappers without rewriting.
