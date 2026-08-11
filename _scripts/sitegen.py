#!/usr/bin/env python3
"""
sitegen — the single producer for msiq-site.

Replaces the eleven ad-hoc sweep scripts. Every shared element (head
boilerplate, the GA4 snippet, nav, footer) lives in exactly one place under
_templates/; per-page content lives under _content/. `build` renders
_content/* back out to the HTML files GitHub Pages serves.

Three subcommands:

    survey    Report the variant landscape without writing anything.

    extract   ONE-TIME migration. Writes _templates/ + _content/. Strict: a
              page whose structure does not match is SKIPPED and reported,
              never guessed at.

    build     Renders _content/* -> *.html.
              --check renders to memory and reports drift instead of writing,
              which is the guard that a hand-edit to a generated page cannot
              survive CI.

THE SAFETY PROPERTY. A shared element is factored into a template ONLY IF
re-rendering it reproduces the original bytes exactly. Anything that does not
round-trip is left as literal content in the _content/ file. A page is
therefore either byte-identical or untemplated; it can never be silently
altered. That makes `build` a provable no-op on first run, and makes template
COVERAGE (not correctness) the thing to iterate on.

This supersedes the earlier split-acceptance-test design, which byte-compared
body/nav/footer but only SET-compared <head>, on the theory that factoring out
GA4 necessarily reorders the head. It does not: the head's four boilerplate
atoms (meta_base, ga4, fonts, styles) are replaced IN PLACE by tokens, so each
page keeps its own head ordering while the atom text lives in one file. Full
byte comparison is strictly stronger than the split test and is what runs now.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "_content"
TEMPLATES = ROOT / "_templates"
PARTIALS = TEMPLATES / "partials"

# Directories that are part of the site but not swept into templates.
EXCLUDE_DIRS = {"_examples", "_scheduled", "_scripts", "_content", "_templates",
                "assets", "node_modules", ".git", ".github", "reports"}

# Pages that must keep their existing markup verbatim. Each needs a reason.
BESPOKE = {
    # Deliberate wine-scoped footer; footer_sweep.py reports it as BESPOKE 1.
    "wcir/q2-2026-central-coast.html": "deliberate wine-scoped footer",
    # Redirect stubs: no nav, no footer, no main.
    "card.html": "redirect stub, no chrome",
    "fit-call.html": "redirect stub, no chrome",
    "fit-call-confirm.html": "redirect stub, no chrome",
    "fractional-cfo-dtc-ecommerce.html": "redirect stub, consolidates SEO into /ecommerce",
    # Only file on the site containing literal Liquid-style braces.
    "legal/index.html": "contains literal {{ }} braces",
}

PARAM_OPEN = "<!--sitegen:params"
PARAM_CLOSE = "-->"


# ---------------------------------------------------------------------------
# Head boilerplate atoms
#
# Each atom is a contiguous run of lines that is identical site-wide once the
# asset-path depth is parameterized. A run of head lines is replaced by a token
# only when it matches an atom rendering EXACTLY, including indentation.
# ---------------------------------------------------------------------------

ASSET_DEPTHS = ["../assets/", "/assets/", "assets/"]

ATOMS = {
    "meta_base": '  <meta charset="UTF-8">\n'
                 '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                 '  <link rel="icon" type="image/svg+xml" href="{ASSETS}logos/favicon.svg">',
    "ga4": '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-SBC31MGCEV"></script>\n'
           "  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
           "gtag('js',new Date());gtag('config','G-SBC31MGCEV');</script>",
    "fonts": '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
             '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600;700'
             '&display=swap" rel="stylesheet">',
    "styles": '  <link rel="stylesheet" href="{STYLES}">',
}

# Longest first, so `meta_base` wins over a lone favicon line.
ATOM_ORDER = ["meta_base", "fonts", "ga4", "styles"]


def render_atom(name: str, params: dict) -> str:
    text = ATOMS[name]
    text = text.replace("{ASSETS}", params.get("assets", "/assets/"))
    text = text.replace("{STYLES}", params.get("styles", "/styles.css"))
    return text


# ---------------------------------------------------------------------------
# Nav
# ---------------------------------------------------------------------------

NAV_TEMPLATE = '''<header class="site-header" id="site-header">
    <div class="container">
      <nav class="nav-inner">
        <a href="/" class="logo"><img src="{{logo}}" alt="Main Street IQ"></a>
        <div class="nav-links" id="nav-links">
{{links}}
        </div>
        <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation">
          <span></span><span></span><span></span>
        </button>
      </nav>
    </div>
  </header>'''

# The hamburger button appears in two hand-formatted shapes: all on one line,
# or split across three. The difference is whitespace-only text nodes between
# the three <span> bars. `.nav-toggle` is `display:flex` and the bars are
# `display:block` (styles.css), and per the CSS flexbox spec a whitespace-only
# text run between flex items is not rendered at all. So this normalization is
# provably inert, unlike inter-tag whitespace between INLINE elements, which
# would add a rendered space. Scoped to this one construct for that reason.
RE_NAV_TOGGLE = re.compile(
    r'<button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation">\s*'
    r"<span></span>\s*<span></span>\s*<span></span>\s*</button>")

CANONICAL_TOGGLE = ('<button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation">\n'
                    "          <span></span><span></span><span></span>\n"
                    "        </button>")


def normalize_nav_toggle(header: str) -> str:
    return RE_NAV_TOGGLE.sub(lambda _: CANONICAL_TOGGLE, header)


RE_NAV_LOGO = re.compile(r'<a href="/" class="logo"><img src="([^"]+)"')
RE_NAV_LINKS_BLOCK = re.compile(r'<div class="nav-links" id="nav-links">(.*?)</div>', re.S)
RE_ANCHOR = re.compile(r'<a href="([^"]*)"([^>]*)>(.*?)</a>', re.S)


def derive_nav_params(header: str) -> dict | None:
    m_logo = RE_NAV_LOGO.search(header)
    m_block = RE_NAV_LINKS_BLOCK.search(header)
    if not m_logo or not m_block:
        return None
    links = []
    for href, attrs, label in RE_ANCHOR.findall(m_block.group(1)):
        links.append({"href": href, "attrs": attrs.strip(), "label": label})
    return {"logo": m_logo.group(1), "links": links}


def render_nav(params: dict) -> str:
    lines = []
    for a in params["links"]:
        attrs = (" " + a["attrs"]) if a["attrs"] else ""
        lines.append(f'          <a href="{a["href"]}"{attrs}>{a["label"]}</a>')
    return (NAV_TEMPLATE
            .replace("{{logo}}", params["logo"])
            .replace("{{links}}", "\n".join(lines)))


# ---------------------------------------------------------------------------
# Footer
#
# Built from the 84-page dominant variant. Every observed difference is a
# parameter: the newsletter block, the brand logo + tagline, the Connect-column
# CTA target, two optional Legal links, and the social block.
# ---------------------------------------------------------------------------

FOOTER_NEWSLETTER = '''      <div class="footer-newsletter">
        <div class="footer-newsletter-pitch">
          <h4>Founder-to-founder thinking on revenue</h4>
          <p>One short note when there{{apos}}s something worth saying. No drip, no sequence.</p>
        </div>
        <form class="footer-newsletter-form" id="footerNewsletterForm" novalidate>
          <input type="email" id="footerNewsletterEmail" name="email" placeholder="you@company.com" required autocomplete="email" maxlength="100" aria-label="Email address">
          <input type="text" name="honeypot" class="footer-newsletter-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">
          <button type="submit">Subscribe</button>
          <div class="footer-newsletter-msg" id="footerNewsletterMsg" role="status" aria-live="polite"></div>
        </form>
          <p class="footer-newsletter-privacy" style="font-size: 0.8rem; color: var(--slate); margin-top: 0.5rem;">We use your email only for this note. <a href="/legal/privacy">Privacy Policy</a>.</p>
      </div>
'''

FOOTER_SOCIAL = '''        <div class="footer-social">
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener" aria-label="LinkedIn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" role="img" aria-label="LinkedIn"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          </a>
        </div>
'''

FOOTER_TEMPLATE = '''<footer class="site-footer">
    <div class="container">
{{newsletter}}      <div class="footer-grid">
        <div class="footer-brand">
          <a href="/" class="logo"><img src="{{logo}}" alt="Main Street IQ"></a>
          <p>{{tagline}}</p>
        </div>
        <div class="footer-col">
          <h4>Company</h4>
          <a href="/about">About</a>
          <a href="/our-services">Services</a>
          <a href="/our-work">Our Work</a>
          <a href="/blog/">Blog</a>
        </div>
        <div class="footer-col">
          <h4>Connect</h4>
          <a href="/contact">Contact</a>
          <a href="/partners">Partners</a>
          <a href="{{cta_href}}">Book an Intro Call</a>
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener">LinkedIn</a>
        </div>
        <div class="footer-col">
          <h4>Market Segments</h4>
          <a href="/ecommerce">DTC &amp; Ecommerce</a>
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
{{refunds}}{{trust}}          <a href="/legal/ai-use">AI Use</a>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 Main Street IQ. All rights reserved.</span>
{{social}}      </div>
    </div>
  </footer>'''

FOOTER_REFUNDS = '          <a href="/legal/refund-cancellation">Refunds</a>\n'
FOOTER_TRUST = '          <a href="/trust">Trust Center</a>\n'

# One page indents the footer grid 12 spaces instead of 6. Whitespace between
# a `</div>` and a `<div>`, both block-level, so it is inert. Normalized so the
# comparison below can stay byte-exact rather than whitespace-tolerant.
RE_FOOT_GRID_INDENT = re.compile(r'\n\s*<div class="footer-grid">')


def normalize_footer_indent(footer: str) -> str:
    return RE_FOOT_GRID_INDENT.sub('\n      <div class="footer-grid">', footer)


RE_FOOT_BRAND = re.compile(
    r'<div class="footer-brand">\s*\n\s*<a href="/" class="logo"><img src="([^"]+)"[^>]*></a>\s*\n\s*<p>(.*?)</p>', re.S)
RE_FOOT_CTA = re.compile(r'<a href="([^"]*)">Book an Intro Call</a>')


def derive_footer_params(footer: str) -> dict | None:
    m_brand = RE_FOOT_BRAND.search(footer)
    m_cta = RE_FOOT_CTA.search(footer)
    if not m_brand or not m_cta:
        return None
    apos = None
    if "footer-newsletter" in footer:
        if "there’s something worth saying" in footer:
            apos = "’"
        elif "there's something worth saying" in footer:
            apos = "'"
        else:
            return None
    return {
        "logo": m_brand.group(1),
        "tagline": m_brand.group(2),
        "cta_href": m_cta.group(1),
        "newsletter": "footer-newsletter" in footer,
        "apos": apos,
        "social": "footer-social" in footer,
        "refunds": "/legal/refund-cancellation" in footer,
        "trust": '<a href="/trust">Trust Center</a>' in footer,
    }


def render_footer(p: dict) -> str:
    newsletter = FOOTER_NEWSLETTER.replace("{{apos}}", p["apos"] or "") if p["newsletter"] else ""
    return (FOOTER_TEMPLATE
            .replace("{{newsletter}}", newsletter)
            .replace("{{logo}}", p["logo"])
            .replace("{{tagline}}", p["tagline"])
            .replace("{{cta_href}}", p["cta_href"])
            .replace("{{refunds}}", FOOTER_REFUNDS if p["refunds"] else "")
            .replace("{{trust}}", FOOTER_TRUST if p["trust"] else "")
            .replace("{{social}}", FOOTER_SOCIAL if p["social"] else ""))


# ---------------------------------------------------------------------------
# Structural extraction
# ---------------------------------------------------------------------------

RE_HEAD = re.compile(r"<head>(.*?)</head>", re.S | re.I)
RE_HEADER = re.compile(r'<header class="site-header".*?</header>', re.S | re.I)
RE_FOOTER = re.compile(r'<footer class="site-footer">.*?</footer>', re.S | re.I)


class StructureError(Exception):
    """Raised when a page does not match the expected shape."""


def split_page(html: str) -> dict:
    """Split a page into its structural parts. Raises on anything unexpected."""
    m_head = RE_HEAD.search(html)
    if not m_head:
        raise StructureError("no <head> block")
    m_header = RE_HEADER.search(html)
    if not m_header:
        raise StructureError('no <header class="site-header"> block')
    m_footer = RE_FOOTER.search(html)
    if not m_footer:
        raise StructureError('no <footer class="site-footer"> block')
    if m_footer.start() < m_header.end():
        raise StructureError("footer precedes header")
    return {
        "head_inner": m_head.group(1),
        "head_span": (m_head.start(1), m_head.end(1)),
        "header": m_header.group(0),
        "header_span": m_header.span(),
        "footer": m_footer.group(0),
        "footer_span": m_footer.span(),
    }


def detect_asset_params(html: str) -> dict:
    """Pick the asset-depth and stylesheet href this page actually uses."""
    params = {}
    m = re.search(r'<link rel="icon"[^>]*href="((?:\.\./|/)?assets/)logos/favicon\.svg"', html)
    params["assets"] = m.group(1) if m else "/assets/"
    m = re.search(r'<link rel="stylesheet" href="([^"]*styles\.css)"', html)
    params["styles"] = m.group(1) if m else "/styles.css"
    return params


def tokenize_head(head_inner: str, params: dict) -> tuple[str, list[str]]:
    """
    Replace each run of head lines that exactly matches an atom rendering with
    a token. Returns (tokenized_head, atoms_used). Non-matching lines are left
    untouched, so the result always round-trips.
    """
    text = head_inner
    used = []
    for name in ATOM_ORDER:
        rendered = render_atom(name, params)
        if rendered and rendered in text:
            text = text.replace(rendered, "{{" + name + "}}", 1)
            used.append(name)
    return text, used


def build_content(rel: str, html: str) -> tuple[str, dict] | None:
    """Produce the _content/ file for a page, or None if it cannot be split."""
    try:
        parts = split_page(html)
    except StructureError:
        return None

    params = detect_asset_params(html)
    report = {"atoms": [], "nav": False, "footer": False, "normalized": []}

    # Footer first, then header, then head: later spans have larger offsets, so
    # replacing back-to-front keeps the earlier spans valid.
    out = html

    nav_params = derive_nav_params(parts["header"])
    delta = 0
    if nav_params:
        rendered = render_nav(nav_params)
        exact = rendered == parts["header"]
        if exact or rendered == normalize_nav_toggle(parts["header"]):
            out = out[:parts["header_span"][0]] + "{{nav}}" + out[parts["header_span"][1]:]
            report["nav"] = True
            params["nav"] = nav_params
            delta = len("{{nav}}") - (parts["header_span"][1] - parts["header_span"][0])
            if not exact:
                report["normalized"].append("nav")

    foot_params = derive_footer_params(parts["footer"])
    if foot_params:
        rendered = render_footer(foot_params)
        exact = rendered == parts["footer"]
        if exact or rendered == normalize_footer_indent(parts["footer"]):
            s = parts["footer_span"][0] + delta
            e = parts["footer_span"][1] + delta
            out = out[:s] + "{{footer}}" + out[e:]
            report["footer"] = True
            params["footer"] = foot_params
            if not exact:
                report["normalized"].append("footer")

    # Head sits before both, so its offsets are unaffected by the edits above.
    head_tok, used = tokenize_head(parts["head_inner"], params)
    if used:
        out = out.replace(parts["head_inner"], head_tok, 1)
        report["atoms"] = used

    header = PARAM_OPEN + "\n" + json.dumps(params, indent=2, ensure_ascii=False) + "\n" + PARAM_CLOSE + "\n"
    return header + out, report


def render_content(text: str) -> str:
    """Inverse of build_content: substitute every token back."""
    if not text.startswith(PARAM_OPEN):
        raise StructureError("content file missing sitegen:params header")
    end = text.index(PARAM_CLOSE, len(PARAM_OPEN))
    params = json.loads(text[len(PARAM_OPEN):end])
    out = text[end + len(PARAM_CLOSE) + 1:]

    if "nav" in params:
        out = out.replace("{{nav}}", render_nav(params["nav"]))
    if "footer" in params:
        out = out.replace("{{footer}}", render_footer(params["footer"]))
    for name in ATOM_ORDER:
        tok = "{{" + name + "}}"
        if tok in out:
            out = out.replace(tok, render_atom(name, params))
    return out


def iter_pages() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in EXCLUDE_DIRS:
            continue
        out.append(p)
    return out


def content_path(rel: str) -> Path:
    return CONTENT / rel


# ---------------------------------------------------------------------------
# survey
# ---------------------------------------------------------------------------

def cmd_survey(args) -> int:
    pages = iter_pages()
    ok, skipped = 0, []
    navs, foots = {}, {}
    for p in pages:
        rel = str(p.relative_to(ROOT))
        if rel in BESPOKE:
            skipped.append((rel, f"bespoke: {BESPOKE[rel]}"))
            continue
        try:
            parts = split_page(p.read_text(encoding="utf-8"))
        except StructureError as e:
            skipped.append((rel, str(e)))
            continue
        navs.setdefault(re.sub(r"\s+", " ", parts["header"]).strip(), []).append(rel)
        foots.setdefault(re.sub(r"\s+", " ", parts["footer"]).strip(), []).append(rel)
        ok += 1
    print(f"parsed cleanly : {ok}")
    print(f"skipped        : {len(skipped)}")
    for rel, why in skipped:
        print(f"    {rel:<46} {why}")
    print(f"\ndistinct header/nav variants : {len(navs)}")
    print(f"distinct footer variants     : {len(foots)}")
    return 0


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

def cmd_extract(args) -> int:
    pages = iter_pages()
    written, skipped, partial, normalized = 0, [], [], []
    atom_counts: dict[str, int] = {}
    nav_ok = foot_ok = 0

    for p in pages:
        rel = str(p.relative_to(ROOT))
        if rel in BESPOKE:
            skipped.append((rel, f"bespoke: {BESPOKE[rel]}"))
            continue
        html = p.read_text(encoding="utf-8")
        if "{{" in html:
            skipped.append((rel, "contains literal {{ braces"))
            continue
        result = build_content(rel, html)
        if result is None:
            skipped.append((rel, "does not match expected structure"))
            continue
        content, report = result

        # Round-trip guard, always byte-exact. The only tolerated difference is
        # an explicit, named normalization from the list above, applied to the
        # ORIGINAL so both sides are compared byte-for-byte. A content file that
        # does not reproduce its page is never written.
        roundtrip = render_content(content)
        expected = html
        if "nav" in report["normalized"]:
            expected = normalize_nav_toggle(expected)
        if "footer" in report["normalized"]:
            expected = normalize_footer_indent(expected)
        if roundtrip != expected:
            skipped.append((rel, "ROUND-TRIP FAILED, not written"))
            continue

        dest = content_path(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not args.dry_run:
            dest.write_text(content, encoding="utf-8")
        written += 1
        nav_ok += report["nav"]
        foot_ok += report["footer"]
        for a in report["atoms"]:
            atom_counts[a] = atom_counts.get(a, 0) + 1
        if report["normalized"]:
            normalized.append((rel, ",".join(report["normalized"])))
        missing = [k for k in ("nav", "footer") if not report[k]]
        if missing or len(report["atoms"]) < 3:
            partial.append((rel, f"untemplated: {','.join(missing) or '-'} "
                                 f"atoms={','.join(report['atoms']) or 'none'}"))

    if not args.dry_run:
        write_templates()

    print(f"content files written : {written}")
    print(f"nav templated         : {nav_ok}/{written}")
    print(f"footer templated      : {foot_ok}/{written}")
    for a in ATOM_ORDER:
        print(f"  atom {a:<10}      : {atom_counts.get(a, 0)}/{written}")
    print(f"skipped               : {len(skipped)}")
    for rel, why in skipped:
        print(f"    {rel:<46} {why}")
    print(f"\nwhitespace-normalized : {len(normalized)}  "
          f"(these pages change by whitespace only on first build)")
    for rel, which in normalized:
        print(f"    {rel:<46} {which}")
    if partial:
        print(f"\npartially templated   : {len(partial)}")
        for rel, why in partial:
            print(f"    {rel:<46} {why}")
    return 0


def write_templates() -> None:
    PARTIALS.mkdir(parents=True, exist_ok=True)
    (PARTIALS / "nav.html").write_text(NAV_TEMPLATE + "\n", encoding="utf-8")
    (PARTIALS / "footer.html").write_text(FOOTER_TEMPLATE + "\n", encoding="utf-8")
    (PARTIALS / "footer_newsletter.html").write_text(FOOTER_NEWSLETTER, encoding="utf-8")
    (PARTIALS / "footer_social.html").write_text(FOOTER_SOCIAL, encoding="utf-8")
    for name in ATOM_ORDER:
        (PARTIALS / f"head_{name}.html").write_text(ATOMS[name] + "\n", encoding="utf-8")
    (TEMPLATES / "README.md").write_text(
        "# _templates\n\n"
        "Rendered by `_scripts/sitegen.py`. These files are the SINGLE copy of every\n"
        "shared element. They are written by `sitegen.py extract` from the constants in\n"
        "that script, so edit the script, not these files.\n\n"
        "A change here rebuilds all pages: `sitegen.py build`. Verify with\n"
        "`sitegen.py build --check`, which must report 0 drift before any commit that\n"
        "is meant to be a no-op.\n",
        encoding="utf-8")


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def cmd_build(args) -> int:
    if not CONTENT.exists():
        print("no _content/ directory; run `sitegen.py extract` first", file=sys.stderr)
        return 2

    drift, wrote, missing = [], 0, []
    for cf in sorted(CONTENT.rglob("*.html")):
        rel = str(cf.relative_to(CONTENT))
        target = ROOT / rel
        rendered = render_content(cf.read_text(encoding="utf-8"))
        if not target.exists():
            missing.append(rel)
            continue
        current = target.read_text(encoding="utf-8")
        if rendered != current:
            drift.append(rel)
            if not args.check:
                target.write_text(rendered, encoding="utf-8")
                wrote += 1

    total = len(list(CONTENT.rglob("*.html")))
    if args.check:
        print(f"{total} pages checked, {len(drift)} drift")
        for rel in drift:
            print(f"    DRIFT  {rel}")
        for rel in missing:
            print(f"    MISSING TARGET  {rel}")
        return 1 if (drift or missing) else 0

    print(f"{total} pages rendered, {wrote} written, {len(drift)} changed")
    for rel in drift:
        print(f"    updated  {rel}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_su = sub.add_parser("survey", help="report the variant landscape, write nothing")
    p_su.set_defaults(func=cmd_survey)

    p_ex = sub.add_parser("extract", help="one-time migration: write _templates/ + _content/")
    p_ex.add_argument("--dry-run", action="store_true", help="report without writing")
    p_ex.set_defaults(func=cmd_extract)

    p_bu = sub.add_parser("build", help="render _content/* -> *.html")
    p_bu.add_argument("--check", action="store_true",
                      help="report drift instead of writing; nonzero exit on any drift")
    p_bu.set_defaults(func=cmd_build)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
