"""
build_ai_visibility_pages.py — generate the 6 AI Discoverability county landing
pages (`ai-visibility-<county>.html`).

Why a generator: the six pages share ~80% boilerplate (nav, footer, the shift,
what-we-read, surface-optimize-manage, scripts). Hand-authoring six 500-line
files guarantees drift. Per-county copy, cities, hero image, and FAQ live in
COUNTIES below; everything else is one template.

Lane note: these are the AI-visibility peers to the `fractional-cfo-<county>`
CFO-lane pages. Different search intent, different lane. `ai-cfo-<county>` is a
THIRD thing (a fractional CFO with an intelligence engine) and is CFO-lane.

PROOF CONSTRAINT (do not "fix" this into symmetry):
The Wine Country Intelligence Report covers Santa Barbara and San Luis Obispo
counties only, and the headline figure is SANTA BARBARA-scoped. So:

REFRESHED 2026-07-30 to Q2 2026. Was "86 of 175 AI-visible" from the Q1 edition.
Q2 measured SB at 100 of 171 cited, so the visible-side framing now describes a
MAJORITY and no longer supports the word "only". The stat was flipped to the
invisible side, which is the honest read of the same measurement and preserves
the loss-aversion frame: 71 of 171 SB tasting rooms are named by no AI assistant.
The rest of the site carries the REGION-wide version of that same figure (228 of
423 across both counties); this page stays SB-scoped on purpose, see below.
  - santa-barbara carries the 86/175 stat, labeled as SB County.
  - san-luis-obispo references the WCIR (which does cover SLO) but asserts NO
    SLO-specific visibility count, because we do not have one published.
  - ventura / los-angeles / orange-county / san-diego carry NO local wine stat.
    They describe the published method and are explicit that the benchmark was
    measured in wine, on the Central Coast. Extrapolating the SB number to a
    county it was never measured in is exactly what reality-checker and
    compliance-review block on.

Run from msiq-site root:
    python3 _scripts/build_ai_visibility_pages.py            # write files
    python3 _scripts/build_ai_visibility_pages.py --dry-run  # report only

Idempotent: regenerating produces byte-identical output for unchanged input.
"""

import argparse
import json
import sys
from pathlib import Path

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
        "cities": ["San Luis Obispo", "Paso Robles", "Templeton", "Atascadero",
                   "Arroyo Grande", "Pismo Beach", "Grover Beach", "Morro Bay", "Nipomo"],
        "wcir": "covered",   # in the WCIR footprint, but no published SLO-specific count
        "verticals_line": ("wineries across Paso Robles and the Edna Valley, DTC ecommerce brands, "
                           "health and wellness practices, and elective medicine practices"),
        "local_para": (
            "San Luis Obispo County runs on businesses a visitor or a buyer has to find before they "
            "can choose: tasting rooms in Paso Robles and the Edna Valley, practices in San Luis "
            "Obispo and Atascadero, brands shipping out of the Five Cities. When the search that "
            "used to surface a map of pins now returns a handful of names, being one of them is the "
            "whole game."),
    },
    {
        "slug": "santa-barbara",
        "home_turf": True,
        "article": "a",
        "county": "Santa Barbara County",
        "short": "Santa Barbara",
        "geo_placename": "Santa Barbara, California",
        "hero_img": "santa-barbara-waterfront.jpg",
        "cities": ["Santa Barbara", "Goleta", "Santa Ynez", "Solvang", "Buellton",
                   "Lompoc", "Los Olivos", "Carpinteria", "Montecito", "Santa Maria"],
        "wcir": "measured",  # the 71-of-171 invisible figure is SB-scoped
        "verticals_line": ("wineries across the Santa Ynez Valley and the Sta. Rita Hills, DTC "
                           "ecommerce brands, health and wellness practices, and elective medicine practices"),
        "local_para": (
            "Between the Santa Ynez Valley, Solvang, Los Olivos, and the Sta. Rita Hills, Santa "
            "Barbara County packs a dense field of businesses into the same short AI answer, and "
            "the gap between the ones the models name and the ones they skip is already wide."),
    },
    {
        "slug": "ventura",
        "home_turf": False,
        "article": "a",
        "county": "Ventura County",
        "short": "Ventura",
        "geo_placename": "Ventura, California",
        "hero_img": "ventura-coastline.jpg",
        "cities": ["Ventura", "Oxnard", "Camarillo", "Thousand Oaks", "Simi Valley",
                   "Moorpark", "Ojai", "Port Hueneme", "Santa Paula", "Fillmore"],
        "wcir": "method",
        "verticals_line": ("DTC ecommerce brands, health and wellness practices, elective medicine "
                           "practices, and wineries"),
        "local_para": (
            "Ventura County businesses sit close enough to Los Angeles to compete with its marketing "
            "budgets and far enough out to lose the default search result. When a buyer in Thousand "
            "Oaks or Camarillo asks an AI who to use, the answer is assembled from a footprint most "
            "owners here have never audited."),
    },
    {
        "slug": "los-angeles",
        "home_turf": False,
        "article": "a",
        "county": "Los Angeles County",
        "short": "Los Angeles",
        "geo_placename": "Los Angeles, California",
        "hero_img": "los-angeles-downtown.jpg",
        "cities": ["Los Angeles", "Santa Monica", "Beverly Hills", "West Hollywood",
                   "Manhattan Beach", "Culver City", "Pasadena", "Burbank", "Long Beach"],
        "wcir": "method",
        "verticals_line": ("DTC ecommerce brands, elective medicine practices, health and wellness "
                           "practices, and wineries"),
        "local_para": (
            "Los Angeles County is the hardest version of this problem: the category is crowded, the "
            "competitors spend heavily, and the AI answer still names only a few. Paid acquisition "
            "can buy attention here, but it cannot buy a place in the answer a buyer gets before "
            "they ever run a search you are bidding on."),
    },
    {
        "slug": "orange-county",
        "home_turf": False,
        "article": "an",
        "county": "Orange County",
        "short": "Orange County",
        "geo_placename": "Irvine, California",
        "hero_img": "newport-beach-harbor.jpg",
        "cities": ["Irvine", "Costa Mesa", "Newport Beach", "Anaheim", "Santa Ana",
                   "Huntington Beach", "Fullerton", "Laguna Beach", "Mission Viejo", "San Clemente"],
        "wcir": "method",
        "verticals_line": ("elective medicine practices, DTC ecommerce brands, health and wellness "
                           "practices, and wineries"),
        "local_para": (
            "Orange County concentrates exactly the businesses this shift hits hardest: "
            "high-consideration practices in Newport Beach and Irvine where a patient researches for "
            "weeks before booking, and DTC brands competing on a category term rather than a "
            "location. Both are decided by what the model says long before the first call."),
    },
    {
        "slug": "san-diego",
        "home_turf": False,
        "article": "a",
        "county": "San Diego County",
        "short": "San Diego",
        "geo_placename": "San Diego, California",
        "hero_img": "san-diego-skyline.jpg",
        "cities": ["San Diego", "La Jolla", "Del Mar", "Encinitas", "Carlsbad",
                   "Escondido", "Ramona", "Chula Vista"],
        "wcir": "method",
        "verticals_line": ("DTC ecommerce brands, health and wellness practices, elective medicine "
                           "practices, and wineries"),
        "local_para": (
            "San Diego County spreads demand across distinct markets, from La Jolla and Encinitas to "
            "Escondido and Chula Vista, and a buyer in each one asks the same AI the same question. A "
            "business visible in one and absent in the others is losing the visit without ever "
            "seeing it happen in the analytics."),
    },
]


# ---------------------------------------------------------------- proof block

def proof_section(c):
    """Wine proof, scoped honestly per county. See PROOF CONSTRAINT in the docstring."""
    if c["wcir"] == "measured":
        body = f"""        <p>Wine is where the AI-search shift hit hardest and earliest, and {c['county']} is where we measured it and published the result. A visitor searching for the best wineries in the county used to get a map; now they get a three-to-five-name answer, and the wineries left off it lose the visit.</p>
        <p>The <a href="/wineries" style="color: var(--color-sky);">Wine Country Intelligence Report</a> benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties on exactly this: who shows up in the AI answer and who does not. The finding in this county was stark.</p>
        <div class="stat-bar" style="border-top-color: rgba(255,255,255,0.15); margin-top: 1.5rem;">
          <div class="stat-item">
            <p class="stat-num" style="color: var(--color-sky);">71 of 171</p>
            <p style="color: rgba(255,255,255,0.7);">Santa Barbara County tasting rooms named by no AI assistant (Q2 2026 WCIR)</p>
          </div>
          <div class="stat-item">
            <p class="stat-num" style="color: var(--color-sky);">Every quarter</p>
            <p style="color: rgba(255,255,255,0.7);">The county benchmark is rebuilt on a quarterly cycle</p>
          </div>
          <div class="stat-item">
            <p class="stat-num" style="color: var(--color-sky);">Re-read monthly</p>
            <p style="color: rgba(255,255,255,0.7);">We track where a business stands against that benchmark every month</p>
          </div>
        </div>
        <p style="margin-top: 1.5rem;">Wine is the proof, not the limit. The same engine reads discoverability for any business we work with in the county.</p>
        <div class="hero-buttons" style="margin-top: 1.5rem;">
          <a href="/winery-visibility-snapshot" class="btn btn-white">See a Winery Visibility Snapshot &rarr;</a>
          <a href="/wineries" class="btn btn-outline-white">How the wine work runs</a>
        </div>"""
    elif c["wcir"] == "covered":
        body = f"""        <p>Wine is where the AI-search shift hit hardest and earliest, so it is where we built the measurement and published it. A visitor searching for the best wineries in the county used to get a map; now they get a three-to-five-name answer, and the wineries left off it lose the visit.</p>
        <p>The <a href="/wineries" style="color: var(--color-sky);">Wine Country Intelligence Report</a> benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties on exactly that question: who the AI answer names, and who it skips. {c['county']} is inside that footprint, which means the read here runs against a benchmark we already publish rather than one we invent for the engagement.</p>
        <p style="margin-top: 1.5rem;">Wine is the proof, not the limit. The same engine reads discoverability for any business we work with in the county.</p>
        <div class="hero-buttons" style="margin-top: 1.5rem;">
          <a href="/winery-visibility-snapshot" class="btn btn-white">See a Winery Visibility Snapshot &rarr;</a>
          <a href="/wineries" class="btn btn-outline-white">How the wine work runs</a>
        </div>"""
    else:
        body = f"""        <p>We did not start with a theory. We built the measurement in wine, on the Central Coast, because that is where the AI-search shift hit hardest and earliest, and then we published it.</p>
        <p>The <a href="/wineries" style="color: var(--color-sky);">Wine Country Intelligence Report</a> benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties on one question: who the AI answer names, and who it skips. That benchmark has not been run on {c['county']}, and we are not going to quote you a number from a county it was never measured in. What carries over is the method: the same engine, the same four layers, read against your category and your market here.</p>
        <p style="margin-top: 1.5rem;">Wine is where the approach was proven in public. {c['county']} is where we would run it for you.</p>
        <div class="hero-buttons" style="margin-top: 1.5rem;">
          <a href="/discoverability" class="btn btn-white">How the engine works &rarr;</a>
          <a href="/our-work" class="btn btn-outline-white">See our work</a>
        </div>"""
    return f"""  <!-- ===== PROOF ===== -->
  <section class="bg-navy">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Proof: we built it in wine first</span>
        <h2 class="section-title">Where we proved discoverability, publicly</h2>
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
        measure = (f"We built the measurement in wine and published it. The Wine Country Intelligence "
                   f"Report benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties "
                   f"on AI visibility, and it found that 71 of 171 {county} tasting rooms were named by no "
                   f"AI assistant at all last quarter. That same benchmark is how we read where your business stands: which "
                   f"surfaces the AI answer is built from, where you show up, and where you are absent. "
                   f"Then we name the fixes and re-check your visibility every month.")
    elif c["wcir"] == "covered":
        measure = (f"We built the measurement in wine and published it. The Wine Country Intelligence "
                   f"Report benchmarks every tracked winery in Santa Barbara and San Luis Obispo counties "
                   f"on AI visibility, so {county} sits inside a benchmark we already run rather than one "
                   f"invented for the engagement. The read is the same for any business here: which "
                   f"surfaces the AI answer is built from, where you show up, where you are absent, then "
                   f"the fixes, then a re-check every month.")
    else:
        measure = (f"We built the measurement in wine, on the Central Coast, and published it as the Wine "
                   f"Country Intelligence Report. That published benchmark covers Santa Barbara and San "
                   f"Luis Obispo counties, not {county}, and we will not quote you a visibility figure "
                   f"from a county where it was never measured. What transfers is the method: we read the "
                   f"same four layers against your category and your market here, name where you are "
                   f"absent, and re-check every month.")

    return [
        (f"How do I get my {short} business to show up in AI search?",
         f"Start by finding out where you currently stand, because the answer is rarely where owners "
         f"assume. The models build their recommendation from your whole footprint, not just your "
         f"website: reviews, directory and map listings, third-party mentions, the schema on your pages, "
         f"and the wider citation trail around your name. We read all of it, rank the gaps by what "
         f"actually moves prospects toward you, and then manage it as the models change. The first step "
         f"is a 30-minute Intro Call."),
        (f"Why is my competitor showing up in AI answers in {county} and I am not?",
         f"Usually not because their product is better. It is because they are legible to the model and "
         f"you are not. A competitor with consistent listings, current reviews, structured pages, and a "
         f"citation footprint the model can corroborate will be named ahead of a better business whose "
         f"signals are thin, stale, or contradictory across sources. That gap is usually fixable, and it is "
         f"mostly fixable off your own website."),
        (f"How is this different from SEO for {short}?",
         f"SEO optimizes for a ranked page of blue links a person scrolls. AI discoverability optimizes "
         f"for a single synthesized answer a model hands back, where there is no page two. The signals "
         f"overlap but they are not the same: the model builds its answer largely from your external "
         f"citation footprint rather than your own pages, so the lever that moves AI visibility usually "
         f"lives off your website. We read both layers and the classical-search layer underneath them."),
        (f"How do you measure AI visibility in {county}?", measure),
        (f"Which businesses in {county} is this for?",
         f"Owner-operated businesses under $50MM in the four verticals we work: {c['verticals_line']}. "
         f"The practice is based on California's Central Coast and {county} is one of six counties where "
         f"our outbound and on-site availability concentrate, which is not a limit on who we accept. If "
         f"buyers in your category are starting to ask AI who to trust, the work applies to you."),
    ]


# ----------------------------------------------------------------- template

def render(c):
    slug = f"ai-visibility-{c['slug']}"
    url = f"{BASE}/{slug}"
    county, short = c["county"], c["short"]
    cities_prose = ", ".join(c["cities"][:-1]) + ", and " + c["cities"][-1]
    article = c["article"]

    # Geographic honesty: only SLO and Santa Barbara are ON the Central Coast. The other four
    # counties are SERVED FROM it. Claiming "based here" on a San Diego page is simply false,
    # and the CFO-lane sibling already gets this right.
    if c["home_turf"]:
        base_clause = "the practice is based here on the Central Coast."
        stat3_num, stat3_cap = "Central Coast", "Where the practice is based"
    else:
        base_clause = f"the practice serves {county} from California's Central Coast."
        stat3_num, stat3_cap = "6 counties", "Where our outbound and on-site availability concentrate"

    # Orange County's short name IS its county name, so cities[1] alone would silently drop Irvine.
    meta_cities = (f"{c['cities'][0]} and {c['cities'][1]}" if short == county
                   else f"{short} and {c['cities'][1]}")
    faq_list = faqs(c)

    title = f"AI Visibility in {county} | Get Found When Buyers Ask AI | Main Street IQ"
    desc = (f"Your next customer in {county} is asking AI who to buy from. Main Street IQ finds every "
            f"place a prospect can discover you across search, answer engines, and AI chat, then "
            f"optimizes and manages that footprint. Serving {meta_cities}. Veteran-owned.")
    og_desc = (f"Buyers in {county} are asking ChatGPT, Claude, and Gemini who to buy from. We find every "
               f"touchpoint that answer is built from, optimize it, and manage it.")

    service_ld = {
        "@context": "https://schema.org", "@type": "Service",
        "name": f"AI Discoverability in {county}",
        "provider": {"@type": "ProfessionalService", "name": "Main Street IQ",
                     "sameAs": ["https://www.linkedin.com/company/107523729",
                                "https://www.linkedin.com/in/johnscotthess"],
                     "url": BASE},
        "serviceType": "AI discoverability and answer-engine optimization",
        "description": (f"Finding, optimizing, and managing every touchpoint a prospect in {county} can "
                        f"use to discover a business across classical search, answer engines, and "
                        f"generative AI chat. Read and managed with a CFO's discipline, proven first in "
                        f"wine through the Wine Country Intelligence Report."),
        "areaServed": area_served(c),
        "audience": {"@type": "Audience",
                     "audienceType": "Owner-operated ecommerce, winery, wellness, and elective medicine businesses under $50MM"},
        "url": url,
    }
    prof_ld = {
        "@context": "https://schema.org", "@type": "ProfessionalService", "name": "Main Street IQ",
        "sameAs": ["https://www.linkedin.com/company/107523729",
                   "https://www.linkedin.com/in/johnscotthess"],
        "description": (f"Veteran-owned and operated. AI discoverability and answer-engine optimization "
                        f"for owner-operated businesses in {county}, California, serving wineries, DTC "
                        f"ecommerce, health and wellness, and elective medicine."),
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
            {"@type": "ListItem", "position": 2, "name": "AI Discoverability",
             "item": f"{BASE}/discoverability"},
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
  <meta name="keywords" content="AI visibility {short}, AI search {short}, answer engine optimization {short}, generative engine optimization {county}, get found on ChatGPT {short}, AI discoverability {county}, AI SEO {short}, local AI search {short}">
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
  <header class="site-header" id="site-header">
    <div class="container">
      <nav class="nav-inner">
        <a href="/" class="logo"><img src="assets/logos/logo-horizontal-light.svg" alt="Main Street IQ"></a>
        <div class="nav-links" id="nav-links">
          <a href="/our-services">Services</a>
          <a href="/discoverability">Discoverability</a>
          <a href="/about">About</a>
          <a href="/our-work">Our Work</a>
          <a href="/blog">Blog</a>
          <a href="/partners">Partners</a>
          <a href="/contact">Contact</a>
          <a href="/intro-call" class="nav-cta">Book an Intro Call</a>
        </div>
        <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation">
          <span></span><span></span><span></span>
        </button>
      </nav>
    </div>
  </header>

  <main id="main">

  <!-- ===== HERO ===== -->
  <section class="hero hero-has-bg">
    <img src="assets/images/locations/{c['hero_img']}" alt="" class="hero-bg" aria-hidden="true">
    <div class="hero-overlay"></div>
    <div class="container">
      <span class="section-label">AI Discoverability | {county}, CA</span>
      <h1>Your next customer in<br>{county} is asking AI.</h1>
      <p>When a buyer here asks ChatGPT, Claude, or Gemini for the best option in your category, the answer names a few businesses and skips the rest. Main Street IQ finds every touchpoint that answer is built from, optimizes it, and manages it, with the goal that more of the prospects already looking for you arrive at your door. Founder Scott Hess is a U.S. Navy veteran, and {base_clause}</p>
      <div class="hero-buttons">
        <a href="/intro-call" class="btn btn-white">Book an Intro Call &rarr;</a>
        <a href="/audit" class="btn btn-outline-white">Start with a finding</a>
      </div>
      <p style="font-size: 0.9rem; color: rgba(255,255,255,0.6); margin-top: 1rem; max-width: 560px;">Book a call, send a message, or just ask a question. No pitch, no obligation.</p>
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
        <h2 class="section-title">Discovery moved, and most businesses did not</h2>
      </div>
      <div style="max-width: 820px; margin: 0 auto; font-size: 1.1rem; line-height: 1.7;">
        <p>A prospect used to find you through a ranked page of links and a map of pins. They compared, they clicked, they decided. That funnel is still there, but a new one now sits in front of it: the buyer asks an AI what to buy and who to trust, reads one synthesized answer, and often stops there.</p>
        <p>{c['local_para']}</p>
        <p>That answer is not built from your website alone. The model assembles it from your reviews, your directory listings, the articles that mention you, the schema on your pages, and the wider citation footprint that surrounds your name. If those signals are thin or stale, you are absent from the answer no matter how good your product is. Often your competitor is not winning because they are better; they are winning because they are legible to the machine and you are not.</p>
      </div>
    </div>
  </section>

  <!-- ===== WHAT WE READ ===== -->
  <section class="bg-light">
    <div class="container">
      <div class="section-header">
        <span class="section-label">What we read</span>
        <h2 class="section-title">Every place a buyer in {short} can find you</h2>
        <p class="section-subtitle">Discoverability is not one channel. It is a footprint. We read all of it the way a CFO reads a P&amp;L, so the fixes are ranked by what actually moves prospects, not by what is easiest to do.</p>
      </div>
      <div class="card-grid">
        <div class="card">
          <h3>Classical search</h3>
          <p>Where you rank when a buyer types the query, and whether your pages are structured so a search engine can read what you sell, where, and to whom. The layer everyone knows, still the floor everything else stands on.</p>
        </div>
        <div class="card">
          <h3>Answer engines</h3>
          <p>The AI-generated summary that now sits above the links, and the featured answers that quietly took the click before the AI did. Winning here means being the source the answer is built from, not a result buried below it.</p>
        </div>
        <div class="card">
          <h3>Generative AI chat</h3>
          <p>What ChatGPT, Claude, and Gemini say when a buyer asks them who to buy from in your category and region. This is decided by your external citation footprint, the part of your presence that lives off your own website, where most owners have never looked.</p>
        </div>
        <div class="card">
          <h3>Reputation and listings</h3>
          <p>Reviews, directories, maps, and the third-party mentions the models lean on to decide who is real and who is trusted. The signals that turn a name into a recommendation.</p>
        </div>
      </div>
      <p style="margin-top: 2rem; font-size: 1rem; max-width: 820px;">A <a href="/audit" style="color: var(--color-navy);">Website Audit</a> reads all four layers and hands back a severity-ranked fix list. <a href="/our-services" style="color: var(--color-navy);">Monitor</a> re-reads them every month, so drift gets caught the month it starts.</p>
    </div>
  </section>

  <!-- ===== HOW IT WORKS ===== -->
  <section>
    <div class="container">
      <div class="section-header">
        <span class="section-label">How the engine works</span>
        <h2 class="section-title">Surface, optimize, manage</h2>
        <p class="section-subtitle">Three moves that turn a scattered, invisible footprint into a managed one that keeps working while you run the business.</p>
      </div>
      <div class="problem-list" style="max-width: 860px;">
        <div class="problem-item">
          <h3>1. Surface every touchpoint</h3>
          <p>We map the full set of places a prospect in {county} can discover you and score each one. You leave knowing exactly where you show up, where you are absent, and which gaps are costing you the most, instead of guessing which channel to chase this quarter.</p>
        </div>
        <div class="problem-item">
          <h3>2. Optimize what actually moves prospects</h3>
          <p>Not every fix is worth making. We sequence the work by what actually pulls prospects toward you, from the schema and pages you control to the citation footprint you influence, so effort lands where it compounds rather than where it is convenient.</p>
        </div>
        <div class="problem-item">
          <h3>3. Manage it as it drifts</h3>
          <p>The models change, competitors move, and a footprint left alone goes stale. Monitor re-reads your visibility every month and flags the drift, so the work you did in month one is still working in month twelve.</p>
        </div>
      </div>
      <p style="margin-top: 1.5rem; font-size: 0.95rem; color: var(--slate); max-width: 860px; font-style: italic;">The outcome we are after is simple: more of the prospects already searching for what you sell end up at your door. How far that moves depends on your starting point and your own execution; we measure it against your real numbers rather than promise a figure.</p>
      <p style="margin-top: 1.5rem;"><a href="/intro-call" class="btn btn-primary">Start with an Intro Call &rarr;</a></p>
    </div>
  </section>

{proof_section(c)}

  <!-- ===== SERVICE AREA ===== -->
  <section class="bg-light">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Where we work</span>
        <h2 class="section-title">AI discoverability across {county}</h2>
      </div>
      <div style="max-width: 820px; margin: 0 auto; font-size: 1.05rem; line-height: 1.7;">
        <p>We work with owner-operated businesses across {cities_prose}. The practice is based on California's Central Coast, and {county} is one of six counties where our outbound and on-site availability concentrate. That is not a limit on who we accept; the work runs remotely for clients elsewhere in the United States.</p>
        <p style="margin-top: 1.25rem;">Looking for the finance side instead? The CFO practice runs in this county too: <a href="/fractional-cfo-{c['slug']}" style="color: var(--color-navy);">fractional CFO in {county} &rarr;</a></p>
      </div>
    </div>
  </section>

  <!-- ===== YOUR VERTICAL ===== -->
  <section>
    <div class="container">
      <div class="section-header">
        <span class="section-label">Your vertical is next</span>
        <h2 class="section-title">The same read, tuned to how buyers find you</h2>
        <p class="section-subtitle">Discoverability is horizontal, but the queries, the touchpoints, and the buyer are not. We tune the engine to your vertical.</p>
      </div>
      <div class="card-grid">
        <div class="card">
          <h3>Ecommerce &amp; DTC</h3>
          <p>When a shopper asks AI what to buy in your category, is your brand in the answer, or is paid acquisition backfilling a gap that keeps getting wider?</p>
          <p style="margin-top: 0.75rem;"><a href="/ecommerce" style="color: var(--color-navy);">Discoverability for ecommerce &rarr;</a></p>
        </div>
        <div class="card">
          <h3>Wineries</h3>
          <p>A visitor planning a trip asks AI which wineries to visit. Being absent from that answer costs the tasting-room visit and the club signup behind it.</p>
          <p style="margin-top: 0.75rem;"><a href="/wineries" style="color: var(--color-navy);">Discoverability for wineries &rarr;</a></p>
        </div>
        <div class="card">
          <h3>Health &amp; wellness</h3>
          <p>Prospective clients ask AI who to trust with their health before they ever call. We read whether your practice is the one the answer recommends.</p>
          <p style="margin-top: 0.75rem;"><a href="/wellness" style="color: var(--color-navy);">Discoverability for wellness &rarr;</a></p>
        </div>
        <div class="card">
          <h3>Elective medicine</h3>
          <p>High-consideration, high-value decisions now start with an AI question. We read your visibility and reputation footprint across the surfaces a patient checks before they book.</p>
          <p style="margin-top: 0.75rem;"><a href="/aesthetics" style="color: var(--color-navy);">Discoverability for elective medicine &rarr;</a></p>
        </div>
      </div>
    </div>
  </section>

  <!-- ===== FAQ ===== -->
  <section class="bg-light">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Common questions</span>
        <h2 class="section-title">What {short} owners ask about AI visibility</h2>
      </div>
      <div class="container-narrow" style="max-width: 820px; margin: 0 auto;">
{faq_html}
      </div>
    </div>
  </section>

  <!-- ===== FINAL CTA ===== -->
  <section class="bg-navy">
    <div class="container" style="text-align: center;">
      <h2 class="section-title">Find out where you show up when {article} {short} buyer asks AI.</h2>
      <p style="max-width: 640px; margin: 0 auto 1.5rem; color: rgba(255,255,255,0.7);">One conversation. A straight read on where you stand and what moves it. No pitch, no obligation.</p>
      <div class="hero-buttons" style="justify-content: center;">
        <a href="/intro-call" class="btn btn-white">Book an Intro Call &rarr;</a>
      </div>
    </div>
  </section>

  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-newsletter">
        <div class="footer-newsletter-pitch">
          <h4>Founder-to-founder thinking on revenue</h4>
          <p>One short note when there's something worth saying. No drip, no sequence, no pitch.</p>
        </div>
        <form class="footer-newsletter-form" id="footerNewsletterForm" novalidate>
          <input type="email" id="footerNewsletterEmail" name="email" placeholder="you@company.com" required autocomplete="email" maxlength="100" aria-label="Email address">
          <input type="text" name="honeypot" class="footer-newsletter-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">
          <button type="submit">Subscribe</button>
          <div class="footer-newsletter-msg" id="footerNewsletterMsg" role="status" aria-live="polite"></div>
        </form>
      </div>
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="/" class="logo"><img src="/assets/logos/logo-horizontal-dark.svg" alt="Main Street IQ"></a>
          <p>A fractional CFO practice with a built-in intelligence engine, for owner-operated businesses under $50MM. Veteran-owned and operated.</p>
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
          <a href="/intro-call">Book an Intro Call</a>
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener">LinkedIn</a>
        </div>
        <div class="footer-col">
          <h4>Verticals</h4>
          <a href="/wineries">Wineries</a>
          <a href="/wellness">Health &amp; Wellness</a>
          <a href="/aesthetics">Elective Medicine</a>
          <a href="/ecommerce">Ecommerce</a>
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
          <a href="/trust">Trust Center</a>
          <a href="/legal/ai-use">AI Use</a>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 Main Street IQ. All rights reserved.</span>
        <div class="footer-social">
          <a href="https://www.linkedin.com/in/johnscotthess" target="_blank" rel="noopener" aria-label="LinkedIn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" role="img" aria-label="LinkedIn"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          </a>
        </div>
      </div>
    </div>
  </footer>

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for c in COUNTIES:
        path = ROOT / f"ai-visibility-{c['slug']}.html"
        html = render(c)
        if args.dry_run:
            existing = path.read_text(encoding="utf-8") if path.exists() else None
            state = "unchanged" if existing == html else ("NEW" if existing is None else "would change")
            print(f"{path.name}: {state} ({len(html.splitlines())} lines)")
        else:
            path.write_text(html, encoding="utf-8")
            print(f"wrote {path.name} ({len(html.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
