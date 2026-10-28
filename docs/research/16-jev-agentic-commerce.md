# Jev System One plus Agentic Commerce: Gemini Deep Research (Oct 28, 2026)

Distilled filing of the full Gemini deep-research output (30+ pages). Structure, numbers, URLs, UNVERIFIED marks, and vendor caveats preserved. Vendor-claimed benchmarks are labeled as such. Nothing here is repo-measured.

## Jev primitives (TypeSafe AI, jev-1.13/1.14)

Discriminative, non-generative model. One forward pass evaluates typed questions in parallel against a shared state (64k token ceiling). Four primitives:

- noul: binary proposition, returns calibrated probability 0 to 1 (no separate confidence field).
- choice: up to 255 options, returns winner plus distribution plus confidence.
- score: ordered rubric levels, returns expectation plus dispersion confidence.
- box: spatial bounding box (1.14 only), for signatures and regions on images.

Training is RLCD (calibration-penalized), not RLHF. Questions in one call are strictly independent. Pin versions (jev-1.13.0/1.14), never calibrate against a moving alias. Keep arithmetic in code.

Vendor-claimed profile (TypeSafe-authored benchmarks, treat as unconfirmed until metered): 70-500ms latency, $0.042 per 1M input tokens, 0.00% schema error.

## Unit economics (vendor-modeled, unconfirmed)

Per 1,000 transcripts: Jev-only $0.081-0.126. Muse Spark Open on Baseten $3.803. Fine-tuned Qwen3-8B LoRA $0.155 plus $4,020 upfront. Hybrid (Jev gate plus 12% Spark escalation) $0.537. Self-hosting Spark Open: $24k-36k/month floor. Our measured Baseten cost ($3.80/1k) matches their model input, which raises confidence in the arithmetic but not in Jev vendor claims.

## Four use cases mapped to Settleye

1. Pre-execution guardrail (AutoModeMiddleware): intercept refund tool calls, evaluate window/final-sale/scope/confirmation/abuse questions in parallel, block or route. Fits Zendesk 10s timeout budgets on paper.
2. Async PromiseCheck plus three-way ledger join: noul detects commitment, choice classifies modality, then Shopify plus Stripe plus ARN verification. Matches our existing join, extended with ARN injection into tickets.
3. BNPL state machines: per-provider rules (Klarna 96h, Afterpay thresholds, Affirm email-first, Sezzle portal). Vision-state, not built-state.
4. VAMP defense plus CE 3.0 evidence: field-pair checks, same-month filing, 13.6 packet assembly. Vision-state.

## A2A vectors (Cheeky Pint ep. 35: Zuckerberg, Wang, Collison)

1. Headless browser risk: cloud-IP checkouts break CE 3.0 telemetry, trigger false declines, misread policies. Entry: machine-readable policy handshake plus ledger-only proof.
2. Agent-to-agent negotiation: buyer agents vs merchant bots, sycophancy exploitation, template floods, token burn. Entry: deterministic M2M settlement gate instead of haggling.
3. Stripe ACS integration: feed race conditions, SPT disputes, Link wallet approvals. Entry: park on Stripe webhooks as the verification layer. Plus MPP/x402 micro-fee monetization ($0.002-0.005 per verified call, vendor-modeled margins).

## Pilot playbook (Reducto plus Collar pattern)

Day 1 read-only shadow ingest. Weeks 1-2 live shadow gating. Week 3 economic buyer review. Week 4 active guardrail cutover. Beachhead: Gorgias Pro merchants, Stripe ACS adopters, operator communities. Pricing ladder from self-serve floor to enterprise ACVs.

## Caveats the report itself discloses

TypeSafe benchmark workflows were authored by TypeSafe. My AskAI ranked its own tool first (88%). micro1 LongExtractionBench was commissioned by Reducto. Cross-industry transcript-evidence uplift is UNVERIFIED. The promised-but-unissued rate remains UNVERIFIED everywhere.

## Verdict for Settleye (recorded)

Architecturally coherent, commercially premature. No Jev key exists. No figure is independently metered. The freeze holds until judging. Post-hackathon order:
(1) live Jev trial on the 12-case eval, metered against our mock-gated baseline.
(2) shadow-audit pilot clause from the impact report.
(3) BNPL rails only after pull. Sources: typesafe.ai, docs.typesafe.ai, langchain.com Jev harness guide, podcastnotes.org Cheeky Pint summary, stripe.com agentic-commerce docs.
