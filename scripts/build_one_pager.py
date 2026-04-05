#!/usr/bin/env python3
"""
Build PS% One-Pager PDF.

Usage:
    python3 scripts/build_one_pager.py
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "pure_ts_one_pager.pdf")

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BLACK = HexColor("#1a1a1a")
DARK_GRAY = HexColor("#333333")
MID_GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#e8e8e8")
ACCENT = HexColor("#1a5276")
WHITE = HexColor("#ffffff")
ROW_ALT = HexColor("#f5f7fa")
GREEN_CHECK = HexColor("#1a7a3a")
RED_X = HexColor("#a93226")

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
title_style = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=15, leading=18,
    textColor=ACCENT, alignment=TA_CENTER, spaceAfter=0,
)
subtitle_style = ParagraphStyle(
    "Subtitle", fontName="Helvetica-Bold", fontSize=9, leading=11,
    textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=3,
)
section_style = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=11, leading=13,
    textColor=ACCENT, spaceBefore=4, spaceAfter=1, alignment=TA_CENTER,
)
body_style = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=8.5, leading=11,
    textColor=DARK_GRAY, spaceAfter=2,
)
formula_style = ParagraphStyle(
    "Formula", fontName="Helvetica-Bold", fontSize=16, leading=19,
    textColor=BLACK, alignment=TA_CENTER, spaceBefore=2, spaceAfter=1,
)
formula_sub_style = ParagraphStyle(
    "FormulaSub", fontName="Helvetica", fontSize=8.5, leading=11,
    textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=1,
)
footer_style = ParagraphStyle(
    "Footer", fontName="Helvetica", fontSize=7, leading=9,
    textColor=MID_GRAY, alignment=TA_CENTER, spaceBefore=2,
)

# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------
TH_STYLE = ParagraphStyle(
    "TH", fontName="Helvetica-Bold", fontSize=8, leading=10.5,
    textColor=WHITE, alignment=TA_CENTER,
)
TD_STYLE = ParagraphStyle(
    "TD", fontName="Helvetica", fontSize=8, leading=10.5,
    textColor=DARK_GRAY, alignment=TA_CENTER,
)
TD_LEFT = ParagraphStyle(
    "TDL", fontName="Helvetica", fontSize=8, leading=10.5,
    textColor=DARK_GRAY, alignment=TA_LEFT,
)
TD_BOLD = ParagraphStyle(
    "TDB", fontName="Helvetica-Bold", fontSize=8, leading=10.5,
    textColor=DARK_GRAY, alignment=TA_CENTER,
)


def th(text):
    return Paragraph(text, TH_STYLE)

def td(text, bold=False, left=False):
    s = TD_BOLD if bold else (TD_LEFT if left else TD_STYLE)
    return Paragraph(str(text), s)


def styled_table(header, rows, col_widths=None):
    data = [[th(h) for h in header]]
    for row in rows:
        data.append(row)

    t = Table(data, colWidths=col_widths, hAlign="CENTER")

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    # Alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build():
    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=letter,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
        topMargin=0.35 * inch, bottomMargin=0.2 * inch,
    )

    # Callout style for the key claim
    callout_style = ParagraphStyle(
        "Callout", fontName="Helvetica-Bold", fontSize=10, leading=13,
        textColor=ACCENT, alignment=TA_CENTER, spaceBefore=2, spaceAfter=2,
    )

    story = []

    # --- 1. Title ---
    story.append(Paragraph("Pure Shooting %: Fixing Basketball's Most-Used Efficiency Stat", title_style))
    story.append(Paragraph(
        "Four box score numbers. No approximations. A true 0-100% scale.", subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=0.8, color=LIGHT_GRAY, spaceAfter=2))

    # --- 2. The Problem ---
    story.append(Paragraph("The Problem", section_style))
    story.append(Paragraph(
        "Shooting efficiency measures one thing: of all the points a player could have scored, how "
        "many did they actually score? Basketball has three ways to score \u2014 2-point field goals, "
        "3-point field goals, and free throws \u2014 and True Shooting Percentage (TS%) is the NBA's "
        "standard attempt to combine all three into a single number. But the formula has a structural "
        "flaw. Its denominator treats every field goal attempt as worth a maximum of 2 points. A "
        "3-pointer is worth 3. This means a player who makes every single 3-point attempt gets a TS% "
        "of 150% \u2014 not 100%. A player who makes every 2-point attempt gets 100%. Both shot perfectly.",
        body_style
    ))

    perfect_table = styled_table(
        ["Scenario", "PTS", "FGA", "FTA", "TS%", "PS%"],
        [
            [td("10/10 on 2-pointers"), td("20"), td("10"), td("0"), td("100.0%"), td("100.0%", bold=True)],
            [td("10/10 on 3-pointers"), td("30"), td("10"), td("0"), td("150.0%"), td("100.0%", bold=True)],
            [td("10/10 on free throws"), td("10"), td("0"), td("10"), td("113.6%"), td("100.0%", bold=True)],
        ],
        col_widths=[1.5 * inch, 0.6 * inch, 0.6 * inch, 0.6 * inch, 0.7 * inch, 0.7 * inch],
    )
    story.append(perfect_table)
    story.append(Paragraph(
        "All three players scored every possible point. Pure Shooting % (PS%) gives all three 100%. "
        "TS% ranges from 100% to 150% depending on shot type.",
        body_style
    ))

    # --- 3. The Fix ---
    story.append(Paragraph("The Fix", section_style))
    story.append(Paragraph("PS% = PTS / (2 x FGA + 3PA + FTA)", formula_style))
    story.append(Paragraph(
        "Points scored divided by maximum points possible. The denominator accounts for the actual "
        "maximum value of each attempt: 2 per 2PT, 3 per 3PT, 1 per FT. "
        "The full derivation uses only the identity 2PA = FGA - 3PA.",
        formula_sub_style
    ))

    # --- 4. 47 Seasons of Distortion ---
    story.append(Paragraph("47 Seasons of Distortion", section_style))
    evidence_table = styled_table(
        ["Season", "League 3PA Rate", "PS%", "TS%", "Delta"],
        [
            [td("2025-26"), td("41.6%"), td("48.3%", bold=True), td("58.0%"), td("-9.7pp")],
            [td("2024-25"), td("41.8%"), td("48.1%", bold=True), td("57.8%"), td("-9.7pp")],
            [td("2015-16"), td("28.5%"), td("49.2%", bold=True), td("55.9%"), td("-6.7pp")],
            [td("2005-06"), td("21.4%"), td("49.3%", bold=True), td("54.4%"), td("-5.1pp")],
            [td("1996-97"), td("22.2%"), td("48.2%", bold=True), td("53.5%"), td("-5.3pp")],
            [td("1989-90"), td("10.4%"), td("49.2%", bold=True), td("51.8%"), td("-2.6pp")],
            [td("1979-80"), td("3.1%"), td("49.6%", bold=True), td("51.1%"), td("-1.5pp")],
        ],
        col_widths=[0.9 * inch, 1.1 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch],
    )
    story.append(evidence_table)
    story.append(Paragraph(
        "The distortion grew from -1.5pp to -9.7pp as the league 3PA rate rose from 3% to 42%. "
        "3PA rate explains 99.86% of the variance (R² = 0.9986).",
        body_style
    ))

    # --- 5. Distortion Across Eras ---
    story.append(Paragraph("Distortion Across Eras", section_style))
    player_table = styled_table(
        ["Player", "Season", "3PA Rate", "TS%", "PS%", "Distortion"],
        [
            [td("Kareem Abdul-Jabbar", left=True), td("1979-80"), td("0.1%"), td("63.9%"), td("62.7%", bold=True), td("+1.1pp")],
            [td("Michael Jordan", left=True), td("1990-91"), td("5.1%"), td("60.5%"), td("58.1%", bold=True), td("+2.4pp")],
            [td("Shaquille O'Neal", left=True), td("1999-00"), td("0.1%"), td("57.8%"), td("56.4%", bold=True), td("+1.4pp")],
            [td("Ray Allen", left=True), td("2001-02"), td("46.0%"), td("59.8%"), td("49.0%", bold=True), td("+10.9pp")],
            [td("Kobe Bryant", left=True), td("2005-06"), td("23.8%"), td("55.9%"), td("49.8%", bold=True), td("+6.1pp")],
            [td("LeBron James", left=True), td("2012-13"), td("18.8%"), td("64.0%"), td("58.2%", bold=True), td("+5.8pp")],
            [td("Steph Curry", left=True), td("2015-16"), td("55.4%"), td("66.9%"), td("53.0%", bold=True), td("+13.9pp")],
            [td("James Harden", left=True), td("2018-19"), td("53.9%"), td("61.6%"), td("49.4%", bold=True), td("+12.2pp")],
            [td("Nikola Jokic", left=True), td("2023-24"), td("16.3%"), td("65.1%"), td("59.7%", bold=True), td("+5.3pp")],
            [td("Shai Gilgeous-Alexander", left=True), td("2025-26"), td("22.5%"), td("66.8%"), td("59.8%", bold=True), td("+7.0pp")],
        ],
        col_widths=[1.55 * inch, 0.7 * inch, 0.7 * inch, 0.6 * inch, 0.75 * inch, 0.85 * inch],
    )
    story.append(player_table)
    story.append(Paragraph(
        "Rim scorers (Kareem, Shaq) are barely affected. High-volume 3-point shooters (Curry, Harden) "
        "are overrated by 10+ percentage points. The distortion is a direct function of 3PA rate.",
        body_style
    ))

    # --- 6. Closing callout ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceBefore=1, spaceAfter=1))
    story.append(Paragraph(
        "At the current league 3PA rate of ~42%, the average distortion is 9.7 percentage points. "
        "If the league reaches 50%, it will exceed 11. The gap is not stabilizing. It is growing.",
        callout_style
    ))

    # --- 7. Closing line ---
    story.append(Paragraph(
        "TS% is not bounded at 100%, cannot be compared across archetypes or eras, and is not a "
        "true percentage. PS% eliminates these problems with a simpler formula and a true 0-100% scale.",
        body_style
    ))

    # --- 8. Footer ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceBefore=1, spaceAfter=1))
    story.append(Paragraph(
        "PS% data available for all NBA players, 47 regular seasons + 46 playoff seasons (1979-80 through 2025-26)",
        footer_style
    ))

    doc.build(story)
    print(f"Written: {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    build()
