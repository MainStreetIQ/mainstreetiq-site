"""
nav_two_lane_sweep.py — convert the inlined header nav to the two-lane IA.

Scott's 2026-08-03 ruling (apps/msiq-site/CLAUDE.md § Two-lane IA): the nav
stops pointing at the blended /our-services page and instead offers the two
lanes a buyer actually arrives on. /our-services keeps its URL and stays
linked from both hub pages, but drops out of the nav.

    Services            -> Fractional CFO      (/our-services -> /fractional-cfo)
    Discoverability     -> AI Discoverability   (href unchanged)

Three transforms, all scoped to the single <div class="nav-links"
id="nav-links"> container:

  1. Rewrite the Services link to the CFO lane hub.
  2. Rename the Discoverability link to "AI Discoverability".
  3. Where a page has NO Discoverability link at all (25 pages predate the
     2026-07-23 nav peer), INSERT one after the CFO lane link, so every page
     carries both lanes. Scott ruled this in on 2026-08-03; 13 of those 25 are
     posts in the AI-visibility blog series, which carried no link into the
     lane they exist to feed.

  Plus the active-state move: /our-services is out of the nav, so
  our-services.html's class="active" has nowhere to sit. Each lane hub marks
  its own nav item instead (fractional-cfo.html, discoverability.html), which
  is the convention the our-work children already follow.

WHY THE CONTAINER ANCHOR MATTERS. /our-services is linked twice on every page:
once in the header nav and once in the footer "Company" column, which orders
About -> Services. The 2026-07-23 pass anchored on the header's Services->About
adjacency; that anchor is now STALE (only 25 pages still read Services->About,
the rest read Services->Discoverability). Scoping every edit to the nav-links
div makes footer contamination structurally impossible rather than something a
post-hoc grep has to catch. Verified before writing: all 144 pages carrying a
Services link have exactly one nav-links div holding exactly one of them, and
exactly one more outside it (the footer).

Deliberately NOT changed: the footer Company column, and the Partners nav item
(present on 10 of 144 pages). Partners is a pre-existing inconsistency
unrelated to the two-lane IA; Scott ruled it out of scope on 2026-08-03.

Idempotent: a second run finds no /our-services link inside any nav-links div
and no page missing a Discoverability link, and reports no changes.

Run from msiq-site root:
    python _scripts/nav_two_lane_sweep.py            # apply
    python _scripts/nav_two_lane_sweep.py --dry-run  # show what would change
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The one structural anchor. Everything below edits only what this captures.
NAV_RE = re.compile(
    r'(<div class="nav-links" id="nav-links">)(.*?)(</div>)', re.DOTALL
)

# The Services link, with or without the active-state class.
SERVICES_RE = re.compile(r'<a href="/our-services"(?:\s+class="active")?>Services</a>')

# The Discoverability link, with or without the active-state class.
DISCO_RE = re.compile(
    r'<a href="/discoverability"(?:\s+class="active")?>(?:AI )?Discoverability</a>'
)

# Pages that mark their own nav item. Path -> which lane link gets class="active".
ACTIVE_ON = {
    "fractional-cfo.html": "cfo",
    "discoverability.html": "disco",
}

# Jekyll serves neither, and neither carries a nav. Listed so the skip is a
# stated decision rather than an accident of the glob.
SKIP_DIRS = {"_examples", "_scripts", "node_modules", "sample_renderer"}


def cfo_link(active: bool) -> str:
    cls = ' class="active"' if active else ""
    return f'<a href="/fractional-cfo"{cls}>Fractional CFO</a>'


def disco_link(active: bool) -> str:
    cls = ' class="active"' if active else ""
    return f'<a href="/discoverability"{cls}>AI Discoverability</a>'


def rewrite_nav(nav_inner: str, rel: str) -> tuple[str, list[str]]:
    """Rewrite the inside of one nav-links div. Returns (new_inner, actions)."""
    actions = []
    lane = ACTIVE_ON.get(rel)

    if not SERVICES_RE.search(nav_inner):
        return nav_inner, actions  # already swept, or a nav without the item

    # 1. Services -> Fractional CFO (carrying the active state if this is the hub)
    nav_inner = SERVICES_RE.sub(cfo_link(lane == "cfo"), nav_inner, count=1)
    actions.append("services->fractional-cfo")

    # 2. Rename an existing Discoverability link, or 3. insert one.
    if DISCO_RE.search(nav_inner):
        nav_inner = DISCO_RE.sub(disco_link(lane == "disco"), nav_inner, count=1)
        actions.append("rename-discoverability")
    else:
        # Insert directly after the CFO link, matching its indentation so the
        # emitted markup is indistinguishable from the hand-authored pages.
        m = re.search(r'([ \t]*)<a href="/fractional-cfo"[^>]*>Fractional CFO</a>', nav_inner)
        indent = m.group(1)
        nav_inner = (
            nav_inner[: m.end()]
            + "\n"
            + indent
            + disco_link(lane == "disco")
            + nav_inner[m.end():]
        )
        actions.append("insert-discoverability")

    return nav_inner, actions


def process(path: Path, dry_run: bool) -> list[str]:
    rel = str(path.relative_to(ROOT))
    text = path.read_text(encoding="utf-8")

    m = NAV_RE.search(text)
    if not m:
        return []

    new_inner, actions = rewrite_nav(m.group(2), rel)
    if not actions:
        return []

    # Everything outside the container is preserved by construction — the two
    # slices are copied verbatim — so the guard that earns its keep is a
    # postcondition on the container itself.
    #
    # Do NOT guard by counting surviving /our-services links in the file: that
    # pattern also matches the footer's copy AND the in-body editorial link
    # that many blog posts carry in a <p>. The first dry run tripped exactly
    # that false positive on a post with three references.
    if SERVICES_RE.search(new_inner):
        raise SystemExit(f"{rel}: a Services link survived inside the nav. Refusing to write.")
    for label, pat in (
        ("Fractional CFO", r'<a href="/fractional-cfo"[^>]*>Fractional CFO</a>'),
        ("AI Discoverability", r'<a href="/discoverability"[^>]*>AI Discoverability</a>'),
    ):
        n = len(re.findall(pat, new_inner))
        if n != 1:
            raise SystemExit(f"{rel}: expected exactly 1 {label} nav link, found {n}. Refusing to write.")

    new_text = text[: m.start(2)] + new_inner + text[m.end(2):]

    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return actions


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    changed = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP_DIRS or part.startswith(".") for part in path.relative_to(ROOT).parts[:-1]):
            continue
        actions = process(path, args.dry_run)
        if actions:
            changed.append((str(path.relative_to(ROOT)), actions))

    verb = "would change" if args.dry_run else "changed"
    print(f"{verb}: {len(changed)} files")
    tally: dict[str, int] = {}
    for _, actions in changed:
        for a in actions:
            tally[a] = tally.get(a, 0) + 1
    for a, n in sorted(tally.items()):
        print(f"  {a}: {n}")
    if args.dry_run:
        for rel, actions in changed:
            print(f"    {rel}  [{', '.join(actions)}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
