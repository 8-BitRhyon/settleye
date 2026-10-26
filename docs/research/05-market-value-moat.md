# Market Value and Moat

Researched 2026-10-26. Two parallel deep-dives: dollars and defensibility.

## Value: TAM/SAM/SOM

Base: ~3.1M active Shopify stores (StoreLeads crawl, Q4-2026).

| Layer | Math | Count | Revenue at $99/mo |
|---|---|---|---|
| TAM: active stores | crawled | 3.1M | $3.7B/yr (fantasy ceiling) |
| SAM: AI agents plus volume worth caring | 3.1M x ~25% AI x ~40% with 200+ orders/mo | ~300K | ~$360M/yr |
| SOM: 3yr via App Store | 1-3% of SAM; comps: Gorgias 17K brands, Chargeflow 20K merchants | 3K-9K | $3.6M-10.7M ARR |

Confidence: HIGH on store counts and GMV; MEDIUM on AI share (66% of service orgs run agents per Salesforce, but only 10% mature); LOW on SOM conversion. Weakest assumption: that a quarter of stores both run AI agents and feel ledger pain acutely. No Shopify-specific AI-penetration source exists.

## Value: ROI and pricing

- Prevention anchor: merchants already pay $15-40 to kill ONE dispute pre-chargeback (Ethoca/RDR alerts). That is the per-incident WTP ceiling.
- Adjacent pricing: Gorgias $10-900/mo, Fin $0.99/outcome, Chargeflow 25% of recovered, fraud apps $19-40/mo. $49-199/mo sits inside the existing support-tooling band: plausible, not obviously cheap.
- Model merchant (500 orders/mo, $90 AOV, $99 plan): ~$494/mo value vs $99 cost, ~5x ROI, ~6-day payback, ~2.5x even at 50% catch rate.
- Buyer: support/ops lead evaluates, founder or finance approves above ~$100/mo. Budget line is reallocated prevention spend (Gorgias plus Chargeflow plus alert fees), not new budget.
- Strongest counter-evidence: merchants win only 8.1% of all disputes outright and rationally abandon small ones; free Shopify Fraud Control plus bundled guardrails compress paid-auditor room. Target mid-market ($10K+/mo GMV, agent live, 1+ disputes/mo). Do not chase the long tail.

## Moat: temporary wedge, not a moat, not just a feature

| Candidate | Verdict |
|---|---|
| Cross-platform join (any agent x Stripe plus Shopify) | REAL, temporary 12-18mo. No incumbent is neutral; each verifies only itself. |
| Dispute-grade audit evidence (promise plus ledger plus remediation as representment bundle) | REAL-ISH wedge. Nobody packages this; manual win rates run under 20%. |
| Promise-extraction accuracy | ILLUSORY. Requirement, not moat; same base models as everyone. |
| Remediation idempotency | ILLUSORY. Documented header pattern; days of work. |
| Eval harness of hallucinated transcripts | ILLUSORY. Trivially replicable sales tooling. |

Absorption ranking: Gorgias ships verified actions first (HIGH, 6-9mo, kills Gorgias-native segment), then Decagon/Sierra add post-execution reconciliation (HIGH, 9-12mo, own agents only), then Zendesk QA / Fin (MEDIUM), Shopify Flow/Sidekick (MEDIUM, verifies only Sidekick), Stripe (LOW, will partner not build).

Data moat: only if we publish the cited reliability benchmark; incumbents see orders of magnitude more data otherwise. Distribution moat: App Store reviews are weak defense; surviving audit apps win by becoming the system of record priced on recovery.

Precedents: Chargeflow HELD against native dispute views by owning evidence assembly plus outcome pricing (lesson: sell the evidence pack, not the dashboard). Magic-wrapper apps got SHERLOCKED as checkboxes (lesson: the join plus remediation plus dispute evidence is the only non-checkbox part).

## What this means for the hackathon

Nothing about the 9-day build changes: judges score the demo, not the 10-year moat. But positioning sharpens: pitch the wedge plus the benchmark vision, price adjacent to recovery ($49-199/mo), target mid-market in every example, and make the audit export (representment-ready evidence pack) a first-class demo beat, not an afterthought.
