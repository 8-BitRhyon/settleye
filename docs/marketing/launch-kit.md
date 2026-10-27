# Launch Kit: Copy-Paste Announcements

## X launch post (post at submission, engagement counts to Nov 8)

> AI support agents promise refunds they never issue. We built the auditor that catches them.
>
> Settleye reads transcripts, reconciles every promise against Stripe/Shopify, and fixes drift in one click. Built on @Meta Muse Spark Open for the Meta Global AI Developer Hackathon.
>
> Demo + repo below. Judges and merchants welcome. [video link] [repo link]

Follow-up reply (same thread, next day): post the top drift figure from testing. Use "12/12 eval verdicts correct, and 0 non-binding commitments ever reached drift". Numbers travel.

## Angle bank (all sourced in `docs/research/15-impact-report.md`)

Use on camera or on X. Every angle carries its qualifier. Never state a number without its scope.

1. ROI hook: "Every $1 of dispute or fraud loss costs US merchants $4.61 to over $5.00. A single chargeback burns $128 before you count the goods." Scope: $4.61 covers goods, fees, and labor across fraud and disputes. $128 is per-incident overhead before goods.
2. Urgency hook: "Miss a promised Klarna refund writeback by 96 hours and Klarna triggers an automatic chargeback." Scope: applies to agreed Klarna order adjustments.
3. Defense hook: "Merchants recover just 10.7% of chargeback dollars net. On Visa Credit Not Processed, win rates jump from ~25% to 45% with locked policy and refund-attempt records." Scope: 10.7% is net across all issued chargebacks. The uplift is travel and hospitality benchmarks.
4. Ops hook: "77% of e-commerce support tickets fail first contact. 69% of billing inquiries need escalation." Scope: async tickets, not live chat.
5. Founder hook: "72% of 7- and 8-figure merchants adopted AI, yet revenue growth trails non-adopters 26.7% to 27.8%." Scope: observational survey, not a controlled experiment.

## Demo video description (YouTube, unlisted)

Settleye: execution auditor for AI support agents. Transcript in, ledger truth out. Built Oct 26 - Nov 4, 2026 for the Meta Global AI Developer Hackathon (Indie track, Push the Frontier). Core intelligence: meta-models/muse-spark-open-1026 via Baseten. Repo: [link]. Setup under 5 minutes. All data synthetic, test ledgers only.

Chapters: 0:00 the $45 phantom refund. 0:45 live extraction. 1:30 the fix. 2:15 the math. 2:45 vision.

## Submission blurb (hackathon platform, short)

Settleye verifies AI support agents keep their money promises. It extracts binding commitments from transcripts with a Meta model. It reconciles each against live Stripe and Shopify state. It surfaces mismatches in a money-sorted exception inbox with one-click idempotent remediation. Push the Frontier means deterministic verification for non-deterministic agents.

## Design-partner outreach (DM or email, copy and customize)

> Subject: found leaking refunds in AI support chats, built the fix
>
> Hi [name], we build Settleye: it audits AI support transcripts against Stripe/Shopify and flags promised-but-unsettled refunds with a one-click fix.
>
> Ask: a 14-day read-only shadow audit over your last 90 days of tickets. Zero write permissions, five-minute setup, you keep the leakage ledger either way. Interested in seeing what your agents promised last quarter?

## Follow-up (one week, no reply)

> Bumping this once: happy to run the shadow audit on a 50-ticket sample instead of 90 days if access is the blocker. Same report, smaller scope.
