#!/usr/bin/env python3
"""Publish the scheduled blog drips on each post's slot date.

Drives one or more series (currently "After the Close" and the AI-visibility
track "Found by the Machine"). This script is idempotent and self-reconciling.
On every run it derives the desired LIVE state purely from today's date plus the
canonical sources in _scheduled/<series>/, then writes only what changed.
Running it twice in a row is a no-op; running it after a new slot date promotes
exactly the newly-due posts.

For each due post (date <= today) it:
  1. Copies _scheduled/<series>/<slug>.html -> blog/<slug>.html, removing any
     in-series forward "next ->" nav link whose target post is not yet live
     (so there are never broken links during the staggered drip; the link
     reappears automatically once its target post goes live).
  2. Rebuilds that series' card grid in blog/index.html (newest first) between
     the series' <!-- *-GRID-START --> / <!-- *-GRID-END --> markers.
  3. Rebuilds that series' block in llms.txt between its
     <!-- *-LLMS-START --> / <!-- *-LLMS-END --> markers.

It does NOT git commit/push -- the GitHub Action does that if anything changed.

Adding a new series: drop an entry in SERIES below, create
_scheduled/<key>/manifest.json + post HTML, and add the matching marker pairs to
blog/index.html and llms.txt. A series whose dir/manifest is absent is skipped.

Usage:
  python _scripts/publish_scheduled.py                # today (UTC date)
  python _scripts/publish_scheduled.py --date 2026-07-14   # simulate a date
  python _scripts/publish_scheduled.py --check        # report only, write nothing
"""
import argparse
import datetime
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "blog"
INDEX = BLOG_DIR / "index.html"
LLMS = ROOT / "llms.txt"

BASE_URL = "https://www.mainstreetiq.com"

# --- Series registry ---------------------------------------------------------
# Each series promotes its own posts and owns its own marker pair in index.html
# and llms.txt. Order does not matter; each is reconciled independently.
SERIES = [
    {
        "key": "atc",
        "case_tag": "After the Close",
        "llms_title": "After the Close Series",
        "grid_start": "<!-- ATC-GRID-START -->",
        "grid_end": "<!-- ATC-GRID-END -->",
        "llms_start": "<!-- ATC-LLMS-START -->",
        "llms_end": "<!-- ATC-LLMS-END -->",
    },
    {
        "key": "aiv",
        "case_tag": "AI Visibility",
        "llms_title": "Found by the Machine Series",
        "grid_start": "<!-- AIV-GRID-START -->",
        "grid_end": "<!-- AIV-GRID-END -->",
        "llms_start": "<!-- AIV-LLMS-START -->",
        "llms_end": "<!-- AIV-LLMS-END -->",
    },
]


def load_posts(series_dir):
    data = json.loads((series_dir / "manifest.json").read_text(encoding="utf-8"))
    return data["posts"]


def strip_unlive_forward_links(html_text, all_slugs, live_slugs):
    """Within each <nav class="post-nav">...</nav> block, drop any anchor that
    points to an in-series post that is not yet live. Backward links, related
    links, and external links are always kept."""
    def nav_repl(m):
        block = m.group(0)

        def anchor_repl(am):
            slug = am.group(1)
            if slug in all_slugs and slug not in live_slugs:
                return ""  # not yet live -> remove this anchor (and its leading whitespace)
            return am.group(0)

        return re.sub(
            r'\s*<a href="/blog/([a-z0-9-]+)"[^>]*>.*?</a>',
            anchor_repl,
            block,
            flags=re.DOTALL,
        )

    return re.sub(
        r'<nav class="post-nav">.*?</nav>',
        nav_repl,
        html_text,
        flags=re.DOTALL,
    )


def build_card(post, case_tag):
    title = html.escape(post["title"], quote=False)
    desc = html.escape(post["card_desc"], quote=False)
    tag = html.escape(case_tag, quote=False)
    return (
        f'        <a href="/blog/{post["slug"]}" class="blog-card">\n'
        f'          <div class="blog-card-body">\n'
        f'            <span class="case-tag">{tag}</span>\n'
        f"            <h3>{title}</h3>\n"
        f"            <p>{desc}</p>\n"
        f'            <div class="blog-card-meta">\n'
        f'              <time datetime="{post["month_datetime"]}">{post["month_label"]}</time>\n'
        f"              <span>{post['read_min']} min read</span>\n"
        f"            </div>\n"
        f"          </div>\n"
        f"        </a>"
    )


def build_llms_block(due_newest_first, llms_title, total):
    n = len(due_newest_first)
    lines = [f"### {llms_title} ({n} of {total} parts live)"]
    # llms.txt reads naturally oldest-first within a series
    for post in reversed(due_newest_first):
        lines.append(
            f'- [{post["title"]}]({BASE_URL}/blog/{post["slug"]}): {post["llms_desc"]}'
        )
    return "\n".join(lines)


def replace_between(text, start, end, new_inner):
    # capture the indentation that precedes the start marker so the regenerated
    # end marker lines up the same way in whichever file we are editing.
    m = re.search(r"^([ \t]*)" + re.escape(start), text, re.MULTILINE)
    if not m:
        raise SystemExit(f"Marker not found: {start}")
    indent = m.group(1)
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{new_inner}\n{indent}{end}"
    return pattern.sub(lambda _m: replacement, text, count=1)


def write_if_changed(path, new_text, changed, check):
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == new_text:
        return
    changed.append(str(path.relative_to(ROOT)))
    if not check:
        path.write_text(new_text, encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="ISO date to simulate (default: today UTC)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    today = args.date or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    changed = []
    summary = []

    # Read index/llms once, apply every series' grid/llms edits, write once.
    idx = INDEX.read_text(encoding="utf-8")
    llms = LLMS.read_text(encoding="utf-8")

    for series in SERIES:
        series_dir = ROOT / "_scheduled" / series["key"]
        if not (series_dir / "manifest.json").exists():
            continue  # series not set up yet -> skip cleanly

        posts = load_posts(series_dir)
        all_slugs = {p["slug"] for p in posts}
        due = [p for p in posts if p["date"] <= today]
        live_slugs = {p["slug"] for p in due}

        # 1. promote each due post into blog/ (forward links hidden until target live)
        for p in due:
            src = (series_dir / f"{p['slug']}.html").read_text(encoding="utf-8")
            out = strip_unlive_forward_links(src, all_slugs, live_slugs)
            write_if_changed(BLOG_DIR / f"{p['slug']}.html", out, changed, args.check)

        # 2. rebuild this series' index grid + 3. its llms block (cards newest-first)
        if due:
            due_newest_first = sorted(due, key=lambda p: p["date"], reverse=True)
            cards = "\n\n".join(build_card(p, series["case_tag"]) for p in due_newest_first)
            idx = replace_between(idx, series["grid_start"], series["grid_end"], cards)
            llms = replace_between(
                llms,
                series["llms_start"],
                series["llms_end"],
                build_llms_block(due_newest_first, series["llms_title"], len(posts)),
            )

        summary.append(f"{series['key']}={len(due)}/{len(posts)}")

    write_if_changed(INDEX, idx, changed, args.check)
    write_if_changed(LLMS, llms, changed, args.check)

    print(f"date={today} {' '.join(summary)}")
    if changed:
        print("CHANGED:")
        for c in changed:
            print(f"  {c}")
    else:
        print("No changes (already in sync).")
    # exit 0 always; the workflow decides whether to commit based on git status
    return 0


if __name__ == "__main__":
    sys.exit(main())
