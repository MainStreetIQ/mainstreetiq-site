"""
One-shot patcher: add veteran-owned credential to the 5 remaining location pages
(Santa Barbara was done manually). Three edits per page:

  1. ProfessionalService JSON-LD: add "award" + founder.hasCredential
  2. Hero stat bar: append "Veteran-owned and operated." line after </div></div></section>
  3. Footer Legal column: insert Trust Center between Refunds and AI Use

Idempotent: skips any edit whose target marker is already present.
Run from apps/msiq-site/ as: python _scripts/add_veteran_to_location_pages.py
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

FILES = [
    "fractional-cfo-san-luis-obispo.html",
    "fractional-cfo-ventura.html",
    "fractional-cfo-los-angeles.html",
    "fractional-cfo-orange-county.html",
    "fractional-cfo-san-diego.html",
]

VETERAN_LINE = (
    '      <p style="font-size: 0.95rem; color: rgba(255,255,255,0.75); '
    'margin-top: 1.5rem; max-width: 720px; letter-spacing: 0.5px;">'
    'Veteran-owned and operated.</p>'
)


def patch_schema_pretty(content: str) -> tuple[str, bool]:
    """Pretty-formatted ProfessionalService schema (SB / SLO / Ventura / LA / OC).
    Insert award after url, and founder.hasCredential after founder.url."""
    if '"award": ["Veteran-Owned Business"]' in content:
        return content, False

    # Add award after the ProfessionalService url line
    pattern_url = re.compile(
        r'(\"@type\": \"ProfessionalService\",[\s\S]*?\"url\": \"[^\"]+\",)\n(\s+)(\"founder\":)'
    )
    new = pattern_url.sub(
        r'\1\n\2"award": ["Veteran-Owned Business"],\n\2\3',
        content,
        count=1,
    )
    if new == content:
        return content, False

    # Add hasCredential inside founder block (after founder.url)
    pattern_founder = re.compile(
        r'(\"founder\": \{[\s\S]*?\"url\": \"https://www\.linkedin\.com/in/johnscotthess\")\n(\s+)(\})'
    )
    new2 = pattern_founder.sub(
        r'\1,\n\2  "hasCredential": {\n\2    "@type": "EducationalOccupationalCredential",\n'
        r'\2    "credentialCategory": "military-service",\n'
        r'\2    "name": "U.S. Navy Veteran"\n\2  }\n\2\3',
        new,
        count=1,
    )
    if new2 == new:
        return new, True  # award added, founder block didn't match (unusual)
    return new2, True


def patch_schema_minified(content: str) -> tuple[str, bool]:
    """Minified ProfessionalService schema on a single line (San Diego format)."""
    if '"award":["Veteran-Owned Business"]' in content or '"award": ["Veteran-Owned Business"]' in content:
        return content, False

    # Find the minified schema line
    pattern = re.compile(
        r'(\{"@context":"https://schema\.org","@type":"ProfessionalService",[^}]*?"founder":\{[^}]*?\"url\":\"https://www\.linkedin\.com/in/johnscotthess\")(\})'
    )
    new = pattern.sub(
        r'\1,"hasCredential":{"@type":"EducationalOccupationalCredential",'
        r'"credentialCategory":"military-service","name":"U.S. Navy Veteran"}\2',
        content,
        count=1,
    )

    # Add award field — insert right after the "url" field of the ProfessionalService
    pattern_award = re.compile(
        r'(\{"@context":"https://schema\.org","@type":"ProfessionalService","name":"Main Street IQ","description":"[^"]+","url":"[^"]+")(,"founder")'
    )
    new = pattern_award.sub(
        r'\1,"award":["Veteran-Owned Business"]\2',
        new,
        count=1,
    )

    return new, new != content


def patch_hero_credential(content: str) -> tuple[str, bool]:
    """Insert veteran-owned line right before the stat-bar's </section> closer.
    Anchor: the closing of the last stat-item block + </div></div></section>."""
    if "Veteran-owned and operated." in content:
        return content, False

    # Look for the stat-bar pattern: </div>\n      </div>\n    </div>\n  </section> where the inner
    # </div> closes .stat-bar, the next </div> closes .container, and </section> closes hero.
    # Insert the veteran line after the .stat-bar </div> but before .container's </div>.
    pattern = re.compile(
        r'(<div class="stat-bar">[\s\S]*?\n      </div>)\n(    </div>\n  </section>)'
    )
    new = pattern.sub(
        lambda m: m.group(1) + "\n" + VETERAN_LINE + "\n" + m.group(2),
        content,
        count=1,
    )
    return new, new != content


def patch_footer_trust_center(content: str) -> tuple[str, bool]:
    """Insert Trust Center link between Refunds and AI Use in footer Legal column."""
    if '<a href="/trust">Trust Center</a>' in content:
        return content, False

    needle = '<a href="/legal/refund-cancellation">Refunds</a>\n          <a href="/legal/ai-use">AI Use</a>'
    replacement = (
        '<a href="/legal/refund-cancellation">Refunds</a>\n'
        '          <a href="/trust">Trust Center</a>\n'
        '          <a href="/legal/ai-use">AI Use</a>'
    )
    if needle not in content:
        return content, False
    new = content.replace(needle, replacement, 1)
    return new, True


def process(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    report = {"file": path.name, "edits": []}

    # Try pretty schema first; if no change, try minified
    text2, ch = patch_schema_pretty(text)
    if not ch:
        text2, ch = patch_schema_minified(text)
    if ch:
        report["edits"].append("schema(award+hasCredential)")
    text = text2

    text, ch = patch_hero_credential(text)
    if ch:
        report["edits"].append("hero(veteran-line)")

    text, ch = patch_footer_trust_center(text)
    if ch:
        report["edits"].append("footer(trust-center)")

    if report["edits"]:
        path.write_text(text, encoding="utf-8")
    return report


def main() -> int:
    here = Path(__file__).resolve().parent.parent
    overall_ok = True
    for fname in FILES:
        p = here / fname
        if not p.exists():
            print(f"  MISSING: {fname}")
            overall_ok = False
            continue
        rep = process(p)
        print(f"  {rep['file']}: {', '.join(rep['edits']) or 'no changes (already patched?)'}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
