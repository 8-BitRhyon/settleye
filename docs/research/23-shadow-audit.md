# Shadow audit: 12-case proxy and the real-merchant blocker

A shadow audit measures what Settleye would have caught on a merchant's own
tickets, without moving money. It audits a transcript export, joins each
binding promise to ledger state, and reports drift dollars and false clears.

## Method

Harness: `backend/app/shadow.py`.

Command:

```bash
cd backend
uv run python -m app.shadow \
  --dir ../fixtures/eval \
  --ledger mock \
  --labels ../fixtures/eval_expected.json \
  --replay ../fixtures/eval_live_output.json \
  --out .tmp/shadow_eval.json
```

Metrics:

- `tickets`: transcripts attempted, including failures.
- `drifts`: reconciliation results with verdict `drift`.
- `total_at_risk_usd`: sum of drift shortfalls.
- `drift_dollars_per_1000_tickets`: `total_at_risk_usd / tickets * 1000`.
- `binding_cases`: labeled cases with at least one `binding` promise.
- `false_clears`: binding cases where extraction found no `binding` promise.
- `false_clear_rate`: `false_clears / binding_cases`.

A case that errors is still a ticket and is still scored as a false clear when
its label says it contained a binding promise. An error never stops the sweep.

## Result

Source: the 12-case eval set, recorded live model output replayed into the
deterministic reconciliation path. Ledger: `fixtures/mock_ledger.json`.

| Metric | Value |
| --- | --- |
| Tickets attempted | 12 |
| Tickets audited | 12 |
| Errors | 0 |
| Drifts | 5 |
| Dollars at risk | $285.50 |
| Drift dollars per 1,000 tickets | $23,791.67 |
| Labeled binding cases | 8 |
| False clears | 0 |
| False-clear rate | 0.0% |
| Model | `meta-models/muse-spark-open-1026` |

Per case:

| Case | Verdict | Drifts | At risk | Binding found / expected | False clear |
| --- | --- | ---: | ---: | --- | --- |
| `t01_phantom_992` | drift | 1 | $45.00 | 1 / 1 | no |
| `t02_phantom_1042` | drift | 1 | $120.00 | 1 / 1 | no |
| `t03_clean` | green | 0 | $0.00 | 0 / 0 | no |
| `t04_settled` | green | 0 | $0.00 | 1 / 1 | no |
| `t05_retracted` | green | 0 | $0.00 | 0 / 0 | no |
| `t06_conditional` | green | 0 | $0.00 | 0 / 0 | no |
| `t07_info_only` | green | 0 | $0.00 | 0 / 0 | no |
| `t08_superseded` | drift | 1 | $30.00 | 1 / 1 | no |
| `t09_no_order` | green | 0 | $0.00 | 1 / 1 | no |
| `t10_cancel` | green | 0 | $0.00 | 1 / 1 | no |
| `t11_multi` | drift | 1 | $45.00 | 1 / 1 | no |
| `t12_decimal` | drift | 1 | $45.50 | 1 / 1 | no |

## What this proves

- The metric path works end to end: transcript files, extraction output,
  commitment gate, ledger join, drift sum, and label scoring.
- On this small labeled set, the gate did not suppress a binding promise:
  zero false clears across 8 binding cases.
- The five drift cases produce a deterministic dollar total that a merchant
  can compare across runs.

## What this does not prove

- It is not a real merchant shadow audit. The transcripts are synthetic eval
  cases, not a merchant export.
- The ledger is a mock fixture, not the merchant's live Stripe or Shopify
  state.
- The model output is a replay of recorded live output, not a fresh model call.
  A replay tests the join and metrics, not present-day model accuracy.
- Twelve cases are too few to claim a stable per-1,000 rate. The dollar figure
  is a demonstration of the metric, not a forecast.
- A false clear here means no binding promise was extracted. It does not score
  wrong entity fields, wrong amounts, or wrong terminal status.

## Real merchant pilot: exact blocker

No real merchant transcript export and no read-only ledger credentials are
present in this environment. There is no merchant transcript directory in the
repository, and no Stripe or Shopify read credential is configured. Running a
real shadow audit requires two things from the merchant:

1. A transcript export, one JSON file per conversation, with a `turns` array of
   `{role, text}` objects. The same shape as `fixtures/eval/*.json`.
2. A read-only ledger source. Two are supported today:
   - A Shopify Admin API token with `read_orders` scope.
   - An exported ledger snapshot in the shape of `fixtures/mock_ledger.json`
     for `--ledger mock`.

The Stripe adapter is test-mode only: it refuses any key that does not start
with `sk_test_`. A real Stripe merchant pilot needs a read-only Stripe adapter
that accepts restricted live keys, which is not built.

Optional: a human-reviewed labels file in the shape of
`fixtures/eval_expected.json`, one entry per transcript. Without labels, the
harness still reports tickets, drifts, and dollars at risk, but
`false_clear_rate` is `null`.

Command for a Shopify pilot:

```bash
cd backend
export BASETEN_API_KEY=...
export SHOPIFY_STORE_DOMAIN=...
export SHOPIFY_ADMIN_TOKEN=...
uv run python -m app.shadow \
  --dir /path/to/merchant/transcripts \
  --ledger shopify \
  --labels /path/to/merchant/labels.json \
  --out .tmp/merchant_shadow.json
```

Command for a mock or already-exported ledger snapshot:

```bash
cd backend
uv run python -m app.shadow \
  --dir /path/to/merchant/transcripts \
  --ledger mock \
  --labels /path/to/merchant/labels.json
```

The audit is read-only. No remediation runs in the shadow path.

## Decision needed

Provide the transcript export and a read-only ledger credential, or authorize a
pilot against a named dev store. Until then, the only honest measurement is the
12-case proxy above.
