# Post-mortem: why Settleye did not place

## Summary

Settleye did not place in the Meta Global AI Developer Hackathon. The field had 5,367 entries and 15 prizes.

The build was sound. The evidence was not. This document records the gap, the warnings that existed before submission, and the experiment that would have closed it.

## What we submitted

Settleye is an execution auditor for AI support agents. It extracts promised actions from a transcript. It reconciles each promise against a Stripe or Shopify ledger. It returns a signed receipt when it fixes a shortfall.

The repository had 235 backend tests and 93 frontend tests. It had idempotent writes, concurrency guards, and key rotation. It had a 180-second film and a live landing page.

## The result

We did not place in the Indie Developer track. We did not win a bonus prize.

The loss was predictable. The remaining sections explain why.

## The evidence gap

Every winning entry we examined compared its result against a reference outside the product's own claims. We compared Settleye against a mock ledger that we wrote.

| Gate field | Winning entries | Settleye |
|---|---|---|
| Ground truth | External labels, sensors, or specifications | Mock ledger written by us |
| Baseline | Naive model or static rules on the same rows | None |
| Holdout | Locked split, reported separately | None |
| Threshold | Written before the run | Chosen after the result |

The 12-case evaluation scored 12 of 12. That number proved the pipeline ran. It did not prove that the problem was real. A reader had no independent reason to trust the labels.

A 300-row public dataset produced no binding promises. That run showed precision on non-promises. It did not measure recall on real promises.

## Doubts before submission

We knew the evidence was weak before the deadline. The record shows it.

- The claim ledger listed the mock ledger as a scope limit.
- The impact report labeled the savings as modeled, not measured.
- The submission notes described the fixtures as synthetic.
- The first commit was two hours before kickoff. The submission text claimed a strict window.

Each note was honest in isolation. Together they described a project with no external proof.

## Theme fit

The project entered Push the Frontier. The guide lists software as in scope. The strongest entries in that track were robots, spacecraft, and scientific instruments.

Settleye was an audit layer for support operations. It fit Build for Your World more closely. We chose the theme after the build, not before it.

## The missed experiment

One experiment would have changed the submission. We did not run it.

The experiment: ask Muse Spark to read the same 12 transcripts and decide whether each refund settled. Compare its answers with the ledger.

The model would read the agent's own claim. In most cases it would agree with the claim. The ledger would disagree. That table is the thesis, measured, with the naive alternative failing beside it.

The experiment needs no merchant. It needs no partner. It needs the fixtures we already had, plus one afternoon.

## Effort and time

The event ran from Oct 26 to Nov 4. Most of that period was a work week. Personal work limited the hours available for the build.

The last 24 hours produced most of the visible work: the film, the landing layout, and the submission text. The first eight days produced infrastructure that judges never saw.

This was a scoping error, not a speed error. We built the system before the proof.

## Model choice

The build used DeepSeek models for the agent work. It did not use a frontier model for the final review.

Model choice was a constraint, not the cause. A frontier model would have improved the prose and the review. It would not have produced the missing labels.

The lesson is about the system, not the model. A strong harness lets a frontier model drop in when one is available. The harness must still demand evidence.

## What we would change

1. Run the baseline in the first two hours. Do not wait for the product.
2. Write the threshold before the first run. Record the miss.
3. Lock a holdout and never tune on it.
4. Label the sample size and state what one miss would move.
5. Name the prior-work boundary in the first commit message.

## What carries forward

The repository, the film, and the test suite remain. The evidence gate now exists as a reusable skill. The next project starts with the gate, not with the build.

The loss was fair. The warning was visible. The fix was cheap.
