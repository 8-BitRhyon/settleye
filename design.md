# Design Notes

One-page architecture note. Update when structure changes. This file owns architectural facts. Do not duplicate them elsewhere.

## Purpose

Settleye catches silent execution drift. AI support agents promise ledger actions (refunds, cancellations) that never settle. It extracts promise entities from transcripts with a Meta model. It diffs them against live Stripe and Shopify state. It surfaces mismatches in an exception inbox with one-click remediation.

## Structure

```
settleye/
  backend/            FastAPI service (uv, Python 3.12)
    app/main.py       App entry: /healthz, /audit, /explain, /remediate, /value
    app/models.py     Pydantic v2 schemas: promises, results, receipts, batches
    app/ledger/       Ledger abstraction; Stripe plus Shopify plus mock adapters
    app/extract/      Meta-model extraction client (validate plus retry)
    app/explain.py    Per-drift plain-English summaries, on demand only
    app/reconcile/    Promise-vs-ledger diff engine with commitment gating
    app/remediate/    Idempotent one-click settlement service
    app/daemon.py     Batch sweep: audit-only default, repeat memory, Modal-ready
    app/value.py      Recovery ledger behind the inbox savings header
    tests/            pytest suite (runs green from clean clone)
  frontend/           Vite plus React plus TS plus Tailwind exception inbox
  fixtures/           Sample transcripts plus mock ledger plus 12-case eval set
  docs/research/      Market, competitor, feasibility, strategy, eval reports
```

## Invariants

- The extraction model output is untrusted text until Pydantic validation passes.
- Baseten does NOT enforce JSON schema for Muse Spark Open: always validate + bounded retry (max 2), never unbounded.
- Remediation writes go through one service with idempotency keys. Stripe and Shopify are separate refund rails that must never double-refund.
- Test-mode keys only (`sk_test_`, `shp_...` on dev stores). Live keys never enter the repo or the demo.
- Data minimization: never ingest, log, or store raw PAN. Pull only charge/refund IDs, amounts, and timestamps over read-only restricted keys, or inherit full PCI DSS scope. Same minimization for transcript PII.
- `main` is always green: CI runs backend tests, frontend typecheck plus build, and secret scan.

## Boundaries

- We own: transcript ingest, promise extraction, reconciliation diff, inbox UI, remediation orchestration, audit log.
- We delegate: inference (Baseten/Modal hosted Meta models), money movement (Stripe/Shopify APIs), hosting (Modal + static frontend).

## Key Decisions

| Decision | Reason | Date |
|---|---|---|
| Model ID `meta-models/muse-spark-open-1026` (event-instructed) | Event guide overrides the public catalog ID. MODEL_ID env selects anything else | 2026-10-27 |
| Rename to Settleye | Exact-name Shopify App Store collision plus rule 4.1.2 barred the old name | 2026-10-27 |
| refundCreate takes order GID plus SALE-parented transaction | Live schema introspection disproved the orderName guess. The idempotent directive sits on the field | 2026-10-27 |
| Daemon is audit-only by default | Scheduled autonomy must never move money. --auto-remediate runs on mock only | 2026-10-27 |
| Explanations fire per drift on demand | Sweeps keep one model call per transcript. Display text is capped and fact-bound | 2026-10-27 |
| Third-eye brand mark in final CTA | Presentation beats perf on first view. Lazy Three.js with static fallback. Floor 85, a11y 100 | 2026-10-27 |
| Jev hybrid evaluated, not adopted pre-judging | No live trial exists, vendor benchmarks unconfirmed, freeze holds. Revisit with metered eval after | 2026-10-28 |
| Challenge track: Push the Frontier | Execution-verification layer for the agent economy is a new capability, not a personal workflow fix | 2026-10-27 |
| Validate-then-retry extraction, not constrained decoding | Baseten accepts but does not enforce `json_schema` for this model | 2026-10-26 |
| Mock ledger adapter behind interface from day one | Shopify auth and idempotency friction is the top integration risk | 2026-10-26 |
| Monorepo (backend plus frontend plus fixtures) | One clone, one CI, sub-5-minute judge setup | 2026-10-26 |
| Python 3.12 plus `uv`, React plus TS via Vite | Fastest credible path per stack research | 2026-10-26 |

## Conventions

- Naming: `snake_case` Python, `camelCase` TS/React.
- Errors: FastAPI raises `HTTPException` with machine-readable `detail`. The frontend surfaces `detail` verbatim, never a generic toast.
- Tests live next to code (`backend/tests/`, `frontend/src/**/*.test.*`). Fixtures live in `fixtures/`.
