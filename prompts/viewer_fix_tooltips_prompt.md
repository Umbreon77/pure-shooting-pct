# Pure TS% Viewer — Tooltip Fixes

## What To Fix

Three issues with the CSS tooltips in `viewer/pure_ts_league_viewer.html`:

### 1. Position: Move Above, Not Below

All tooltips currently appear below the column headers. Move them above instead — they interfere with the actual data rows when below.

Update the CSS `::after` positioning to place tooltips above the element (e.g., `bottom: 100%` instead of `top: 100%`). Add a small gap so the tooltip doesn't touch the header. The little arrow/caret (if any) should point down toward the header.

### 2. Left-Edge Tooltips Getting Cut Off

Tooltips on the far-left columns (Rank, Player) extend beyond the left edge of the viewport and the text gets cut off. Fix by detecting or styling so that left-side tooltips are left-aligned (tooltip's left edge aligns with the element's left edge) rather than centered.

### 3. Right-Edge Tooltips Getting Cut Off

Same issue on the far-right columns (Std TS%, Delta) — tooltips extend beyond the right edge of the viewport. Fix by right-aligning those tooltips (tooltip's right edge aligns with the element's right edge).

### Implementation Approach

A clean way to handle this: add a `data-tooltip-align` attribute (left, center, right) to headers based on their position, and style each alignment differently in CSS. Or use a smarter CSS approach that keeps all tooltips within the viewport regardless of column position.

This should be a CSS-only fix — no JavaScript needed for tooltip positioning.

### Validation

- Hover over every column header on every tab
- All tooltips should appear above the header
- Far-left tooltips should be fully visible (not cut off on the left)
- Far-right tooltips should be fully visible (not cut off on the right)
- Middle tooltips should be centered as they are now

Rebuild with `python viewer/build_viewer.py` after changes.
