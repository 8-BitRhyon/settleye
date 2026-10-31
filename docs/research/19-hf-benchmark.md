# Wild-Transcript Benchmark: Bitext 300 (Oct 31, 2026)

Dataset: bitext/Bitext-customer-support-llm-chatbot-training-dataset (26,872 rows, Hub parquet). Sample: 300 rows, seed 7. Mix: 150 refund intents, 75 cancel_order, 75 payment and order mix. Model: meta-models/muse-spark-open-1026 via Baseten, 8-way concurrency, 228.8 seconds, about $1.20.

## Result

- Completed: 300 of 300. Crashes: 0. Pipeline failures: 0.
- Rows with entities: 1 of 300 (one non-binding entity in change_order).
- Binding promises extracted: 0.

## Reading

These inputs are templated canned replies ("I am here to provide information"), not real transcripts. Most promise nothing, so near-zero extraction is the correct outcome, not a miss. The run measures two things. First, false-positive resistance on non-promises (299 of 300 clean, zero false binding drifts). Second, robustness outside curated fixtures (zero crashes across 300 live calls).

## What this proves and what it does not

Proves: the pipeline holds on wild text. No crashes, no repair-loop escapes, no false money promises across 300 money-adjacent rows. Combined with the 12-case eval (recall on true promises) and the live ledger proof (join correctness), the three legs cover precision, recall, and settlement.

Does not prove: recall on real transcripts (no labels exist for our schema here), usefulness to merchants, or moat. The owned shadow-audit dataset remains the moat play.

Reproduce: parquet URL via the Hub datasets-server, same seed and intent mix, runner pattern in backend/app/eval practice (kept out of the product surface deliberately).
