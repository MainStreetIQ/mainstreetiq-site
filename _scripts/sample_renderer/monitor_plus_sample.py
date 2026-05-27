"""
Render the Monitor Plus sample PDF for the public site.

Generates a fictional Monitor Plus monthly briefing for "Three Acre Vineyards"
benchmarked against two fictional peer wineries. All names, URLs, and
findings are illustrative; this is published as a sample of the deliverable
structure on the public MSIQ Wine surface (no real wineries referenced).

Output: samples/monitor-plus-sample.pdf

Run from apps/msiq-site/:
  python _scripts/sample_renderer/monitor_plus_sample.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# --- MSIQ brand tokens (mirrors brand-book.md) ---
COLOR_MIDNIGHT = HexColor("#0F1C2E")
COLOR_NAVY = HexColor("#2B4E8C")
COLOR_SKY = HexColor("#5BB8FF")
COLOR_NEUTRAL = HexColor("#6B7480")
COLOR_BORDER = HexColor("#E5E2DC")
COLOR_ICE = HexColor("#FAFAF7")
COLOR_DARK_TEXT = HexColor("#1A1F2B")
COLOR_WHITE = HexColor("#FFFFFF")

# --- Page setup ---
PAGE_W, PAGE_H = letter
MARGIN_X = 0.85 * inch
MARGIN_Y = 0.85 * inch


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "sample_banner": ParagraphStyle(
            "sample_banner", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8, textColor=COLOR_WHITE,
            backColor=COLOR_NAVY, alignment=TA_CENTER, leading=14,
            borderPadding=4,
        ),
        "cover_eyebrow": ParagraphStyle(
            "cover_eyebrow", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, textColor=COLOR_SKY,
            spaceAfter=4, leading=14, alignment=TA_LEFT,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=28, textColor=COLOR_MIDNIGHT,
            leading=32, spaceAfter=8, alignment=TA_LEFT,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=14, textColor=COLOR_NEUTRAL,
            leading=18, spaceAfter=24, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=18, textColor=COLOR_MIDNIGHT,
            leading=22, spaceBefore=16, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=13, textColor=COLOR_NAVY,
            leading=18, spaceBefore=12, spaceAfter=4,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8, textColor=COLOR_SKY,
            leading=11, spaceBefore=8, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, textColor=COLOR_DARK_TEXT,
            leading=15, spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, textColor=COLOR_NEUTRAL,
            leading=11,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, textColor=COLOR_MIDNIGHT,
            leading=12,
        ),
    }


def header_footer(canvas, doc):
    """Branded header + footer on every content page."""
    canvas.saveState()
    # Top eyebrow strip
    canvas.setFillColor(COLOR_NAVY)
    canvas.rect(0, PAGE_H - 0.35 * inch, PAGE_W, 0.35 * inch, fill=1, stroke=0)
    canvas.setFillColor(COLOR_WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN_X, PAGE_H - 0.23 * inch, "MSIQ WINE — MONITOR PLUS SAMPLE")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        PAGE_W - MARGIN_X, PAGE_H - 0.23 * inch,
        "mainstreetiq.com  ·  Illustrative / fictional cohort",
    )
    # Bottom hairline + page number + sample marker
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, 0.55 * inch, PAGE_W - MARGIN_X, 0.55 * inch)
    canvas.setFillColor(COLOR_NEUTRAL)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN_X, 0.38 * inch, f"Page {doc.page}")
    canvas.drawRightString(
        PAGE_W - MARGIN_X, 0.38 * inch,
        "SAMPLE — illustrative content; fictional cohort. Not a real engagement.",
    )
    canvas.restoreState()


def section_label(text: str, styles: dict) -> Paragraph:
    return Paragraph(text.upper(), styles["eyebrow"])


def divider() -> Table:
    t = Table([[""]], colWidths=[PAGE_W - 2 * MARGIN_X], rowHeights=[1])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), COLOR_BORDER)]))
    return t


def build_story(styles: dict) -> list:
    story = []

    # --- COVER ---
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph(
        "&nbsp;&nbsp;SAMPLE DELIVERABLE &nbsp;·&nbsp; ILLUSTRATIVE CONTENT &nbsp;·&nbsp; "
        "FICTIONAL COHORT &nbsp;·&nbsp; NOT A REAL ENGAGEMENT&nbsp;&nbsp;",
        styles["sample_banner"],
    ))
    story.append(Spacer(1, 0.8 * inch))
    story.append(Paragraph("MSIQ WINE — MONITOR PLUS", styles["cover_eyebrow"]))
    story.append(Paragraph("Monthly Briefing", styles["cover_title"]))
    story.append(Paragraph(
        "Three Acre Vineyards — Sample, May 2026",
        styles["cover_subtitle"],
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "<b>What this is.</b> A representative sample of the monthly Monitor Plus "
        "briefing that subscribers receive. The focal winery, peer cohort, scores, "
        "and findings shown here are entirely fictional and used only to illustrate "
        "the deliverable's structure, depth, and analytical lens. Your actual "
        "briefing uses your real cohort, your real data, and your real positioning.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Prepared by</b> Scott Hess, MSIQ Wine (a practice of Main Street IQ).<br/>"
        "<b>Issue:</b> May 2026 (sample). <b>Cohort size:</b> 3 (focal + 2 peers).",
        styles["small"],
    ))

    story.append(PageBreak())

    # --- HEADLINE ---
    story.append(Spacer(1, 0.1 * inch))
    story.append(section_label("This month", styles))
    story.append(Paragraph("Where Three Acre stands", styles["h1"]))
    story.append(Paragraph(
        "Three Acre Vineyards moved up 1.7 points on the composite this month, "
        "to 62.4 of 100. The gain came from the AI visibility and review "
        "authority dimensions; the website performance dimension lost 0.3 points "
        "(slower mobile load time after the new tasting-room photography went "
        "live without compression). Peer cohort movement was mixed: one peer "
        "gained 0.8 points, the other lost 1.1.",
        styles["body"],
    ))
    story.append(Paragraph(
        "<b>Bottom line for this month:</b> the AI visibility work from April is "
        "paying back. The mobile regression is a small fix and is the top "
        "prioritized action this issue.",
        styles["body"],
    ))

    story.append(section_label("Composite movement", styles))
    move_data = [
        ["Winery", "Apr 2026", "May 2026", "Change", "Cohort rank"],
        ["Three Acre Vineyards (focal)", "60.7", "62.4", "+1.7", "1 of 3"],
        ["Pine Hollow Estate (peer)", "59.3", "60.1", "+0.8", "2 of 3"],
        ["Slate Run Cellars (peer)", "57.2", "56.1", "-1.1", "3 of 3"],
    ]
    move_table = Table(move_data, colWidths=[2.4 * inch, 0.95 * inch, 0.95 * inch, 0.95 * inch, 1.1 * inch])
    move_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MIDNIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), COLOR_DARK_TEXT),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_ICE, COLOR_WHITE]),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(move_table)
    story.append(Spacer(1, 0.15 * inch))

    # --- AI VISIBILITY ---
    story.append(section_label("AI visibility this month", styles))
    story.append(Paragraph("AI search mention rate by engine", styles["h2"]))
    story.append(Paragraph(
        "We probed 10 wine-buyer queries (\"Best Pinot Noir in Sta. Rita Hills,\" "
        "\"Santa Ynez Valley winery weekend recommendations,\" and similar) "
        "across ChatGPT, Claude, Perplexity, and Gemini with grounded web "
        "search, three samples per query. The table below shows brand mention "
        "rate (you appeared in the answer) and URL citation rate (your domain "
        "was cited as the source).",
        styles["body"],
    ))
    ai_data = [
        ["Winery", "Claude", "ChatGPT", "Perplexity", "Gemini", "Citation rate"],
        ["Three Acre Vineyards", "27%", "33%", "20%", "47%", "12%"],
        ["Pine Hollow Estate", "20%", "27%", "27%", "40%", "8%"],
        ["Slate Run Cellars", "13%", "13%", "20%", "33%", "5%"],
    ]
    ai_table = Table(ai_data, colWidths=[2.3 * inch, 0.85 * inch, 0.95 * inch, 1.05 * inch, 0.85 * inch, 1.1 * inch])
    ai_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MIDNIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), COLOR_DARK_TEXT),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_ICE, COLOR_WHITE]),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ai_table)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<b>What this means.</b> Three Acre is now the cohort leader on every "
        "engine. The biggest jump month-over-month was on ChatGPT (+13 points), "
        "driven by the new \"Sta. Rita Hills harvest 2025\" blog post published "
        "April 18. URL citation rate also moved up (+4 points), which means AI "
        "is starting to cite the source pages, not just paraphrase from memory.",
        styles["body"],
    ))

    story.append(PageBreak())

    # --- PRIORITIZED ACTIONS ---
    story.append(Spacer(1, 0.1 * inch))
    story.append(section_label("Three prioritized actions for May", styles))
    story.append(Paragraph("Actions, in order", styles["h1"]))

    actions = [
        (
            "Fix mobile LCP regression on the homepage",
            "The new tasting-room photography uploaded April 24 was not compressed; "
            "the hero image is now 2.1MB which pushed mobile LCP from 2.8s to 4.6s. "
            "Re-export the hero at WebP or AVIF, target under 250KB, add to picture "
            "element with srcset. ~30 minutes for the operator or web partner.",
            "High",
        ),
        (
            "Schedule three more Sta. Rita Hills authority posts",
            "The April 18 harvest post was the single biggest AI visibility lift "
            "this month. Three more in the same vein (vineyard practice, "
            "varietal-specific tasting notes, single-vineyard provenance) over the "
            "next six weeks will compound the gain through July. Topic outlines "
            "and target queries attached in the appendix.",
            "High",
        ),
        (
            "Reply to two of the three new Tripadvisor reviews from this month",
            "Both reviews are 4-star and constructive. A short, named reply within "
            "21 days lifts review-authority score and signals an engaged operator "
            "to both human and AI search systems. Slate Run Cellars is doing this "
            "consistently and pulled ahead on this dimension last quarter.",
            "Medium",
        ),
    ]
    for title, body, prio in actions:
        story.append(Paragraph(f"<b>{title}</b> &nbsp;·&nbsp; <font color='#5BB8FF'>{prio} priority</font>", styles["h2"]))
        story.append(Paragraph(body, styles["body"]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(divider())
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Closing note from Scott.</b> The April content investment is paying "
        "back this month exactly the way the AI engines reward it: through "
        "mention-rate gains, not citation-rate gains, in the first two months "
        "after publish. Citations will follow in months three to four if the "
        "pages stay linked from internal navigation and pick up at least one "
        "external link. Continue the cadence.",
        styles["body"],
    ))

    story.append(PageBreak())

    # --- WHAT'S IN A FULL MONITOR PLUS BRIEFING ---
    story.append(Spacer(1, 0.1 * inch))
    story.append(section_label("What a full briefing includes", styles))
    story.append(Paragraph("Sections in the full monthly briefing", styles["h1"]))
    story.append(Paragraph(
        "This sample shows the headline pages of a Monitor Plus deliverable. "
        "The full monthly briefing also includes the following sections, all "
        "tuned to your business and your cohort.",
        styles["body"],
    ))

    sections = [
        ("Peer movement detail", "Per-peer composite + dimension-by-dimension changes month over month. Names the operator gaining and losing ground."),
        ("AI visibility drift", "Per-query, per-engine appearance log. Catches a model swapping you out before it shows up in the aggregate."),
        ("Pricing drift", "Per-SKU price tracking across your cohort plus your wine club tiers. Flags peer price moves within 24 hours of publication."),
        ("Sentiment scan", "Tripadvisor, Yelp, Google Reviews, Instagram comments. Net sentiment delta with the top three positive and negative themes called out."),
        ("Visual asset inventory", "Hero, gallery, tasting-room, vineyard photography across your site and your cohort's. Flags stale assets and missing categories."),
        ("Three prioritized actions", "Two to four pages on the highest-leverage moves for the coming month, each scoped to operator-time or web-partner-time."),
        ("Quarterly synthesis (every third issue)", "A 3-month rollup that maps observed change against the prior quarter's prioritized actions. Closes the loop on what worked and what did not."),
    ]
    for title, body in sections:
        story.append(Paragraph(f"<b>{title}.</b> {body}", styles["body"]))

    story.append(Spacer(1, 0.25 * inch))
    story.append(divider())
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>About this sample.</b> This document is a publicly-published illustration "
        "of the MSIQ Wine Monitor Plus monthly deliverable. The focal winery "
        "(Three Acre Vineyards), peer cohort (Pine Hollow Estate, Slate Run "
        "Cellars), and all scores, queries, and recommendations shown are "
        "fictional. Any resemblance to real wineries is unintentional. The "
        "actual deliverable you receive uses your real business, your real "
        "cohort, and your real performance data; you own that data, and we "
        "never share your data outside of your engagement.",
        styles["small"],
    ))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        "Questions: scott@mainstreetiq.com  ·  Subscribe at "
        "https://www.mainstreetiq.com/wineries",
        styles["small"],
    ))

    return story


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent.parent / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "monitor-plus-sample.pdf"

    doc = BaseDocTemplate(
        str(out_path), pagesize=letter,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=0.6 * inch, bottomMargin=0.7 * inch,
        title="MSIQ Wine — Monitor Plus Sample",
        author="Main Street IQ",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        PAGE_W - 2 * doc.leftMargin, PAGE_H - doc.topMargin - doc.bottomMargin,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="content", frames=[frame], onPage=header_footer)])

    styles = make_styles()
    story = build_story(styles)
    doc.build(story)

    size_kb = out_path.stat().st_size // 1024
    print(f"Wrote {out_path} ({size_kb} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
