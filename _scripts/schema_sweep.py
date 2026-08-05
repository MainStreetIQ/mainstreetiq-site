"""
schema_sweep.py — inject Service JSON-LD on the three pages flagged by the
2026-05-27 website audit as missing schema.

Pages and payloads:
  partners.html     -> Service: Center of Influence referral program
  fit-call.html     -> Service: Fit Call (introductory consultation)
  ecommerce.html    -> Service: Fractional CFO for ecommerce brands
                      (keeps existing FAQPage block; adds Service alongside)

Run from msiq-site root:
    python _scripts/schema_sweep.py            # apply
    python _scripts/schema_sweep.py --dry-run  # show what would change

Idempotent: skips any page that already has a Service JSON-LD block.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Marker comment so future runs can detect prior injection unambiguously
INJECTION_MARKER = "<!-- Structured Data: Service (schema_sweep) -->"

PAYLOADS: dict[str, str] = {
    "partners.html": """  __MARKER__
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Center of Influence Referral Program",
    "provider": {
      "@type": "ProfessionalService",
      "name": "Main Street IQ",
      "url": "https://www.mainstreetiq.com"
    },
    "serviceType": "Professional referral partnership",
    "description": "A small, deliberate network of accountants, bankers, and advisors who introduce their owner-operator clients on the California coast to Main Street IQ for fractional CFO advisory and customer acquisition intelligence work.",
    "areaServed": [
      {
        "@type": "State",
        "name": "California"
      },
      {
        "@type": "Place",
        "name": "California Central Coast"
      }
    ],
    "audience": {
      "@type": "Audience",
      "audienceType": "Accountants, bankers, attorneys, wealth advisors, and consultants serving owner-operated businesses under $50MM"
    },
    "url": "https://www.mainstreetiq.com/partners"
  }
  </script>
""",
    "fit-call.html": """  __MARKER__
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Fit Call",
    "provider": {
      "@type": "ProfessionalService",
      "name": "Main Street IQ",
      "url": "https://www.mainstreetiq.com"
    },
    "serviceType": "Introductory consultation",
    "description": "A twenty-minute founder-to-founder call with Scott Hess, founder of Main Street IQ. Walk away with a clear read on whether Main Street IQ can help and what to do if it cannot. Free and paid variants available.",
    "areaServed": [
      {
        "@type": "State",
        "name": "California"
      },
      {
        "@type": "Place",
        "name": "California Central Coast"
      }
    ],
    "audience": {
      "@type": "Audience",
      "audienceType": "Owner and founder-led companies under $50MM in wine, health and wellness, elective medicine, and ecommerce"
    },
    "url": "https://www.mainstreetiq.com/fit-call"
  }
  </script>
""",
    "ecommerce.html": """  __MARKER__
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Fractional CFO for Owner-Operated Ecommerce Brands",
    "provider": {
      "@type": "ProfessionalService",
      "name": "Main Street IQ",
      "url": "https://www.mainstreetiq.com"
    },
    "serviceType": "Fractional CFO advisory",
    "description": "Fractional CFO and customer acquisition intelligence for owner-operated DTC, Amazon, wholesale, and retail ecommerce brands on the California coast. Channel-level CAC, contribution margin, inventory cash modeling, cohort and LTV math, and halo attribution between DTC ad spend and Amazon conversions.",
    "areaServed": [
      {
        "@type": "State",
        "name": "California"
      },
      {
        "@type": "Place",
        "name": "California Central Coast"
      }
    ],
    "audience": {
      "@type": "Audience",
      "audienceType": "Multi-channel ecommerce and DTC brands under $50MM"
    },
    "url": "https://www.mainstreetiq.com/ecommerce"
  }
  </script>
""",
}


def already_injected(text: str) -> bool:
    """True if a prior schema_sweep run already wrote a Service block here."""
    if INJECTION_MARKER in text:
        return True
    # Conservative fallback: any existing Service JSON-LD counts as injected.
    return bool(re.search(r'"@type"\s*:\s*"Service"', text))


def process_file(path: Path, payload: str, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8")

    if "</head>" not in text:
        return "no-head"

    if already_injected(text):
        return "skipped"

    block = payload.replace("__MARKER__", INJECTION_MARKER)
    new_text = text.replace("</head>", block + "</head>", 1)

    if dry_run:
        return "would-update"

    path.write_text(new_text, encoding="utf-8")
    return "updated"


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    print(f"schema_sweep.py — root={ROOT} dry_run={dry_run}\n")

    summary: dict[str, int] = {}
    for filename, payload in PAYLOADS.items():
        path = ROOT / filename
        if not path.exists():
            status = "missing"
        else:
            status = process_file(path, payload, dry_run)
        summary[status] = summary.get(status, 0) + 1
        print(f"  {filename:32s} {status}")

    print(f"\nDone. {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
