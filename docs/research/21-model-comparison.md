# Model comparison: open-weight versus frontier on promise extraction

Measured 2026-11-02. Same 12 cases, same prompt, same scoring.

## Arms

- **Muse Spark Open** (`meta-models/muse-spark-open-1026`, Baseten), running the production pipeline.
- **Gemini 4 Argon**, running the identical production prompt inside OpenCode Go agent scaffolding.

Both arms are scored against `fixtures/eval_expected.json` with one shared normalizer (order ids lose a leading `#`).

## Result

| Arm | Exact entity matches | Hallucinated order ids | False clears |
|---|---|---|---|
| Muse Spark Open | 11 of 12 | 0 | 0 |
| Gemini 4 Argon | 11 of 12 | 1 | 0 |

Both arms scored the same. The difference is which case each one failed.

- Muse failed **t07** (a policy explanation) by returning an empty list where the manifest holds an info-only entity. The outcome is green either way: no drift reported, no money claimed.
- Argon failed **t09** (a refund with no order number) by inventing `order_id: "EVAL09"`. That string exists nowhere in the transcript. It is a fabricated identifier.

## Why the failure mode matters more than the score

Both arms got eleven of twelve. Only one of them failed in a direction that costs money.

A fabricated order id is dangerous in a reconciliation product. If the invented value happens to match a real order in the ledger, the join reports a verdict about the wrong order. The merchant sees a confident answer attached to the wrong customer. Our pipeline treats a missing order as unverifiable and stops. It never invents one.

Under-reporting is the failure we chose. On a 12-case set that is the difference between eleven-twelfths and eleven-twelfths.

## Limits, stated plainly

- Twelve cases. This is a signal, not a benchmark.
- One run per case. No repeated sampling, so variance is unmeasured.
- The Argon arm ran inside agent scaffolding with its own system prompt and tools. That is not a bare API baseline. Do not read it as "Argon is worse than Muse" in general.
- The eval set is our own writing, so both arms face the same author bias.
- The hallucination is one instance. It is not a rate.

## What this supports

One claim follows. On our task a frontier model did not beat an open-weight model. Its single error would have produced a wrong answer about money. The other arm's error produced no answer. That supports the harness and the open model. It does not prove either.

## Reproduce

```bash
python3 bench/score.py
```

Inputs: `fixtures/eval_expected.json`, `fixtures/eval_live_output.json`, `bench/argon_output.json`.
