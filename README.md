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

## Live model proof (how extraction is tested)

Everything below the model call is unit-tested with mock transports
(`backend/tests/`, 36 green, no network). The live call needs real
Baseten credits exactly once per verification:

```bash
export BASETEN_API_KEY=...
cd backend
uv run python -m app.extract.live_check ../fixtures/transcript_phantom_refund.json
```

Exit 0 prints the model ID, wall time, and validated entities. Anything
else fails loudly: `2` means no key (nothing was called), `3` means the
endpoint is unreachable (bad key, wrong URL, or cold start), `4` means
the output never validated after bounded repairs. Expected result on the
phantom fixture: one `refund $45 order #992` entity.

Failure guide: 401 means the key is wrong; model-not-found means the ID
drifted (it must stay `meta-models/muse-spark-open`); a first-call
timeout usually means a cold start, wait and retry once.

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

- Intelligence core is Meta models (`meta-models/muse-spark-open-1026` per event guide; `MODEL_ID` env overrides). See `design.md`.
- Challenge track: Push the Frontier (new capability for real-world agent systems).
- Test-mode and dev-store credentials only. No live payments, no real customer data. All fixtures are synthetic.
- Repository is public and greenfield: created for this event, every commit timestamped here. Demo opens with the required pre-existing-vs-built line (nothing pre-existed: repo did not exist before Oct 26).
- Submission bundle: 3-minute video, this repo, contributor names. Post the demo on X for the Most Viral award; community vote opens Nov 9.
