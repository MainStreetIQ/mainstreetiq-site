"""
footer_sweep.py — one-off script to replace the legacy footer-grid block
with the canonical version on all msiq-site pages still carrying the old
"Industries" column / Central Coast IQ / CFO Diagnostic links.

Run from the msiq-site root:
    python _scripts/footer_sweep.py

Skips pages that already use the canonical footer (Verticals column).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Canonical footer-grid block (matches index.html post-rebuild).
# First line has NO leading whitespace because the regex match starts at
# "<div class=\"footer-grid\">" and preserves the original file's indent
# before that point.
CANONICAL_FOOTER = """<div class="footer-grid">
        <div class="footer-brand">
          <a href="/" class="logo"><img src="/assets/logos/logo-horizontal-dark.svg" alt="Main Street IQ - AI-Augmented Strategic Advisory"></a>
          <p>AI-Augmented Strategic Advisory. Outcomes you can justify, without the headcount.</p>
        </div>
        <div class="footer-col">
          <h4>Company</h4>
          <a href="/about">About</a>
          <a href="/our-services">Services</a>
          <a href="/our-work">Our Work</a>
          <a href="/blog">Blog</a>
        </div>
        <div class="footer-col">
          <h4>Connect</h4>
          <a href="/contact">Contact</a>
          <a href="/partners">Partners</a>
          <a href="https://calendly.com/scott_mainstreetiq/30min" target="_blank" rel="noopener">Book a Fit Call</a>
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener">LinkedIn</a>
        </div>
        <div class="footer-col">
          <h4>Verticals</h4>
          <a href="/wineries">Wineries</a>
          <a href="/wellness">Health &amp; Wellness</a>
          <a href="/aesthetics">Elective Medicine</a>
        </div>
        <div class="footer-col">
          <h4>Locations</h4>
          <a href="/fractional-cfo-san-luis-obispo">San Luis Obispo</a>
          <a href="/fractional-cfo-santa-barbara">Santa Barbara</a>
          <a href="/fractional-cfo-ventura">Ventura</a>
          <a href="/fractional-cfo-los-angeles">Los Angeles</a>
          <a href="/fractional-cfo-orange-county">Orange County</a>
          <a href="/fractional-cfo-san-diego">San Diego</a>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <a href="/legal/privacy">Privacy</a>
          <a href="/legal/terms">Terms of Use</a>
          <a href="/legal/cookies">Cookies</a>
          <a href="/legal/subscription-terms">Subscription Terms</a>
          <a href="/legal/refund-cancellation">Refunds</a>
          <a href="/legal/ai-use">AI Use</a>
        </div>
      </div>"""

# Match from "<div class=\"footer-grid\">" through the closing </div>
# immediately before "<div class=\"footer-bottom\">"
LEGACY_FOOTER_RE = re.compile(
    r'<div class="footer-grid">.*?</div>\s*(?=<div class="footer-bottom">)',
    re.DOTALL,
)


def process_file(path: Path) -> str:
    """Return 'updated', 'skipped', or 'no-match' for a given file."""
    text = path.read_text(encoding="utf-8")

    # Skip files without a footer-grid at all
    if '<div class="footer-grid">' not in text:
        return "skipped"

    # Skip files that already have the canonical Verticals column
    if "<h4>Verticals</h4>" in text:
        return "skipped"

    new_text, count = LEGACY_FOOTER_RE.subn(CANONICAL_FOOTER + "\n      ", text, count=1)
    if count == 0:
        return "no-match"
    if count > 1:
        print(f"WARN: {path.relative_to(ROOT)} matched {count} times")

    path.write_text(new_text, encoding="utf-8", newline="")
    return "updated"


def main():
    updated = []
    skipped = []
    no_match = []

    # Collect all .html files
    html_files = sorted(ROOT.rglob("*.html"))

    for path in html_files:
        # Skip _scripts, node_modules, anything in dot-dirs
        if any(part.startswith(("_scripts", "node_modules", ".")) for part in path.relative_to(ROOT).parts):
            continue

        result = process_file(path)
        rel = path.relative_to(ROOT)
        if result == "updated":
            updated.append(rel)
        elif result == "no-match":
            no_match.append(rel)
        else:
            skipped.append(rel)

    print(f"Updated:  {len(updated)} files")
    for p in updated:
        print(f"  {p}")
    print(f"Skipped:  {len(skipped)} files (already canonical or no footer)")
    if no_match:
        print(f"NO MATCH: {len(no_match)} files (had Industries but regex did not find footer-grid)")
        for p in no_match:
            print(f"  {p}")
        sys.exit(1)


if __name__ == "__main__":
    main()
