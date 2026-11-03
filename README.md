# Settleye

**Your AI agent promised a refund. Did the money move?**

Settleye is the execution auditor for AI support agents. AI agents tell customers a refund is processed while the underlying tool call silently fails or never runs. Settleye extracts each promise from the transcript with a Meta model, reconciles it against live Stripe and Shopify state, and surfaces mismatches in an exception inbox with a one-click fix.

Live demo: https://8-bitrhyon.github.io/settleye/landing.html

Built for the Meta Global AI Developer Hackathon (Indie Developer Track, Push the Frontier, Oct 26 to Nov 4, 2026).

## How it works

1. **Extract.** `meta-models/muse-spark-open-1026` (via Baseten) returns structured promise objects. Every reply passes Pydantic validation. Bad output gets two repairs, then a loud failure instead of a guess.
2. **Gate.** Only binding commitments reach the ledger. Retracted, conditional, superseded, and info-only text never reports drift.
3. **Reconcile.** Each binding refund diffs against settled ledger state: verified, drift, unverifiable, or not binding.
4. **Explain.** Each drift gets a plain-English summary on demand.
5. **Remember.** A batch daemon flags orders promised across several tickets.
6. **Remediate.** One click settles drift through an idempotent service. Retries return the original receipt, never a second refund.

## Measured proof

- Eval set (`fixtures/eval/`, 12 cases): 12 of 12 verdicts correct, 11 of 12 entities exact. Zero non-binding drifts in four chances. See `docs/research/12-eval-results.md`.
- Live Shopify run: dev-store order #1001 showed $6.00 settled of $50.00 promised. The daemon reported $44.00 at risk in 4.07 seconds.
- Free gate bench: a 55 MB TinyBERT fine-tune kept 10 of 10 commitments on the 12-case eval and discarded 12.7% of 300 money-adjacent wild rows at threshold 0.50. Bench-only, not wired into the API. See `docs/research/22-free-gate-finetune.md`.
- Suite: 97 backend checks plus 34 frontend checks, green on every push.

## Run it yourself (under five minutes)

Backend:

```bash
cd backend
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Paste the sample transcript, click Audit transcript.

Batch sweep without the server:

```bash
cd backend
uv run python -m app.daemon --dir ../fixtures/eval --ledger mock
```

Copy `.env.example` to `.env` and fill in test-mode credentials only. Never commit `.env`.

## API

- `POST /audit` takes a transcript and returns promises, results, drifts, and totals.
- `POST /explain` takes one drift and returns a plain-English summary.
- `POST /remediate` takes a drift and returns an idempotent receipt.
- `GET /value` returns recovered dollars and avoided disputes.

## Docs

- `design.md` holds architecture, invariants, and key decisions.
- `docs/research/12-eval-results.md` holds the measured eval results.
- `docs/research/22-free-gate-finetune.md` holds the fine-tuned free-gate result.
- `docs/marketing/landing-copy.md` holds the landing page copy.
- `docs/marketing/deploy-cloudflare.md` holds the static deploy path.
- `AGENTS.md` holds the operating contract for coding agents.

## Notes

- Intelligence core is Meta open weights (`meta-models/muse-spark-open-1026` per event guide, `MODEL_ID` env overrides).
- Test-mode and dev-store credentials only. No live payments. No real customer data. All fixtures are synthetic.
- Greenfield repository built during the event. MIT licensed (see `LICENSE`).
