#!/usr/bin/env python3
"""
import_wcir.py — turn an approved WCIR report build into an unlisted site page.

    python _scripts/import_wcir.py <source.md> <slug>
    python _scripts/import_wcir.py "~/WCI/.../Main Street IQ Central Coast Wine Country Report - Q3 2026.md" q3-2026-central-coast

Writes _content/wcir/<slug>.html. Then run `python _scripts/sitegen.py build`
to render wcir/<slug>.html (sitegen owns the head atoms and the nav; the wine
footer is literal here because the shared footer template cannot express it).

THE RULE. Every figure on the page comes from the source markdown, which WCI's
build.py renders from the same composed blocks as the PDF. Nothing here types a
number. If a figure looks wrong, the fix belongs in WCI, not in this script and
not in the output.

STRICT. The converter knows the markdown subset WCI emits (headings, paragraphs,
blockquotes, pipe tables, ordered and bulleted lists, <small> fine print). A
line it does not recognise is an error, never a guess, so a change in the WCI
renderer surfaces here instead of shipping as mangled HTML.

DETERMINISTIC. The output depends only on the source text and the slug: no
clock, no environment. Running it twice produces identical bytes.

The page is UNLISTED: noindex, not in sitemap.xml or llms.txt, linked from no
other page. See the msiq-site operating doc, "WCIR quarterly delivery pages".
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Cover lines that only make sense on the printed page.
COVER_LINES = {"MAIN STREET IQ", "Wine Country Intelligence"}
# The build hash: a print footer line (to 2026-10-09 10:33) or an HTML comment (from 10:58).
RE_BUILD_LINE = re.compile(r"^<small>.*\bbuild ([0-9a-f]{6,})</small>$")
RE_BUILD_COMMENT = re.compile(r"^<!-- build ([0-9a-f]{6,}) -->$")
# The print running footer ("mainstreetiq.com | ... | Q3 2026"): print-only, dropped.
RE_PRINT_FOOTER = re.compile(r"^<small>mainstreetiq\.com \|.*</small>$")
# Print-only cross references. None exist today; if one appears, stop.
RE_PRINT_REF = re.compile(r"\bsee page \d+|\bpage \d+ of\b|\bon page \d+", re.I)

RE_H = re.compile(r"^(#{1,6}) (.+)$")
RE_OL = re.compile(r"^(\d+)\. (.+)$")
RE_SMALL = re.compile(r"^<small>(.+)</small>$")

RE_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
RE_EMAIL = re.compile(r"(?<![\w.+-])([\w.+-]+@[\w-]+(?:\.[\w-]+)+)")
RE_SITE = re.compile(r"(?<![\w/@.])((?:www\.)?(?:mainstreetiq|calendly)\.com(?:/[\w\-/]*\w)?)")
RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
RE_ITAL = re.compile(r"(?<![\w*])_(?=\S)(.+?)(?<=\S)_(?!\w)")


class ImportError_(Exception):
    pass


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def attr(text: str) -> str:
    return html.escape(text, quote=True)


def web_url(url: str) -> str:
    # The report's links are tagged for the PDF; on the page they are web clicks.
    return url.replace("utm_medium=pdf", "utm_medium=web")


def inline(text: str) -> str:
    """Markdown inline -> HTML. Links and autolinks are parked as placeholders
    first so the emphasis passes never see the underscores inside a URL."""
    parked: list[str] = []

    def park(s: str) -> str:
        parked.append(s)
        return f"\x00{len(parked) - 1}\x00"

    out = RE_MD_LINK.sub(
        lambda m: park(f'<a href="{attr(web_url(m.group(2)))}">{esc(m.group(1))}</a>'), text)
    out = RE_EMAIL.sub(lambda m: park(f'<a href="mailto:{m.group(1)}">{esc(m.group(1))}</a>'), out)

    def site(m: re.Match) -> str:
        host_path = m.group(1)
        href = "https://" + (host_path if host_path.startswith("www.") or host_path.startswith("calendly")
                             else "www." + host_path)
        return park(f'<a href="{attr(href)}">{esc(host_path)}</a>')

    out = RE_SITE.sub(site, out)
    out = esc(out)
    out = RE_BOLD.sub(r"<strong>\1</strong>", out)
    out = RE_ITAL.sub(r"<em>\1</em>", out)
    if "**" in out:
        raise ImportError_(f"unbalanced bold: {text!r}")
    return re.sub(r"\x00(\d+)\x00", lambda m: parked[int(m.group(1))], out)


def slugify(text: str, seen: dict) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60].strip("-") or "section"
    n = seen.get(s, 0)
    seen[s] = n + 1
    return s if n == 0 else f"{s}-{n + 1}"


def plain(text: str) -> str:
    """Heading text without markdown markers, for ids and labels."""
    return re.sub(r"[*_]", "", text)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_cover(lines: list[str]) -> dict:
    cover = {}
    for line in lines:
        s = line.strip()
        if not s or s in COVER_LINES:
            continue
        m = RE_H.match(s)
        if m and len(m.group(1)) == 1 and "title" not in cover:
            cover["title"] = m.group(2)
        elif m and len(m.group(1)) == 2 and "subtitle" not in cover:
            cover["subtitle"] = m.group(2)
        elif "Edition" in s and "edition" not in cover:
            cover["edition"] = s
        elif s.startswith("_") and s.endswith("_") and "byline" not in cover:
            cover["byline"] = s
        else:
            raise ImportError_(f"unrecognised cover line: {s!r}")
    for k in ("title", "subtitle", "edition", "byline"):
        if k not in cover:
            raise ImportError_(f"cover is missing its {k}")
    m = re.match(r"(Q[1-4] \d{4}) Edition \| (.+)$", cover["edition"])
    if not m:
        raise ImportError_(f"edition line not in the expected shape: {cover['edition']!r}")
    cover["quarter"], cover["count_phrase"] = m.group(1), m.group(2)
    return cover


def is_block_start(s: str) -> bool:
    return bool(RE_H.match(s) or s.startswith(">") or s.startswith("|") or s.startswith("- ")
                or RE_OL.match(s) or RE_SMALL.match(s) or s == "---")


def parse_table(rows: list[str]) -> dict:
    def cells(row: str) -> list[str]:
        if not (row.startswith("|") and row.endswith("|")):
            raise ImportError_(f"table row not pipe-delimited: {row!r}")
        return [c.strip() for c in row[1:-1].split("|")]

    if len(rows) < 3:
        raise ImportError_("table has no body")
    head, sep, body = cells(rows[0]), cells(rows[1]), [cells(r) for r in rows[2:]]
    align = []
    for c in sep:
        if not re.fullmatch(r":?-{3,}:?", c):
            raise ImportError_(f"bad table separator: {rows[1]!r}")
        align.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "")
    for r in body:
        if len(r) != len(head):
            raise ImportError_(f"table row has {len(r)} cells, header has {len(head)}")
    return {"type": "table", "head": head, "align": align, "body": body}


def parse_body(lines: list[str]) -> tuple[list[dict], str | None]:
    blocks: list[dict] = []
    build = None
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].rstrip("\n")
        st = s.strip()
        if not st or st == "---":
            i += 1
            continue
        if RE_PRINT_REF.search(st):
            raise ImportError_(f"print-only page reference needs a rule: {st!r}")
        m = RE_H.match(st)
        if m:
            level = len(m.group(1))
            if level not in (2, 3):
                raise ImportError_(f"unexpected heading level {level}: {st!r}")
            blocks.append({"type": f"h{level}", "text": m.group(2)})
            i += 1
            continue
        mb = RE_BUILD_LINE.match(st) or RE_BUILD_COMMENT.match(st)
        if mb:
            build = mb.group(1)
            i += 1
            continue
        if RE_PRINT_FOOTER.match(st):
            i += 1
            continue
        ms = RE_SMALL.match(st)
        if ms:
            blocks.append({"type": "small", "text": ms.group(1)})
            i += 1
            continue
        if st.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({"type": "quote", "text": " ".join(buf)})
            continue
        if st.startswith("|"):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i].strip())
                i += 1
            blocks.append(parse_table(buf))
            continue
        if st.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            blocks.append({"type": "ul", "items": items})
            continue
        if RE_OL.match(st):
            items = []
            while i < n:
                mo = RE_OL.match(lines[i].strip())
                if not mo:
                    break
                if int(mo.group(1)) != len(items) + 1:
                    raise ImportError_(f"ordered list numbering breaks at {lines[i]!r}")
                items.append(mo.group(2))
                i += 1
                # Items may be separated by one blank line; keep going if the next is an item.
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and RE_OL.match(lines[j].strip()):
                    i = j
            blocks.append({"type": "ol", "items": items})
            continue
        if st.startswith(("<", "#", "* ", "![", "```")):
            raise ImportError_(f"unrecognised construct: {st!r}")
        # Paragraph: consecutive plain lines. A line ending in two spaces is a hard break.
        buf = []
        while i < n and lines[i].strip() and not is_block_start(lines[i].strip()):
            buf.append(lines[i].rstrip("\n"))
            i += 1
        blocks.append({"type": "p", "lines": buf})
    return blocks, build


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_blocks(blocks: list[dict]) -> tuple[str, list[tuple[str, str]]]:
    seen: dict = {}
    toc: list[tuple[str, str]] = []
    out: list[str] = []
    label = "Table"
    for b in blocks:
        t = b["type"]
        if t in ("h2", "h3"):
            hid = slugify(plain(b["text"]), seen)
            label = plain(b["text"])
            if t == "h2":
                toc.append((hid, plain(b["text"])))
            out.append(f'<{t} id="{hid}">{inline(b["text"])}</{t}>')
        elif t == "p":
            parts = []
            for k, line in enumerate(b["lines"]):
                hard = line.endswith("  ") and k < len(b["lines"]) - 1
                parts.append(inline(line.strip()) + ("<br>" if hard else ""))
            text = "\n".join(parts)
            whole = " ".join(l.strip() for l in b["lines"])
            if whole.startswith("_") and whole.endswith("_"):
                out.append(f'<p class="wcir-note">{text}</p>')
            elif re.fullmatch(r"\*\*[^*]+\*\*", whole):
                out.append(f'<p class="wcir-table-title">{text}</p>')
                label = plain(whole)
            else:
                out.append(f"<p>{text}</p>")
        elif t == "quote":
            out.append(f'<blockquote class="wcir-callout"><p>{inline(b["text"])}</p></blockquote>')
        elif t == "small":
            out.append(f'<p class="wcir-fine">{inline(b["text"])}</p>')
        elif t in ("ul", "ol"):
            items = "\n".join(f"  <li>{inline(x)}</li>" for x in b["items"])
            out.append(f"<{t}>\n{items}\n</{t}>")
        elif t == "table":
            def cell(tag: str, text: str, a: str) -> str:
                style = f' class="num"' if a == "right" else (' class="ctr"' if a == "center" else "")
                return f"<{tag}{style}>{inline(text)}</{tag}>"
            head = "".join(cell("th", c, a) for c, a in zip(b["head"], b["align"]))
            rows = "\n".join("      <tr>" + "".join(cell("td", c, a) for c, a in zip(r, b["align"])) + "</tr>"
                             for r in b["body"])
            out.append(f'<div class="wcir-table-wrap" role="region" tabindex="0" aria-label="{attr(label)}">\n'
                       f'  <table>\n    <thead><tr>{head}</tr></thead>\n    <tbody>\n{rows}\n    </tbody>\n'
                       f'  </table>\n</div>')
        else:
            raise ImportError_(f"no renderer for block {t}")
    body = "\n".join("          " + line if line else line
                     for chunk in out for line in chunk.split("\n"))
    return body, toc


PAGE_CSS = """  <style>
    /* WCIR report pages (_scripts/import_wcir.py). Scoped here, not in styles.css. */
    .wcir-hero-meta { color: rgba(255,255,255,0.75); font-size: 1rem; margin-top: 0.75rem; }
    .wcir-hero-meta a { color: var(--color-sky); }
    .wcir-pdf { margin-top: 1.25rem; font-size: 0.95rem; }
    .wcir-pdf a { color: var(--color-white); text-decoration: underline; text-underline-offset: 3px; }
    .wcir-toc { max-width: 820px; border: 1px solid var(--color-border); border-radius: 6px; padding: 1.25rem 1.5rem; margin-bottom: 2.5rem; }
    .wcir-toc h2 { font-size: 1rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-navy); margin: 0 0 0.75rem; }
    .wcir-toc ol { margin: 0; padding-left: 1.25rem; columns: 2; column-gap: 2rem; }
    .wcir-toc li { margin: 0.25rem 0; break-inside: avoid; }
    .wcir-toc a { color: var(--color-navy); }
    .wcir-report { max-width: 820px; color: var(--color-dark-text); }
    .wcir-report h2 { margin: 3.5rem 0 1rem; color: var(--color-dark-text); scroll-margin-top: 96px; }
    .wcir-report h3 { margin: 2rem 0 0.75rem; scroll-margin-top: 96px; }
    .wcir-report p, .wcir-report li { line-height: 1.7; margin-bottom: 1rem; }
    .wcir-report ol, .wcir-report ul { padding-left: 1.5rem; margin-bottom: 1.25rem; }
    .wcir-report a { color: var(--color-navy); overflow-wrap: anywhere; }
    .wcir-callout { border-left: 3px solid var(--color-navy); background: var(--color-ice); padding: 1rem 1.25rem; margin: 1.5rem 0; }
    .wcir-callout p { margin: 0; }
    .wcir-note, .wcir-fine { font-size: 0.875rem; color: var(--color-neutral); }
    .wcir-table-title { margin: 1.5rem 0 0.25rem; }
    .wcir-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 1rem 0 1.25rem; border: 1px solid var(--color-border); border-radius: 6px; }
    .wcir-table-wrap:focus-visible { outline: 2px solid var(--color-navy); outline-offset: 2px; }
    .wcir-table-wrap table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
    .wcir-table-wrap th, .wcir-table-wrap td { padding: 0.55rem 0.8rem; text-align: left; border-bottom: 1px solid var(--color-border); vertical-align: top; }
    .wcir-table-wrap th { background: var(--color-ice); font-weight: 600; color: var(--color-dark-text); white-space: nowrap; }
    .wcir-table-wrap tbody tr:last-child td { border-bottom: 0; }
    .wcir-table-wrap .num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .wcir-table-wrap .ctr { text-align: center; }
    .wcir-options { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr)); gap: 1.25rem; margin-top: 1.5rem; }
    .wcir-option { position: relative; background: var(--color-white); border: 1px solid var(--color-border); border-top: 3px solid var(--color-navy); border-radius: 6px; padding: 1.5rem 1.25rem 1.25rem; display: flex; flex-direction: column; }
    .wcir-option-featured { border-color: var(--color-navy); }
    .wcir-option-badge { position: absolute; top: -0.8rem; left: 1.25rem; background: var(--color-navy); color: var(--color-white); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; padding: 0.2rem 0.6rem; border-radius: 4px; }
    .wcir-option h3 { font-size: 1.2rem; margin: 0 0 0.35rem; color: var(--color-dark-text); }
    .wcir-option-price { font-weight: 600; color: var(--color-navy); margin: 0 0 0.75rem; }
    .wcir-option p { line-height: 1.6; }
    .wcir-option-buy { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: auto; padding-top: 0.75rem; }
    .wcir-option-buy .btn { font-size: 0.9rem; }
    .wcir-option-detail { margin: 0.75rem 0 0; font-size: 0.9rem; }
    .wcir-option-detail a, .wcir-options-terms a { color: var(--color-navy); text-decoration: underline; text-underline-offset: 2px; }
    .wcir-options-terms { max-width: 820px; margin-top: 1.5rem; font-size: 1rem; line-height: 1.6; color: var(--color-dark-text); font-weight: 500; }
    .wcir-subscribe { max-width: 640px; }
    .wcir-subscribe form { display: grid; gap: 0.75rem; margin-top: 1.25rem; }
    .wcir-subscribe [hidden] { display: none; }
    .wcir-subscribe a { color: var(--color-navy); text-decoration: underline; text-underline-offset: 2px; }
    .wcir-subscribe label { font-size: 0.9rem; font-weight: 500; color: var(--color-dark-text); }
    .wcir-subscribe input[type="email"], .wcir-subscribe input[type="text"] { width: 100%; padding: 0.7rem 0.85rem; border: 1px solid var(--color-border); border-radius: 6px; font: inherit; }
    .wcir-subscribe .wcir-honeypot { position: absolute; left: -9999px; }
    .wcir-subscribe-msg { font-size: 0.9rem; min-height: 1.2em; }
    .wcir-subscribe-msg.ok { color: var(--color-success); }
    .wcir-subscribe-msg.err { color: var(--color-error); }
    @media (max-width: 640px) { .wcir-toc ol { columns: 1; } .wcir-table-wrap table { font-size: 0.875rem; } }
  </style>"""

# "Choose your option" cards (spec amendment 2026-10-09). Page copy, not report
# copy: each card's wording is ONE entry here, then re-run the importer.
# Prices: canonical-facts.md § Discover and § Monitor (public prices allowed for
# wine Discover, Monitor and Monitor Plus only). Links: Payment Link URLs from
# ~/MSIQ/infra/stripe-bootstrap/stripe-bootstrap-manifest-live.json, no UTMs.
# Monitor / Monitor Plus wording follows the gated /wineries subscribe block.
# "{quarter}" is filled from the report cover.
OPTIONS = [
    {"title": "County edition, annual", "badge": "Recommended",
     "body": "The county report every quarter plus the Wine Pricing Report twice a year, for Santa Barbara County or San Luis Obispo County, with every winery ranked. You choose the county at checkout.",
     "price": "$800/yr per county",
     "buy": [("County edition, annual", "https://buy.stripe.com/00w4gA1ib19q8H8duRa3u01", "wine-wcir-county-annual")],
     "detail": "#subscribe-county"},
    {"title": "County edition, one issue", "badge": None,
     "body": "The {quarter} county report for one county, one time. Single issues are not discounted. You'll confirm your county after checkout.",
     "price": "$250 per county",
     "buy": [("County edition, one issue", "https://buy.stripe.com/dRm5kE9OHcS8bTkbmJa3u16", "wine-wcir-county-single")],
     "detail": "#subscribe-county"},
    {"title": "Monitor", "badge": None,
     "body": "The monthly report card for your own winery. The annual plan includes the county edition for the one county you choose: the county report every quarter plus the Wine Pricing Report twice a year.",
     "price": "$400/mo, or $4,000/yr",
     "buy": [("Monitor, annual", "https://buy.stripe.com/8x2bJ21ib7xO2iKcqNa3u0W", "wine-monitor-annual"),
             ("Monitor, monthly", "https://buy.stripe.com/7sY8wQ5yr05m5uW1M9a3u05", "wine-monitor-monthly")],
     "detail": "#subscribe-monitor"},
    {"title": "Monitor Plus", "badge": None,
     "body": "The same report card with four peers you name, tracked beside you. Each extra peer beyond the four is $50/mo, or $500/yr on the annual plan. The annual plan includes the county edition for the one county you choose: the county report every quarter plus the Wine Pricing Report twice a year.",
     "price": "$600/mo, or $6,000/yr",
     "buy": [("Monitor Plus, annual", "https://buy.stripe.com/6oUcN6d0T7xOe1saiFa3u08", "wine-monitor-plus-annual"),
             ("Monitor Plus, monthly", "https://buy.stripe.com/aFa9AUe4X2du3mO76ta3u07", "wine-monitor-plus-monthly")],
     "detail": "#subscribe-monitor-plus"},
]

# Renewal and cancellation line, exactly as /wineries states it beside its Payment
# Links (canonical-facts 2026-08-13 ruling 4: a Payment Link buyer sees no other
# disclosure before paying).
RENEWAL_LINE = ('Subscriptions bought online renew until canceled; cancel online anytime, effective at the end of your current '
                'paid period. Annual plans run a 12-month initial term, and prices are subject to a standard annual '
                'adjustment of up to 10% at renewal, with at least 30 days notice. See '
                '<a href="/legal/subscription-terms">Subscription Terms</a> and '
                '<a href="/legal/refund-cancellation">Refunds</a>.')


# Second county (Scott, 2026-10-09, canonical-facts § Discover): 25% off, invoiced, no Payment Link.
SECOND_COUNTY_LINE = ('Adding a second county? A second county edition, annual, is 25% off: $600/yr instead of $800, '
                      'including when your first county comes with a Monitor or Monitor Plus annual plan, and it stays '
                      '25% off as long as you keep both counties. The second county is invoiced: we send a renewal invoice '
                      'before each term, it renews when paid, and you cancel by replying. To set it up, write to '
                      '<a href="mailto:scott@mainstreetiq.com?subject=Second%20county">scott@mainstreetiq.com</a>.')


def render_options(quarter: str) -> str:
    cards = []
    for o in OPTIONS:
        badge = f'\n            <span class="wcir-option-badge">{esc(o["badge"])}</span>' if o["badge"] else ""
        buttons = "".join(
            f'<a href="{attr(url)}" target="_blank" rel="noopener" class="btn {"btn-primary" if k == 0 else "btn-secondary"}" '
            f'data-stripe-product="{prod}" data-vertical="wine">{esc(label)} &rarr;</a>'
            for k, (label, url, prod) in enumerate(o["buy"]))
        cards.append(f"""          <div class="wcir-option{' wcir-option-featured' if o['badge'] else ''}">{badge}
            <h3>{esc(o['title'])}</h3>
            <p class="wcir-option-price">{esc(o['price'])}</p>
            <p>{esc(o['body'].replace('{quarter}', quarter))}</p>
            <p class="wcir-option-buy">{buttons}</p>
            <p class="wcir-option-detail"><a href="/wineries{o['detail']}" data-vertical="wine">What this includes &rarr;</a></p>
          </div>""")
    return "\n".join(cards)


# Wine-scoped footer, modelled on wcir/q2-2026-central-coast.html (BESPOKE in
# footer_sweep.py and sitegen.py). Tagline per canonical-facts 2026-10-02.
WINE_FOOTER = """  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="/" class="logo"><img src="/assets/logos/logo-horizontal-dark.svg" alt="Main Street IQ"></a>
          <p>Financial IQ for lower middle market companies. Veteran-owned and operated.</p>
        </div>
        <div class="footer-col">
          <h4>Company</h4>
          <a href="/about">About</a>
          <a href="/our-services">Services</a>
          <a href="/interim-finance-leadership">Interim Leadership</a>
          <a href="/our-work">Our Work</a>
          <a href="/blog/">Blog</a>
        </div>
        <div class="footer-col">
          <h4>Connect</h4>
          <a href="/contact">Contact</a>
          <a href="/intro-call">Book an Intro Call</a>
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener">LinkedIn</a>
        </div>
        <div class="footer-col">
          <h4>Wine</h4>
          <a href="/wineries">Winery practice</a>
          <a href="/wine-country-intelligence">The report</a>
          <a href="/winery-visibility-snapshot">Free visibility snapshot</a>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <a href="/legal/privacy">Privacy</a>
          <a href="/legal/terms">Terms of Use</a>
          <a href="/trust">Trust Center</a>
          <a href="/legal/ai-use">AI Use</a>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 Main Street IQ. All rights reserved.</span>
        <div class="footer-social">
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener" aria-label="LinkedIn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" role="img" aria-label="LinkedIn"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          </a>
        </div>
      </div>
    </div>
  </footer>"""


def render_page(cover: dict, body: str, toc: list, slug: str, source_name: str, build: str | None) -> str:
    q, title = cover["quarter"], cover["title"]
    count = cover["count_phrase"][0].upper() + cover["count_phrase"][1:]
    desc = f"{title}, {q} edition: {cover['count_phrase'].lower()} across {cover['subtitle']}."
    pdf = f"/reports/wcir-{slug}.pdf"
    toc_items = "\n".join(f'              <li><a href="#{hid}">{esc(text)}</a></li>' for hid, text in toc)
    subject = f"Send me the next {title}"
    mailto = "mailto:wci@mainstreetiq.com?subject=" + subject.replace(" ", "%20")
    provenance = f"{source_name}" + (f", build {build}" if build else "")
    return f"""<!--sitegen:params
{{
  "assets": "/assets/",
  "styles": "/styles.css",
  "nav": {{
    "logo": "/assets/logos/logo-horizontal-light.svg"
  }}
}}
-->
<!DOCTYPE html>
<html lang="en">
<head>
{{{{meta_base}}}}
  <title>{esc(title)} | {q} | Main Street IQ</title>

  <!-- UNLISTED DELIVERY PAGE. Do NOT add this URL to sitemap.xml, llms.txt, or any
       nav/footer/body link on any other page. The only path to it is the emailed
       link. See the msiq-site operating doc, "WCIR quarterly delivery pages".
       GENERATED by _scripts/import_wcir.py from {esc(provenance)}.
       Do not hand-edit: fix the report in WCI and re-run the importer. -->
  <meta name="robots" content="noindex, nofollow, noarchive">

{{{{ga4}}}}

  <meta name="description" content="{attr(desc)}">

  <meta property="og:title" content="{attr(title)} | {q}">
  <meta property="og:description" content="{attr(desc)}">
  <meta property="og:type" content="article">
  <meta property="og:image" content="https://www.mainstreetiq.com/assets/images/og-image.jpg">

{{{{fonts}}}}
{{{{styles}}}}
{PAGE_CSS}
</head>
<body>
  <a href="#main" class="skip-link">Skip to main content</a>

  {{{{nav}}}}

  <main id="main">

  <section class="hero">
    <div class="container">
      <span class="section-label">{esc(q)} Edition</span>
      <h1>{esc(title)}</h1>
      <p>{esc(cover['subtitle'])} | {esc(count)}</p>
      <p class="wcir-hero-meta">{inline(cover['byline'])}</p>
      <p class="wcir-pdf"><a href="{pdf}" target="_blank" rel="noopener" data-vertical="wine">Download the PDF</a></p>
    </div>
  </section>

  <section>
    <div class="container">
      <nav class="wcir-toc" aria-label="In this report">
        <h2>In this report</h2>
        <ol>
{toc_items}
        </ol>
      </nav>
      <article class="wcir-report">
{body}
      </article>
    </div>
  </section>

  <section class="bg-light" id="options">
    <div class="container">
      <div class="section-header section-header-left">
        <span class="section-label">Choose your option</span>
        <h2 class="section-title">See where your own winery stands</h2>
        <p class="section-subtitle">Buy online. Each card links to more about the option on our wineries page.</p>
      </div>
      <div class="wcir-options">
{render_options(q)}
      </div>
      <p class="wcir-options-terms">{SECOND_COUNTY_LINE}</p>
      <p class="wcir-options-terms">{RENEWAL_LINE}</p>
    </div>
  </section>

  <section id="subscribe">
    <div class="container">
      <div class="wcir-subscribe">
        <h2 class="section-title">Get the next edition when it is out.</h2>
        <p>The {esc(title)} is free and comes out every quarter. Wine Country Intelligence keeps its own list, separate from the Main Street IQ email list.</p>
        <p id="wcirSubscribeFallback">Email <a href="{mailto}" data-vertical="wine">wci@mainstreetiq.com</a> to get the next edition.</p>
        <form id="wcirSubscribeForm" data-list="wcir" novalidate hidden>
          <label for="wcirEmail">Email</label>
          <input type="email" id="wcirEmail" name="email" required autocomplete="email" maxlength="100" placeholder="you@winery.com">
          <label for="wcirWinery">Winery (optional)</label>
          <input type="text" id="wcirWinery" name="winery" autocomplete="organization" maxlength="120">
          <input type="text" name="honeypot" class="wcir-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">
          <p class="wcir-fine">Sending this adds you to the Wine Country Intelligence list.</p>
          <button type="submit" class="btn btn-primary">Send me the next edition</button>
          <div class="wcir-subscribe-msg" id="wcirSubscribeMsg" role="status" aria-live="polite"></div>
        </form>
        <p class="wcir-fine">Unsubscribe anytime. <a href="/legal/privacy">Privacy Policy</a>.</p>
      </div>
    </div>
  </section>

  </main>

{WINE_FOOTER}

  <script src="/assets/js/wcir-subscribe.js" defer></script>
  <script>
    const header = document.getElementById('site-header');
    window.addEventListener('scroll', () => {{
      header.classList.toggle('scrolled', window.scrollY > 20);
    }});
    const toggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    toggle.addEventListener('click', () => {{
      navLinks.classList.toggle('open');
      toggle.classList.toggle('active');
    }});
  </script>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    src, slug = Path(argv[1]).expanduser(), argv[2]
    if not re.fullmatch(r"q[1-4]-\d{4}-[a-z0-9-]+", slug):
        print(f"slug must look like q3-2026-central-coast, got {slug!r}", file=sys.stderr)
        return 2
    text = src.read_text(encoding="utf-8")
    lines = text.split("\n")
    try:
        cut = lines.index("---")
    except ValueError:
        print("source has no cover rule (---)", file=sys.stderr)
        return 1
    try:
        cover = parse_cover(lines[:cut])
        blocks, build = parse_body(lines[cut + 1:])
        body, toc = render_blocks(blocks)
    except ImportError_ as e:
        print(f"import_wcir: {e}", file=sys.stderr)
        return 1
    page = render_page(cover, body, toc, slug, src.name, build)
    for bad in ("—", "–"):
        if bad in page:
            print(f"import_wcir: output contains {bad!r}; fix the source in WCI", file=sys.stderr)
            return 1
    out = ROOT / "_content" / "wcir" / f"{slug}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    old = out.read_text(encoding="utf-8") if out.exists() else None
    out.write_text(page, encoding="utf-8")
    print(f"{'unchanged' if old == page else 'wrote'} {out.relative_to(ROOT)} "
          f"({len(blocks)} blocks, {sum(b['type'] == 'table' for b in blocks)} tables, {len(toc)} sections)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
