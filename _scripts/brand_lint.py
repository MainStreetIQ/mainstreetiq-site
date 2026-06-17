"""
brand_lint.py — render-aware brand Red Line checker for the msiq-site corpus.

Catches the two mechanical Red Lines that read as AI-generated and must never
ship in reader- or crawler-facing text:
  1. Em dashes (U+2014), in literal form or as the HTML entities &mdash; /
     &#8212; / &#x2014;. Use a comma, semicolon, colon, period, or "|" in titles.
  2. Emoji (high-plane pictographs U+1F000-U+1FAFF, the emoji-presentation
     selector U+FE0F, and regional-indicator pairs). Brand rule: no emoji icons.

The check is RENDER-AWARE: it strips <script> blocks, <style> blocks, and
<!-- HTML comments --> before scanning, so em dashes left in dev comments (the
boilerplate gtag and Calendly comments) and in JS do not trip it. Only what a
reader or a crawler actually sees is checked.

Arrows (&rarr; / &larr; / U+2190-U+21FF) and typographic marks (™ © …) are NOT
emoji and are intentionally allowed.

Exit code is 1 if any violation is found, 0 if the corpus is clean, so this can
gate a pre-commit hook or CI step. It never mutates files.

Run from msiq-site root:
    python _scripts/brand_lint.py            # check whole site, report, exit 1 on hit
    python _scripts/brand_lint.py blog       # check only blog/
    python _scripts/brand_lint.py --quiet    # summary only
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.IGNORECASE | re.DOTALL)
STYLE_RE = re.compile(r"<style\b.*?</style>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

EM_DASH_RE = re.compile(r"—|&mdash;|&#8212;|&#x2014;", re.IGNORECASE)

# Strong-signal emoji only, to avoid false-positiving on legit UI glyphs
# (checkmarks, arrows). Astral-plane pictographs, the emoji presentation
# selector, and regional-indicator letters are unambiguous.
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF]"  # pictographs, emoji, supplemental symbols
    "|️"                   # variation selector-16 (emoji presentation)
    "|[\U0001F1E6-\U0001F1FF]"  # regional indicators (flags)
)


def strip_non_rendered(text: str) -> str:
    """Remove script/style/comment regions so only rendered text remains."""
    text = SCRIPT_RE.sub("", text)
    text = STYLE_RE.sub("", text)
    text = COMMENT_RE.sub("", text)
    return text


def snippet(text: str, start: int, end: int, pad: int = 35) -> str:
    """A one-line context window around a hit, for the report."""
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    frag = text[lo:hi].replace("\n", " ").strip()
    return re.sub(r"\s+", " ", frag)


def find_violations(rendered: str) -> list[tuple[str, str]]:
    """Return (kind, context) for every Red Line hit in rendered text."""
    hits: list[tuple[str, str]] = []
    for m in EM_DASH_RE.finditer(rendered):
        hits.append(("em-dash", snippet(rendered, m.start(), m.end())))
    for m in EMOJI_RE.finditer(rendered):
        hits.append(("emoji", snippet(rendered, m.start(), m.end())))
    return hits


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    quiet = "--quiet" in sys.argv

    scope = ROOT / args[0] if args else ROOT
    if not scope.exists():
        print(f"brand_lint.py: path not found: {scope}")
        return 2

    print(f"brand_lint.py — scope={scope.relative_to(ROOT) if scope != ROOT else '.'}\n")

    html_files = sorted(scope.rglob("*.html"))
    total_files = 0
    flagged: dict[str, list[tuple[str, str]]] = {}

    for path in html_files:
        rel_parts = path.relative_to(ROOT).parts
        if any(p.startswith(("_scripts", "node_modules", ".")) for p in rel_parts):
            continue
        total_files += 1
        rendered = strip_non_rendered(path.read_text(encoding="utf-8"))
        hits = find_violations(rendered)
        if hits:
            flagged[str(path.relative_to(ROOT))] = hits

    if not flagged:
        print(f"PASS — {total_files} files checked, no em dashes or emoji in rendered text.")
        return 0

    em = sum(1 for hs in flagged.values() for k, _ in hs if k == "em-dash")
    emo = sum(1 for hs in flagged.values() for k, _ in hs if k == "emoji")
    print(f"FAIL — {len(flagged)}/{total_files} files have violations "
          f"({em} em-dash, {emo} emoji).\n")

    if not quiet:
        for f in sorted(flagged):
            print(f"{f}:")
            for kind, ctx in flagged[f]:
                print(f"  [{kind}] ...{ctx}...")
            print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
