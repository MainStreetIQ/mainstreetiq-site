"""
build_ai_visibility_pages.py — generate the AI-visibility county landing pages
(`ai-visibility-<county>.html`) AND their sitegen sources (`_content/<same>.html`).

WINERY-ONLY FROM 2026-10-27 (Scott, site-cleanup ruling 4). AI discoverability
outside wine is not its own service; it is part of how the Fractional CFO work
reads a business. So:
  - santa-barbara and san-luis-obispo are WINERY-ONLY pages under Wine Country
    Intelligence: no non-wine segment cards, no DTC / wellness / elective
    medicine pitch, no "outbound", never "the practice" as the company name.
  - ventura, los-angeles, orange-county and san-diego are RETIRED. They are
    hand-written redirect stubs to /fractional-cfo-<county>, listed in sitegen's
    BESPOKE skip list. This script no longer emits them; do not add them back.

Both outputs are written on every run: the root HTML (what Pages serves) and the
`_content/` source (what `sitegen.py build` renders). The source is derived with
sitegen's own build_content() and must round-trip to the root file byte for byte,
or the run fails. That is what keeps `sitegen.py build --check` at 0 drift.

Why a generator: the pages share ~80% boilerplate (nav, footer, the shift,
what-we-read, surface-optimize-manage, scripts). Per-county copy, cities, hero
image, and FAQ live in COUNTIES below; everything else is one template.

PROOF CONSTRAINT (do not "fix" this into symmetry):
The Wine Country Intelligence Report covers Santa Barbara and San Luis Obispo
counties only. Never quote a wine figure on a county page (see EVERGREEN below), and
never imply the benchmark measured a county it did not. So:

EVERGREEN from 2026-10-10 (Scott: "I only want to have to update one page every
quarter"). The county pages carry NO quarterly figure: the stat slot reads "7 categories"
and the copy points to the report page, which is the one page refreshed each quarter.
Do not reintroduce a per-county number here; the stat_invisible field is retired.
Census vs scored (base gate brief): "benchmarks every tracked winery" describes the
census and is accurate; a SCORED claim never says "every tracked". AI naming is NOT
in the score: the stat caption names a score category (Citation Readiness), and the
lead-in says naming is read "beside a score on seven categories".

REFRESHED 2026-10-09 to Q3 2026 (WCI bundle.json build 4011d659f802). The Q3
story is concentration, not invisibility: 388 of 442 wineries were named at least
once for their own county, and 45 of 442 account for 47.5% of every naming. That
headline is REGION-wide, so it does not go on a county page. Each measured county
page now carries its own county's "never named in an answer to its own county's
questions" count: Santa Barbara 16 of 169, San Luis Obispo 38 of 273. Use that
exact meaning only; never restate it as "invisible to AI".

SUPERSEDED HISTORY below (every instruction in it is void since 2026-10-10;
kept for context only).

REFRESHED 2026-07-30 to Q2 2026. Was "86 of 175 AI-visible" from the Q1 edition.
Q2 measured SB at 100 of 171 cited, so the visible-side framing now describes a
MAJORITY and no longer supports the word "only". The stat was flipped to the
invisible side, which is the honest read of the same measurement and preserves
the loss-aversion frame: 71 of 171 SB tasting rooms are named by no AI assistant.
The rest of the site carries the REGION-wide version of that same figure (228 of
423 across both counties); this page stays SB-scoped on purpose, see below.
  - santa-barbara carries the SB-scoped invisible stat (71 of 171), labeled as SB County.
  - san-luis-obispo moved from the "covered" variant to "measured" on 2026-08-05
    (Scott's ruling): Q2 published an SLO-specific count (95 of 252 cited), so the
    page now carries the SLO-scoped invisible stat, 157 of 252. Each measured
    county prints ITS OWN county-scoped figure via the stat_invisible field;
    never print one county's number on the other's page.
  - ventura / los-angeles / orange-county / san-diego carried NO local wine stat
    (the "method" variant). Those pages were retired to redirect stubs on
    2026-10-27 and the "method" branch was removed with them. Extrapolating the
    SB number to a county it was never measured in is still exactly what
    reality-checker and compliance-review block on.

Run from msiq-site root:
    python3 _scripts/build_ai_visibility_pages.py            # write files
    python3 _scripts/build_ai_visibility_pages.py --dry-run  # report only

Idempotent: regenerating produces byte-identical output for unchanged input.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sitegen import (PARAM_CLOSE, PARAM_OPEN, RE_HEAD, detect_asset_params,  # noqa: E402
                     render_content, render_footer, render_nav, tokenize_head)  # one copy of the chrome

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.mainstreetiq.com"

COUNTIES = [
    {
        "slug": "san-luis-obispo",
        "home_turf": True,
        "article": "a",
        "county": "San Luis Obispo County",
        "short": "San Luis Obispo",
        "geo_placename": "San Luis Obispo, California",
        "hero_img": "slo-downtown.jpg",
        "cities": ["San Luis Obispo", "Paso Robles", "Templeton", "Atascadero", "Arroyo Grande"],
        "wcir": "measured",  # Q2 2026 published the SLO count; switched from "covered" per Scott 2026-08-05
        "audience_line": ("Small and family wineries across Paso Robles, Templeton, the Edna Valley, "
                          "and the Arroyo Grande Valley."),
        "local_para": (
            "San Luis Obispo County has hundreds of tasting rooms, from Paso Robles and Templeton to "
            "the Edna Valley and the Arroyo Grande Valley, and a visitor has to find one before they "
            "can choose it. When the search that used to surface a map of pins now returns a handful "
            "of names, being one of them is the whole game."),
    },
    {
        "slug": "santa-barbara",
        "home_turf": True,
        "article": "a",
        "county": "Santa Barbara County",
        "short": "Santa Barbara",
        "geo_placename": "Santa Barbara, California",
        "hero_img": "santa-barbara-waterfront.jpg",
        "cities": ["Santa Barbara", "Santa Ynez", "Solvang", "Buellton",
                   "Los Olivos", "Lompoc", "Santa Maria"],
        "wcir": "measured",  # SB-scoped invisible figure
        "audience_line": ("Small and family wineries across the Santa Ynez Valley, the Sta. Rita "
                          "Hills, and the Santa Maria Valley."),
        "local_para": (
            "Between the Santa Ynez Valley, Solvang, Los Olivos, and the Sta. Rita Hills, Santa "
            "Barbara County packs a dense field of wineries into the same short AI answer, and "
            "the gap between the ones the models name and the ones they skip is already wide."),
    },
]


# ---------------------------------------------------------------- proof block

def proof_section(c):
    """Wine proof, scoped honestly per county. See PROOF CONSTRAINT in the docstring.

    It describes a published MEASUREMENT, not a proven result: the report benchmarks
    which wineries AI names; it does not show that our fixes raise anyone's visibility.
    """
    if c["wcir"] == "measured":
        body = f"""        <p>Wine is where the AI-search shift hit hardest and earliest, and {c['county']} is where we measure it and publish the result. A visitor searching for the best wineries in the county used to get a map; now they get a three-to-five-name answer, and the wineries left off it lose the visit.</p>
        <p>The <a href="/wine-country-intelligence" style="color: var(--color-sky);">Wine Country Intelligence Report</a> benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties on exactly this: which wineries the AI answer names, and how often, beside a score on seven categories. This county's standings are in the latest edition.</p>
        <div class="stat-bar" style="border-top-color: rgba(255,255,255,0.15); margin-top: 1.5rem;">
          <div class="stat-item">
            <p class="stat-num" style="color: var(--color-sky);">7 categories</p>
            <p style="color: rgba(255,255,255,0.7);">Including whether an AI assistant reading a winery's site can get the facts out</p>
          </div>
          <div class="stat-item">
            <p class="stat-num" style="color: var(--color-sky);">Every quarter</p>
            <p style="color: rgba(255,255,255,0.7);">The county benchmark is rebuilt on a quarterly cycle</p>
          </div>
          <div class="stat-item">
            <p class="stat-num" style="color: var(--color-sky);">Monthly</p>
            <p style="color: rgba(255,255,255,0.7);">With Monitor, a winery's own AI visibility is re-checked every month between editions</p>
          </div>
        </div>
        <div class="hero-buttons" style="margin-top: 1.5rem;">
          <a href="/wine-country-intelligence" class="btn btn-white">Read the quarterly report &rarr;</a>
          <a href="/wineries" class="btn btn-outline-white">How the wine work runs</a>
        </div>"""
    elif c["wcir"] == "covered":
        body = f"""        <p>Wine is where the AI-search shift hit hardest and earliest, so it is where we built the measurement and publish it. A visitor searching for the best wineries in the county used to get a map; now they get a three-to-five-name answer, and the wineries left off it lose the visit.</p>
        <p>The <a href="/wine-country-intelligence" style="color: var(--color-sky);">Wine Country Intelligence Report</a> benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties on exactly that question: who the AI answer names, and who it skips. {c['county']} is inside that footprint, which means the read here runs against a benchmark we already publish rather than one we invent for the engagement.</p>
        <div class="hero-buttons" style="margin-top: 1.5rem;">
          <a href="/wine-country-intelligence" class="btn btn-white">Read the quarterly report &rarr;</a>
          <a href="/wineries" class="btn btn-outline-white">How the wine work runs</a>
        </div>"""
    else:
        raise ValueError(f"{c['slug']}: only 'measured' and 'covered' remain; the 'method' "
                         f"variant was retired with its four pages on 2026-10-27")
    return f"""  <!-- ===== PROOF ===== -->
  <section class="bg-navy">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Where we measure it in public</span>
        <h2 class="section-title">A benchmark we publish every quarter</h2>
      </div>
      <div class="container-narrow" style="max-width: 820px; margin: 0 auto; font-size: 1.05rem; line-height: 1.7;">
{body}
      </div>
    </div>
  </section>"""


# ------------------------------------------------------------------- schema

def area_served(c):
    county_area = {"@type": "AdministrativeArea", "name": f"{c['county']}, California"}
    out = [county_area]
    for city in c["cities"]:
        out.append({"@type": "City", "name": city,
                    "containedInPlace": {"@type": "AdministrativeArea",
                                         "name": f"{c['county']}, California"}})
    return out


def faqs(c):
    short, county = c["short"], c["county"]
    if c["wcir"] == "measured":
        measure = (f"We built the measurement in wine and publish it. The Wine Country Intelligence "
                   f"Report benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties "
                   f"on AI visibility, including how many {county} wineries are never named in an AI answer "
                   f"to their own county's questions, and publishes the results every quarter. That same benchmark is how we read where your winery stands: which "
                   f"surfaces the AI answer is built from, where you show up, and where you are absent. "
                   f"Then we name the fixes, and with Monitor we re-check your visibility every month.")
    elif c["wcir"] == "covered":
        measure = (f"We built the measurement in wine and publish it. The Wine Country Intelligence "
                   f"Report benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties "
                   f"on AI visibility, so {county} sits inside a benchmark we already run rather than one "
                   f"invented for the engagement. The read is the same for every winery here: which "
                   f"surfaces the AI answer is built from, where you show up, where you are absent, then "
                   f"the fixes, and with Monitor a re-check every month.")
    else:
        raise ValueError(f"{c['slug']}: unknown wcir variant {c['wcir']!r}")

    return [
        (f"How do I get my {short} winery to show up in AI search?",
         f"Start by finding out where you currently stand, because the answer is rarely where owners "
         f"assume. The models build their recommendation from your whole footprint, not just your "
         f"website: reviews, directory and map listings, third-party mentions, the schema on your pages, "
         f"and the wider citation trail around your name. We read all of it and rank the gaps by what "
         f"actually moves visitors toward your tasting room. The first step is a 30-minute Intro Call."),
        (f"Why is another winery showing up in AI answers in {county} and mine is not?",
         f"Usually not because their wine is better. It is because they are legible to the model and "
         f"you are not. A winery with consistent listings, current reviews, structured pages, and a "
         f"citation footprint the model can corroborate will be named ahead of a better winery whose "
         f"signals are thin, stale, or contradictory across sources. That gap is usually fixable, and it is "
         f"mostly fixable off your own website."),
        (f"How is this different from SEO for {short}?",
         f"SEO optimizes for a ranked page of blue links a person scrolls. AI discoverability optimizes "
         f"for a single synthesized answer a model hands back, where there is no page two. The signals "
         f"overlap but they are not the same: the model builds its answer largely from your external "
         f"citation footprint rather than your own pages, so the lever that moves AI visibility usually "
         f"lives off your website. We read both layers and the classical-search layer underneath them."),
        (f"How do you measure AI visibility in {county}?", measure),
        (f"Which wineries in {county} is this for?",
         f"{c['audience_line']} This page covers the AI-visibility work for wineries, which runs as "
         f"Wine Country Intelligence. If visitors are starting to ask AI which wineries to visit, "
         f"the work applies to you."),
    ]


# ----------------------------------------------------------------- template

def render(c, tokens=False):
    """The page. tokens=True leaves sitegen's {{nav}} / {{footer}} tokens in place of the chrome."""
    slug = f"ai-visibility-{c['slug']}"
    url = f"{BASE}/{slug}"
    county, short = c["county"], c["short"]
    nav, footer = (("{{nav}}", "{{footer}}") if tokens
                   else (render_nav({}), render_footer({})))
    cities_prose = ", ".join(c["cities"][:-1]) + ", and " + c["cities"][-1]
    article = c["article"]

    # Geographic honesty: only SLO and Santa Barbara are ON the Central Coast. The other four
    # counties are SERVED FROM it. Claiming "based here" on a San Diego page is simply false,
    # and the CFO-lane sibling already gets this right.
    if c["home_turf"]:
        base_clause = "Main Street IQ is based here on the Central Coast."
        stat3_num, stat3_cap = "Central Coast", "Where Main Street IQ is based"
    else:
        base_clause = f"Main Street IQ serves {county} from California's Central Coast."
        stat3_num, stat3_cap = "6 counties", "Where we work in person"

    # Orange County's short name IS its county name, so cities[1] alone would silently drop Irvine.
    meta_cities = (f"{c['cities'][0]} and {c['cities'][1]}" if short == county
                   else f"{short} and {c['cities'][1]}")
    faq_list = faqs(c)

    title = f"AI Visibility for {county} Wineries | Wine Country Intelligence | Main Street IQ"
    desc = (f"Visitors to {county} are asking AI which wineries to visit. Wine Country Intelligence from "
            f"Main Street IQ reads every place a visitor can find your winery across search, answer "
            f"engines, and AI chat, then ranks the fixes and tracks them. Serving {meta_cities}. "
            f"Veteran-owned.")
    og_desc = (f"Visitors to {county} are asking ChatGPT, Claude, and Gemini which wineries to visit. We find every "
               f"touchpoint that answer is built from, rank what to fix, and track it.")

    service_ld = {
        "@context": "https://schema.org", "@type": "Service",
        "name": f"AI Visibility for Wineries in {county}",
        "provider": {"@type": "ProfessionalService", "name": "Main Street IQ",
                     "sameAs": ["https://www.linkedin.com/company/107523729",
                                "https://www.linkedin.com/in/johnscotthess"],
                     "url": BASE},
        "serviceType": "AI discoverability and answer-engine optimization",
        "description": (f"Finding every touchpoint a visitor to {county} can "
                        f"use to discover a winery across classical search, answer engines, and "
                        f"generative AI chat, ranking the fixes and tracking them, read against the Wine Country Intelligence Report, the "
                        f"quarterly benchmark we publish for Santa Barbara and San Luis Obispo counties."),
        "areaServed": area_served(c),
        "audience": {"@type": "Audience",
                     "audienceType": "Wineries"},
        "url": url,
    }
    prof_ld = {
        "@context": "https://schema.org", "@type": "ProfessionalService", "name": "Main Street IQ",
        "sameAs": ["https://www.linkedin.com/company/107523729",
                   "https://www.linkedin.com/in/johnscotthess"],
        "description": (f"Veteran-owned and operated. AI visibility and answer-engine optimization "
                        f"for wineries in {county}, California, through Wine Country Intelligence."),
        "url": url,
        "award": ["Veteran-Owned Business"],
        "founder": {"@type": "Person", "name": "Scott Hess", "jobTitle": "Founder & Fractional CFO",
                    "url": "https://www.linkedin.com/in/johnscotthess",
                    "sameAs": ["https://www.linkedin.com/in/johnscotthess"],
                    "hasCredential": {"@type": "EducationalOccupationalCredential",
                                      "credentialCategory": "military-service",
                                      "name": "U.S. Navy Veteran"}},
        "areaServed": area_served(c),
        "serviceType": ["AI Discoverability", "AI Visibility", "Answer Engine Optimization",
                        "Generative Engine Optimization", "AI Search Optimization",
                        "Local Search Visibility", "Reputation and Listings Management"],
        "priceRange": "$$$$",
        "knowsAbout": [f"AI visibility {short}", f"AI search optimization {short}",
                       f"answer engine optimization {county}", "generative engine optimization",
                       "AI citation footprint", "schema markup", "local search visibility"],
    }
    crumb_ld = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Wine Country Intelligence",
             "item": f"{BASE}/wine-country-intelligence"},
            {"@type": "ListItem", "position": 3, "name": county, "item": url},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_list],
    }

    def ld(obj):
        return ('  <script type="application/ld+json">\n  '
                + json.dumps(obj, indent=2, ensure_ascii=False).replace("\n", "\n  ")
                + "\n  </script>")

    faq_html = "\n".join(f"""        <div class="faq-item">
          <button class="faq-question" aria-expanded="false">
            <span>{q}</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div class="faq-answer">
            <p>{a}</p>
          </div>
        </div>""" for q, a in faq_list)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="assets/logos/favicon.svg">
  <title>{title}</title>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-SBC31MGCEV"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-SBC31MGCEV');</script>
  <meta name="description" content="{desc}">
  <meta name="keywords" content="AI visibility {short} wineries, winery AI search {short}, answer engine optimization wineries {short}, generative engine optimization {county} wineries, get found on ChatGPT {short} winery, AI discoverability {county} wineries, winery AI SEO {short}">
  <link rel="canonical" href="{url}">
  <meta name="geo.region" content="US-CA">
  <meta name="geo.placename" content="{c['geo_placename']}">

  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{BASE}/assets/images/og-image.jpg">
  <meta property="og:locale" content="en_US">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{og_desc}">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">

  <!-- Structured Data: Service -->
{ld(service_ld)}

  <!-- Structured Data: ProfessionalService -->
{ld(prof_ld)}

  <!-- Structured Data: BreadcrumbList -->
{ld(crumb_ld)}

  <!-- Structured Data: FAQPage -->
{ld(faq_ld)}
</head>
<body>
  <a href="#main" class="skip-link">Skip to main content</a>

  <!-- ===== HEADER ===== -->
  {nav}

  <main id="main">

  <!-- ===== HERO ===== -->
  <section class="hero hero-has-bg">
    <img src="assets/images/locations/{c['hero_img']}" alt="" class="hero-bg" aria-hidden="true">
    <div class="hero-overlay"></div>
    <div class="container">
      <span class="section-label">Wine Country Intelligence | {county}, CA</span>
      <h1>Your next visitor in<br>{county} is asking AI.</h1>
      <p>When a visitor planning a trip here asks ChatGPT, Claude, or Gemini which wineries to visit, the answer names a few and skips the rest. Wine Country Intelligence, Main Street IQ's AI advisory work for wineries, finds every touchpoint that answer is built from, ranks what to fix, and tracks it, with the goal that more of the visitors already looking for a winery like yours arrive at your tasting room. Founder Scott Hess is a U.S. Navy veteran, and {base_clause}</p>
      <div class="hero-buttons">
        <a href="/intro-call" class="btn btn-white">Book an Intro Call &rarr;</a>
        <a href="/audit" class="btn btn-outline-white">Start with a finding</a>
      </div>
      <p style="font-size: 0.9rem; color: rgba(255,255,255,0.6); margin-top: 1rem; max-width: 560px;">Book a call, send a message, or just ask a question.</p>
      <div class="stat-bar">
        <div class="stat-item">
          <p class="stat-num">4 layers</p>
          <p>Search, answer engines, AI chat, reputation</p>
        </div>
        <div class="stat-item">
          <p class="stat-num">Monthly</p>
          <p>How often we re-check where you show up</p>
        </div>
        <div class="stat-item">
          <p class="stat-num">{stat3_num}</p>
          <p>{stat3_cap}</p>
        </div>
      </div>
      <p style="font-size: 0.95rem; color: rgba(255,255,255,0.75); margin-top: 1.5rem; max-width: 720px; letter-spacing: 0.5px;">Veteran-owned and operated.</p>
    </div>
  </section>

  <!-- ===== THE SHIFT ===== -->
  <section>
    <div class="container">
      <div class="section-header">
        <span class="section-label">Why this matters now</span>
        <h2 class="section-title">Discovery moved, and most wineries did not</h2>
      </div>
      <div style="max-width: 820px; margin: 0 auto; font-size: 1.1rem; line-height: 1.7;">
        <p>A visitor used to find you through a ranked page of links and a map of pins. They compared, they clicked, they decided. That funnel is still there, but a new one now sits in front of it: the visitor asks an AI which wineries to visit, reads one synthesized answer, and often stops there.</p>
        <p>{c['local_para']}</p>
        <p>That answer is not built from your website alone. The model assembles it from your reviews, your directory listings, the articles that mention you, the schema on your pages, and the wider citation footprint that surrounds your name. If those signals are thin or stale, you are absent from the answer no matter how good the wine is. Often the winery that gets named is not winning because it is better; it is winning because it is legible to the machine and you are not.</p>
      </div>
    </div>
  </section>

  <!-- ===== WHAT WE READ ===== -->
  <section class="bg-light">
    <div class="container">
      <div class="section-header">
        <span class="section-label">What we read</span>
        <h2 class="section-title">Every place a visitor to {short} can find you</h2>
        <p class="section-subtitle">Discoverability is not one channel. It is a footprint. We read all of it the way a CFO reads a P&amp;L, so the fixes are ranked by what actually moves visitors, not by what is easiest to do.</p>
      </div>
      <div class="card-grid">
        <div class="card">
          <h3>Classical search</h3>
          <p>Where you rank when a visitor types the query, and whether your pages are structured so a search engine can read what you pour, where, and when you are open. The layer everyone knows, still the floor everything else stands on.</p>
        </div>
        <div class="card">
          <h3>Answer engines</h3>
          <p>The AI-generated summary that now sits above the links, and the featured answers that quietly took the click before the AI did. Winning here means being the source the answer is built from, not a result buried below it.</p>
        </div>
        <div class="card">
          <h3>Generative AI chat</h3>
          <p>What ChatGPT, Claude, and Gemini say when a visitor asks them which wineries to visit in your region. This is decided by your external citation footprint, the part of your presence that lives off your own website, where most owners have never looked.</p>
        </div>
        <div class="card">
          <h3>Reputation and listings</h3>
          <p>Reviews, directories, maps, and the third-party mentions the models lean on to decide who is real and who is trusted. The signals that turn a name into a recommendation.</p>
        </div>
      </div>
      <p style="margin-top: 2rem; font-size: 1rem; max-width: 820px;">A <a href="/audit" style="color: var(--color-navy);">Website Audit</a> reads all four layers and hands back a severity-ranked fix list. <a href="/monitor" style="color: var(--color-navy);">Monitor</a> re-reads them every month, an outside check that catches drift the month it starts.</p>
    </div>
  </section>

  <!-- ===== HOW IT WORKS ===== -->
  <section>
    <div class="container">
      <div class="section-header">
        <span class="section-label">How the engine works</span>
        <h2 class="section-title">Surface, optimize, manage</h2>
        <p class="section-subtitle">Three moves that turn a scattered, invisible footprint into a managed one that keeps working while you run the winery.</p>
      </div>
      <div class="problem-list" style="max-width: 860px;">
        <div class="problem-item">
          <h3>1. Surface every touchpoint</h3>
          <p>We map the full set of places a visitor to {county} can discover you and score each one. You leave knowing exactly where you show up, where you are absent, and which gaps are costing you the most, instead of guessing which channel to chase this quarter.</p>
        </div>
        <div class="problem-item">
          <h3>2. Optimize what actually moves visitors</h3>
          <p>Not every fix is worth making. We sequence the work by what actually pulls visitors toward you, from the schema and pages you control to the citation footprint you influence, so effort lands where it compounds rather than where it is convenient.</p>
        </div>
        <div class="problem-item">
          <h3>3. Manage it as it drifts</h3>
          <p>The models change, competitors move, and a footprint left alone goes stale. Monitor is the outside check that the work is still working: it re-reads your visibility every month and flags the drift, so the gains you made in month one still hold in month twelve.</p>
        </div>
      </div>
      <p style="margin-top: 1.5rem; font-size: 0.95rem; color: var(--slate); max-width: 860px; font-style: italic;">The outcome we are after is simple: more of the visitors already planning a trip end up in your tasting room. How far that moves depends on your starting point and your own execution; we measure it against your real numbers rather than promise a figure.</p>
      <p style="margin-top: 1.5rem;"><a href="/intro-call" class="btn btn-primary">Start with an Intro Call &rarr;</a></p>
    </div>
  </section>

{proof_section(c)}

  <!-- ===== SERVICE AREA ===== -->
  <section class="bg-light">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Where we work</span>
        <h2 class="section-title">AI visibility for wineries across {county}</h2>
      </div>
      <div style="max-width: 820px; margin: 0 auto; font-size: 1.05rem; line-height: 1.7;">
        <p>We work with wineries across {cities_prose}. Main Street IQ is based on California's Central Coast, and {county} is one of six coastal counties where we work in person.</p>
        <p style="margin-top: 1.25rem;">Looking for the finance side instead? Our Fractional CFO line works in this county too: <a href="/fractional-cfo-{c['slug']}" style="color: var(--color-navy);">fractional CFO in {county} &rarr;</a></p>
      </div>
    </div>
  </section>

  <!-- ===== FAQ ===== -->
  <section class="bg-light">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Common questions</span>
        <h2 class="section-title">What {short} wineries ask about AI visibility</h2>
      </div>
      <div class="container-narrow" style="max-width: 820px; margin: 0 auto;">
{faq_html}
      </div>
    </div>
  </section>

  <!-- ===== FINAL CTA ===== -->
  <section class="bg-navy">
    <div class="container" style="text-align: center;">
      <h2 class="section-title">Find out where your winery shows up when {article} {short} visitor asks AI.</h2>
      <p style="max-width: 640px; margin: 0 auto 1.5rem; color: rgba(255,255,255,0.7);">One conversation. A straight read on where you stand and what moves it.</p>
      <div class="hero-buttons" style="justify-content: center;">
        <a href="/intro-call" class="btn btn-white">Book an Intro Call &rarr;</a>
      </div>
    </div>
  </section>

  </main>

  {footer}

  <script src="/assets/js/newsletter.js" defer></script>

  <script>
    const header = document.getElementById('site-header');
    window.addEventListener('scroll', () => {{
      header.classList.toggle('scrolled', window.scrollY > 20);
    }});
    const toggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    toggle.addEventListener('click', () => {{
      navLinks.classList.toggle('open');
      toggle.classList.toggle('active');
    }});
    document.querySelectorAll('a[href*="calendly.com"]').forEach(a => {{
      a.addEventListener('click', () => {{
        gtag('event', 'book_call_click', {{
          page_path: window.location.pathname,
          link_url: a.href
        }});
      }});
    }});

    // FAQ accordion toggle
    document.querySelectorAll('.faq-question').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const item = btn.parentElement;
        const isOpen = item.classList.contains('active');
        document.querySelectorAll('.faq-item').forEach(i => {{
          i.classList.remove('active');
          i.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
        }});
        if (!isOpen) {{
          item.classList.add('active');
          btn.setAttribute('aria-expanded', 'true');
        }}
      }});
    }});
  </script>

</body>
</html>
"""


def content_source(c, html):
    """The sitegen source for a generated page, built the way `sitegen extract` builds one:
    chrome as {{nav}} / {{footer}} tokens, head boilerplate as atom tokens. It must render
    back to the generated page byte for byte, or the run fails."""
    tok = render(c, tokens=True)
    params = detect_asset_params(tok)
    head = RE_HEAD.search(tok).group(1)
    head_tok, _used = tokenize_head(head, params)
    tok = tok.replace(head, head_tok, 1)
    params["nav"], params["footer"] = {}, {}
    content = (PARAM_OPEN + "\n" + json.dumps(params, indent=2, ensure_ascii=False) + "\n"
               + PARAM_CLOSE + "\n" + tok)
    if render_content(content) != html:
        raise SystemExit(f"ai-visibility-{c['slug']}: _content source does not round-trip")
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for c in COUNTIES:
        rel = f"ai-visibility-{c['slug']}.html"
        html = render(c)
        targets = [(ROOT / rel, html), (ROOT / "_content" / rel, content_source(c, html))]
        for path, text in targets:
            name = str(path.relative_to(ROOT))
            if args.dry_run:
                existing = path.read_text(encoding="utf-8") if path.exists() else None
                state = "unchanged" if existing == text else ("NEW" if existing is None else "would change")
                print(f"{name}: {state} ({len(text.splitlines())} lines)")
            else:
                path.write_text(text, encoding="utf-8")
                print(f"wrote {name} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
