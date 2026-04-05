# Prompt: Pull NBA Tracking Passing Data (Sample)

## Goal

Pull a sample of the NBA Tracking > Passing data from stats.nba.com for the 2025-26 season using the `nba_api` Python package. This is an exploratory pull — we want to see exactly what fields are available before designing anything around it.

## Context

- We already have `nba_api` suggested as the approach (handles required headers automatically)
- Install it if not already installed: `pip install nba_api`
- We got rate-limited previously when making ~600 requests to stats.nba.com. This pull should be MUCH lighter — we only need the season-level leaderboard, not per-game data.
- The data we're after is under Tracking > Passing on stats.nba.com. The relevant fields listed on the site are: PASSES MADE, PASSES RECEIVED, AST, SECONDARY AST, POTENTIAL AST, AST PTS CREATED, AST ADJ, FT AST.

## What to Do

### Step 1 — Find the right endpoint

The `nba_api` package has endpoints that map to stats.nba.com pages. The Tracking > Passing data likely lives in one of these:
- `PlayerDashboardByGameSplits` 
- `LeagueDashPlayerPtShot`
- `PlayerDashPtPass` — this is probably the one (player dashboard passing tracking)
- Or search the `nba_api` source for "pass" or "tracking" related endpoints

List all available endpoints that might contain passing/tracking data. Check `nba_api.stats.endpoints` for anything with "pass", "track", "pt" (player tracking), or similar in the name.

### Step 2 — Pull data for one player first

Pick a high-usage player (e.g., Luka Doncic, player ID 1629029) and pull their passing data for the 2025-26 season. Print ALL fields/columns that come back so we can see the full data structure.

### Step 3 — Pull the full league leaderboard

If Step 2 works, pull the passing data for ALL players for the 2025-26 season. This should be a single API call to a leaderboard-style endpoint (not per-player). 

Add a 2-3 second delay before the call to be respectful of rate limits.

### Step 4 — Save the output

Save the full dataset as `data/tracking_passing_2025-26.csv` and print:
- Total number of players returned
- All column names
- Top 10 players by AST PTS CREATED (or whatever the equivalent column name is)
- A sample row so we can see the full data shape

### Step 5 — Also pull Tracking > Touches if possible

The Touches endpoint has: TOUCHES, FRONT CT TOUCHES, TIME OF POSS, AVG SEC PER TOUCH, AVG DRIB PER TOUCH, PTS PER TOUCH. 

If you can identify the right endpoint, pull this too and save as `data/tracking_touches_2025-26.csv`. Same approach — league-wide season totals.

## Important Notes

- Use `nba_api` — do NOT make raw HTTP requests to stats.nba.com
- Add proper delays between calls (2-3 seconds minimum)
- If you get rate-limited or blocked, stop immediately and report what happened. Don't retry in a loop.
- The season string format for 2025-26 is likely `'2025-26'` but check the `nba_api` docs
- Print everything — we want to see all available columns even if some seem irrelevant. The goal is to inventory what's available.
- If `PlayerDashPtPass` or similar doesn't exist or doesn't work, try searching the `nba_api` GitHub issues for "tracking" or "passing" to see if there's a known working endpoint.
