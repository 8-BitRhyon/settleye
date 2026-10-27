# Buyer Blueprints: SMB, Enterprise, and the Wedge Ladder

Synthesized Oct 27, 2026 from three parallel research tracks (SMB merchants, enterprise audit buyers, startup wedge plays). Sources carry URLs below. Gaps are marked UNVERIFIED, never filled.

## The pop-shop question, answered first

A rural pop-shop owner finds an auditor intimidating by default. It becomes a must-buy on one condition only. The first screen after Install must show found money plus one Approve button, with zero config. She buys "we found $X you were owed." She never buys "reconciliation." This matches our tier math in `07-tangible-value.md`. Under ~50 orders a month there is no recurring pain and no honest subscription. Serve that tier with a free scan plus per-catch pricing, or say no.

## SMB patterns to replicate

- Install auto-connects, no keys. Shopify Inbox and Gorgias sync orders and policies through App Store OAuth with a free Install button. Copy: Install, auto-scan 90 days, dollar findings. Sources: apps.shopify.com/inbox, apps.shopify.com/helpdesk.
- Free entry plus a $9 to $29 ladder. Seal Subscriptions runs Free Forever then $5.95 to $24.95. Analytics apps cluster at $9 to $29 (sellerboard $9, Kleio $29, Lifetimely free to 50 orders then $49+). Price the auditor at $0 scan and $19/mo or percent-of-recovered, billed in Shopify. Sources: apps.shopify.com/seal-subscriptions, digismoothie.com profit-analytics roundup.
- Money language, never ledger language. Disputifier (4.7 stars) sells "Never worry about chargebacks again." Intimidating words stay in settings or higher-tier bullets. Source: apps.shopify.com/disputifier.
- Done-for-you setup as the product. Analyzify bundles free white-glove implementation for server-side tracking and states that no technical knowledge is needed. Reviews call it white-glove. Prebuilt rules, auto-drafted emails, and human chat support are the product downmarket. Sources: analyzify.com, apps.shopify.com/analyzify.
- Simplification precedent: Gorgias beat Zendesk by deleting setup. Zendesk needs 6 to 12 weeks plus developers. Gorgias won with native order data in every ticket. Macros need no custom coding. Refunds happen inside the ticket from $10. Fewer concepts won, not more AI. Sources: hoop.app and ringly.io Gorgias-vs-Zendesk comparisons.

## Enterprise motion to replicate (four steps)

- Land with a read-only shadow pilot. 14-day free trial on read-only keys, no write actions. Datadog runs the full suite free for 14 days with audit trails that change nothing in customer infra. Source: datadoghq.com/product/audit-trail.
- Gate the pilot on a trust packet, not a full cert. Signed DPA, data minimization, 30 to 90 day retention with customer-owned archive. Datadog defaults to 90-day searchable retention with 15-minute archive cadence. Full SOC 2 cost and timeline is UNVERIFIED. Rule of thumb says $15k to $60k over 3 to 12 months, with no live source. Sources: docs.datadoghq.com/account_management/audit_trail, datadoghq.com/trust.
- Sell auditability as the wedge, expand to prevention. Vanta turned point-in-time SOC 2 into continuous monitoring across 400+ integrations with proof-sharing Trust Centers. Our version: every flagged promise becomes exportable evidence the buyer auditor accepts. That flips security review from blocker to accelerator. Source: vanta.com.
- Price hybrid: seat floor plus usage plus performance kicker. PagerDuty Professional runs $21 per user per month. incident.io runs $15 to $25. Datadog log management runs $0.10 per GB. Performance share (percent of recovered leakage) UNVERIFIED live, but matches post-purchase warranty norms. Recommendation: $499 to $2k platform floor plus per-action usage plus 10 to 20 percent of recovered leakage, capped. Sources: pagerduty.com/pricing, incident.io/pricing, datadoghq.com/pricing.

## Wedge ladder to replicate (three phases)

- Phase 1, free audit at $0 with no card. Trigger: first missed refund found. Triple Whale Free unifies Shopify plus ad data with no card. Our version reconciles the last 100 promises and shows dollars at risk. Source: triplewhale.com/free.
- Phase 2, mid-market ramp at $49 (500 promises) to $299 (5k) to $899 (25k) with per-promise overage. Trigger: overage math that favors upgrade. Gorgias ramps $10 (50 tickets) to $900 (5,000) with $0.36 to $0.40 overages. It gates AI allotments plus analytics per tier. Source: gorgias.com/pricing.
- Phase 3, enterprise custom with VPC plus SLA. Trigger: procurement and throughput. Reducto runs Standard per-1k-page rates ($10 Parse, $20 Extract, $40 Deep Extract). Growth adds volume discount and residency. Enterprise adds VPC and custom MSA. Source: reducto.ai/pricing.
- Scope discipline from all four: Reducto shipped rough UI but refused to compromise core accuracy. Enterprise gates (VPC, residency) arrived only after pull. Gorgias started as a Shopify-only shared inbox, not a CX platform. Triple Whale started as a pixel plus dashboard, not an AI OS. One metered primitive, one champion, enterprise controls only after pull. Sources: reducto.ai/blog/reducto-enterprise-sales, gorgias.com/pricing, triplewhale.com/pricing.

## What changes for Settleye

- Landing page: lead every card with dollars, bury ledger words. Already specified in `landing-design.md`. No change needed.
- Pricing teaser: add the $0 scan plus $19/mo SMB line beside the $299 starter. Current teaser starts too high for the App Store long tail.
- Demo: open on found money, never on architecture. Current script already does this. No change needed.
- Post-hackathon: the free 90-day shadow audit is the Phase 1 wedge. The export pack is the Phase 3 seed. Both already exist as concepts. Build order stays: page, video, submit.
