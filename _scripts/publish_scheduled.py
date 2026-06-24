#!/usr/bin/env python3
"""Publish the scheduled "After the Close" blog drip on each post's slot date.

This script is idempotent and self-reconciling. On every run it derives the
desired LIVE state purely from today's date plus the canonical sources in
_scheduled/atc/, then writes only what changed. Running it twice in a row is a
no-op; running it after a new slot date promotes exactly the newly-due posts.

For each due post (date <= today) it:
  1. Copies _scheduled/atc/<slug>.html -> blog/<slug>.html, removing any
     in-series forward "next ->" nav link whose target post is not yet live
     (so there are never broken links during the staggered drip; the link
     reappears automatically once its target post goes live).
  2. Rebuilds the "After the Close" card grid in blog/index.html (newest first)
     between the <!-- ATC-GRID-START --> / <!-- ATC-GRID-END --> markers.
  3. Rebuilds the After the Close block in llms.txt between the
     <!-- ATC-LLMS-START --> / <!-- ATC-LLMS-END --> markers.

It does NOT git commit/push -- the GitHub Action does that if anything changed.

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
ATC_DIR = ROOT / "_scheduled" / "atc"
BLOG_DIR = ROOT / "blog"
INDEX = BLOG_DIR / "index.html"
LLMS = ROOT / "llms.txt"
MANIFEST = ATC_DIR / "manifest.json"

GRID_START = "<!-- ATC-GRID-START -->"
GRID_END = "<!-- ATC-GRID-END -->"
LLMS_START = "<!-- ATC-LLMS-START -->"
LLMS_END = "<!-- ATC-LLMS-END -->"

BASE_URL = "https://www.mainstreetiq.com"


def load_posts():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
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


def build_card(post):
    title = html.escape(post["title"], quote=False)
    desc = html.escape(post["card_desc"], quote=False)
    return (
        f'        <a href="/blog/{post["slug"]}" class="blog-card">\n'
        f'          <div class="blog-card-body">\n'
        f'            <span class="case-tag">After the Close</span>\n'
        f"            <h3>{title}</h3>\n"
        f"            <p>{desc}</p>\n"
        f'            <div class="blog-card-meta">\n'
        f'              <time datetime="{post["month_datetime"]}">{post["month_label"]}</time>\n'
        f"              <span>{post['read_min']} min read</span>\n"
        f"            </div>\n"
        f"          </div>\n"
        f"        </a>"
    )


def build_llms_block(due_newest_first):
    n = len(due_newest_first)
    lines = [f"### After the Close Series ({n} of 7 parts live)"]
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

    posts = load_posts()
    all_slugs = {p["slug"] for p in posts}
    due = [p for p in posts if p["date"] <= today]
    live_slugs = {p["slug"] for p in due}
    changed = []

    # 1. promote each due post into blog/ (forward links hidden until target live)
    for p in due:
        src = (ATC_DIR / f"{p['slug']}.html").read_text(encoding="utf-8")
        out = strip_unlive_forward_links(src, all_slugs, live_slugs)
        write_if_changed(BLOG_DIR / f"{p['slug']}.html", out, changed, args.check)

    # 2. rebuild index grid + 3. rebuild llms block (newest-first for cards)
    due_newest_first = sorted(due, key=lambda p: p["date"], reverse=True)
    if due:
        cards = "\n\n".join(build_card(p) for p in due_newest_first)
        idx = INDEX.read_text(encoding="utf-8")
        idx = replace_between(idx, GRID_START, GRID_END, cards)
        write_if_changed(INDEX, idx, changed, args.check)

        llms = LLMS.read_text(encoding="utf-8")
        llms = replace_between(llms, LLMS_START, LLMS_END, build_llms_block(due_newest_first))
        write_if_changed(LLMS, llms, changed, args.check)

    print(f"date={today} due={len(due)}/{len(posts)} live={sorted(live_slugs)}")
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
