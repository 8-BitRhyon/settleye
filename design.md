# Design Notes

One-page architecture note. Update when structure changes. This is the owner of architectural facts; do not duplicate them elsewhere.

## Purpose

PromiseCheck catches silent execution drift: AI support agents promise ledger actions (refunds, cancellations) that never settle. It extracts structured promise entities from transcripts with a Meta model, diffs them against live Stripe/Shopify state, and surfaces mismatches in an exception inbox with one-click remediation.

## Structure

```
promise-check/
  backend/            FastAPI service (uv, Python 3.12)
    app/main.py       App entry, /healthz, router wiring
    app/models.py     Promise entity + reconciliation result schemas (Pydantic v2)
    app/ledger/       Ledger abstraction; Stripe + Shopify + mock adapters
    app/extract/      Meta-model extraction client (validate + retry)
    app/reconcile/    Promise-vs-ledger diff engine
    tests/            pytest suite (runs green from clean clone)
  frontend/           Vite + React + TS + Tailwind exception inbox
  fixtures/           Sample transcripts (incl. hallucination bugs) + mock ledger
  docs/research/      Market, competitor, feasibility, strategy reports
```

## Invariants

- The extraction model output is untrusted text until Pydantic validation passes.
- Baseten does NOT enforce JSON schema for Muse Spark Open: always validate + bounded retry (max 2), never unbounded.
- Remediation writes go through one service with idempotency keys; Stripe and Shopify are separate refund rails that must never double-refund.
- Test-mode keys only (`sk_test_`, `shp_...` on dev stores). Live keys never enter the repo or the demo.
- `main` is always green: CI runs backend tests, frontend typecheck+build, and secret scan.

## Boundaries

- We own: transcript ingest, promise extraction, reconciliation diff, inbox UI, remediation orchestration, audit log.
- We delegate: inference (Baseten/Modal hosted Meta models), money movement (Stripe/Shopify APIs), hosting (Modal + static frontend).

## Key Decisions

| Decision | Reason | Date |
|---|---|---|
| Model ID `meta-models/muse-spark-open` (no `-1026` suffix) | Suffixed ID does not exist on any provider; verified 2026-10-26 | 2026-10-26 |
| Validate-then-retry extraction, not constrained decoding | Baseten accepts but does not enforce `json_schema` for this model | 2026-10-26 |
| Mock ledger adapter behind interface from day one | Shopify auth/idempotency friction is the top integration risk | 2026-10-26 |
| Monorepo (backend + frontend + fixtures) | One clone, one CI, sub-5-minute judge setup | 2026-10-26 |
| Python 3.12 + `uv`, React + TS via Vite | Fastest credible path per stack research | 2026-10-26 |

## Conventions

- Naming: `snake_case` Python, `camelCase` TS/React.
- Errors: FastAPI raises `HTTPException` with machine-readable `detail`; frontend surfaces `detail` verbatim, never a generic toast.
- Tests live next to code (`backend/tests/`, `frontend/src/**/*.test.*`); fixtures live in `fixtures/`.
