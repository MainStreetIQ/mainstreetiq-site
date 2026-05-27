---
name: MSIQ Design Spec
description: Machine-readable canonical brand voice, color, typography, layout rules and prohibitions for Main Street IQ. Loaded by any agent producing MSIQ-branded output.
version: 1.0.0
applies_to: msiq-site, msiq-claude-skills, all MSIQ deliverables (audits, blog posts, LinkedIn, emails, decks, lead magnets)
last_reviewed: 2026-05-01
---

# MSIQ Design Spec

Canonical brand spec for Main Street IQ. Single source of truth for any agent or human producing MSIQ-branded output. Supersedes scattered design notes; memory entries link here for the why.

## Brand tokens

Source: `msiq-site/styles.css` (canonical) and `~/MSIQ/CCIQ/cciq_brand.py` (Python mirror).

### Color

| Token | Hex | Use |
|---|---|---|
| `--color-midnight` | `#0F1C2E` | Dark backgrounds, overlays, footer |
| `--color-navy` | `#2B4E8C` | Primary — CTAs, headings, logo, card top-border |
| `--color-sky` | `#5BB8FF` | Single accent — links, hover, emphasis on dark backgrounds |
| `--color-neutral` | `#6B7480` | Warm gray — body text, nav, captions |
| `--color-border` | `#E5E2DC` | Warm gray — borders, dividers |
| `--color-ice` | `#FAFAF7` | True warm off-white — light sections |
| `--color-white` | `#FFFFFF` | White surfaces |
| `--color-dark-text` | `#1A1F2B` | Slightly warm near-black, primary text on light |
| Success-only | `#10B981` | Reserved for confirmation states; not decorative |

### Typography

- **Font family:** `'Outfit', 'Helvetica Neue', Arial, sans-serif` for both headings and body. No serifs anywhere.
- **Hierarchy:** Outfit weights 200-700 are loaded; lean on weight (300/400 body, 500/600 headings) and size for hierarchy, not on font swaps.
- **Line height:** body ~1.5, headings ~1.2.

### Layout

- **Section padding:** `6rem 0` standard; `4rem 0` for tighter dense sections.
- **Container width:** 1140px standard, 800px narrow (long-form reading, blog posts, this spec).
- **Asymmetric layouts** preferred over centered/symmetric. Off-grid heroes, intentional whitespace on one side.
- **Border radius:** subtle (4-8px). Never bubbly. No oversized pill shapes.

## Voice

**Default voice: MSIQ.** Empathetic, founder-to-founder, direct. CFO speaking to a CFO-curious founder, not an agency speaking to a buyer.

- Sentences are short. No throat-clearing.
- No agency-speak ("solutions," "synergies," "leverage," "unlock value").
- Numbers > adjectives. "$10M-$100M revenue band" beats "growth-stage."
- Hope + story framing on every report. Explain WHY the business is performing this way, end with a credible path forward (not a failure list + price tag).

**Voice flips to client voice** only when ghost-writing under a client's brand (a specific winery, medspa, etc.). Load the client voice file from `~/.claude/skills/copy-lab/voice-library/<client>/`. Always declare the voice mode in the run log.

**Brand-guardian gate:** any externally visible text passes through the `brand-guardian` agent before send/publish. Internal-only artifacts (Zoho notes, Notion tasks, Scott's briefs) skip the gate.

## Prohibitions

These are non-negotiable. No exceptions, no "just this once."

- **No em dashes.** Anywhere. Reads as AI-generated. Use comma, semicolon, colon, period, parentheses, or `|` in titles. Source: `feedback_no_em_dashes.md`.
- **No emoji icons.** Not in nav, not in cards, not in callouts, not in body copy. Use SVG line icons or letter-mark indicators.
- **No gold accents.** Gold has been deprecated everywhere. Legacy `--gold` CSS variable resolves to navy; do not add new gold tints.
- **No serif fonts.** Outfit only.
- **No bubbly radius.** No fully-rounded pills, no chunky 16px+ corner radii on cards. Subtle 4-8px max.
- **No stock-photo people.** Diagrams, abstractions, or no image. Founder-aware audiences spot stock instantly.
- **No "as an AI" / generic LLM tells.** Output must read as written by Scott. Pre-flight check before any externally visible artifact.

## Layout principles

- **Asymmetric, not centered.** Heroes weighted left or right. Whitespace on one side, content on the other.
- **One accent per surface.** Sky on dark, navy on light. Never both as accents on the same surface.
- **Density signals craft.** Numbers, tables, real client examples > hero illustrations and feature grids.
- **Mobile-first.** Audit every component at 375px before declaring it shipped.
- **Motion is rare and purposeful.** No autoplay, no parallax, no carousel. Static beats clever.

## Protocols and conventions

- **Blog publishing:** posts staged in repo but NOT linked in nav/index until the LinkedIn counterpart ships at 7:30am PT. (`project_msiq_blog_protocol.md`)
- **Audit naming:** Audit / Benchmark / Diagnostic as category words; Pro = self-depth; Plus = cohort-aware. (`project_audit_naming_taxonomy.md`)
- **Quarter convention:** April = Q1, July = Q2, Oct = Q3, Jan = Q4. Label reflects the data quarter, not the publish month. (`project_quarter_convention.md`)
- **No pricing in Valley reports.** Pricing reserved for individual winery engagements. (`feedback_report_no_pricing.md`)
- **Phone number is card-only.** (805) 270-3323 lives on `card.html`; reports / audits / deliverables stay email-only. (`project_msiq_no_public_phone.md`)
- **Zoho field constraints:** Designation ≤100 chars; Industry must match a picklist value exactly; Lead_Source must exist in picklist before deploy. (`reference_zoho_lead_constraints.md`, `feedback_zoho_webtolead_picklist_strict.md`)

## How agents should use this file

When producing any MSIQ-branded artifact (HTML, markdown, image, deck, email, audit report, blog post, LinkedIn post, lead magnet copy), an agent should:

1. **Load this file at the start of the run.** It is small enough to keep in context for the duration.
2. **Match a reference artifact.** This spec defines the rules; the canonical artifacts in `~/.claude/skills/CLAUDE.md` show the rules applied. Reference both.
3. **Self-check before declaring done:**
   - No em dashes anywhere?
   - No emoji icons?
   - Color palette matches the table above (no off-tokens)?
   - Voice = MSIQ unless ghost-writing flag set?
   - Asymmetric layout, not centered?
4. **Pass externally visible output through `brand-guardian`** before send/publish.

## Versioning

Bump `version` in the frontmatter when prohibitions change, when tokens shift, or when voice rules evolve. Minor (1.0.x): clarifications and protocol pointer additions. Major (1.x.0): token changes, new prohibitions, voice updates. Breaking (x.0.0): would require re-rendering shipped artifacts.

## See also

- `~/MSIQ/CLAUDE.md` — portfolio-wide always-on rules
- `~/.claude/skills/CLAUDE.md` — skill-building rules + canonical reference artifact list
- `~/MSIQ/CCIQ/cciq_brand.py` — Python mirror of these tokens for the CCIQ pipeline
- Memory index: `~/.claude/projects/c--Users-scott-MSIQ/memory/MEMORY.md`
