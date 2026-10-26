# Pivot Scouting: Stay vs Switch

Researched 2026-10-26. Three alternative territories developed head-to-head against PromiseCheck by independent scouts. All three recommend staying.

## Candidates and scorecards (1-10, Alternative vs PromiseCheck)

### ToolTrap: prompt-injection and tool-abuse firewall

| Criterion | ToolTrap | PromiseCheck |
|---|---|---|
| Impact | 6 | 8 |
| Use of Meta AI | 8 | 7 |
| Technical Depth | 6 | 8 |
| Demo Quality | 5 | 8 |

Security is real but abstract; blocking demos as absence. Crowded archetype with a first-party Meta incumbent (Llama Prompt Guard 2, SecAlign) plus AgentDojo/CaMeL benchmarks. Feasibility killers: needs a 30-plus-case adversarial suite (a second project), live interception is harder than post-hoc audit, false-positive tuning has no time. Reuse ~55%; the ledger integration (the most differentiated code) is thrown away. Verdict: do not switch. Only candidate where Meta tooling is the hero. Consider as a stretch flag-rule inside PromiseCheck later.

### ProofShot: visual warranty-claim adjudicator

| Criterion | ProofShot | PromiseCheck |
|---|---|---|
| Impact | 7 | 8 |
| Use of Meta AI | 9 | 6 |
| Technical Depth | 7 | 7 |
| Demo Quality | 9 | 6 |

Best demo ceiling (fraud call-out on the pixels in 10 seconds) and the only candidate that genuinely uses the model's vision input. But Loop Intelligence and Redo already ship "AI reviews images, recommends approve/deny" as checkbox features, with PixelProof and Appriss on point solutions. Feasibility killers: 15-20 labeled photo fixtures (2 days alone), vision variance on camera reads as rigged when cached, per-merchant policy engine must be invented. Reuse ~50-60%. Verdict: do not switch. Steal one vision-cited evidence card inside PromiseCheck if photos are wanted without the pivot.

### CancelGuard: subscription-cancellation verifier

| Criterion | CancelGuard | PromiseCheck |
|---|---|---|
| Impact | 6 | 8 |
| Use of Meta AI | 7 | 8 |
| Technical Depth | 6 | 8 |
| Demo Quality | 9 | 7 |

Best 10 seconds of any candidate (promised-cancelled vs billed-anyway, $19.99 zombie charge). Narrower is better for demo, worse everywhere else; risks reading as PromiseCheck with a filter. Caveat: the FTC click-to-cancel rule was vacated by the 8th Circuit in July 2025, so the honest pitch is "the rule died, the problem didn't." Reuse ~75%; roughly 1 day to fork. Verdict: do not switch. Steal the cancellation scenario as the lead 60 seconds of the PromiseCheck demo, then show one refund case to prove generality.

## Decision

Stay with PromiseCheck. No candidate beats it on balance; each wins at most one axis while losing the war on feasibility, crowdedness, or scope. Incorporate the steals: cancellation-first demo ordering, one vision evidence card as stretch, injection flag-rules as stretch.
