# Settleye

**Your AI agent promised a refund. Did the money move?**

Settleye is the execution auditor for AI support agents. AI agents tell customers a refund is processed while the underlying tool call silently fails or never runs. Operating post-execution directly against financial ledgers, Settleye extracts each promise from the transcript with a Meta model, reconciles it against Stripe and Shopify ledger state, clamps shortfalls and enforces original charge ceilings, and surfaces mismatches in an exception inbox with durable, tamper-evident Ed25519 execution receipts.

Live demo: https://8-bitrhyon.github.io/settleye/landing.html

Built for the Meta Global AI Developer Hackathon (Indie Developer Track, Push the Frontier, Oct 26 to Nov 4, 2026).

## How it works

1. **Extract.** `meta-models/muse-spark-open-1026` (via Baseten) returns structured promise objects. Every reply passes Pydantic validation. Bad output gets two repairs, then a loud failure instead of a guess.
2. **Gate.** Only binding commitments reach the ledger. Retracted, conditional, superseded, and info-only text never reports drift.
3. **Reconcile.** Each binding refund diffs against settled ledger state: verified, drift, unverifiable, or not binding.
4. **Explain.** Each drift gets a plain-English summary on demand.
5. **Remember.** A batch daemon flags orders promised across several tickets.
6. **Remediate.** One click settles drift against the demo's mock ledger through an idempotent service. Receipts persist to an append-only JSONL store keyed by the promise, so a restart cannot double-refund and a retry returns the original receipt. When an issuer key and audit context are configured, the live response also carries a signed execution receipt. The Shopify and Stripe write adapters pass tests but are not selected by the HTTP route in this build.

## Proof hierarchy: measured, labeled, modeled

Settleye validates its execution auditing and settlement layer through a three-tier proof hierarchy:

### Tier 1: Live, Read-Only Dev-Store Proof ($44.00 caught)
- **Live Shopify run**: On dev-store order #1001, the customer was promised a $50.00 refund while the Shopify ledger settled only $6.00. Settleye's audit daemon queried Shopify Admin GraphQL in read-only mode and reported $44.00 at risk in 4.07 seconds. One test-mode order, no money moved, not a fleet sample.
- **Hardened credential safety**: Secret app keys (`shpss_`) are rejected before transmission (exit code 3); only short-lived `shpua_` OAuth access tokens are accepted.

### Tier 2: Ground-Truth Labeled Eval Replay (12 Transcripts)
- **Eval set (`fixtures/eval/`, 12 cases)**: 12 of 12 verdicts correct, 11 of 12 entities exact. See `docs/research/12-eval-results.md`.
- **Zero non-binding drift**: 0 of 4 non-binding promises (retracted, conditional, superseded, info-only) reached drift; the superseded case drifts only on its replacement binding promise.
- **Zero false clears**: 0.0% false-clear rate across labeled binding cases (0 of 8 missed).
- **Frontier comparison**: Benchmarked on identical prompts between `meta-models/muse-spark-open-1026` and `gemini-4-argon`. Both achieved 11/12 exact; Argon hallucinated an invented order ID (`EVAL09`), whereas Muse hallucinated zero orders.
- **Shadow audit proxy**: 12 tickets, 5 drifts, $285.50 at risk ($23,791.67 per 1,000 tickets). See `docs/research/23-shadow-audit.md`.

### Tier 3: Modeled Fleet Exposure & Pipeline Benchmarks
Using empirical support queue distributions from the ABCD retail corpus (10.6% refund intent, 66.7% binding commitment rate, 4.0% agent tool-call execution failure rate, $52.50 average refund):

| Volume Tier | Monthly Tickets | Annual Drift Events | Direct Dollars Caught | Dispute Loss Prevention (4.61x) | Chargeback Fee Savings ($128/ea) | Modeled Annual Exposure Protected |
|---|---|---|---|---|---|---|
| **Mid-Market** | 10,000/mo | 336 drifts/yr | $17,640.00 | $81,320.40 | $43,008.00 | **$124,328.40** |
| **Large E-Commerce** | 100,000/mo | 3,396 drifts/yr | $178,290.00 | $821,916.96 | $434,688.00 | **$1,256,604.96** |
| **Global Enterprise** | 1,000,000/mo | 33,936 drifts/yr | $1,781,640.00 | $8,213,360.40 | $4,343,808.00 | **$12,557,168.40** |

- **Pipeline micro-benchmark**: about 95,000 to 122,000 transcript audits per second on this machine, p50 about 0.009 ms, over 1,000 canned transcripts and a mock ledger. No model or network calls. Model inference is seconds per transcript, not milliseconds.
- **Latency scope**: the p50 above describes the deterministic pipeline only. They are not model latency and not an end-to-end merchant SLA.
- **Modeled dispute and fee avoidance**: uses the LexisNexis 4.61x multiplier for true dispute cost and a $128.00 card network chargeback fee. These are assumptions, not merchant measurements.
- **Assumptions**: 10.6% refund intent, 66.7% binding commitment, 4.0% execution failure, $52.50 average refund, 4.61x dispute cost, $128 chargeback fee. The 4.0% failure rate is an assumption, not a merchant measurement. The table is a projection, not a guarantee or a merchant result.
- **Cross-Ticket Memory**: `find_repeat_orders` groups drift across tickets, catching repeat promises (e.g. order #992 promised in 4 transcripts, flagging $165.50 concentrated risk).

### Cryptographic & Operational Hardening
- **Signed receipts**: Ed25519 issuer and merchant signatures verify in the browser with pinned keys; a one-digit amount change or altered merchant timestamp fails verification. See `docs/receipt-spec.md`.
- **Live signed path**: A binding refund for `#992` returned a signed envelope, the registry accepted it, a restarted service returned the same envelope, and the replay moved $0.00. Retired keys verify old receipts; revoked or unknown keys fail.
- **Concurrency & Ceilings**: Concurrent duplicate fixes produce one refund and one receipt. Forged larger promises after a refund are rejected by the original charge ceiling (HTTP 422).
- **Free gate bench**: A 55 MB TinyBERT fine-tune kept 10 of 10 commitments on eval, but on 10,042 real ABCD dialogues filtered only 0.9% to 1.7% of tickets. Documented as a transparent negative result rather than claiming artificial cost savings. See `docs/research/22-free-gate-finetune.md`.
- **Test Suite**: 235 backend checks plus 93 frontend checks, green on every push.

## Run it yourself

### 60-Second Judge Path (Dual-Track)

#### Track A: Instant Web Verifier (30 seconds, zero install)
Open the sample inbox at https://8-bitrhyon.github.io/settleye/index.html?sample=1. It is a static recording of a live audit, not a model call.
1. Click `Issue $45.00 refund`. One `Remediation receipt` appears with valid issuer and merchant signatures.
2. Click `Retry the same fix`. It returns `Already executed. $0.00 additional movement.` with the same idempotency key.
3. Click `Try tamper demo`. Both signatures fail; `Reset` restores both.
Nothing moves and no credentials are required.

#### Track B: 10-Second Zero-Credential Local Terminal CLI
For judges evaluating the cloned repository locally:

```bash
# 1. Run full backend test suite (235 passing tests in <1s)
cd backend && uv run pytest

# 2. Offline daemon sweep with verified drift reconciliation (12 tickets, 5 drifts, $285.50 at risk)
uv run python -m app.daemon --dir ../fixtures/eval --ledger mock --replay ../fixtures/eval_live_output.json

# 3. Pipeline micro-benchmark (about 95k to 122k audits/sec, p50 about 0.009ms; canned extraction, mock ledger, no model calls)
python3 ../bench/fleet_benchmark.py

# 4. Modeled fleet exposure projection (not measured; assumptions in bench/fleet_projection.py)
python3 ../bench/fleet_projection.py
```

Or run the complete verification suite in one command:
```bash
bash tools/judge_audit.sh
```

### Full Local Pipeline (Optional, requires model key)

To run live extraction against the model:

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

`keyring init` writes a fresh issuer keypair and public registry under `backend/.tmp/`, both gitignored. Without it, remediations still persist but the response carries no signed envelope.

3. Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

4. Open http://localhost:5173 and click `Audit transcript`. That calls the model. Without `BASETEN_API_KEY`, `/audit` returns 503 by design.

No-key paths that run offline with zero credentials: `uv run pytest`, `uv run python -m app.daemon --dir ../fixtures/eval --ledger mock --replay ../fixtures/eval_live_output.json`, `python3 bench/fleet_benchmark.py`, `python3 bench/fleet_projection.py`, `python -m app.keyring init` and `list`, the browser sample verifier, `POST /receipt/verify`, `GET /receipt/keys`, and the frontend tests and build. Live daemon execution without `--replay` and `/explain` call the model and require `BASETEN_API_KEY`.

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

The Dev Dashboard app `Settleye Auditor` exchanges its client ID and secret for a 24-hour `shpua_` access token. `token --write` refreshes that token in `.env` without printing it. The live check reads settled refunds for order #1001. The daemon replays the $50 fixture and reports $44 at risk. Neither writes money. A `shpss_` value is the app secret, not the access token; use the token command. A custom app's `shpat_` token also works if you prefer that setup.

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
