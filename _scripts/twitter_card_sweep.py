"""
twitter_card_sweep.py — inject twitter:card / twitter:title / twitter:description
on the seven pages flagged by the 2026-05-27 website audit as missing Twitter
card metadata.

For each target page, the script reads the existing og:title and og:description
content values and mirrors them into twitter:title and twitter:description.
The card type is summary_large_image, matching the canonical pattern set in
about.html. twitter:image is intentionally omitted so platforms fall back to
og:image (kept consistent with the rest of the site, which does not set a
separate twitter:image).

Run from msiq-site root:
    python _scripts/twitter_card_sweep.py            # apply
    python _scripts/twitter_card_sweep.py --dry-run  # show what would change

Idempotent: skips any page that already has a twitter:card meta tag.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INJECTION_MARKER = "<!-- Twitter Card (twitter_card_sweep) -->"

TARGETS: list[str] = [
    "partners.html",
    "fit-call.html",
    "ecommerce.html",
    "wine-country-intelligence.html",
    "wellness-assessment.html",
    "aesthetics-assessment.html",
    "ecommerce-assessment.html",
]

OG_TITLE_RE = re.compile(
    r'<meta\s+property="og:title"\s+content="([^"]*)"\s*/?>',
    re.IGNORECASE,
)
OG_DESC_RE = re.compile(
    r'<meta\s+property="og:description"\s+content="([^"]*)"\s*/?>',
    re.IGNORECASE,
)

# Match any og: meta tag; we anchor the injection after the LAST one in head.
OG_ANY_RE = re.compile(
    r'^[ \t]*<meta\s+property="og:[^"]+"\s+content="[^"]*"\s*/?>\s*$',
    re.IGNORECASE | re.MULTILINE,
)

TWITTER_CARD_PRESENT_RE = re.compile(
    r'<meta\s+name="twitter:card"',
    re.IGNORECASE,
)


def build_block(og_title: str, og_desc: str, indent: str) -> str:
    return (
        f'\n{indent}{INJECTION_MARKER}\n'
        f'{indent}<meta name="twitter:card" content="summary_large_image">\n'
        f'{indent}<meta name="twitter:title" content="{og_title}">\n'
        f'{indent}<meta name="twitter:description" content="{og_desc}">'
    )


def process_file(path: Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8")

    if TWITTER_CARD_PRESENT_RE.search(text) or INJECTION_MARKER in text:
        return "skipped"

    title_m = OG_TITLE_RE.search(text)
    desc_m = OG_DESC_RE.search(text)
    if not title_m or not desc_m:
        return "no-og-source"

    og_title = title_m.group(1)
    og_desc = desc_m.group(1)

    matches = list(OG_ANY_RE.finditer(text))
    if not matches:
        return "no-og-anchor"

    last = matches[-1]
    anchor_line = last.group(0)
    indent = re.match(r'^([ \t]*)', anchor_line).group(1)

    block = build_block(og_title, og_desc, indent)
    new_text = text[: last.end()] + block + text[last.end() :]

    if dry_run:
        return "would-update"

    path.write_text(new_text, encoding="utf-8")
    return "updated"


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    print(f"twitter_card_sweep.py — root={ROOT} dry_run={dry_run}\n")

    summary: dict[str, int] = {}
    for filename in TARGETS:
        path = ROOT / filename
        if not path.exists():
            status = "missing"
        else:
            status = process_file(path, dry_run)
        summary[status] = summary.get(status, 0) + 1
        print(f"  {filename:36s} {status}")

    print(f"\nDone. {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
