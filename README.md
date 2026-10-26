# PromiseCheck

**Autonomous state-reconciliation and execution auditor for AI support agents.** Built for the Meta Global AI Developer Hackathon (Indie Developer Track, Oct 26 - Nov 4, 2026).

AI agents promise ledger actions in natural language ("I have processed your $50 refund") while the underlying tool call silently fails or never happens. PromiseCheck extracts structured promise entities from transcripts with a Meta model, diffs them against live Stripe/Shopify state, and surfaces mismatches in an exception inbox with one-click remediation.

## Quickstart (under 5 minutes)

Backend:

```bash
cd backend
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run typecheck
npm run build
npm run dev
```

Copy `.env.example` to `.env` and fill in test-mode credentials only. Never commit `.env`.

## How it works

1. **Ingest:** support transcript or audio in, normalized to text.
2. **Extract:** `meta-models/muse-spark-open` (via Baseten) returns strict JSON promise entities (Pydantic-validated, bounded retry).
3. **Reconcile:** daemon diffs asserted state against Stripe test-mode / Shopify dev-store ledger APIs.
4. **Remediate:** mismatches land in the exception inbox; one click executes the corrective API payload and writes the audit entry.

## Deterministic test harness

- Case A (`fixtures/transcript_happy_path.json`): pleasantries, zero promises, `Verified Green`.
- Case B (`fixtures/transcript_phantom_refund.json`): $45 refund promised for order #992, ledger shows $0 refunded, `STATE_DRIFT_EXCEPTION`.

## Docs

- `design.md`: architecture, invariants, key decisions.
- `docs/research/`: market, competitor, feasibility, and strategy reports.
- `AGENTS.md`: operating contract for coding agents.

## Compliance notes

- Intelligence core is Meta models (`meta-models/muse-spark-open`); see `design.md` for the verified model ID.
- Test-mode and dev-store credentials only. No live payments, no real customer data. All fixtures are synthetic.
