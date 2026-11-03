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

## Open System One model, zero-shot (Laya, Apache 2.0)

Measured 2026-11-03 with `convaiinnovations/laya` (ModernBERT-large, 421M), CPU, no fine-tuning. Same questions our gate asks Jev: is there a financial promise, and what is its end state.

### Promise presence on our 12 curated cases

11 of 12. The miss is the clean status-check case, which scored 0.62 for "yes" and would have been kept rather than skipped.

### Commitment modality on the 11 promise cases

8 of 11. The three misses all collapse to `binding`: a retracted promise, an info-only policy explanation, and a superseded amount were each labelled binding. That is the dangerous direction for an auditor, because it would raise drift on things the agent never actually owed.

### Cost gate on 300 wild transcripts

Kept 294 of 300. A 2.0 percent discard rate, at about 150 ms per request on CPU. As a cost filter this is close to useless out of the box: it says "possible promise" to nearly everything.

### Calibration

The runtime warns on load that this checkpoint ships invalid temperatures. It tells you to treat the affected confidence values as uncalibrated. The model card says the same. The base checkpoints are near chance zero-shot, and they need per-question-type temperature fitting before the probabilities mean anything.

### What this supports

Laya is a promising base to fine-tune, not a drop-in gate. Its own card says as much. The measured failure is useful for three reasons:

1. It shows why a calibrated decision model needs fitting on domain data first. That is the fine-tune path in the impact research.
2. It rules out the cheap shortcut. An open checkpoint does not remove the need for a hosted calibrated model or a fine-tuning step.
3. It gives the write-up an honest negative result next to the positive ones. Two of three models were measured against our task and neither is a free lunch.

Weights: https://huggingface.co/convaiinnovations/laya. Reproduce with the two scripts recorded in this folder.

## Free open decision models, zero-shot (measured 2026-11-03)

The question this answers: can a free local checkpoint replace a paid calibrated model for the gate. Three were tested on the same 12 cases with the same two questions.

| Model | License | Presence agreement | Modality agreement | Wild discard | Notes |
|---|---|---|---|---|---|
| Laya (ModernBERT-large, 421M) | Apache 2.0 | 11 of 12 | 8 of 11 | 2 percent of 300 | Runtime warns shipped temperatures are invalid |
| d1-omni-600M, noul phrasing | LFM1.0 | 8 of 12 | 7 of 11 | not run | Near-zero probability on a transcript that states a refund twice |
| d1-omni-600M, described choice | LFM1.0 | 9 of 12 | 6 of 11 | not run | Presence improves, modality degrades |

Neither configuration reaches the hosted model's 11 of 12 and 8 of 11, and neither would save meaningful money at the gate. Laya keeps 98 percent of wild transcripts, so the cost saving it promises does not arrive.

### The honest answer on free

There is no free zero-shot option that works on this task. Every open checkpoint tested is near chance on our domain, which both model cards predicted. Free in practice means downloading weights and fine-tuning on labeled promise data, which is the path already costed in the impact research.

That leaves three honest positions, and we should pick one rather than blur them:

1. Ship the gate against a hosted calibrated model, and say it needs an account.
2. Ship no gate and present the measurements as the finding.
3. Fine-tune an open checkpoint, which does not fit in the remaining time.

Recorded scripts: `bench/laya/` for Laya. The d1 runs are reproducible from the model card's own example with the two question phrasings above.

Follow-up: the fine-tune path was tested in `22-free-gate-finetune.md` on 2026-11-03.
