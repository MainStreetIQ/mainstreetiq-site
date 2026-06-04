# Main Street IQ — Brand Guide

**Tagline:** Financial IQ for Main Street.

---

## Colors

### Brand palette (3 blues + warm neutrals)

| Token | Hex | Usage |
|---|---|---|
| Midnight | `#0F1C2E` | Dark backgrounds, footer, hero overlays, email header/footer bg |
| Navy | `#2B4E8C` | Primary — CTAs, headings, logo on light bg, card top-borders, button bg |
| Navy Hover | `#1A3560` | Hover state for Navy CTAs and primary buttons |
| Sky | `#5BB8FF` | Accent — links, hover states, emphasis on dark backgrounds |
| Dark Text | `#1A1F2B` | Primary body text on light backgrounds |
| Neutral | `#6B7480` | Secondary text, captions, nav links, muted body copy |
| Border | `#E5E2DC` | Borders, dividers, subtle separators |
| Ice | `#FAFAF7` | Light section backgrounds, off-white (not pure white) |
| White | `#FFFFFF` | Card backgrounds, clean sections |

### Semantic palette (functional UI states only)

These exist outside the brand palette for state semantics. Use only for the listed purpose.

| Token | Hex | Usage |
|---|---|---|
| Error | `#B54040` | Form validation errors, destructive action confirmations |
| Success | `#10B981` | Success states, form submission confirmations |

CSS tokens: `--color-error`, `--color-success`. Do not introduce other semantic colors without updating this guide and `canonical-facts.md`.

### Color rules
- **Dark sections** use Midnight (`#0F1C2E`) background with white text. Links/accents use Sky (`#5BB8FF`).
- **Light sections** use Ice (`#FAFAF7`) or White background. Headings and CTAs use Navy (`#2B4E8C`). Body text uses Dark Text (`#1A1F2B`) or Neutral (`#6B7480`).
- **Buttons** — primary is Navy bg with white text. Hover darkens to Navy Hover (`#1A3560`). On dark backgrounds, use white bg with Navy text.
- **No gold, no warm accent colors.** The old gold (`#D4913B`) has been fully retired.

---

## Typography

**Font family:** Outfit (Google Fonts)

```
https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600;700&display=swap
```

| Weight | Usage |
|---|---|
| 200 | Decorative/display only (sparingly) |
| 300 | Body text, paragraphs, descriptions (default body weight) |
| 400 | Labels, nav links, form inputs |
| 500 | Subheadings, card titles, emphasized text |
| 600 | H2/H3 headings, button text, strong labels |
| 700 | H1 headings, hero text |

- Body text uses `letter-spacing: 0.3px` for readability at weight 300.
- **No serif pairing.** Outfit is the only typeface across all materials.
- Fallback stack: `'Outfit', 'Helvetica Neue', Arial, sans-serif`

---

## Logo System

All files in `assets/logos/`. Available in SVG format.

### Naming convention
- **`-light` suffix** = designed for LIGHT backgrounds (navy-colored logo)
- **`-dark` suffix** = designed for DARK backgrounds (white/sky-colored logo)

### Variants

The kit splits into three layers: full lockups (mark + name + tagline), namemark (mark + name only), and standalone components (each piece alone).

| File | Layer | Use case |
|---|---|---|
| `logo-full-light.svg` / `-dark.svg` | Lockup | Hero sections, marketing materials, deliverable covers |
| `logo-stacked-light.svg` / `-dark.svg` | Lockup | Social cards, square formats, email sigs |
| `logo-horizontal-light.svg` / `-dark.svg` | Lockup | Nav headers (default), footer, compact horizontal applications |
| `logo-namemark-light.svg` / `-dark.svg` | Mark + name | Reserved alternative when tagline space is too tight (currently unused on the site) |
| `logo-mark-light.svg` / `-dark.svg` | Component | App icons, social avatars, small spaces |
| `logo-wordmark-light.svg` / `-dark.svg` | Component | Compositing, text-only contexts |
| `logo-tagline-light.svg` / `-dark.svg` | Component | Footers, sub-block under custom marks |
| `favicon.svg` | Icon | Browser tab favicon |

All lockup SVGs embed the tagline: **Financial IQ for Main Street** in Outfit, Title Case.

### Logo usage rules
- Light-bg pages: use `-light` logo (navy on white/ice)
- Dark-bg pages/sections: use `-dark` logo (white on midnight)
- Footer always uses `-dark` on Midnight background
- Minimum clear space: maintain padding equal to the height of the "IQ" in the logo mark

---

## Email Templates

### Header
- Background: Midnight (`#0F1C2E`)
- Logo: `logo-horizontal-dark.svg` (white on dark), centered or left-aligned
- Padding: 24px–32px vertical

### Body
- Background: White (`#FFFFFF`) or Ice (`#FAFAF7`)
- Text color: Dark Text (`#1A1F2B`)
- Font: Outfit 300, 16px, line-height 1.6
- Headings: Outfit 600, Navy (`#2B4E8C`)
- Links: Navy (`#2B4E8C`), underlined

### CTA Buttons
- Background: Navy (`#2B4E8C`)
- Text: White, Outfit 500, 14–16px
- Border-radius: 4px–6px
- Padding: 12px 24px
- No drop shadows, no gradients

### Footer
- Background: Midnight (`#0F1C2E`)
- Text: Neutral (`#6B7480`) at 12–13px
- Links: Sky (`#5BB8FF`)
- Include: Logo (stacked-dark or horizontal-dark), tagline, LinkedIn link, unsubscribe link
- No phone number in mass emails (use on 1:1 correspondence only)

### Email fallback fonts
For email clients that don't support Google Fonts:
```
font-family: 'Helvetica Neue', Arial, sans-serif;
```

---

## Do / Don't

**Do:**
- Use the 3-blue palette consistently (Midnight, Navy, Sky)
- Use Outfit as the only typeface
- Keep layouts clean with generous whitespace
- Use asymmetric layouts where possible (left-aligned headers, right content)
- Use 2px Navy top-border accent on cards

**Don't:**
- Use emoji icons anywhere
- Use gold/warm accent colors
- Use serif fonts (no Playfair, no DM Serif)
- Use large border-radius (keep to 4–8px max)
- Add phone number to public-facing marketing pages (card page and 1:1 only)
- Use gradients or drop shadows on buttons
- Center every section header — prefer left-aligned with right-side content

---

## Contact Info (for email signatures, materials)

- **Name:** Scott Hess
- **Title:** Fractional CFO
- **Company:** Main Street IQ
- **Email:** scott@mainstreetiq.com
- **Phone:** Not listed publicly — see /card for 1:1 networking use
- **Website:** mainstreetiq.com
- **LinkedIn:** linkedin.com/in/johnscotthess
- **Calendly:** calendly.com/scott_mainstreetiq/30min
- **Digital card:** mainstreetiq.com/card
