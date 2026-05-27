"""
Trust Center footer sweep.

Insert <a href="/trust">Trust Center</a> between the Refunds and AI Use links
in the Legal footer column of every HTML file in the site that has the standard
footer pattern. Idempotent.

Per project_msiq_site_trust_center_pattern_2026-05-27 (memory): every page in
the site should expose the Trust Center link in the Legal column, between
Refunds and AI Use, so security/compliance/legal-curious buyers can route there
without it competing in main nav.

Skips files where the link is already present.
Run from apps/msiq-site/ as: python _scripts/trust_center_footer_sweep.py
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

# Match the canonical footer pattern, allowing for variable whitespace and the
# exact Refunds -> AI Use sequence with no Trust Center between them.
PATTERN = re.compile(
    r'(<a href="/legal/refund-cancellation">Refunds</a>)(\s*\n\s*)(<a href="/legal/ai-use">AI Use</a>)'
)


def patch(path: Path) -> str:
    """Return one of: 'patched', 'already', 'no-match', 'skip-no-html'."""
    if path.suffix.lower() != ".html":
        return "skip-no-html"
    text = path.read_text(encoding="utf-8")
    if 'href="/trust">Trust Center</a>' in text:
        return "already"
    if not PATTERN.search(text):
        return "no-match"
    new_text = PATTERN.sub(
        lambda m: f'{m.group(1)}{m.group(2)}<a href="/trust">Trust Center</a>{m.group(2)}{m.group(3)}',
        text,
        count=1,
    )
    path.write_text(new_text, encoding="utf-8")
    return "patched"


def main() -> int:
    here = Path(__file__).resolve().parent.parent
    counts = {"patched": 0, "already": 0, "no-match": 0, "skip-no-html": 0}
    patched_files: list[str] = []
    no_match_files: list[str] = []

    for path in sorted(here.rglob("*.html")):
        # Skip node_modules / vendor / _examples if they exist
        if any(part in {"node_modules", "_examples", "samples", "_scripts"} for part in path.parts):
            continue
        rel = path.relative_to(here)
        result = patch(path)
        counts[result] = counts.get(result, 0) + 1
        if result == "patched":
            patched_files.append(str(rel))
        elif result == "no-match":
            no_match_files.append(str(rel))

    print(f"Patched: {counts['patched']}")
    print(f"Already had Trust Center: {counts['already']}")
    print(f"No footer match (skipped): {counts['no-match']}")
    print()
    if patched_files:
        print("Patched files:")
        for f in patched_files:
            print(f"  + {f}")
    if no_match_files:
        print()
        print("Files with no Refunds/AI Use footer pattern (review manually if needed):")
        for f in no_match_files:
            print(f"  - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
