"""
geo_service_align.py — one-off surgical alignment for the 6 geo pages
and 3 kept service pages.

SEO-safe by design: touches only hard errors. Does NOT touch title tags,
H1s, county-keyword body content, geo meta, or schema structure.

Fixes:
1. Body CTA "30 Minutes. No Pitch." calendly-direct -> "Book a Fit Call"
   -> /fit-call (hero button + CTA banner).
2. Schema founder jobTitle "Fractional CFO" -> "Founder & Fractional CFO".
3. var(--gold) -> var(--navy) (forbidden brand color).
4. Old revenue bands -> "under $50MM" (longest phrasings first so the
   sentences stay grammatical).

Run from msiq-site root:  python _scripts/geo_service_align.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    "fractional-cfo-santa-barbara.html",
    "fractional-cfo-san-luis-obispo.html",
    "fractional-cfo-ventura.html",
    "fractional-cfo-los-angeles.html",
    "fractional-cfo-orange-county.html",
    "fractional-cfo-san-diego.html",
    "fractional-cfo-vs-cpa.html",
    "interim-finance-leadership.html",
    "finance-director-services.html",
]

CTA_RE = re.compile(
    r'<a href="https://calendly\.com[^"]*" class="btn btn-white" '
    r'target="_blank" rel="noopener">30 Minutes\. No Pitch\. &rarr;</a>'
)
CTA_NEW = '<a href="/fit-call" class="btn btn-white">Book a Fit Call &rarr;</a>'

# Revenue-band phrasings, longest/most-specific first.
REVENUE_SUBS = [
    ("companies in the $10M to $100M range", "owner-operated companies under $50MM"),
    ("companies in the $10M–$100M range", "owner-operated companies under $50MM"),
    ("companies in the $10M-$100M range", "owner-operated companies under $50MM"),
    ("between $10M and $100M in revenue", "under $50MM in revenue"),
    ("between $10M and $300M in revenue", "under $50MM in revenue"),
    ("$10M to $300M client revenue range", "under-$50MM revenue range"),
    ("$10M–$300M client revenue range", "under-$50MM revenue range"),
    ("$10M–$300M range", "under-$50MM range"),
    ("$10M to $300M range", "under-$50MM range"),
    ("$10M–$100M companies", "owner-operated companies under $50MM"),
    ("$10M-$100M companies", "owner-operated companies under $50MM"),
    ("$10M to $100M", "under $50MM"),
    ("$10M–$100M", "under $50MM"),
    ("$10M-$100M", "under $50MM"),
    ("$10M–$300M", "under $50MM"),
    ("$10M to $300M", "under $50MM"),
    ("$10M-$300M", "under $50MM"),
]


def main():
    for name in TARGETS:
        path = ROOT / name
        if not path.exists():
            print(f"SKIP (missing): {name}")
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        notes = []

        text, n = CTA_RE.subn(CTA_NEW, text)
        if n:
            notes.append(f"cta={n}")

        n = text.count('"jobTitle": "Fractional CFO"')
        if n:
            text = text.replace(
                '"jobTitle": "Fractional CFO"',
                '"jobTitle": "Founder & Fractional CFO"',
            )
            notes.append(f"jobtitle={n}")

        n = text.count("var(--gold)")
        if n:
            text = text.replace("var(--gold)", "var(--navy)")
            notes.append(f"gold={n}")

        rev = 0
        for old, new in REVENUE_SUBS:
            c = text.count(old)
            if c:
                text = text.replace(old, new)
                rev += c
        if rev:
            notes.append(f"revenue={rev}")

        if text != original:
            path.write_text(text, encoding="utf-8", newline="")
            print(f"  {name}: " + ", ".join(notes))
        else:
            print(f"  {name}: no change")


if __name__ == "__main__":
    main()
