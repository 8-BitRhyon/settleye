# Settleye

**Your AI agent promised a refund. Did the money move?**

Settleye is the execution auditor for AI support agents. AI agents tell customers a refund is processed while the underlying tool call silently fails or never runs. Settleye extracts each promise from the transcript with a Meta model, reconciles it against Stripe and Shopify ledger state, and surfaces mismatches in an exception inbox with a one-click fix.

Live demo: https://8-bitrhyon.github.io/settleye/landing.html

Built for the Meta Global AI Developer Hackathon (Indie Developer Track, Push the Frontier, Oct 26 to Nov 4, 2026).

## How it works

1. **Extract.** `meta-models/muse-spark-open-1026` (via Baseten) returns structured promise objects. Every reply passes Pydantic validation. Bad output gets two repairs, then a loud failure instead of a guess.
2. **Gate.** Only binding commitments reach the ledger. Retracted, conditional, superseded, and info-only text never reports drift.
3. **Reconcile.** Each binding refund diffs against settled ledger state: verified, drift, unverifiable, or not binding.
4. **Explain.** Each drift gets a plain-English summary on demand.
5. **Remember.** A batch daemon flags orders promised across several tickets.
6. **Remediate.** One click settles drift through an idempotent service. Receipts persist to an append-only JSONL store keyed by the promise, so a restart cannot double-refund and a retry returns the original receipt. When an issuer key and audit context are configured, the live response also carries a signed two-party execution receipt.

## Measured proof

- Eval set (`fixtures/eval/`, 12 cases): 12 of 12 verdicts correct, 11 of 12 entities exact. Zero non-binding drifts in four chances. See `docs/research/12-eval-results.md`.
- Live Shopify run: dev-store order #1001 showed $6.00 settled of $50.00 promised. The daemon reported $44.00 at risk in 4.07 seconds.
- Free gate bench: a 55 MB TinyBERT fine-tune kept 10 of 10 commitments on the 12-case eval. On 10,042 real ABCD support dialogues it discarded only 0.9% at threshold 0.20 and 1.7% at 0.50, with zero false clears in the four skipped refund threads. Safe, but not a cost saver. Bench-only, not wired into the API. See `docs/research/22-free-gate-finetune.md`.
- Signed receipt: the sample's Ed25519 issuer and merchant signatures verify in the browser with pinned keys; a one-digit amount change or a changed merchant acknowledgement time fails. See `docs/receipt-spec.md`.
- Live signed path: a binding refund for `#992` returned a signed envelope, the registry accepted it, a restarted service returned the same envelope, and the replay moved $0.00. A retired key still verifies its old receipt; a revoked or unknown key fails.
- Shadow-audit proxy: 12 tickets, 5 drifts, $285.50 at risk, 0 of 8 false clears. This is recorded-output replay on synthetic cases with a mock ledger, not a merchant pilot and not a forecast. See `docs/research/23-shadow-audit.md`.
- Suite: 222 backend checks plus 76 frontend checks, green on every push.

## Run it yourself

**No key, no install, under one minute:** open the sample inbox at
https://8-bitrhyon.github.io/settleye/index.html?sample=1. It is a static
recording of a live audit, not a model call. Click `Issue $45.00 refund`, then
`Retry the same fix`, then `Try tamper demo`. Nothing moves and no credentials
are needed.

**Local API, full audit (needs a model key):**

1. Copy `backend/.env.example` to `backend/.env` and set `BASETEN_API_KEY`.
   Test-mode credentials only. Never commit `.env`.
2. Backend:

```bash
cd backend
uv sync
uv run pytest
uv run python -m app.keyring init
uv run uvicorn app.main:app --reload
```

`keyring init` writes a fresh issuer keypair and public registry under
`backend/.tmp/`, both gitignored. Without it, remediations still persist but the
response carries no signed envelope.

3. Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

4. Open http://localhost:5173 and click `Audit transcript`. That calls the
   model. Without `BASETEN_API_KEY`, `/audit` returns 503 by design.

No-key paths that really work: `uv run pytest`, `python -m app.keyring init`
and `list`, the browser sample verifier, `POST /receipt/verify`,
`GET /receipt/keys`, and the frontend tests and build. The daemon and
`/explain` still need `BASETEN_API_KEY` because they call the model; the mock
ledger replaces the ledger, not the model.

Batch sweep once the key is set:

```bash
cd backend
uv run python -m app.daemon --dir ../fixtures/eval --ledger mock
```

Shopify dev-store check (read-only, Dev Dashboard app):

```bash
uv run python -m app.ledger.token --write
uv run python -m app.ledger.live_check 1001
uv run python -m app.daemon --dir ../fixtures/live --ledger shopify
```

The Dev Dashboard app `Settleye Auditor` exchanges its client ID and secret for
a 24-hour `shpua_` access token. `token --write` refreshes that token in `.env`
without printing it. The live check reads settled refunds for order #1001. The
daemon replays the $50 fixture and should report $44 at risk. Neither writes
money. A `shpss_` value is the app secret, not the access token; use the token
command. A custom app's `shpat_` token also works if you prefer that setup.

## API

- `POST /audit` takes a transcript and returns promises, results, drifts, totals, and audit provenance.
- `POST /explain` takes one drift and returns a plain-English summary.
- `POST /remediate` takes a drift plus optional audit context and returns an idempotent receipt, with a signed envelope when a key is configured.
- `POST /receipt/verify` verifies an issuer-only or two-party receipt with a pin or the published registry.
- `GET /receipt/keys` returns public issuer key history and lifecycle state.
- `GET /value` returns recovered dollars and avoided disputes.

## Docs

- `design.md` holds architecture, invariants, and key decisions.
- `docs/research/12-eval-results.md` holds the measured eval results.
- `docs/research/22-free-gate-finetune.md` holds the fine-tuned free-gate result.
- `docs/research/23-shadow-audit.md` holds the 12-case shadow-audit proxy and the real-merchant blocker.
- `docs/receipt-spec.md` defines the signed execution receipt, key lifecycle, and merchant countersignature.
- `docs/marketing/landing-copy.md` holds the landing page copy.
- `docs/marketing/deploy-cloudflare.md` holds the static deploy path.
- `AGENTS.md` holds the operating contract for coding agents.

## Notes

- Intelligence core is Meta open weights (`meta-models/muse-spark-open-1026` per event guide, `MODEL_ID` env overrides).
- Test-mode and dev-store credentials only. No live payments. No real customer data. All fixtures are synthetic.
- The issuer and merchant signatures prove which pinned keys issued and acknowledged the exact payload. They do not independently prove that Stripe or Shopify state is true, that the transcript is authentic, or that money moved.
- Issuer and merchant private keys stay under `backend/.tmp/` and are never committed. Only public keys and public fixtures are tracked.
- Greenfield repository built during the event. MIT licensed (see `LICENSE`).
