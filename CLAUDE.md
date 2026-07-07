# msiq-site — Operating Rules

Promoted from Scott's session memory (2026-07-06, agent-native plan P1). This file is CANONICAL for site mechanics; the memory files are one-line pointers back here. Composes with `~/MSIQ/CLAUDE.md` and `~/.claude/CLAUDE.md`.

## Deploy & publish mechanics

- **Deploy is GitHub Pages, on push to `main`** (the `pages-build-deployment` Action). This repo is its OWN git repo (`MainStreetIQ/mainstreetiq-site`), separate from the parent `~/MSIQ` repo. It is NOT on Vercel — `vercel.json` (19 redirects) and `.vercelignore` are DEAD config, inert on Pages (adjudication pending, plan P5). Before asserting anything about deploy behavior, probe the live surface (`curl -sI` headers, a URL that should/shouldn't exist) — config-file presence is weak evidence and has already put a wrong platform claim into a committed doc.
- **Draft privacy gate = Jekyll's underscore-directory exclusion.** `_scheduled/` and `_scripts/` stay off the live site ONLY because of the leading underscore. **NEVER add `.nojekyll`** (the common asset-fix reflex) — it would instantly publish every staged draft.
- **Scheduled publish:** `.github/workflows/scheduled-publish.yml` runs `_scripts/publish_scheduled.py` daily and stages ONLY `git add blog/ llms.txt`. A post change that also touches `sitemap.xml` or other files must be committed separately or it won't ship with the post.

## Blog drip system

- Posts stage in `_scheduled/<series>/` with a per-series `manifest.json`; the daily Action promotes each into `blog/` on its slot date and rebuilds the card grid in `blog/index.html` + the `llms.txt` block between marker pairs (`ATC-GRID-*`, `AIV-GRID-*`). Multi-series via the `SERIES` registry in the script. A NEW series needs: registry entry + `_scheduled/<key>/manifest.json` + post HTML + marker pairs in `blog/index.html` and `llms.txt`. Edit a pre-date post in its `_scheduled/` source; picked up on its cron run. Dry-run: `python _scripts/publish_scheduled.py --check` or `--date YYYY-MM-DD`.
- Blog posts drafted via the blog-draft skill must NOT include a `## TL;DR` heading in `body_md` — render.py builds the styled aside from the separate `tldr` field; a body TL;DR renders twice.
- LinkedIn is manual (batch docs in `~/MSIQ/_reference/linkedin-*.md`, loaded into LinkedIn's native scheduler). Only the blog auto-publishes.

## Verification harness

- Browser-verify style work before commit with `~/MSIQ/.venv/bin/python` + Playwright headless Chromium on `file://` URLs; screenshot to scratchpad and Read the PNG; catch JS errors via `page.on('pageerror')`. Desktop 1440x900 + mobile 390x844 covers both breakpoints.
- **`:focus-visible` must be verified with a real keyboard Tab** (`page.keyboard.press('Tab')` loop until `document.activeElement` is the target). Programmatic `element.focus()` + getComputedStyle false-negatives (outline reads back as currentColor).

## Gate adjudications

Settled checker false positives for this site's pages live in `~/.claude/skills/pre-publish-gate/adjudications.yaml` (injected into every checker prompt by the orchestrators). Highlights an agent editing site copy must know:

- "Website Audit" / "Website Audit Pro" are CURRENT service names (the 2026-05-20 rename was reverted 2026-05-22). Never "fix" them to Customer Acquisition Audit.
- Nationwide language is fine: six counties = outbound concentration + on-site availability, NOT client acceptance (canonical-facts § Geographic scope, amended 2026-07-03).
- "U.S. Navy Veteran" is the canonical phrasing (Entity table); LinkedIn not displaying it is not a contradiction.
- "verticals" vs "practices" is a Scott decision, not an auto-fix — "verticals" is the established sitewide convention.
- "Fit Call" is KILLED from all public-facing surfaces (Scott, 2026-07-05) — site copy, metas, JSON-LD, FAQ schema, CTAs. Do not reintroduce it.

Before editing copy on any checker's say-so, verify the finding against `~/MSIQ/canonical-facts.md` yourself — read the FULL change history for the item (renames get reverted; rules get amended).
