# Round-2 Findings: Vendors, Pain Data, Evals, Rails, Inbox UX, Regulation

Researched 2026-10-27 by six parallel tracks. Each section ends with the build implication.

## 1. Adjacent vendors: boundary holds, steals identified

Loop Intelligence, Redo, Corso, Extend, and Appriss all decide claims or score fraud BEFORE money moves; Klaus/MaestroQA/EvaluAgent score what was SAID. None checks afterwards whether the promised amount settled. Boundary sentence: they decide claims or score chats; we prove the money moved after the promise, sorted by dollars at risk.

Steals: Redo-style HIGH/MED/LOW money-sorted queue; Appriss-style cited-factors evidence trail per row; Corso-style performance pricing (share of recovered leakage, zero-fixed-fee pilot); EvaluAgent-style explicit "promised-but-unsettled" flag type; Rippit-style at-cost usage metering.

Build implication: add risk tiers to exception cards and a performance-pricing page; adopt the flag taxonomy.

## 2. Pain data: quantified, with one expiry date

- FTC Sentinel: $12.5B reported fraud losses in 2024 (+25% YoY); 38% of reporters lost money (vs 27% in 2023). https://www.ftc.gov/news-events/news/press-releases/2025/03/new-ftc-data-show-big-jump-reported-losses-fraud-125-billion-2024
- Negative-option complaints ~70/day in 2024, up from 42/day in 2021. Online shopping is the 2nd-most-reported fraud category.
- CFPB complaint DB is downloadable (CSV ZIP plus API) and public domain, ideal fixture material with one catch: narratives FROZE on Aug 14, 2026 (no new text after; historical archive via FOIA ZIPs). Pin `CCDB_Export_21_August_2026.zip` now; supplement with synthetic agent-chat fixtures.
- Paraphrased archetypes for fixtures: card-issuer/store-credit loop, remittance reversal stall, cancel-then-charge loop, fee-waiver bait, pay-to-delete.
- No published "promised-but-unissued refund rate" exists anywhere. That absence is itself a pitch point: nobody measures promise settlement.

Build implication: download the CFPB snapshot this week; write 5 fixtures from the archetypes; quote only the three FTC stats on stage.

## 3. Eval design: the gap is real, the template exists

- tau-bench (Sierra, MIT): deterministic DB-state comparison, pass^k consistency, airline refund tasks. Copy the DB-plus-tools-plus-verifier pattern; do not copy frozen tasks. Weaknesses to avoid: annotation ceilings, LLM-simulator fidelity gaps, no partial credit.
- AgentDojo: attack/defense environment with utility-plus-ASR triple metrics. Template for our adversarial robustness split.
- Corpora: ABCD (best seed: policy-constrained service actions), Taskmaster (spoken disfluencies), MultiWOZ (messy chatter, noisy labels), SGD (schema generalization; CC BY-SA, keep segregated).
- Gap verdict: partial grounding exists everywhere; NO benchmark extracts natural-language promises from dialogue AND reconciles each against independent ledger state with precision/recall on both stages.
- Recommended harness: 300-500 cases (150 rewritten ABCD/Taskmaster turns, 150 tau-style simulator dialogues with ground-truth DB writes, 50 AgentDojo-style injections), private 20% holdout, deterministic-first grader (tuple match plus ledger join), LLM judge only for span normalization, metrics led by false-all-clear rate and abstention rate, plus cost/latency and pass^2 stability. Open dataset, harness, and leaderboard; human-adjudicate 10%; score a regex baseline.

Build implication: start the fixture corpus now (CFPB archetypes plus rewritten ABCD turns); the open eval is the Reducto play and the moat seed.

## 4. Rails and dispute evidence: expansion order plus exact schema

- All five rails have usable sandboxes. Priority for a 2-person team: Affirm first (best self-serve sandbox, cleanest refund plus events API, merchant-pays-plus-$15 pain), then Adyen, PayPal, Klarna, Afterpay last (gated per-region creds).
- The merchant eats phantom refunds on every BNPL rail (lender already paid upfront). BNPL fraud 3-4%; friendly fraud ~20% of disputes; 16% of consumers admit false claims ($361 avg).
- Visa CE3.0 exact bar: 2 prior undisputed txns 120-365 days old, merchandise-or-services categorization, 2 of 4 matching elements with at least one being IP or device fingerprint. Win means issuer liability, no arbitration.
- Ethoca/RDR/CDRN pricing anchors hold ($15-40 per alert); RDR auto-refunds only, CDRN allows manual review.
- Export schema: disputed txn block (processor, IDs, amount, category, product description, account, email, address, IP, device) plus 2 priors plus refund evidence (promised_at, channel, amount, ledger IDs) plus alert block. Specified in full in the track report.

Build implication: Affirm adapter is next after Shopify; shape the export pack to the CE3.0 schema now so representment works later without rework.

## 5. Inbox UX rules (from incident.io, Rootly, PagerDuty)

1. Sort by amount_at_risk DESC, age DESC; severity chip from ledger delta, never model prose.
2. Card order: status chip, amount, 1-2 line quote with timestamp, ledger row (id, state, date), age timer, owner, one primary button.
3. Three states only (Open, Acked, Resolved); Ack halts escalation and records owner; only Resolve needs ledger evidence.
4. Two timers per card: time-to-ack (~4h, auto-escalate) and ack-timeout (~24h, flip back to Open). Countdown on card.
5. Triage holding state for low-confidence extractions (Confirm/Discard only, no paging).
6. Export is an append-only audit pack (quote plus snapshot plus transition log plus fix plus owner/due date), one-click HTML/PDF, drafted on Resolve, owner required to Close.

Build implication: implement rules 1-3 this week (sort, card order, three states); timers and triage next; export pack before demo day.

## 6. Regulation: tailwinds plus one trap

- EU AI Act Art 50 transparency duties apply from Aug 2, 2026; fines to EUR 15M or 3% turnover. Pitch: bots need disclosure plus an evidentiary trail; we are the trail.
- CA AB 2863 live for post-July-2025 contracts (consent records, annual reminders); ROSCA federal floor survives; click-to-cancel died procedurally July 2025 but UDAP/state actions live on. Pitch: "the rule died, the problem didn't."
- Moffatt v Air Canada stands (tribunal, persuasive not binding); US corroboration is regulatory (CFPB 2023 chatbot warning, joint AI statement, Utah disclosure law).
- SOC 2 Type I $15-30k / Type II $30-60k+, months of distraction: budget $25-60k first year, start readiness tooling early.
- TRAP: never ingest, log, or store raw PAN. Pull only charge/refund IDs, amounts, timestamps over read-only restricted keys, or inherit full PCI DSS scope and become unpurchasable. Same minimization for transcript PII.

Build implication: add a data-minimization invariant to design.md now (no PAN, IDs-plus-amounts only); put the three tailwind sentences in the demo script appendix.
