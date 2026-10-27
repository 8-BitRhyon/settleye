# Settleye

**Auditor for AI support agents that promise money.** Built for the Meta Global AI Developer Hackathon (Indie Developer Track, Oct 26 to Nov 4, 2026).

AI agents tell customers a refund is processed while the tool call fails or never runs. Settleye extracts each promise from the transcript with a Meta model. It reconciles each promise against live Stripe and Shopify state. Mismatches land in an exception inbox with a one-click fix.

## What it does

- Extract: `meta-models/muse-spark-open-1026` (via Baseten) returns promise objects. Output passes Pydantic validation. Bad output gets two repairs, then a loud failure.
- Gate: only binding commitments reach the ledger. Retracted, conditional, superseded, and info-only text never reports drift.
- Reconcile: each binding refund diffs against settled ledger state. Result is verified, drift, unverifiable, or not binding.
- Explain: each drift gets a plain-English summary on demand through POST /explain.
- Remember: the daemon sweep flags orders promised across several tickets.
- Remediate: one click settles drift through an idempotent service. Retries return the original receipt.

## Measured proof

- Eval set (`fixtures/eval/`, 12 cases): 12 of 12 verdicts correct. 11 of 12 entities exact. Zero non-binding drifts in four chances. See `docs/research/12-eval-results.md`.
- Live Shopify run: order #1001 showed $6.00 settled of $50.00 promised. The daemon reported $44.00 at risk in 4.07 seconds. A two-ticket sweep flagged the repeat at $88.00.
- Suite: 82 backend checks plus 6 frontend checks. CI runs tests, typecheck, build, and a secret scan on every push.

## Quickstart (under five minutes)

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

Batch sweep:

```bash
cd backend
uv run python -m app.daemon --dir ../fixtures/eval --ledger mock
```

Copy `.env.example` to `.env`. Fill in test-mode credentials only. Never commit `.env`.

## API

- POST /audit takes a transcript and returns promises, results, drifts, and totals.
- POST /explain takes one drift and returns a plain-English summary.
- POST /remediate takes a drift and returns an idempotent receipt.
- GET /value returns recovered dollars and avoided disputes.

## Docs

- `design.md` holds architecture, invariants, and key decisions.
- `docs/research/` holds market, competitor, feasibility, strategy, eval, and impact reports.
- `docs/demo-script.md` holds the word-for-word demo script.
- `docs/marketing/` holds landing copy, launch kit, and growth plan.
- `docs/submission/checklist.md` holds the human steps to the deadline.
- `AGENTS.md` holds the operating contract for coding agents.

## Compliance notes

- Intelligence core is Meta open weights (`meta-models/muse-spark-open-1026` per event guide, `MODEL_ID` env overrides). See `design.md`.
- Challenge track is Push the Frontier (new verification layer for agent systems).
- Test-mode and dev-store credentials only. No live payments. No real customer data. All fixtures are synthetic.
- Repository is public and greenfield. It did not exist before Oct 26. Every commit carries a timestamp here.
- Submission bundle is a 3-minute video, this repo, and contributor names. Post the demo on X for the Most Viral award. Community vote opens Nov 9.
