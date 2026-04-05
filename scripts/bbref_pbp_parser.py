#!/usr/bin/env python3
"""
BBRef PBP Parser — PS% Component Classifier

Parses Basketball Reference play-by-play JSON (from scrape_bbref_pbp.py cache)
and classifies every scoring event into the 12 PS% components (C1a–C6f).

Produces the same output format as pure_ts_pct_single_game.classify_scoring_events()
so it can plug into the existing season/league aggregation pipeline.

Usage:
    python3 scripts/bbref_pbp_parser.py <game_json_path> "<player_name>"

    # As a module:
    from bbref_pbp_parser import classify_bbref_game
    components = classify_bbref_game("data/bbref_pbp_cache/199611010BOS.json", "M. Jordan")
"""

import json
import os
import re
import sys
import unicodedata
import warnings

# Reuse COMPONENTS definition from the CDN parser
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
# Player matching
# ---------------------------------------------------------------------------

def normalize_name(name):
    """Strip diacritics and lowercase for comparison.

    Handles mangled UTF-8 from BBRef scraper where chars like ć (U+0107,
    UTF-8 bytes c4 87) were decoded as latin-1, producing 'Ä\\x87'.
    We re-encode as latin-1 and decode as UTF-8 to recover the original,
    then strip diacritics normally.
    """
    try:
        fixed = name.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        fixed = name
    nfkd = unicodedata.normalize("NFKD", fixed)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}


def _strip_suffix(name_parts):
    """Remove name suffixes like Jr., III, etc."""
    while name_parts and name_parts[-1].rstrip(".") in _SUFFIXES:
        name_parts = name_parts[:-1]
    return name_parts


def _match_player(events, target_name):
    """Find all (player, player_id) pairs that match target_name.

    BBRef uses abbreviated names like "M. Jordan". We match on normalized
    name equality, falling back to last-name + first-initial matching.
    Handles suffix differences (e.g., "O. Porter Jr." vs "O. Porter").

    Returns the best-matching (player, player_id) tuple, or None.
    """
    target = normalize_name(target_name)
    target_parts = _strip_suffix(target.replace(".", " ").split())
    target_last = target_parts[-1] if target_parts else ""
    target_first_init = target_parts[0][0] if len(target_parts) > 1 else None

    # Collect all unique (player, player_id) pairs
    seen = {}
    for e in events:
        p = e.get("player")
        pid = e.get("player_id")
        if p and pid and pid not in seen:
            seen[pid] = p

    # Exact normalized match
    for pid, name in seen.items():
        if normalize_name(name) == target:
            return (name, pid)

    # Last name + first initial match
    matches = []
    for pid, name in seen.items():
        norm = normalize_name(name)
        parts = _strip_suffix(norm.replace(".", " ").split())
        if not parts:
            continue
        last = parts[-1]
        first_init = parts[0][0] if len(parts) > 1 else None
        if last == target_last:
            if target_first_init is None or first_init == target_first_init:
                matches.append((name, pid))

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Multiple matches — try tighter matching
        for name, pid in matches:
            norm = normalize_name(name)
            if norm.startswith(target_parts[0]):
                return (name, pid)
        return matches[0]  # fallback to first

    return None


# ---------------------------------------------------------------------------
# Foul classification helpers
# ---------------------------------------------------------------------------

def _classify_other_foul(description):
    """Classify an 'other_foul' event by its description prefix.

    Returns one of:
        'shooting'  — shooting block foul (treated as shooting foul)
        'tech'      — defensive 3-sec, delay, hanging, ill-defined, etc.
        'take'      — personal take foul
        'charge'    — offensive charge (not a scoring event)
        'inbound'   — inbound foul (bonus FTs)
        'block'     — personal block foul (bonus FTs)
        'punch'     — punching foul (flagrant-like)
        'elbow'     — elbow foul (flagrant-like)
        'team'      — team foul (bonus FTs if followed by FTs)
        'unknown'   — anything else
    """
    desc = description.lower()
    if "shooting block" in desc:
        return "shooting"
    if "def 3 sec" in desc or "delay tech" in desc or "hanging tech" in desc \
       or "ill def tech" in desc or "non unsport tech" in desc \
       or "excess timeout tech" in desc:
        return "tech"
    if "take foul" in desc:
        return "take"
    if "offensive charge" in desc:
        return "charge"
    if "inbound foul" in desc:
        return "inbound"
    if "personal block" in desc:
        return "block"
    if "punching" in desc:
        return "punch"
    if "elbow foul" in desc:
        return "elbow"
    if desc.startswith("teamfoul") or desc.startswith("team foul"):
        return "team"
    return "unknown"


def _find_foul_backward(events, ft_index, ft_player_id):
    """Walk backward from an FT event to find the foul that caused it.

    Skips substitutions, timeouts, FTs belonging to other sequences,
    and other non-action events. When a foul is found, checks that any
    FTs between the foul and ft_index belong to a different player
    (i.e., the foul's own FTs are already accounted for). If the foul
    has FTs from the same player between it and ft_index, it's the right
    foul. If a foul has FTs from another player between it and ft_index,
    that foul is already consumed — skip it and keep looking.

    Returns the foul event dict, or None.
    """
    for j in range(ft_index - 1, max(-1, ft_index - 15), -1):
        ev = events[j]
        if "foul" in ev["type"]:
            # Check if there's ANOTHER foul between this candidate and our
            # target FT index. If so, that intervening foul likely owns any
            # intervening FTs, meaning THIS candidate foul's FTs are either
            # before it or are our target FTs. We want the closest foul that
            # isn't consumed by intervening FTs from a different player.
            #
            # A foul is "consumed" if there is a different-player FT directly
            # following it (before any other foul) between j and ft_index.
            consumed = False
            for k in range(j + 1, ft_index):
                mid = events[k]
                if mid["type"] in ("made_ft", "miss_ft"):
                    if mid.get("player_id") != ft_player_id:
                        consumed = True
                    break  # Only check the first FT after this foul
                if "foul" in mid["type"]:
                    break  # Hit another foul before any FT — not consumed
            if consumed:
                continue
            return ev
        # Skip events that can appear between a foul and its FTs
        if ev["type"] in ("substitution", "timeout", "violation",
                          "offensive_rebound", "defensive_rebound",
                          "period_start", "period_end", "other",
                          "made_ft", "miss_ft"):
            continue
        # A shot or turnover means we've passed the foul context
        break
    return None


def _find_concurrent_made_fg(events, foul_index):
    """Check if there's a made field goal at the same (quarter, time) as a foul.

    Looks backward from the foul for a made_2pt or made_3pt at the same time.
    Returns the FG event or None.
    """
    foul = events[foul_index]
    fq, ft_ = foul["quarter"], foul["time"]
    for j in range(foul_index - 1, max(-1, foul_index - 5), -1):
        ev = events[j]
        if ev["type"] in ("made_2pt", "made_3pt") \
           and ev["quarter"] == fq and ev["time"] == ft_:
            return ev
        if ev["type"] == "substitution":
            continue
        if ev["quarter"] != fq or ev["time"] != ft_:
            break
    return None


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------

def classify_bbref_game(game_path_or_data, player_name):
    """Classify all scoring events for a player from a BBRef PBP JSON file.

    Args:
        game_path_or_data: path to JSON file, or already-loaded dict
        player_name: player name to match (e.g. "M. Jordan")

    Returns:
        dict mapping component IDs (C1a..C6f) to lists of event dicts,
        same format as pure_ts_pct_single_game.classify_scoring_events().
        Returns None if the player is not found in the game.
    """
    if isinstance(game_path_or_data, dict):
        game = game_path_or_data
    else:
        with open(game_path_or_data) as f:
            game = json.load(f)

    events = game["events"]

    # Resolve player
    match = _match_player(events, player_name)
    if match is None:
        return None
    player_display, player_id = match

    components = {k: [] for k in COMPONENTS}

    # Index events by position for fast lookup
    # Collect player's FG events and FT events
    player_fgs = []       # (index, event)
    player_fts = []       # (index, event)
    for i, e in enumerate(events):
        if e.get("player_id") != player_id:
            continue
        if e["type"] in ("made_2pt", "miss_2pt", "made_3pt", "miss_3pt"):
            player_fgs.append((i, e))
        elif e["type"] in ("made_ft", "miss_ft"):
            player_fts.append((i, e))

    # Build a set of (quarter, time) keys for all player made FGs
    # Used for And-1 detection
    made_fg_by_qt = {}
    for idx, e in player_fgs:
        if e["type"] in ("made_2pt", "made_3pt"):
            key = (e["quarter"], e["time"])
            made_fg_by_qt.setdefault(key, []).append((idx, e))

    # Track which FG indices and FT indices have been claimed
    claimed_fg_indices = set()
    claimed_ft_indices = set()

    # ---- Pass 1: Process FT sequences to classify foul-based components ----
    # Group player FTs into sequences by (quarter, time) and ft_num ordering
    ft_groups = []  # list of lists of (index, event)
    current_group = []
    for idx, e in player_fts:
        ft_num = e.get("ft_num", 1)
        if ft_num == 1 and current_group:
            ft_groups.append(current_group)
            current_group = [(idx, e)]
        else:
            current_group.append((idx, e))
    if current_group:
        ft_groups.append(current_group)

    for ft_group in ft_groups:
        first_ft_idx, first_ft = ft_group[0]
        ft_total = first_ft.get("ft_total", len(ft_group))
        ft_made = sum(1 for _, e in ft_group if e["type"] == "made_ft")
        ft_attempted = len(ft_group)
        quarter = first_ft["quarter"]
        time_ = first_ft["time"]
        is_tech = first_ft.get("is_technical", False)
        is_flagrant_ft = first_ft.get("is_flagrant_ft", False)

        # Find the foul that caused these FTs
        foul = _find_foul_backward(events, first_ft_idx, player_id)
        foul_type = foul["type"] if foul else None
        foul_desc = foul.get("description", "") if foul else ""
        foul_index = None
        if foul:
            # Get the actual index of the foul in events
            for fi in range(first_ft_idx - 1, max(-1, first_ft_idx - 10), -1):
                if events[fi] is foul:
                    foul_index = fi
                    break

        component = None
        fg_pts = 0
        total_pts = ft_made

        # --- Technical FTs ---
        if is_tech:
            component = "C6a"

        # --- Flagrant FTs (from FT flag) ---
        elif is_flagrant_ft:
            # Check if this was a shooting flagrant (concurrent made FG = And-1)
            if foul_index is not None:
                concurrent_fg = _find_concurrent_made_fg(events, foul_index)
                if concurrent_fg and ft_total == 1:
                    # Flagrant And-1
                    is_3pt = concurrent_fg["type"] == "made_3pt"
                    fg_pts = 3 if is_3pt else 2
                    total_pts = fg_pts + ft_made
                    component = "C5" if is_3pt else "C4"
                    # Claim the FG
                    for fg_idx, fg_e in player_fgs:
                        if fg_e is concurrent_fg:
                            claimed_fg_indices.add(fg_idx)
                            break
                else:
                    component = "C6b"
            else:
                component = "C6b"

        # --- Shooting foul ---
        elif foul_type == "shooting_foul":
            # Check for And-1: shooting foul + concurrent made FG + 1 FT
            if foul_index is not None and ft_total == 1:
                concurrent_fg = _find_concurrent_made_fg(events, foul_index)
                if concurrent_fg:
                    is_3pt = concurrent_fg["type"] == "made_3pt"
                    fg_pts = 3 if is_3pt else 2
                    total_pts = fg_pts + ft_made
                    component = "C5" if is_3pt else "C4"
                    for fg_idx, fg_e in player_fgs:
                        if fg_e is concurrent_fg:
                            claimed_fg_indices.add(fg_idx)
                            break

            # Not an And-1 → regular shooting foul
            if component is None:
                if ft_total == 3:
                    component = "C3"
                elif ft_total == 2:
                    component = "C2"
                elif ft_total == 1:
                    # Edge case: 1 FT shooting foul without concurrent FG
                    # This can happen with flagrant upgrades or data quirks
                    # Check if there's a made FG at same time anyway
                    key = (quarter, time_)
                    if key in made_fg_by_qt:
                        fg_candidates = made_fg_by_qt[key]
                        for fg_idx, fg_e in fg_candidates:
                            if fg_idx not in claimed_fg_indices:
                                is_3pt = fg_e["type"] == "made_3pt"
                                fg_pts = 3 if is_3pt else 2
                                total_pts = fg_pts + ft_made
                                component = "C5" if is_3pt else "C4"
                                claimed_fg_indices.add(fg_idx)
                                break
                    if component is None:
                        # Truly 1 FT shooting foul with no FG — unusual, treat as C2
                        component = "C2"
                        warnings.warn(
                            f"1-FT shooting foul with no concurrent FG: "
                            f"Q{quarter} {time_} {foul_desc}")

        # --- Flagrant foul (from foul type) ---
        elif foul_type == "flagrant_foul":
            # Check for shooting flagrant (concurrent made FG)
            if foul_index is not None:
                concurrent_fg = _find_concurrent_made_fg(events, foul_index)
                if concurrent_fg and ft_total == 1:
                    is_3pt = concurrent_fg["type"] == "made_3pt"
                    fg_pts = 3 if is_3pt else 2
                    total_pts = fg_pts + ft_made
                    component = "C5" if is_3pt else "C4"
                    for fg_idx, fg_e in player_fgs:
                        if fg_e is concurrent_fg:
                            claimed_fg_indices.add(fg_idx)
                            break
                else:
                    component = "C6b"
            else:
                component = "C6b"

        # --- Clear path foul ---
        elif foul_type == "clear_path_foul":
            component = "C6c"

        # --- Away from play foul ---
        elif foul_type == "away_from_play_foul":
            component = "C6e"

        # --- Technical foul (from foul type, in case is_technical was missing) ---
        elif foul_type == "technical_foul":
            component = "C6a"

        # --- other_foul subtypes ---
        elif foul_type == "other_foul":
            subtype = _classify_other_foul(foul_desc)
            if subtype == "shooting":
                # Shooting block foul — same as regular shooting foul
                # Check for And-1 first
                if foul_index is not None and ft_total == 1:
                    concurrent_fg = _find_concurrent_made_fg(events, foul_index)
                    if concurrent_fg:
                        is_3pt = concurrent_fg["type"] == "made_3pt"
                        fg_pts = 3 if is_3pt else 2
                        total_pts = fg_pts + ft_made
                        component = "C5" if is_3pt else "C4"
                        for fg_idx, fg_e in player_fgs:
                            if fg_e is concurrent_fg:
                                claimed_fg_indices.add(fg_idx)
                                break
                if component is None:
                    component = "C3" if ft_total == 3 else "C2"
            elif subtype == "tech":
                component = "C6a"
            elif subtype == "take":
                # Take fouls in BBRef always give 2 FTs (pre-transition rule)
                component = "C6f"
            elif subtype in ("punch", "elbow"):
                component = "C6b"
            elif subtype in ("inbound", "block", "team", "unknown"):
                # Non-shooting fouls that result in FTs → bonus
                component = "C6f"
            elif subtype == "charge":
                # Offensive charge — not a scoring event, skip
                continue

        # --- Personal foul / loose ball foul → bonus (C6f) ---
        elif foul_type in ("personal_foul", "loose_ball_foul"):
            # Check description for take foul
            if foul_type == "personal_foul" and "take foul" in foul_desc.lower():
                component = "C6f"  # Take fouls give 2 FTs in BBRef era
            else:
                component = "C6f"

        # --- No foul found ---
        elif foul is None:
            # FTs without a preceding foul — check FT description
            ft_desc = first_ft.get("description", "").lower()
            if "technical" in ft_desc:
                component = "C6a"
            elif "flagrant" in ft_desc:
                component = "C6b"
            elif "clear path" in ft_desc:
                component = "C6c"
            else:
                # Check for And-1 with missing shooting foul event:
                # ft_total == 1 and made FG at same (quarter, time)
                key = (quarter, time_)
                if ft_total == 1 and key in made_fg_by_qt:
                    fg_candidates = made_fg_by_qt[key]
                    for fg_idx, fg_e in fg_candidates:
                        if fg_idx not in claimed_fg_indices:
                            is_3pt = fg_e["type"] == "made_3pt"
                            fg_pts = 3 if is_3pt else 2
                            total_pts = fg_pts + ft_made
                            component = "C5" if is_3pt else "C4"
                            claimed_fg_indices.add(fg_idx)
                            break

                if component is None:
                    # Truly unlinked FTs — default to C6a if 1 FT, C6f if 2
                    if ft_total == 1:
                        component = "C6a"
                    else:
                        component = "C6f"
                    warnings.warn(
                        f"FTs with no preceding foul: Q{quarter} {time_} "
                        f"{first_ft.get('description', '')}")

        if component:
            event = {
                "period": quarter,
                "clock": time_,
                "pts": total_pts,
                "fg_pts": fg_pts,
                "ft_made": ft_made,
                "ft_attempted": ft_attempted,
                "description": foul_desc or first_ft.get("description", ""),
            }
            # Override max_pts if actual FT count differs from component default
            if component.startswith("C6"):
                actual_max = ft_attempted
                if component in ("C4", "C5"):
                    pass  # And-1s have fixed max
                elif actual_max != COMPONENTS[component]["max"]:
                    event["max_pts"] = actual_max
            components[component].append(event)

        # Mark all FTs in this group as claimed
        for idx, _ in ft_group:
            claimed_ft_indices.add(idx)

    # ---- Pass 2: Clean field goal events (C1a / C1b) ----
    for fg_idx, fg_e in player_fgs:
        if fg_idx in claimed_fg_indices:
            continue

        # Check if this FG has a shooting foul at the same (quarter, time)
        # that we already processed as an And-1 — if so, skip
        # (This handles the case where the FG was claimed in Pass 1)

        # Check for unclaimed And-1: made FG with shooting foul at same time
        # where the FTs were somehow not linked to this player
        # (This shouldn't happen normally but is a safety check)
        is_3pt = fg_e["type"] in ("made_3pt", "miss_3pt")
        made = fg_e["type"] in ("made_2pt", "made_3pt")
        pts = (3 if is_3pt else 2) if made else 0
        component = "C1b" if is_3pt else "C1a"

        components[component].append({
            "period": fg_e["quarter"],
            "clock": fg_e["time"],
            "pts": pts,
            "made": made,
            "fg_pts": pts,
            "ft_made": 0,
            "ft_attempted": 0,
            "description": fg_e.get("description", ""),
        })

    return components


# ---------------------------------------------------------------------------
# Convenience: load game and return all players' components
# ---------------------------------------------------------------------------

def classify_all_players(game_path_or_data):
    """Classify scoring events for ALL players in a BBRef PBP game.

    Returns dict: player_name → components dict.
    """
    if isinstance(game_path_or_data, dict):
        game = game_path_or_data
    else:
        with open(game_path_or_data) as f:
            game = json.load(f)

    events = game["events"]

    # Collect all unique players
    players = {}
    for e in events:
        pid = e.get("player_id")
        pname = e.get("player")
        if pid and pname and pid not in players:
            players[pid] = pname

    results = {}
    for pid, pname in players.items():
        comps = classify_bbref_game(game, pname)
        if comps:
            # Check if player had any scoring events
            total = sum(len(evts) for evts in comps.values())
            if total > 0:
                results[pname] = comps

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    # Import here to allow module use without the CDN parser on sys.path
    sys.path.insert(0, os.path.dirname(__file__))
    from pure_ts_pct_single_game import calculate_pure_ts, box_score_from_components

    if len(sys.argv) < 3:
        print("Usage: python3 scripts/bbref_pbp_parser.py <game.json> \"<player_name>\"")
        sys.exit(1)

    game_path = sys.argv[1]
    player_name = sys.argv[2]

    with open(game_path) as f:
        game = json.load(f)

    print(f"Game: {game['game_id']} — {game['teams']['away']} @ {game['teams']['home']}")
    print(f"Player: {player_name}")
    print()

    components = classify_bbref_game(game, player_name)
    if components is None:
        print(f"Player '{player_name}' not found in game.")
        sys.exit(1)

    pure_ts, total_poss, details = calculate_pure_ts(components)
    box = box_score_from_components(components)

    print(f"PS%: {pure_ts:.1%}")
    print(f"Scoring Possessions: {total_poss}")
    print(f"Box: {box['pts']} PTS, {box['fg_made']}/{box['fga']} FG, "
          f"{box['fg3_made']}/{box['fg3a']} 3P, {box['ft_made']}/{box['fta']} FT")
    print()

    W = 60
    print(f"{'Component':<8} {'Name':<28} {'Events':>6} {'PTS':>5} "
          f"{'Max':>5} {'Eff':>7}")
    print("-" * W)
    for cid in COMPONENTS:
        if cid not in details:
            continue
        d = details[cid]
        print(f"{cid:<8} {COMPONENTS[cid]['name']:<28} {d['events']:>6} "
              f"{d['pts']:>5} {d['max_pts']:>5} {d['eff']:>7.1%}")
    print("-" * W)
    total_pts = sum(d["pts"] for d in details.values())
    total_max = sum(d["max_pts"] for d in details.values())
    print(f"{'TOTAL':<8} {'':28} {total_poss:>6} {total_pts:>5} "
          f"{total_max:>5} {pure_ts:>7.1%}")


if __name__ == "__main__":
    main()
