# Landing Design: Brand, Scope, and Build Spec

Status: the live page follows the Eclipse variant composition (dark photo hero, serif display, countdown to Nov 4). The system below stays as the token reference. Copy rules still hold: every claim already true in the repo.

## Brand

Voice stays plain and dollar-denominated. No emoji. No hype adjectives the product cannot prove.

## Typeface

- Body and headlines: Inter (weights 400, 500, 600, 700). Hero uses 700 with tracking minus 0.02em at 40 to 56px.
- Money and evidence: IBM Plex Mono (weights 400, 500, 600). Dollar figures always carry the `$` prefix and use tabular numerals.
- Buttons and labels: Inter 600. Mono never appears in buttons.
- Fallback stacks: system sans after Inter, system mono after Plex Mono.
- Load through Google Fonts with `display=swap`. Two families only.

## Color (Tailwind v4 theme tokens, light-first)

Light-first per the reference set (memoe, Collar, Global Citizens): airy ground, dark pill CTA, product mock beside the headline. The inbox console stays dark. Marketing pages are light everywhere. That split is standard practice.

| Token | Hex | Use |
|---|---|---|
| cream-50 | f7f6f3 | Page background (warm paper) |
| card-white | ffffff | Cards |
| line-200 | e7e5e0 | Hairline borders only |
| ink-900 | 131316 | Headlines and body |
| ink-600 | 3f3f46 | Secondary paragraphs |
| ink-500 | 52525b | Captions only |
| pine-700 | 047857 | Trust accent: links, money numerals, verified states |
| pine-800 | 065f46 | Accent hover |
| alarm-700 | b91c1c | Drift pills and phantom story, on alarm-50 ground |
| alarm-50 | fef2f2 | Drift pill ground |
| gold-700 | b45309 | Proof numerals, large sizes only |

Rules: CTA pills are ink-900 with white text (reference pattern). Green stays deep pine on light, never lime. Body text never drops below ink-600. All pairs pass WCAG AA on cream-50. One dark rounded card closes the page (final CTA) as a deliberate contrast beat that ties to the inbox console.

## Scope (sections in order)

1. Sticky header: wordmark, repo link, one audit button. Anchor links to Demo, Proof, Pricing.
2. Hero split: hook headline plus subhead plus CTAs on the left. Static product mock (drift card with $44.00 at risk) on the right. Full-bleed to max-w-6xl.
3. Problem strip: three cards verbatim (phantom refunds, policy breaches, silent cancellations) plus the liability footnote.
4. How it works: three numbered steps (connect read-only, backfill 90 days, fix in one click).
5. Demo slot: 16:9 placeholder labeled for the 3-minute video. No fake player controls.
6. Proof bar: four measured numerals, each linked to evidence. No charts.
7. Objections: native accordion answering the top judge objections (agents, guardrails, platform risk, model role). Content comes from the demo script.
8. Pricing teaser: one line plus the audit button. No matrix, no checkout.
9. Final CTA: dark rounded card, one sentence plus the audit button.
10. Footer: model attribution, synthetic-data honesty, repo link, model ID.

Out of scope: full pricing page, live interactive demo, testimonials or badges, blog or docs, any second CTA, any number not already in the repo.

The page optimizes audit signups. Stars measure curiosity. Signups prove merchants will open real ledgers.

## Build spec

- Same Vite app, second static entry (`landing.html`) through rollup options input. Inbox stays at root. Both entries must pass `npm run build`.
- The landing carries one lazy Three.js module (`src/landing-eye.ts`) for the third-eye brand mark in the final CTA card. It loads only on viewport entry, disposes offscreen, and falls back to static CSS under reduced motion or WebGL failure. Performance floor is 85. Accessibility stays 100.
- Theme tokens go in CSS through Tailwind v4 `@theme`. Fonts load in the entry head.
- Copy comes verbatim from `landing-copy.md`. Any deviation needs a repo source first.
- Acceptance: typecheck clean and build clean. Every CTA scrolls or links somewhere real. Only the video slot and the audit contact may stay placeholders.
