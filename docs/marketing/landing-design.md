# Landing Design: Brand, Scope, and Build Spec

Single static page for judges and merchant ops leads. It must read as the same product as the zinc inbox. Every claim on it already holds in the repo (rule from `plan.md`).

## Brand

Voice stays plain and dollar-denominated. No emoji. No hype adjectives the product cannot prove.

## Typeface

- Body and headlines: Inter (weights 400, 500, 600, 700). Hero uses 700 with tracking minus 0.02em at 40 to 56px.
- Money and evidence: IBM Plex Mono (weights 400, 500, 600). Dollar figures always carry the `$` prefix and use tabular numerals.
- Buttons and labels: Inter 600. Mono never appears in buttons.
- Fallback stacks: system sans after Inter, system mono after Plex Mono.
- Load through Google Fonts with `display=swap`. Two families only.

## Color (Tailwind v4 theme tokens, dark-first)

Dark-first because the inbox is zinc-950 plus emerald. A light page into a dark app breaks trust at signup.

| Token | Hex | Use |
|---|---|---|
| ink-950 | 09090b | Page background (matches app) |
| ink-900 | 101014 | Alternate section background |
| ink-800 | 1a1a20 | Cards |
| ink-700 | 2a2a33 | Hairline borders only |
| paper-100 | f4f4f5 | Headlines and body |
| paper-300 | d4d4d8 | Secondary paragraphs |
| paper-400 | a1a1aa | Captions and timestamps only |
| mint-400 | 34d399 | Trust accent: primary CTA, links, verified states |
| mint-500 | 10b981 | Accent hover |
| alarm-400 | f87171 | Phantom-refund story and drift pills only |
| proof-300 | fcd34d | Proof numerals only |

Rules: red stays under 10 percent of any viewport and always resolves into mint beside it. Green stays desaturated emerald, never lime. Body text never drops below paper-300. All pairs pass WCAG AA on ink-950.

## Scope (sections in order)

1. Sticky header: wordmark, repo link, one audit button. Anchor links to Demo, Proof, Pricing.
2. Hero: the 10-second hook as headline, landing-copy subhead, primary CTA button, demo text link.
3. Problem strip: three cards verbatim (phantom refunds, policy breaches, silent cancellations) plus the liability footnote.
4. How it works: three numbered steps (connect read-only, backfill 90 days, fix in one click).
5. Demo slot: 16:9 placeholder labeled for the 3-minute video. No fake player controls.
6. Proof bar: four measured bullets, each linked to evidence. No charts.
7. Pricing teaser: one line plus the audit button. No matrix, no checkout.
8. Final CTA: one sentence plus the audit button.
9. Footer: model attribution, synthetic-data honesty, repo link, model ID.

Out of scope: full pricing page, live interactive demo, testimonials or badges, blog or docs, any second CTA, any number not already in the repo.

The page optimizes audit signups. Stars measure curiosity. Signups prove merchants will open real ledgers.

## Build spec

- Same Vite app, second static entry (`landing.html`) through rollup options input. Inbox stays at root. Both entries must pass `npm run build`.
- Theme tokens go in CSS through Tailwind v4 `@theme`. Fonts load in the entry head.
- Copy comes verbatim from `landing-copy.md`. Any deviation needs a repo source first.
- Acceptance: typecheck clean and build clean. Every CTA scrolls or links somewhere real. Only the video slot and the audit contact may stay placeholders.
