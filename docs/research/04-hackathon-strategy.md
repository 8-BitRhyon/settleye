# Hackathon Win Strategy

Researched 2026-10-26, corrected 2026-10-27 against the official participant guide.

## Authoritative weights (guide, not the FAQ)

Impact 30%, Meta AI Tooling 25%, Demo 25%, Technical Depth 20%. Impact is the biggest lever: lead every pitch with dollars and liability.

## Problem statement

Push the Frontier: an execution-verification layer for the agent economy is a new machine capability, not a personal workflow fix.

## Bonus targets

- Best Agentic Use-Case ($5k): frame the detect-decide-remediate-audit loop as an autonomous agent; keep bounded retries and idempotent writes as the autonomy evidence.
- Best Build on Meta Open Weight Models ($10k): Baseten path plus model string in logs, README, and captions keeps us eligible; flagged in round one automatically.
- Most Viral ($20k): post the demo on X at submission; engagement counts through Nov 8 EOD.
- Community Vote ($10k): gallery opens Nov 9, one vote per verified account, winner Nov 16.

## Calendar

- Oct 27 noon ET: Agents 101. Oct 28 noon ET: Agents 102 (verifiable agents, directly relevant). Oct 30 noon ET: Fireworks inference/training.
- Office hours weekdays 10-11am ET (no weekends) for card/credit issues.
- Nov 3: last day for submission questions. Nov 4 9pm ET: hard submission stop. Submit by noon.
- Nov 5-8 judging; Nov 9 noon closing ceremony plus live finals (top 5 per track).

## Submission checklist (from the kickoff stream)

- [ ] Repository public and reviewable (disqualifier trap: closed-source repos get tossed). Verified public 2026-10-27.
- [ ] Open the submission form early and read every field; do not meet it for the first time on Nov 4.
- [ ] Video link works in an incognito window; repo link works logged-out.
- [ ] Every contributor listed; one representative submits.
- [ ] Submit by noon ET Nov 4, never the last hour.
- [ ] Demo opens with the pre-existing-vs-built line.
- [ ] Post demo on X at submission for Most Viral (engagement to Nov 8 EOD).

## What past Meta winners did

One painful workflow, live data in, visible action out, in under 90 seconds. LlamaCon 2025: OrgLens (knowledge graph over Jira/GitHub), Compliance Wizards (risk scorer plus alerts), Llama CCTV (plain-language vision detection). Llama India 2024: CurePharma (WhatsApp prescription scan), CivicFix (photo pothole routing). Judges: lead with frustration, one flow end to end, pre-filled forms, mocked slow calls, honest about what works. Sources: https://ai.meta.com/blog/llamacon-hackathon/, https://ai.meta.com/blog/llama-hackathon-india, https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/

Takeaway: frame as CivicFix for support ops. Broken promise, caught, fixed, ledger proof. No architecture tour.

## Per-criterion checklist (3-minute video)

- Impact: open with real cost, show a dollar number prevented, one persona (support lead triaging the inbox).
- Meta tooling: the model does extraction plus verdict (not regex); show prompt plus structured JSON on screen; call via a sanctioned path; name the model verbally, in README, in captions.
- Technical depth: live diff transcript-vs-ledger side by side; show a failure mode with confidence plus evidence span; one-click fix writes back plus audit entry. Real API calls, real commit history.
- Demo quality: working in 90 seconds, pre-seeded data, voiceover plus captions plus timestamps, end card with GitHub and sub-5-minute setup.

## Pitfalls

1. Meta model is decorative. Fix: it is the only path from transcript to promise JSON; log the model ID on camera.
2. Slideware or hardcoded demo. Fix: raw transcript to raw model JSON to diff code, no cuts; include one imperfect extraction.
3. Wrong track fit. Enter Indie; stress solo-dev leverage.
4. Scope sprawl and dead air. Cut auth, multi-tenant, fancy UI. Pre-fill everything. Record a backup run.
5. Rules miss: Nov 4 9pm ET hard stop, submit 24h early, original code, synthetic test data.

## Priority sketch (Oct 27 - Nov 4)

Non-negotiable for video: seeded transcripts, model extraction, ledger diff, inbox UI, one-click fix plus audit log, 3-minute script. Oct 27: freeze scope, wire model, log one transcript to JSON. Oct 28: ledgers plus diff. Oct 29: inbox plus fix plus audit. Oct 30: three scripted cases, dry run. Oct 31: harden, timeouts, offline backup video. Nov 1: README, arch diagram, model-call evidence. Nov 2: shoot final video. Nov 3: fresh-eyes test, submit draft. Nov 4: submit by noon ET, no new features. Cut: real OAuth, prod deploy, multi-user, eval dashboard, second model.
