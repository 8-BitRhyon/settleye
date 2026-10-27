# Gemini Verdict: Prompt Plus Cache Plus Verify, Distill Past 1.5M Tickets

Full report received 2026-10-27 (images). Distilled decisions below; numbers are the report's.

## Fine-tune vs prompt: do not fine-tune for 3 months

- Stay on `meta-models/muse-spark-open-1026` via Baseten with prefix caching, prompt evolution (GEPA/DSPy), and deterministic post-extraction verification.
- Unit cost: $3.80 per 1,000 audits at 85% cache hit ($0.315/1M cached, $1.25/1M fresh, $4.25/1M out, 1.07x retry). $190.17/mo at 50k audits/mo.
- SFT suffers representational collapse and rule memorization on out-of-distribution phrasing; GEPA beats GRPO by 6-19pp with 35x fewer rollouts.
- Crossover where fine-tuning wins: 50k-100k requests/day (1.5M-3.0M transcripts/mo). Fine-tuning is Series-A unit-cost compression, not an early moat. Moat is the labeled promise-to-ledger corpus plus the deterministic reconciliation engine.
- License note: Muse Model License requires a visible "Built with Muse Spark Open" label (added to UI footer and README). Separate commercial agreement only above $20M revenue via Model-as-a-Service.

## The one function (Candidate C)

Citation-grounded promise-to-ledger verification join: extract only net-binding, un-retracted commitments with character-span citations, reconcile deterministically across rails. Implemented as `terminal_status` (binding, conditional, superseded, retracted, info_only) plus `not_binding` verdict plus verbatim citation check.

## Enterprise accuracy bars (gold benchmark targets)

- False-all-clear rate at most 0.5% (recall at least 99.5% on broken promises).
- Inbox precision at least 98.0% (at most 2% false alarms, via verify loop).
- Leaf accuracy (amount, currency, order, action) at least 99.3%.
- Citation spans: exact substring match, enforced deterministically.
- Ledger state: 100% deterministic, zero LLM guessing on money movement.
- Confidence calibration error at most 0.03.

## Transferable Reducto patterns (adopted or queued)

- Single-pass joint extraction plus grounding (adopted: one model call does intent, entities, escalation, quotes).
- Agentic verify-and-correct with domain invariants (queued: arithmetic check like $40 minus $8 fee equals $32 settled; conditional/temporal critic for RMA-style contingencies).
- Sub-agent decomposition for multi-ticket histories (queued, post-hackathon).
- NOT transferable: OCR/layout pipelines, self-contained document truth (ours lives across async external ledgers).
- Open eval harness PromiseBench, Reducto-style: 500 paired cases, 5 diagnostic axes, synthetic failure injector, deterministic-first grader, checksums, 100-case private holdout. Human-verify every gold label twice (Pulse found 43 bad files in RD-TableBench).

## Commercial corrections applied to our docs

- Collar's own Terms (Oct 5, 2026) state site screens use made-up sample data: "$300B market cap" and "never invents a number" are UNVERIFIED. Our competitor note already says this; keep it.
- Reducto independent benches rank it 3rd/7th on text and financial tables, Deep Extract costs to 50.6c/page: the playbook (playground, verify loop, open evals) transfers, the accuracy boasts do not.
- Pricing shape to copy: free wedge (shadow audit, Reducto playground equivalent), Starter $299/5k tickets, Growth $999/25k tickets cross-rail, Enterprise custom. Price per audited resolution at 2-4% of the agent's own resolution cost.
- Pilot: 14-day read-only shadow audit over 90 days of tickets, 4-bucket leakage ledger readout to support ops plus finance.
- BNPL adjudication invariants for remediation guards: exact-match rules, Klarna 96-hour auto-chargeback, 21-day escalation blocks, Affirm off-amount email requirement, installment-deduction illusion, evidence pack format limits.
- 8 merchant profiles documented in the report images (fashion/BNPL, subscriptions/Recharge, 3PL/Gorgias, high-AOV/Affirm, Fin hybrids, Freshdesk email, VAMP-cliff flash sales, HubSpot B2B2C).
