"""
skip_link_sweep.py — inject the accessibility skip link on every page that
has a <main> element, and ensure that <main> carries id="main" so the skip
link has a target.

Closes the audit's "missing skip link to main content" finding.

For each HTML file under the msiq-site root (excluding _scripts, node_modules,
dot-dirs):
  - Skip if no <main> tag at all (e.g., card.html, the digital business card).
  - Skip if a class="skip-link" element already exists on the page (idempotent).
  - If the <main> tag has no id, add id="main".
  - Inject <a href="#main" class="skip-link">Skip to main content</a> as the
    first line after the <body ...> opening tag.

CSS for .skip-link already exists in styles.css (focus-visible reveal).

Run from msiq-site root:
    python _scripts/skip_link_sweep.py            # apply
    python _scripts/skip_link_sweep.py --dry-run  # show what would change
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_LINK_HTML = '<a href="#main" class="skip-link">Skip to main content</a>'

SKIP_LINK_PRESENT_RE = re.compile(r'class="skip-link"', re.IGNORECASE)

MAIN_TAG_RE = re.compile(r'<main\b([^>]*)>', re.IGNORECASE)
MAIN_HAS_ID_RE = re.compile(r'\bid\s*=\s*"[^"]*"', re.IGNORECASE)

BODY_OPEN_RE = re.compile(r'(<body\b[^>]*>)', re.IGNORECASE)


def ensure_main_id(text: str) -> tuple[str, bool]:
    """Return (new_text, changed). If the first <main> tag has no id attribute,
    add id="main". Otherwise leave it alone."""
    m = MAIN_TAG_RE.search(text)
    if not m:
        return text, False

    attrs = m.group(1)
    if MAIN_HAS_ID_RE.search(attrs):
        return text, False

    new_main = f"<main id=\"main\"{attrs}>"
    new_text = text[: m.start()] + new_main + text[m.end() :]
    return new_text, True


def inject_skip_link(text: str) -> tuple[str, bool]:
    """Insert the skip-link anchor as the first line after <body>."""
    m = BODY_OPEN_RE.search(text)
    if not m:
        return text, False

    body_tag = m.group(1)
    # Preserve existing line ending after <body>.
    injection = f"{body_tag}\n  {SKIP_LINK_HTML}"
    # If the original line already ends with a newline, keep it once.
    new_text = text[: m.start()] + injection + text[m.end() :]
    return new_text, True


def process_file(path: Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8")

    if "<main" not in text.lower():
        return "no-main"

    if SKIP_LINK_PRESENT_RE.search(text):
        return "skipped"

    new_text, id_changed = ensure_main_id(text)
    new_text, link_added = inject_skip_link(new_text)

    if not link_added:
        return "no-body-anchor"

    if dry_run:
        return "would-update"

    path.write_text(new_text, encoding="utf-8")
    return "updated"


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    print(f"skip_link_sweep.py — root={ROOT} dry_run={dry_run}\n")

    summary: dict[str, int] = {}
    files_per_status: dict[str, list[str]] = {}

    html_files = sorted(ROOT.rglob("*.html"))
    for path in html_files:
        rel_parts = path.relative_to(ROOT).parts
        if any(p.startswith(("_scripts", "node_modules", ".")) for p in rel_parts):
            continue

        status = process_file(path, dry_run)
        summary[status] = summary.get(status, 0) + 1
        files_per_status.setdefault(status, []).append(str(path.relative_to(ROOT)))

    for status in ("updated", "would-update", "skipped", "no-main", "no-body-anchor"):
        if status not in summary:
            continue
        files = files_per_status.get(status, [])
        print(f"\n{status} ({len(files)}):")
        for f in files:
            print(f"  {f}")

    print(f"\nDone. {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
