# Settleye submission

**Your AI agent promised a refund. Did the money move?**

Settleye is the execution auditor for AI support agents. It extracts binding
promises from transcripts, reconciles each one against Stripe or Shopify ledger
state, surfaces the gap in an exception inbox, and fixes the shortfall against
the demo's mock ledger with a durable, signed, idempotent receipt.

## Links

- Live landing page: https://8-bitrhyon.github.io/settleye/landing.html
- No-install sample inbox: https://8-bitrhyon.github.io/settleye/index.html?sample=1
- 3-minute film with voiceover: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-film.mp4
- 15-second proof: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-proof.mp4
- Receipt verification clip: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-verify.mp4
- Repository: https://github.com/8-BitRhyon/settleye
- Submission tag: https://github.com/8-BitRhyon/settleye/tree/submission-2026-11-04

## 60-second judge path

Judges can verify Settleye either instantly in the browser or locally in the terminal with zero credentials.

### Track A: Instant Web Verifier (30 seconds, zero install)

1. Open the sample inbox: https://8-bitrhyon.github.io/settleye/index.html?sample=1 (renders a real recorded audit with `1 drift · $45.00 at risk`).
2. Click `Issue $45.00 refund`. One `Remediation receipt` appears with `Issuer signature valid`, `Merchant countersigned`, the receipt id, and `refund:992:stripe:45.00`.
3. Click `Retry the same fix`. It returns `Already executed. $0.00 additional movement.` with the same idempotency key.
4. Click `Try tamper demo`. Both signature rows turn invalid and the card reports the altered payload. `Reset` restores both valid rows.
5. Watch the 15-second proof (https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-proof.mp4), the receipt verification clip, and the 3-minute film.

### Track B: 10-Second Zero-Credential Local Terminal CLI

For judges evaluating the cloned repository locally:

```bash
# 1. Run full backend test suite (235 passing tests in <1s)
(cd backend && uv run pytest)

# 2. Offline daemon sweep with verified drift reconciliation (12 tickets, 5 drifts, $285.50 at risk)
(cd backend && uv run python -m app.daemon --dir ../fixtures/eval --ledger mock --replay ../fixtures/eval_live_output.json)

# 3. Pipeline micro-benchmark (about 95k to 122k audits/sec, p50 about 0.009ms; canned extraction, mock ledger, no model calls)
python3 bench/fleet_benchmark.py

# 4. Modeled fleet exposure projection (not measured; assumptions in bench/fleet_projection.py)
python3 bench/fleet_projection.py
```

Or run the complete verification suite in one command:
```bash
bash tools/judge_audit.sh
```

## The wedge

The support industry grades the conversation. The money only settles at the
ledger. Nobody joins the two per order.

- Guardrails check words before send.
- QA tools sample transcripts for tone.
- Dispute vendors act after the chargeback, often for 25% of recovered money.

Settleye sits after execution and before the dispute. It is not a better
chatbot. It is the proof layer between what the agent said and what the ledger
did.

## The frontier: Post-execution refusal and signed receipts

Extraction is commodity. The refusal path is not.

When autonomous AI agents act on behalf of merchants, words are not money. The central financial risk of agentic workflows is silent execution drift: an agent promises a refund to a customer, but the tool call silently drops, fails on the payment rail, or is never dispatched.

Settleye is not another prompt filter or LLM tone scorer. It is an execution auditor operating post-execution directly against financial ledgers.

### Invariants of Post-Execution Refusal

- **Server-Side Ledger Reconcile**: Queries live or test-mode ledger state before touching money.
- **Shortfall Clamping**: Clamps refunds strictly to the unledgered shortfall, even if the client requests a different amount. On order #1001, when $6.00 had settled on a $50.00 promise, Settleye issued exactly $44.00.
- **Charge Ceilings**: Refuses any promise or remediation exceeding the original captured transaction amount (HTTP 422), blocking balance drain attempts.
- **Non-Binding Interception**: Retracted, conditional, superseded, and informational promises are filtered before querying the ledger. Only unconditional binding commitments trigger reconciliation.
- **Append-Only Fsync Ledger**: Persists remediation receipts in an append-only JSONL store keyed by action, order, rail, and promised amount. A partial refund cannot mint a second key; a restart cannot forget the receipt; a corrupted receipt store fails closed.
- **Idempotent Settlement**: A retry returns the original receipt and moves exactly $0.00.

### The new artifact: two-party execution receipts

A remediation emits a portable, tamper-evident cryptographic receipt formatted as canonical RFC 8785 JSON. Settleye signs the payload with Ed25519, binding:
- Transcript SHA-256 digest
- Extracted promise
- Ledger observation
- Deterministic idempotency key
- Remediation result

A merchant can countersign the receipt id, establishing mutual non-repudiation between the autonomous agent and the merchant ledger.

- **In-Browser Local Verification**: The browser verifier pins issuer and merchant public keys and validates both signatures locally using Web Crypto.
- **Published Key Registry**: `GET /receipt/keys` exposes the public key registry supporting `active`, `retired`, and `revoked` states.
- **Fail-Closed Security**: Rotated keys still verify historical receipts. Revoked or unregistered keys fail immediately (`revoked_key`, `unknown_key`).
- **Cryptographic Tamper-Evidence**: Altering a single digit of the promised amount invalidates the issuer signature. Altering the merchant acknowledgement timestamp invalidates the merchant signature.

Spec: `docs/receipt-spec.md`.

This is the frontier claim: not another audit dashboard, but a two-party cryptographic proof artifact for autonomous agent execution.

## Three-tier proof hierarchy

Settleye separates its proof into three tiers: one live, one labeled, and one modeled. Only the first two are measurements.

### Tier 1: Live, Read-Only Dev-Store Proof ($44.00 caught)
- **Real Dev-Store Order #1001**: On a live Shopify dev store, the agent promised a full $50.00 refund for a damaged jacket. Only $6.00 had settled on Shopify.
- **Real-Time Detection**: Settleye's audit daemon queried Shopify Admin GraphQL in read-only mode, caught the $44.00 shortfall in 4.07 seconds, and surfaced the unledgered liability. One test-mode order, no money moved, not a fleet sample.
- **Credential Hardening**: Tested against live credential refusal. Secret tokens (`shpss_`) are intercepted and rejected before network transmission (exit code 3); only short-lived `shpua_` OAuth tokens are accepted.

### Tier 2: Ground-Truth Labeled Eval Replay (12 Transcripts)
- **12 of 12 Verdicts Correct, 11 of 12 Entities Exact**: Tested against 12 complex edge cases (`fixtures/eval/`), including phantom refunds, settled refunds, retractions, conditionals, policy explanations, supersessions, and missing order IDs.
- **Zero False Clears**: 0.0% false-clear rate across labeled binding cases (0 of 8 missed).
- **100% Non-Binding Refutation**: 0 of 4 non-binding promises reached drift. A superseded promise drifts only on its final binding commitment.
- **Frontier Model Comparison**: Benchmarked on identical prompts between `meta-models/muse-spark-open-1026` and `gemini-4-argon`. Both achieved 11/12 exact matches; Argon hallucinated an invented order ID (`EVAL09`), whereas Muse hallucinated zero orders.
- **Eval Drift Rate**: 5 drifts caught totaling $285.50 at risk.

### Tier 3: Modeled Fleet Exposure & Pipeline Benchmarks
Using stated funnel assumptions grounded in the ABCD retail corpus (10.6% refund intent, 66.7% binding commitment, 4.0% execution failure, $52.50 mean refund). The 4.0% failure rate is an assumption, not a merchant measurement:

| Volume Tier | Monthly Tickets | Annual Drift Events | Direct Exposure | Dispute Exposure (4.61x) | Chargeback Fees ($128/ea) | Modeled Annual Exposure Protected |
|---|---|---|---|---|---|---|
| **Mid-Market** | 10,000/mo | 336 drifts/yr | $17,640.00 | $81,320.40 | $43,008.00 | **$124,328.40** |
| **Large E-Commerce** | 100,000/mo | 3,396 drifts/yr | $178,290.00 | $821,916.96 | $434,688.00 | **$1,256,604.96** |
| **Global Enterprise** | 1,000,000/mo | 33,936 drifts/yr | $1,781,640.00 | $8,213,360.40 | $4,343,808.00 | **$12,557,168.40** |

- **Pipeline micro-benchmark**: about 95,000 to 122,000 transcript audits per second on this machine, p50 about 0.009 ms, over 1,000 canned transcripts and a mock ledger. No model or network calls. Model inference is seconds per transcript, not milliseconds.
- **Latency scope**: the p50 above describes the deterministic pipeline only. It is not model latency and not an end-to-end merchant SLA.
- **Modeled dispute loss avoidance**: based on the LexisNexis 4.61x multiplier for true dispute cost (lost merchandise, customer support labor, investigation overhead, and churn). Not a merchant measurement.
- **Modeled administrative chargeback fee savings**: evaluated at a $128.00 card network dispute fee per filing. Not a merchant measurement.
- **Projection assumptions**: 10.6% refund intent, 66.7% binding commitment, 4.0% execution failure, $52.50 average refund, 4.61x dispute cost, $128 chargeback fee. The 4.0% failure rate is an assumption, not a merchant measurement. The table is a projection, not a guarantee or a merchant result.
- **Cross-Ticket Memory**: `find_repeat_orders` groups unfulfilled commitments across tickets, detecting escalating customer friction on repeat orders (e.g. order #992 promised across 4 transcripts, flagging $165.50 concentrated risk).

### Additional Technical Evidence
- **Test Suite**: 235 backend tests and 93 frontend tests passing cleanly on every push.
- **Live Signed Keyring Path**: A binding refund for #992 returns an Ed25519 signed envelope; `POST /receipt/verify` validates it via the active registry key; service restarts return the identical receipt and move $0.00.
- **Concurrency & Ceilings**: Concurrent duplicate requests produce exactly one `executed` and one `already_executed` response. Forged amounts exceeding captured charges are blocked with 422.
- **Key Lifecycle**: Retired keys verify historical receipts; revoked keys fail with `revoked_key`; unregistered keys fail with `unknown_key`.
- **Free-Gate Exploration**: A 55 MB TinyBERT model trained on 1,500 domain examples retained 10/10 commitments on eval, but on 10,042 real ABCD dialogues filtered only 0.9% to 1.7% of tickets. Documented as a transparent negative result rather than claiming artificial cost savings.
- **Repository Integrity**: Git history begins at `c629cb9` on 2026-10-26 09:00 CDT, strictly within the hackathon window.

## Scope

- Fixtures are synthetic. The HTTP one-click fix uses the mock fixture; Stripe and Shopify adapters are test-mode only.
- No live payments. No real merchant savings claimed.
- The HTTP one-click fix does not reach Shopify or Stripe. Those write adapters pass tests but are not selected by the API route. The live dev-store proof is read-only.
- The HTTP API is a local demo without authentication and trusts the caller's promise shape. A charge ceiling blocks refunds beyond the captured amount, but production needs authentication and a server-stored audit binding.
- The idempotency lock is process-local. Run one API worker, or add a shared file or database lock for a multi-process deployment.
- The public sample receipt is signed by a demo issuer key and countersigned by a demo merchant key. The signatures prove those keys issued and acknowledged the payload; they do not independently prove Stripe or Shopify state.
- The live `/remediate` path signs only when `backend/.tmp/keyring.json` and the issuer private key are configured and the request carries audit context. Without them, the durable receipt is still recorded and `receipt` is `null`.
- The live path trusts the caller's transcript digest and audit time; it does not re-hash a stored audit. The signature binds the claim but does not prove the audit produced it. `audited_at` is transport metadata, not signed content.
- The published key registry is a local JSON file and a read-only endpoint, not a hosted certificate authority. Rotation and revocation are CLI operations.
- The shadow audit is a 12-case recorded-output replay, not a real merchant measurement. A real pilot needs a transcript export plus a Shopify read-only token or an exported ledger snapshot. The Stripe adapter is test-mode only, so a live Stripe pilot needs a new read-only adapter. The exact blocker and command are in `docs/research/23-shadow-audit.md`.
- The product path needs a transcript export and read-only ledger keys. The public sample and the 15-second proof need no install and no credentials.
- SOC 2 is a roadmap item, not a claim.

## Stack

- Meta Muse Spark Open (`meta-models/muse-spark-open-1026`) via Baseten.
- FastAPI, Python 3.12, Pydantic v2.
- Ed25519 receipts, canonical JSON, issuer key registry, merchant countersignatures.
- React, TypeScript, Vite, Tailwind.
- Stripe and Shopify test-mode adapters.
- Append-only JSONL remediation receipt store.
- Open-weight TinyBERT gate benchmark, kept out of the product path.

## Short pitch for the form

> AI support agents tell customers a refund is processed, then the tool call
> fails silently. Settleye pulls every binding promise from the transcript,
> diffs it against Stripe and Shopify ledger state, and fixes the shortfall with
> an idempotent receipt that survives restarts. The live fix emits a signed
> Ed25519 receipt; a merchant can countersign it, and the browser verifies both.
> Resolved is not settled. We prove it on a live dev store and a no-install
> public sample.

## What the judge should remember

**Resolved is not Settled.**

Settleye is the receipt between an AI agent's promise and the money that
actually moved.
