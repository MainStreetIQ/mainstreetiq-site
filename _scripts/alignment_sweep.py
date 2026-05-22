"""
alignment_sweep.py — one-off positioning-alignment sweep.

Three site-wide replacements that bring legacy pages onto the rebuilt
MSIQ positioning:

1. Header nav CTA: a calendly-direct "Book a Call" / "Book a Fit Call"
   anchor with class="nav-cta" becomes "/fit-call" + "Book a Fit Call".
2. Footer Connect-column "Book a Fit Call" calendly-direct link becomes
   "/fit-call".
3. Footer brand line: the older "AI-Augmented Strategic Advisory..."
   sentence becomes the locked CFO positioning sentence.

Run from the msiq-site root:
    python _scripts/alignment_sweep.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 1. Header nav CTA -> /fit-call
NAV_CTA_RE = re.compile(
    r'<a href="https://calendly\.com[^"]*" class="nav-cta"[^>]*>Book a (?:Fit )?Call</a>'
)
NAV_CTA_NEW = '<a href="/fit-call" class="nav-cta">Book a Fit Call</a>'

# 2. Footer Connect-column Fit Call link -> /fit-call
FOOTER_LINK_OLD = (
    '<a href="https://calendly.com/scott_mainstreetiq/30min" '
    'target="_blank" rel="noopener">Book a Fit Call</a>'
)
FOOTER_LINK_NEW = '<a href="/fit-call">Book a Fit Call</a>'

# 3. Footer brand line
FOOTER_TAGLINE_OLD = (
    "AI-Augmented Strategic Advisory. Outcomes you can justify, "
    "without the headcount."
)
FOOTER_TAGLINE_NEW = (
    "Fractional CFO and business advisory for owner and founder-led "
    "companies on the California coast."
)


def process_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    original = text
    counts = {"nav_cta": 0, "footer_link": 0, "footer_tagline": 0}

    text, counts["nav_cta"] = NAV_CTA_RE.subn(NAV_CTA_NEW, text)
    n = text.count(FOOTER_LINK_OLD)
    if n:
        text = text.replace(FOOTER_LINK_OLD, FOOTER_LINK_NEW)
        counts["footer_link"] = n
    n = text.count(FOOTER_TAGLINE_OLD)
    if n:
        text = text.replace(FOOTER_TAGLINE_OLD, FOOTER_TAGLINE_NEW)
        counts["footer_tagline"] = n

    if text != original:
        path.write_text(text, encoding="utf-8", newline="")
        return counts
    return {}


def main():
    changed = 0
    totals = {"nav_cta": 0, "footer_link": 0, "footer_tagline": 0}
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(p.startswith(("_scripts", "node_modules", ".")) for p in rel.parts):
            continue
        c = process_file(path)
        if c:
            changed += 1
            for k in totals:
                totals[k] += c.get(k, 0)
            print(f"  {rel}: " + ", ".join(
                f"{k}={c[k]}" for k in c if c.get(k)
            ))
    print()
    print(f"Files changed: {changed}")
    print(f"  nav CTA fixes:        {totals['nav_cta']}")
    print(f"  footer link fixes:    {totals['footer_link']}")
    print(f"  footer tagline fixes: {totals['footer_tagline']}")


if __name__ == "__main__":
    main()
