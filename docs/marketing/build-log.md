# Settleye Build Log: a Hackathon Series in Real Time

Running record of every decision, pivot, and proof behind Settleye, from blank repo to submission. Written for builders. Each entry stands alone as one post.

## Day 1 morning: the problem picks us

- AI support agents promise refunds in words while the tool call silently fails. Nobody checks. That is the whole company in one sentence.
- Stack choice took one session: Python plus FastAPI plus uv plus pytest, Vite plus React plus TS, Modal later. Familiar tools ship faster than perfect tools.
- Model choice is event-instructed (`meta-models/muse-spark-open-1026` via Baseten), switchable through one env var. Zero code changes to swap models.
- Rule zero: evidence over hope. Every claim ends in a test result or a runtime log. "Seems right" never ships.

## Day 1 morning: research before code

- Ran parallel research tracks first: market, competitors, feasibility, hackathon strategy, infra cost ($0 verdict with guardrails), moat, pivot scouting. Three alternative briefs all said stay.
- Competitor scan found the adjacent validator (Collar, YC F26, Singaporean founders, warm intro). Adjacent, not overlapping. Different buyer, different ledger.
- Fine-tune verdict via Gemini: no fine-tuning before ~1.5M tickets a month. Prompt plus cache plus verify wins until Series-A scale.

## Day 1 midday: the rename (nearly free today, expensive forever)

- Our name PromiseCheck collided exactly with a $79.99/mo Shopify App Store listing. Same name, same marketplace, adjacent buyer.
- Shopify rule 4.1.2 bars identical or similar names. Keeping it meant permanent exile from our own distribution channel.
- Two subagents confirmed it in parallel: rename, drop the Promise root entirely. Picked Settleye (verified free .com). One commit, repo renamed, CI caught a dirname-coupled test the same hour. That is what CI is for.

## Day 1 midday: live proof or it did not happen

- Baseten key in, one perfect refund entity out in 4.18 seconds (conf 0.98, exact evidence quote). The suffixed model ID is empirically confirmed. The 403 on the other ID is closed.
- That run caught a real bug: the model returns `#992`, the ledger keys `992`. One-spot normalization plus a test. Live runs find what unit tests cannot imagine.
- Shopify auth proven against the dev store. Live introspection corrected our refunds query shape (plain list with totals, not a connection). The provisional mutation stayed provisional until exercised.

## Day 1 afternoon: the $50 order that proved the loop

- Built a draft order, converted it, collected payment. Order #1001: $50.00, PAID.
- Reads blocked instantly on protected customer data (empty stores return nothing, real orders enforce). Fixed in app settings with a one-line justification. New token not even needed.
- `refundCreate` shape corrected against the live schema: order GID plus SALE-parented transaction plus gateway, directive on the field. $5 test plus $1 through the fixed adapter settled to $6.00. Idempotent replay correctly rejected.

## Day 1 afternoon: the daemon (auditors run themselves)

- The API serves humans. The daemon is the autonomous half: batch sweep, per-item failure isolation, money-sorted report. Default pass is audit-only. Auto-remediate refuses live ledgers (verified exit 2).
- Modal-ready with zero Modal imports: one wrapper function when credits land.
- Live sweep vs #1001: $44.00 drift in 4.07 seconds, exit 0.

## Day 1 evening: numbers behind the frontier claim

- 12-case eval set: phantoms, settled, retracted, conditional, info-only, superseded, no-order, cancel, multi, decimal. Live accuracy 12 of 12 verdicts, 11 of 12 exact entities. Zero non-binding drifts in four chances.
- The miss is documented, not hidden: t07 returned `[]` instead of an info_only entity. Same green outcome, stricter behavior.

## Day 1 evening: the model gets two more jobs

- Per-drift explanations on demand (drifts only, capped, fact-bound). Live #1001 output is camera-ready.
- Repeat-offender memory across tickets, zero model calls. Two-ticket sweep flagged #1001 at $88 at risk.
- Inbox gained a "Why does this matter?" button. No gratuitous calls: clean transcripts still cost one call each.

## Day 1 night: docs become true

- README rewritten (it still claimed 36 tests and retired verdict names). Landing proof bar switched from targets to measured numbers. Demo script gained eval plus explain beats.
- Caught a wrong number mid-edit: $45 x 52 is $2,340 a year, not $2,600. Judges catch these. We caught it first.
- All 10 living docs pass the STE linter. Numbered research stays frozen as dated history.
- Wrote the Gemini impact prompt (leakage rates, buyer pool, ad angles). Distribution is the game now.

## Day 1 night: scope first, then the page

- Three parallel tracks (type, color, structure) produced the landing design doc before any code. Inter plus Plex Mono. Dark-first tokens. Nine sections, five hard exclusions.
- Defended dark against the white-page objection: Global Citizens sells institutional trust to families. We sell night-shift infrastructure to ops leads. Color never conveys frontier. Evidence does.
- Buyer blueprints filed: pop shops buy found money on first install or nothing. Enterprise buys shadow pilots plus trust packets. Wedge ladder runs free audit to usage ramp to custom.

## Standing rules of this build

- Test first, verify with the real runtime, sign every commit, keep CI green.
- One logical change per commit. No drive-by refactoring.
- Rename early, freeze features early, frame impact always.
- The pitch carries most of the score. Code earns the right to be pitched.
