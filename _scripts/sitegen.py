#!/usr/bin/env python3
"""
sitegen — the single producer for msiq-site.

Replaces the eleven ad-hoc sweep scripts. Every shared element (head
boilerplate, the GA4 snippet, nav, footer) lives in exactly one place under
_templates/; per-page content lives under _content/. `build` renders
_content/* back out to the HTML files GitHub Pages serves.

Two subcommands:

    extract   ONE-TIME migration. Splits the existing HTML into _content/
              entries + the shared partials. Strict: a page whose structure
              does not match is SKIPPED and reported, never guessed at.

    build     Renders _content/* -> *.html.
              --check renders to a scratch dir and reports drift instead of
              writing, which is the guard that a hand-edit to a generated
              page cannot survive CI.

Why the acceptance test is split (this matters, do not "simplify" it):
the GA4 snippet currently sits BETWEEN per-page tags in <head> (title, then
gtag, then description). Factoring GA4 into a partial necessarily reorders the
head, so head cannot be byte-compared. Body, nav and footer CAN be, and are.
Head is compared as a SET of normalized elements, which catches a dropped or
altered tag while tolerating order.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "_content"
TEMPLATES = ROOT / "_templates"

# Directories that are part of the site but not swept into templates.
EXCLUDE_DIRS = {"_examples", "_scheduled", "_scripts", "_content", "_templates",
                "assets", "node_modules", ".git", ".github", "reports"}

# Pages that must keep their existing markup verbatim. Each needs a reason.
BESPOKE = {
    # Deliberate wine-scoped footer; footer_sweep.py reports it as BESPOKE 1.
    "wcir/q2-2026-central-coast.html": "deliberate wine-scoped footer",
    # Redirect stubs: no nav, no footer, no main.
    "card.html": "redirect stub, no chrome",
    "fit-call.html": "redirect stub, no chrome",
    "fit-call-confirm.html": "redirect stub, no chrome",
    "fractional-cfo-dtc-ecommerce.html": "redirect stub, consolidates SEO into /ecommerce",
    # Only file on the site containing literal Liquid-style braces.
    "legal/index.html": "contains literal {{ }} braces",
}

# ---------------------------------------------------------------------------
# Head classification
#
# A head line is either shared boilerplate (goes to the template, one copy) or
# per-page (rides with the content). Anything unrecognized is treated as
# per-page, which is the safe direction: it stays with its page rather than
# being silently applied site-wide.
# ---------------------------------------------------------------------------

BOILERPLATE_PATTERNS = [
    re.compile(r'<meta\s+charset=', re.I),
    re.compile(r'<meta\s+name="viewport"', re.I),
    re.compile(r'<link\s+rel="icon"', re.I),
    re.compile(r'googletagmanager\.com/gtag', re.I),
    re.compile(r'window\.dataLayer\s*=\s*window\.dataLayer', re.I),
    re.compile(r'<link\s+rel="preconnect"', re.I),
    re.compile(r'fonts\.googleapis\.com/css2', re.I),
    re.compile(r'<link\s+rel="stylesheet"\s+href="/?styles\.css"', re.I),
]


def is_boilerplate(line: str) -> bool:
    return any(p.search(line) for p in BOILERPLATE_PATTERNS)


# ---------------------------------------------------------------------------
# Structural extraction
# ---------------------------------------------------------------------------

RE_HEAD = re.compile(r"<head>(.*?)</head>", re.S | re.I)
RE_HEADER = re.compile(r'<header class="site-header".*?</header>', re.S | re.I)
RE_FOOTER = re.compile(r'<footer class="site-footer">.*?</footer>', re.S | re.I)


class StructureError(Exception):
    """Raised when a page does not match the expected shape."""


def split_page(html: str) -> dict:
    """Split a page into its structural parts. Raises on anything unexpected."""
    m_head = RE_HEAD.search(html)
    if not m_head:
        raise StructureError("no <head> block")

    m_header = RE_HEADER.search(html)
    if not m_header:
        raise StructureError("no <header class=\"site-header\"> block")

    m_footer = RE_FOOTER.search(html)
    if not m_footer:
        raise StructureError("no <footer class=\"site-footer\"> block")

    if m_footer.start() < m_header.end():
        raise StructureError("footer precedes header")

    head_inner = m_head.group(1)
    boiler, per_page = [], []
    for line in head_inner.splitlines():
        if not line.strip():
            per_page.append(line)
        elif is_boilerplate(line):
            boiler.append(line)
        else:
            per_page.append(line)

    return {
        "head_boilerplate": boiler,
        "head_per_page": _trim_blank_edges(per_page),
        "pre_header": html[m_head.end():m_header.start()],
        "header": m_header.group(0),
        "body": html[m_header.end():m_footer.start()],
        "footer": m_footer.group(0),
        "post_footer": html[m_footer.end():],
        "doctype": html[:m_head.start()],
    }


def _trim_blank_edges(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def normalize_head_elements(head_inner: str) -> set[str]:
    """
    Reduce a <head> to a comparable set of elements. Collapses whitespace so
    indentation and line-wrapping differences do not register as drift, but
    preserves every tag and its attributes.
    """
    text = re.sub(r"\s+", " ", head_inner).strip()
    parts = re.findall(r"<(?:meta|title|link|script)\b.*?(?:</script>|</title>|>)", text, re.I)
    return {p.strip() for p in parts}


def iter_pages() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in EXCLUDE_DIRS:
            continue
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

def cmd_extract(args) -> int:
    pages = iter_pages()
    ok, skipped = [], []

    variants_nav: dict[str, list[str]] = {}
    variants_footer: dict[str, list[str]] = {}

    for p in pages:
        rel = str(p.relative_to(ROOT))
        if rel in BESPOKE:
            skipped.append((rel, f"bespoke: {BESPOKE[rel]}"))
            continue
        try:
            parts = split_page(p.read_text(encoding="utf-8"))
        except StructureError as e:
            skipped.append((rel, str(e)))
            continue

        nav_key = re.sub(r'\s+', ' ', parts["header"]).strip()
        foot_key = re.sub(r'\s+', ' ', parts["footer"]).strip()
        variants_nav.setdefault(nav_key, []).append(rel)
        variants_footer.setdefault(foot_key, []).append(rel)
        ok.append((rel, parts))

    print(f"parsed cleanly : {len(ok)}")
    print(f"skipped        : {len(skipped)}")
    for rel, why in skipped:
        print(f"    {rel:<46} {why}")
    print()
    print(f"distinct header/nav variants : {len(variants_nav)}")
    for key, files in sorted(variants_nav.items(), key=lambda kv: -len(kv[1])):
        print(f"    {len(files):>4} pages   e.g. {files[0]}")
    print()
    print(f"distinct footer variants     : {len(variants_footer)}")
    for key, files in sorted(variants_footer.items(), key=lambda kv: -len(kv[1])):
        print(f"    {len(files):>4} pages   e.g. {files[0]}")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ex = sub.add_parser("extract", help="one-time migration survey / split")
    p_ex.set_defaults(func=cmd_extract)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
