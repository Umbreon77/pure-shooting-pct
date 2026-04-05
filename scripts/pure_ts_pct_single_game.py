#!/usr/bin/env python3
"""
Pure TS% — Single Game Calculator

Calculates Pure True Shooting Percentage for a single player in a single game
using NBA play-by-play data from the NBA CDN.

Usage:
    python pure_ts_pct_single_game.py <game_id> "<player_name>"
    python pure_ts_pct_single_game.py <game_id> "<player_name>" --local <filepath>

Examples:
    python pure_ts_pct_single_game.py 0022501007 "Luka Doncic"
    python pure_ts_pct_single_game.py 0022501007 "Luka Doncic" --local pbp_raw.json
"""

import argparse
import json
import re
import sys
import unicodedata
import urllib.request

# ---------------------------------------------------------------------------
# Component definitions — max possible points per scoring possession
# ---------------------------------------------------------------------------

COMPONENTS = {
    "C1a": {"name": "Clean 2PT FGA",              "max": 2},
    "C1b": {"name": "Clean 3PT FGA",              "max": 3},
    "C2":  {"name": "2PT Shooting Foul",          "max": 2},
    "C3":  {"name": "3PT Shooting Foul",          "max": 3},
    "C4":  {"name": "And-1 2PT",                  "max": 3},
    "C5":  {"name": "And-1 3PT",                  "max": 4},
    "C6a": {"name": "Tech FT",                    "max": 1},
    "C6b": {"name": "Flagrant FT (non-shooting)", "max": 2},
    "C6c": {"name": "Clear Path FT",              "max": 2},
    "C6d": {"name": "Take Foul FT",               "max": 1},
    "C6e": {"name": "Away-From-Play FT",          "max": 1},
    "C6f": {"name": "Bonus Foul FT",              "max": 2},
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def fetch_pbp(game_id, local_path=None):
    """Fetch play-by-play JSON from NBA CDN or a local file."""
    if local_path:
        with open(local_path) as f:
            return json.load(f)
    url = (
        f"https://cdn.nba.com/static/json/liveData/playbyplay/"
        f"playbyplay_{game_id}.json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

# ---------------------------------------------------------------------------
# Player resolution
# ---------------------------------------------------------------------------

def normalize_name(name):
    """Strip diacritics and lowercase for comparison."""
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def resolve_player_id(actions, player_name):
    """Scan PBP events to find the personId matching a player name."""
    target = normalize_name(player_name)
    target_parts = target.split()
    target_last = target_parts[-1]
    target_first_init = target_parts[0][0] if len(target_parts) > 1 else None

    # Build a map of personId → set of normalized name strings
    name_map = {}
    for a in actions:
        pid = a.get("personId", 0)
        if pid == 0:
            continue
        for field in ("playerNameI", "playerName", "foulDrawnPlayerName"):
            val = a.get(field, "")
            if val:
                name_map.setdefault(pid, set()).add(normalize_name(val))

    # Match on last name
    matches = []
    for pid, names in name_map.items():
        for name in names:
            parts = name.replace(".", " ").split()
            if parts and parts[-1] == target_last:
                matches.append((pid, names))
                break

    # Disambiguate with first initial if needed
    if len(matches) > 1 and target_first_init:
        refined = []
        for pid, names in matches:
            for name in names:
                parts = name.replace(".", " ").split()
                if len(parts) > 1 and parts[0] and parts[0][0] == target_first_init:
                    refined.append((pid, names))
                    break
            if len(refined) == 1:
                return refined[0][0]
        if refined:
            matches = refined

    if len(matches) == 1:
        return matches[0][0]
    if not matches:
        sys.exit(f"Error: No player found matching '{player_name}'")
    print(f"Error: Ambiguous name '{player_name}'. Matches:")
    for pid, names in matches:
        print(f"  personId={pid}: {names}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Event classification
# ---------------------------------------------------------------------------

def _ft_count_from_qualifiers(qualifiers):
    """Extract expected FT count from a foul's qualifiers list."""
    for q in qualifiers:
        if q == "1freethrow":
            return 1
        if q == "2freethrow":
            return 2
        if q == "3freethrow":
            return 3
    return 0


def _fts_for_foul(foul_action_num, ft_count, player_fts_sorted, claimed_ft_ids,
                   foul_period=None, foul_clock=None):
    """Select exactly ft_count FTs belonging to a specific foul.

    Strategy 1 (preferred): look for unclaimed FTs at the same (period, clock)
    as the foul. This handles out-of-order actionNumbers in the NBA PBP feed.

    Strategy 2 (fallback): pick the first ft_count unclaimed FT events whose
    actionNumber > foul_action_num.

    Returns a list of FT action dicts.
    """
    # Strategy 1: FTs at the same (period, clock) as the foul
    if foul_period is not None and foul_clock is not None:
        result = []
        for ft in player_fts_sorted:
            if ft["actionNumber"] in claimed_ft_ids:
                continue
            if ft["period"] == foul_period and ft["clock"] == foul_clock:
                result.append(ft)
                if len(result) == ft_count:
                    break
        if len(result) == ft_count:
            return result

    # Strategy 2: FTs after the foul in actionNumber order
    result = []
    for ft in player_fts_sorted:
        if ft["actionNumber"] in claimed_ft_ids:
            continue
        if ft["actionNumber"] > foul_action_num:
            result.append(ft)
            if len(result) == ft_count:
                break
    return result


def _has_concurrent_fga(player_fgs, period, clock):
    """Check if the player had a field goal attempt at the same game moment."""
    return any(
        f["period"] == period and f["clock"] == clock
        for f in player_fgs
    )


def classify_scoring_events(actions, player_id):
    """
    Parse every PBP action for *player_id* and classify each scoring event
    into a Pure TS% component.

    Returns a dict: component_id → list of event dicts.
    """
    # Index all fouls by (period, clock) for tech-FT lookups
    all_fouls_by_time = {}
    for a in actions:
        if a.get("actionType") == "foul":
            key = (a["period"], a["clock"])
            all_fouls_by_time.setdefault(key, []).append(a)

    # Player field-goal attempts
    player_fgs = [
        a for a in actions
        if a.get("personId") == player_id and a.get("isFieldGoal") == 1
    ]

    # Player free throws sorted by actionNumber (for linking to fouls)
    player_fts_sorted = sorted(
        [a for a in actions
         if a.get("actionType") == "freethrow" and a.get("personId") == player_id],
        key=lambda a: a["actionNumber"],
    )

    # Also keep the old (period, clock) groups for Pass 2 fallback
    ft_groups = {}
    for a in player_fts_sorted:
        key = (a["period"], a["clock"])
        ft_groups.setdefault(key, []).append(a)

    components = {k: [] for k in COMPONENTS}
    and1_fg_keys = set()       # (period, clock) of And-1 FGs → exclude from C1
    claimed_ft_ids = set()     # actionNumbers of FTs already assigned to a foul

    # ---- Pass 1: fouls drawn by the player --------------------------------
    for a in actions:
        if a.get("actionType") != "foul":
            continue
        if a.get("foulDrawnPersonId") != player_id:
            continue

        qualifiers = a.get("qualifiers", [])
        descriptor = (a.get("descriptor") or "").lower()
        sub_type = (a.get("subType") or "").lower()
        period, clock = a["period"], a["clock"]
        key = (period, clock)
        foul_action_num = a["actionNumber"]

        ft_count = _ft_count_from_qualifiers(qualifiers)
        if ft_count == 0:
            continue  # no FTs → not a scoring possession

        # Link FTs to this specific foul using actionNumber ordering
        fts = _fts_for_foul(foul_action_num, ft_count, player_fts_sorted,
                            claimed_ft_ids, foul_period=period,
                            foul_clock=clock)
        ft_made = sum(1 for ft in fts if ft.get("shotResult") == "Made")
        for ft in fts:
            claimed_ft_ids.add(ft["actionNumber"])

        component = None
        fg_pts = 0
        total_pts = ft_made

        # Check for shooting-context flagrant first
        is_flagrant = "flagrant" in descriptor or "flagrant" in sub_type
        is_shooting = descriptor == "shooting"
        has_concurrent_fg = _has_concurrent_fga(player_fgs, period, clock)

        # And-1 detection: 1 FT + concurrent made FG, regardless of
        # descriptor (some And-1s lack descriptor="shooting" in PBP data)
        if ft_count == 1 and has_concurrent_fg:
            fg = next(
                (f for f in player_fgs
                 if f["period"] == period
                 and f["clock"] == clock
                 and f.get("shotResult") == "Made"),
                None,
            )
            if fg:
                is_3pt = fg["actionType"] == "3pt"
                fg_pts = 3 if is_3pt else 2
                total_pts = fg_pts + ft_made
                component = "C5" if is_3pt else "C4"
                and1_fg_keys.add(key)

        elif is_shooting or (is_flagrant and has_concurrent_fg):
            # Shooting foul (or flagrant during a shot attempt)
            if ft_count == 3:
                component = "C3"
            elif ft_count == 2:
                component = "C2"

        elif is_flagrant:
            component = "C6b"

        elif "take" in descriptor:
            # 1 FTA → transition take foul (C6d); 2 FTA → bonus/late-game (C6f)
            component = "C6d" if ft_count == 1 else "C6f"

        elif "clear" in descriptor:
            component = "C6c"

        elif "away" in descriptor:
            component = "C6e"

        else:
            # Non-shooting foul with FTs → bonus (C6f)
            component = "C6f"

        if component:
            event = {
                "period": period,
                "clock": clock,
                "pts": total_pts,
                "fg_pts": fg_pts,
                "ft_made": ft_made,
                "ft_attempted": len(fts),
                "description": a.get("description", ""),
            }
            # For C6 penalty components, override max per-event based on
            # actual FT count (e.g., flagrant in penalty can award 3 FTs
            # instead of the default 2).
            if component.startswith("C6") and ft_count != COMPONENTS[component]["max"]:
                event["max_pts"] = ft_count
            components[component].append(event)

    # ---- Pass 2: unmatched FT groups (designated-shooter FTs) --------------
    # Handles cases where the player shot FTs but didn't draw the foul:
    #   - Technical fouls (any player can shoot) → C6a
    #   - Flagrant fouls (designated shooter) → C6b
    #   - Transition take fouls (any offensive player can shoot) → C6d
    #   - Away-from-play fouls (any player can shoot) → C6e
    #
    # Process each unclaimed FT individually, grouping consecutive unclaimed
    # FTs that share the same (period, clock) into events.
    unclaimed_ft_groups = {}
    for ft in player_fts_sorted:
        if ft["actionNumber"] in claimed_ft_ids:
            continue
        key = (ft["period"], ft["clock"])
        unclaimed_ft_groups.setdefault(key, []).append(ft)

    for key, fts in unclaimed_ft_groups.items():
        period, clock = key

        # Split the FT group into individual events based on "X of Y" subType
        # E.g., "1 of 1" + "1 of 1" at the same time = 2 separate events
        ft_events = []
        current_event = []
        for ft in sorted(fts, key=lambda f: f["actionNumber"]):
            sub = (ft.get("subType") or "").lower()
            # Start a new event if this is "1 of N" and we already have FTs
            if sub.startswith("1 of") and current_event:
                ft_events.append(current_event)
                current_event = [ft]
            else:
                current_event.append(ft)
        if current_event:
            ft_events.append(current_event)

        for event_fts in ft_events:
            ft_made = sum(1 for ft in event_fts
                          if ft.get("shotResult") == "Made")

            # First check the FT event's own descriptor (most reliable signal)
            ft_descriptor = (event_fts[0].get("descriptor") or "").lower()

            # Then check the foul event at the same timestamp
            fouls = all_fouls_by_time.get(key, [])
            foul_sub = ""
            foul_descriptor = ""
            foul_desc_text = ""
            matched_foul = None
            for foul in fouls:
                foul_sub = (foul.get("subType") or "").lower()
                foul_descriptor = (foul.get("descriptor") or "").lower()
                foul_desc_text = (foul.get("description") or "").lower()
                matched_foul = foul
                break  # take the first foul at this timestamp

            # Classify using the FT's own descriptor first (most reliable —
            # tech FTs can be administered at a different clock time than the
            # tech foul itself, so the foul at the same timestamp may be
            # unrelated).  Fall back to the foul event if the FT descriptor
            # is empty.
            component = None
            if "technical" in ft_descriptor:
                component = "C6a"
            elif "transition" in ft_descriptor and "take" in ft_descriptor:
                component = "C6d"
            elif "away" in ft_descriptor:
                component = "C6e"
            elif "technical" in foul_sub or "technical" in foul_desc_text:
                component = "C6a"
            elif "flagrant" in foul_sub or "flagrant" in foul_desc_text:
                component = "C6b"
            elif "transition" in foul_descriptor and "take" in foul_descriptor:
                component = "C6d"
            elif "away" in foul_descriptor:
                component = "C6e"

            if component:
                event = {
                    "period": period,
                    "clock": clock,
                    "pts": ft_made,
                    "fg_pts": 0,
                    "ft_made": ft_made,
                    "ft_attempted": len(event_fts),
                    "description": (matched_foul or event_fts[0]).get(
                        "description", ""),
                }
                # Override max if actual FT count differs from component default
                actual_ft_count = len(event_fts)
                if actual_ft_count != COMPONENTS[component]["max"]:
                    event["max_pts"] = actual_ft_count
                components[component].append(event)
            for ft in event_fts:
                claimed_ft_ids.add(ft["actionNumber"])

    # ---- Pass 3: field-goal events (C1a / C1b) ----------------------------
    for fg in player_fgs:
        key = (fg["period"], fg["clock"])
        if key in and1_fg_keys:
            continue  # already counted under C4/C5

        is_3pt = fg["actionType"] == "3pt"
        made = fg.get("shotResult") == "Made"
        pts = (3 if is_3pt else 2) if made else 0
        component = "C1b" if is_3pt else "C1a"

        components[component].append({
            "period": fg["period"],
            "clock": fg["clock"],
            "pts": pts,
            "made": made,
            "fg_pts": pts,
            "ft_made": 0,
            "ft_attempted": 0,
            "description": fg.get("description", ""),
        })

    return components

# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------

def calculate_pure_ts(components):
    """
    Compute Pure TS% as total points scored divided by total max possible
    points across all scoring possessions (Approach B).

    Per-component details (eff, weight, contribution) are still populated
    for reporting and CSV output, but the final pure_ts value is:
        pure_ts = sum(pts) / sum(max_pts)

    Returns (pure_ts, total_possessions, details_dict).
    """
    total_poss = sum(len(evts) for evts in components.values())
    if total_poss == 0:
        return 0.0, 0, {}

    details = {}
    for comp_id, events in components.items():
        n = len(events)
        if n == 0:
            continue
        pts = sum(e["pts"] for e in events)
        # Use per-event max_pts when available (C6 events where FT count
        # differs from the component's default max, e.g. flagrant in penalty)
        max_pts = sum(e.get("max_pts", COMPONENTS[comp_id]["max"])
                      for e in events)
        eff = pts / max_pts
        if eff > 1.0:
            import sys
            print(f"WARNING: {comp_id} efficiency {eff:.4f} > 1.0 "
                  f"({pts} pts / {max_pts} max from {n} events)",
                  file=sys.stderr)
        weight = n / total_poss
        contrib = weight * eff
        details[comp_id] = {
            "events": n, "pts": pts, "max_pts": max_pts,
            "eff": eff, "weight": weight, "contribution": contrib,
        }

    # Approach B: total pts / total max possible pts
    total_pts = sum(d["pts"] for d in details.values())
    total_max_pts = sum(d["max_pts"] for d in details.values())
    pure_ts = total_pts / total_max_pts if total_max_pts > 0 else 0.0

    return pure_ts, total_poss, details


def box_score_from_components(components):
    """Reconstruct box-score totals from classified component events."""
    pts = fg_made = fga = fg3_made = fg3a = ft_made = fta = 0

    for comp_id, events in components.items():
        for e in events:
            pts += e["pts"]
            fta += e.get("ft_attempted", 0)
            ft_made += e.get("ft_made", 0)

        if comp_id == "C1a":
            fga += len(events)
            fg_made += sum(1 for e in events if e.get("made"))
        elif comp_id == "C1b":
            fga += len(events)
            fg3a += len(events)
            fg_made += sum(1 for e in events if e.get("made"))
            fg3_made += sum(1 for e in events if e.get("made"))
        elif comp_id == "C4":
            fga += len(events)   # And-1 FG counts as FGA
            fg_made += len(events)
        elif comp_id == "C5":
            fga += len(events)
            fg3a += len(events)
            fg_made += len(events)
            fg3_made += len(events)

    return {
        "pts": pts, "fg_made": fg_made, "fga": fga,
        "fg3_made": fg3_made, "fg3a": fg3a,
        "ft_made": ft_made, "fta": fta,
    }

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _fmt_clock(clock_str):
    """'PT11M13.00S' → '11:13'"""
    m = re.match(r"PT(\d+)M([\d.]+)S", clock_str)
    if not m:
        return clock_str
    mins = int(m.group(1))
    secs = float(m.group(2))
    if secs == int(secs):
        return f"{mins}:{int(secs):02d}"
    return f"{mins}:{secs:04.1f}"


def print_results(player_name, game_id, components, pure_ts, total_poss,
                  details, box):
    """Print the full Pure TS% report to stdout."""
    W = 72
    print(f"\n{'=' * W}")
    print(f"  PURE TS% REPORT")
    print(f"  Player:  {player_name}")
    print(f"  Game ID: {game_id}")
    print(f"  Box:     {box['pts']} PTS | {box['fg_made']}-{box['fga']} FG | "
          f"{box['fg3_made']}-{box['fg3a']} 3PT | "
          f"{box['ft_made']}-{box['fta']} FT")
    print(f"{'=' * W}")

    # -- Component breakdown table ------------------------------------------
    print(f"\n  COMPONENT BREAKDOWN\n")
    hdr = (f"  {'Comp':<6} {'Type':<28} "
           f"{'Ev':>4} {'PTS':>5} {'Max':>5} {'Eff':>8} {'Wt':>7}")
    print(hdr)
    print(f"  {'─' * 6} {'─' * 28} {'─' * 4} {'─' * 5} {'─' * 5} "
          f"{'─' * 8} {'─' * 7}")

    for cid in COMPONENTS:
        if cid not in details:
            continue
        d = details[cid]
        print(f"  {cid:<6} {COMPONENTS[cid]['name']:<28} "
              f"{d['events']:>4} {d['pts']:>5} {d['max_pts']:>5} "
              f"{d['eff']:>8.4f} {d['weight']:>7.4f}")

    print(f"  {'─' * 6} {'─' * 28} {'─' * 4} {'─' * 5} {'─' * 5} "
          f"{'─' * 8} {'─' * 7}")
    total_pts = sum(d["pts"] for d in details.values())
    total_max = sum(d["max_pts"] for d in details.values())
    print(f"  {'TOTAL':<6} {'':28} {total_poss:>4} {total_pts:>5} "
          f"{total_max:>5}")

    # -- Per-component event detail -----------------------------------------
    print(f"\n  EVENT DETAIL\n")
    for cid in COMPONENTS:
        if cid not in details:
            continue
        events = components[cid]
        label = f"{cid}: {COMPONENTS[cid]['name']}"
        print(f"  {label}")
        for e in events:
            q = f"Q{e['period']}"
            clk = _fmt_clock(e["clock"])
            desc = e["description"]
            pts = e["pts"]
            # Show FT detail for foul components
            if cid in ("C1a", "C1b"):
                result = "MADE" if e.get("made") else "MISS"
                print(f"    {q} {clk:>6}  {result:<5}  {pts} pts  {desc}")
            elif cid in ("C4", "C5"):
                ft_s = f"FT {e['ft_made']}/{e['ft_attempted']}"
                print(f"    {q} {clk:>6}  AND-1  {pts} pts ({e['fg_pts']}fg+{e['ft_made']}ft)  {ft_s}  {desc}")
            else:
                ft_s = f"FT {e['ft_made']}/{e['ft_attempted']}"
                print(f"    {q} {clk:>6}  {pts} pts  {ft_s}  {desc}")
        print()

    # -- Box score reconciliation -------------------------------------------
    print(f"  BOX SCORE RECONCILIATION\n")
    print(f"    FG:  {box['fg_made']}-{box['fga']:<6}"
          f"  3PT: {box['fg3_made']}-{box['fg3a']:<6}"
          f"  FT: {box['ft_made']}-{box['fta']:<6}"
          f"  PTS: {box['pts']}")

    # -- Pure TS% calculation -----------------------------------------------
    print(f"\n  PURE TS% CALCULATION\n")
    print(f"    Total Scoring Possessions: {total_poss}\n")

    active = [cid for cid in COMPONENTS if cid in details]

    # Weight × Efficiency terms
    terms_we = []
    for cid in active:
        d = details[cid]
        terms_we.append(f"({d['events']}/{total_poss} x "
                        f"{d['pts']}/{d['max_pts']})")
    print(f"    Pure TS% = {' + '.join(terms_we)}")

    terms_dec = [f"({details[c]['weight']:.4f} x {details[c]['eff']:.4f})"
                 for c in active]
    print(f"              = {' + '.join(terms_dec)}")

    contribs = [f"{details[c]['contribution']:.4f}" for c in active]
    print(f"              = {' + '.join(contribs)}")
    print(f"              = {pure_ts:.4f}")
    print(f"              = {pure_ts * 100:.1f}%")

    # -- Standard TS% -------------------------------------------------------
    tsa = box["fga"] + 0.44 * box["fta"]
    std_ts = box["pts"] / (2 * tsa) if tsa > 0 else 0.0
    print(f"\n  STANDARD TS%\n")
    print(f"    = {box['pts']} / (2 x ({box['fga']} + 0.44 x {box['fta']}))")
    print(f"    = {box['pts']} / (2 x {tsa:.2f})")
    print(f"    = {box['pts']} / {2 * tsa:.2f}")
    print(f"    = {std_ts:.4f}")
    print(f"    = {std_ts * 100:.1f}%")

    # -- Comparison box -----------------------------------------------------
    delta = (pure_ts - std_ts) * 100
    bw = 36  # box inner width
    print()
    print(f"  ┌{'─' * bw}┐")
    print(f"  │  {'Metric':<18} {'Value':>13}   │")
    print(f"  ├{'─' * bw}┤")
    print(f"  │  {'Pure TS%':<18} {pure_ts * 100:>12.1f}%  │")
    print(f"  │  {'Standard TS%':<18} {std_ts * 100:>12.1f}%  │")
    print(f"  ├{'─' * bw}┤")
    print(f"  │  {'Delta':<18} {delta:>+11.1f} pp  │")
    print(f"  └{'─' * bw}┘")
    print(f"\n{'=' * W}\n")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Calculate Pure TS%% for a single player in a single game."
    )
    parser.add_argument("game_id", help="NBA game ID (e.g. 0022501007)")
    parser.add_argument("player_name", help='Player name (e.g. "Luka Doncic")')
    parser.add_argument(
        "--local", metavar="FILEPATH",
        help="Read PBP from a local JSON file instead of fetching from NBA CDN",
    )
    args = parser.parse_args()

    # Load data
    source = args.local if args.local else "NBA CDN"
    print(f"Loading play-by-play for game {args.game_id} from {source}...")
    try:
        data = fetch_pbp(args.game_id, args.local)
    except Exception as e:
        sys.exit(f"Error loading data: {e}")

    actions = data["game"]["actions"]
    print(f"  {len(actions)} actions loaded.")

    # Resolve player
    player_id = resolve_player_id(actions, args.player_name)
    print(f"  Resolved '{args.player_name}' → personId {player_id}")

    # Classify events
    components = classify_scoring_events(actions, player_id)

    # Calculate
    pure_ts, total_poss, details = calculate_pure_ts(components)
    box = box_score_from_components(components)

    # Report
    print_results(
        args.player_name, args.game_id, components,
        pure_ts, total_poss, details, box,
    )


if __name__ == "__main__":
    main()
