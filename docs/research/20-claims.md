# Claim ledger

Every number the landing page shows, where it comes from, and what it does not cover. If a claim is not here, it does not ship.

## Our measurements

| Claim | Value | Source | Scope |
|---|---|---|---|
| Model cost | Same shape: Opus $0.034, Sonnet $0.017, Astra $0.085; Claude Haiku 5.5 about $0.00085. We do not claim to beat it | `docs/research/21-model-comparison.md` | Cost only, not quality |
| Frontier comparison | 11 of 12 exact, same as ours | `docs/research/21-model-comparison.md`, `bench/score.py` | Single run per case on a 12-case set, Argon arm ran with agent scaffolding, one hallucination observed |
| Eval verdicts | 12 of 12 | `docs/research/12-eval-results.md` | Our own 12-case set, written by us |
| Exact entity matches | 11 of 12 | `fixtures/eval_live_output.json`, `backend/tests/test_eval_replay.py` | One documented miss: t07 returns an empty list where the manifest holds an info-only entity. Both are green |
| Non-binding promises that drifted | 0 of 4 | `docs/research/12-eval-results.md` | Retracted, conditional, superseded, info-only. The superseded case can still drift on its replacement binding promise |
| Wild transcripts processed | 300 of 300 | `docs/research/19-hf-benchmark.md` | Bitext sample, seed 7. Zero crashes, zero false binding promises |
| Free gate discard on real support text | 0.9% at 0.20, 1.7% at 0.50 | `bench/finetune/results/abcd_gate.json` | ABCD public human-human retail support, not merchant transcripts. Four skipped refund threads inspected, zero false clears |
| Live drift caught | $44.00 on order #1001 in 4.07s | `README.md` | Single Shopify test-mode dev-store order, read-only GraphQL. $6.00 of $50.00 settled. No money moved, not a fleet sample |
| Live signed remediation | Signed envelope, registry verify, restart replay, $0.00 additional | `backend/tests/test_signing_service.py`, `backend/tests/test_receipt_registry_api.py` | Local keyring and mock ledger. Proves the path, not a merchant deployment |
| Concurrent duplicate remediation | One refund, one receipt | `backend/tests/test_remediate.py` | Single process, including lazy cold-start creation and a duplicate arriving mid-append. The HTTP demo runs one worker; multi-process needs a shared lock |
| Forged larger promise | 422, ledger unchanged | `backend/tests/test_remediate.py` | Mock ledger charge ceiling. Production also needs authentication and a stored audit binding |
| Unpinned HTTP verification | `unpinned`, not valid | `backend/tests/test_receipt_registry_api.py` | The HTTP endpoint requires a caller pin or a configured registry |
| Key lifecycle | Retired verifies, revoked and unknown fail | `backend/tests/test_keyring.py` | Local JSON registry, not a hosted certificate authority |
| Two-party sample receipt | Issuer and merchant valid; tamper fails each | `frontend/src/sample-receipt.test.ts`, `frontend/src/receipt-merchant.test.ts` | Frozen demo keys and synthetic payload |
| Shadow-audit proxy | 12 tickets, 5 drifts, $285.50, 0/8 false clears | `docs/research/23-shadow-audit.md` | Recorded live model output replay on synthetic eval cases with a mock ledger. Not a merchant pilot, not a forecast. The per-1,000 figure stays in the research note only |
| Modeled fleet exposure | $124,328.40 / $1,256,604.96 / $12,557,168.40 per year at 10k / 100k / 1M monthly tickets | `bench/fleet_projection.py` | Deterministic projection from stated assumptions. The 4.0% execution failure rate is an assumption, not a merchant measurement. Not a guarantee or a merchant result |
| Pipeline benchmark | about 95,000 to 122,000 transcript audits/sec, p50 about 0.009 ms | `bench/fleet_benchmark.py`, local runs on 2026-11-04 | 1,000 canned transcripts and a mock ledger, no model or network calls. Not model throughput and not an end-to-end merchant SLA |
| Automated checks | 235 backend, 93 frontend | CI | Counted at the commit named in the run |

## Borrowed numbers, with qualifiers

| Claim | Value | Source | Qualifier that must appear with it |
|---|---|---|---|
| Chargeback administrative cost | about $128 per incident before goods | Mastercard 2025 chargeback research, via `docs/research/15-impact-report.md` | Fees plus internal labor. Excludes the lost order |
| Total cost per dollar of loss | $4.61 | LexisNexis True Cost of Fraud, 2025, N=569 | Fraud and dispute loss across retail and e-commerce, including goods and labor. Not specific to unissued refunds |
| Klarna auto-chargeback window | 96 hours after agreeing an adjustment | Klarna merchant dispute rules, via `docs/research/15-impact-report.md` | Applies to agreed order adjustments on return-not-refunded inquiries |
| Visa 13.6 win-rate uplift | about 25% to 45% with policy plus refund-attempt evidence | Travel and hospitality benchmarks, via `docs/research/15-impact-report.md` | Travel and hospitality vertical. Not general retail |

## Claims we will not make

- Prevent every agent error. We verify after execution.
- Work with every ledger. Stripe and Shopify are the rails today.
- SOC 2 certified. It is a roadmap item.
- Real merchant savings. Every proof above uses synthetic fixtures or test-mode data.
- A real merchant shadow audit. The 12-case result is a labeled proxy, not a merchant transcript export.
- Guaranteed enterprise savings from the modeled Tier 3 table. It is a projection from stated assumptions, not a merchant result.
- 133,000 audits/sec or 0.007 ms as model or end-to-end throughput. Those figures did not reproduce; the pipeline benchmark is about 95,000 to 122,000 audits/sec at p50 about 0.009 ms, with no model calls.
- A production certificate authority or hosted key transparency log. The registry is a local JSON file with CLI rotation.
- Fully automate production remediation. Auto-remediate runs against the mock ledger only.
- Replace guardrails. We sit after execution, not before the send.
- Saves 10x or more versus a frontier model. The measured gap is about 3.5x against the Opus tier, 1.8x against Sonnet, and we lose to small cheap models. The wedge is failing closed on money, not being the cheapest.

## Two numbers we retired

- The $4.61 figure was earlier written as "$5.00 and rising" from a second edition. The edition we can cite says $4.61.
- An earlier version said "100% deterministic ledger state". Reconciliation is deterministic code. Extraction is model output that is validated and fails loudly. The page now separates the two.
