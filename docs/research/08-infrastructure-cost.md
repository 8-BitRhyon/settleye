# Infrastructure Cost: Literally $0 Build

Researched 2026-10-26, corrected 2026-10-27 per event FAQ (card required for Meta API credits).

## Verdict table

| Component | Verdict | Limit / terms |
|---|---|---|
| Modal compute (FastAPI plus cron) | FREE, no card | Starter: $0 plus $30/mo compute, resets monthly. Includes scheduled and web functions. CPU ~$0.047/core-hr, billed per second, $0 idle. |
| Modal Shared Endpoints (token API) | COSTS MONEY from request one | Free usage is not part of Starter (eff. 2026-09-01). Never use for the demo. |
| Baseten Muse Spark Open | FREE with hackathon credit | Pay-go $1.25/1M in, $0.15 cached, $4.25/1M out. ~$30 trial credit reported; no perpetual free tier. |
| Meta Model API | FREE with credit, CARD REQUIRED | $1.25 in / $4.25 out per 1M; $20 one-time credit per new US-preview account. Event FAQ: a card is required to use credits; temporary pre-auth hold applies. |
| GitHub repo plus Actions (public) | FREE | Public repo: standard runners free, unlimited minutes. |
| Shopify dev store plus custom app | FREE, no time limit | Partner account free; unlimited dev stores; up to 10 custom apps per store. |
| Stripe test mode | FREE, no card, no expiry | Account plus `sk_test_` keys plus test cards. Live activation never needed for test. |
| Frontend hosting | FREE, no card | Cloudflare Pages: 500 builds/mo, unmetered bandwidth. GitHub Pages bars commercial SaaS in TOS; use Pages. |
| Demo video | FREE | macOS screen capture plus iMovie plus unlisted YouTube. |
| Custom domain | COSTS MONEY | ~$8-15/yr. Free alt: `*.pages.dev`. Skipped. |

Sources: https://modal.com/pricing, https://baseten.co/pricing, https://docs.baseten.co/organization/billing, https://dev.meta.ai/resources/blog/build-with-muse-spark, https://github.com/pricing, https://shopify.dev/docs/storefronts/themes/tools/development-stores, https://docs.stripe.com/testing, https://developers.cloudflare.com/pages/platform/limits

## Cost math (worst case, credits claimed)

50 demo extractions x (3k in plus 1k out) = 150k in plus 50k out = ~$0.19 + ~$0.21 = ~$0.40. Even 10x larger prompts = ~$4. Covered by $20 Meta plus $100 Baseten plus $150 hackathon credits plus 2M TPM allowance. Modal backend (scale-to-zero API plus daily cron): cents to single dollars inside $30/mo free. Total out-of-pocket: $0.00, excluding the skipped domain.

## Gotchas

1. Modal Shared Endpoints bill from token one even inside $30 free: avoid them.
2. A credit card is REQUIRED to use Meta API credits (temporary pre-auth hold, released in days). $0 out-of-pocket still holds, but cardless is false on that path. Prefer partner credits where cardless; set budget alerts anywhere a card is on file.
3. Conflicting reports on Baseten/Modal card-at-signup: current Modal signup is cardless OAuth; treat any card prompt as optional upsell and stop.
4. Shopify post-Jan-2026: no copy-paste Admin token; install custom app plus OAuth code exchange via Postman/curl. Free but fiddly.
5. GitHub Pages TOS excludes commercial SaaS: demo on Cloudflare Pages.

## Blunt verdict

Literally-$0 build plus demo plus judging week is achievable. Skip the custom domain. Single biggest threat: a card on file (Baseten or Shared Endpoints) plus one misconfigured loop burning metered usage into auto-charge. Keep cards off except the mandatory Meta API hold, stay off Shared Endpoints, keep the repo public.
