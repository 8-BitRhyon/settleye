# Alpha Loop

- Decision: Base thesis A, the 20-second execution proof, with two grafts: "Resolved is not Settled" and the idempotent receipt ending.
- Owner: Settleye
- Date: 2026-11-03
- Time budget: internal freeze 2026-11-03 18:00; official deadline 2026-11-04 21:00 ET
- Win metric: 5 of 5 fresh viewers can state the promise-versus-settlement gap and the $44 number within 20 seconds; the public sample inbox renders a drift and a repeat-safe remediation on desktop and mobile with no API key.

## Frame

- Goal: make Settleye the project a hackathon judge remembers as a new machine capability, not another support chatbot, and give it a durable product wedge after the event.
- Decision it forces: which single surface to fix before the deadline, and what to cut.
- User: hackathon judge first; proxy buyer is a support ops lead at a merchant running 5,000 to 50,000 tickets a month with an AI agent handling refunds.
- Job: see that the agent's promise did not settle, and that Settleye can fix it exactly once.
- Current workaround: trust the transcript, sample QA, chargebacks after the customer waits.
- Constraints: no real merchant transcripts, synthetic fixtures, $10 model spend, Lighthouse 85, accessibility 100, one writer per file.
- Non-goals: production deployment, SOC 2, full auto-remediation on live money, model-scale benchmark, cost-per-token race.

## Facet Findings

| Lens | Finding | Evidence | Implication | Bet |
|---|---|---|---|---|
| User | The buyer needs a dollar number they can defend at month-end and in a chargeback rebuttal. No real merchant denominator exists yet. | `docs/research/20-claims.md:34`; `README.md:23` | Accuracy is already table stakes; a buyer-shaped receipt with own transcripts matters more. | Add a paste-your-own-transcript path and test it with 3 non-team users. |
| Market | Nobody joins what the agent promised to what the ledger settled. Agent vendors charge per resolution; recovery vendors take 25% after the dispute. | Gorgias $0.90/interaction; Intercom Fin $0.99/outcome; Chargeflow 25% of recovered chargebacks | Own the gap between "resolved" and "settled", before the dispute. | Rewrite the hero around the Chargeflow arbitrage and the $44 proof. |
| Technical | The audit loop is stateless. Idempotency lives in memory, the key is derived from the residual shortfall, and the daemon only sees one batch. | `backend/app/remediate/service.py:18-33`; `backend/app/daemon.py:44-76`; no persistence layer in the repo | Extraction is commodity; a replay-provable promise ledger is the defensible state. | Append-only `sweeps.jsonl` keyed by transcript digest, order, action, and original amount; double-run the daemon. |
| Design | The public sample inbox renders a real drift, but the landing page buries it. The sample fix button calls the local API and fails. | `frontend/landing.html:373`; `frontend/src/App.tsx:44-50,102-135`; live browser check on `./index.html?sample=1` | The 60-second path dies at the exact moment the product should prove the moat. | Promote the sample inbox to the primary CTA and simulate the receipt locally in sample mode. |
| Distribution | The only reachable audience before the event is the event's own surface. Merchant channels are closed or slow. | Event community-vote and viral bonus; r/shopify promotion ban; Gorgias app review is two weeks | Distribution is scored today, not a post-launch concern. | Ship a shareable receipt card and seed the event community. |
| Risk | The public app needs a local API, `/audit` returns 503 without a key, and all proof is synthetic or test-mode. | `frontend/src/api.ts:4`; `backend/app/main.py:56-60`; `docs/research/20-claims.md:34-35` | Demo fragility is the likeliest loss, not legal or claims. | Record an unedited 60-second live run and embed it above the sample button. |
| Alpha | The refusal path is the moat: server-side re-reconcile, clamp to the live shortfall, same receipt on retry, cross-rail idempotency. | `backend/app/main.py:115-133`; `backend/app/remediate/service.py:18-33`; `backend/app/ledger/shopify.py:144-167` | A competitor can copy extraction in days; the refusal path takes ledger adapters and adversarial tests. | Show repeat remediation returning the same receipt and $0 additional movement on screen. |

Additional findings:

- Rules: official judging is creativity, technical ambition, and whether it works. The official deadline is Nov 4, 9:00 PM ET, not the internal Nov 3 freeze. The frontier claim should be "a machine trusted to move money", not "refunds save hours." Source: https://dev.meta.ai/events/global-hackathon and https://cerebralvalley.ai/e/meta-ai-developer-hackathon
- Critic: the public root does not run the product, the default model ID contradicts the code's own comment, the proof is synthetic, the cost story is a negative result, and the 60-second path dead-ends at a GitHub issue. These are fixable, but they must be fixed on the demo surface, not in a README.
- Marketer: the enemy is "the chat transcript accepted as settlement proof." The proof order is the live Shopify drift, the 12-case eval, the frontier comparison, and the test counts. The negative free-gate result is rigor, not the headline.

## Theses

| ID | Who | Job | Mechanism | Alpha | Risk |
|---|---|---|---|---|---|
| A | Hackathon judge | See the product work and understand the new capability | Unedited 20-second capture above the fold: promise, $0 settled, drift, repeat-safe fix; primary CTA to the sample inbox | Scores creativity, technical ambition, and whether it works at once; no install | Video can look staged; the static sample currently fails at remediation |
| B | Technical judge and support ops lead | Prove every promise is replay-provable and never double-paid | Append-only `sweeps.jsonl` keyed by content hash; daemon double-run; adversarial `/remediate` repeat and tampered amount | Stateful audit trail plus cross-rail idempotency is hard to copy | Not visible in 20 seconds; persistence rewrite before freeze |
| C | Support ops lead at 5k-50k tickets/month | Stop paying for resolved tickets that never settled | "Resolved is not Settled" hero; Chargeflow 25% arbitrage; flat fee before the dispute; $44 calculator | Category creation and a competitor price anchor | No real merchant data; judges score creativity, not ROI |
| D | Hackathon judge and event community | Paste a transcript, get a shareable receipt card | Public `/audit` page on Modal or three precomputed audits behind one URL; event community seed | Viral asset plus proof; distribution bonus | Deployment time and keys; mock ledger |

## Scores

Score 0-2. Judge blind to author and model.

| Criterion | A | B | C | D |
|---|---|---|---|---|
| Evidence | 2 | 1 | 0 | 1 |
| Alpha durability | 0 | 2 | 1 | 1 |
| Feasibility | 2 | 1 | 2 | 0 |
| Wedge size | 1 | 2 | 2 | 1 |
| Speed to proof | 2 | 0 | 1 | 1 |
| Total | 7 | 6 | 6 | 4 |

- Judge model: Muse Spark 1.3 Contributor
- Base: A
- Grafts, max 2: C's "Resolved is not Settled" line and $44 caption; B-light's repeat-remediation receipt at the end of the capture.
- Dissent: demo-first can win judges yet leave the double-pay bug unanswered for ops buyers.
- Tie means reframe, not average.

## Alpha Test

- Insight the market lacks: support vendors grade "resolved"; the money only settles at the ledger. Nobody joins the two per order.
- Unfair edge: the refusal path. Re-reconcile server-side, clamp to the live shortfall, return the original receipt on retry, and keep Stripe and Shopify idempotency primitives aligned. It is integration and safety, not model quality.
- Copyability: extraction is days. The refusal path is two to three weeks because it needs two ledger adapters, a durable key, and adversarial tests.
- Compounding: every audited transcript becomes a labeled promise-versus-settlement pair. The shadow-audit dataset improves the gate, the eval, and the sales proof at the same time.
- Edge per week of proof: highest for A because the demo proof and the durable receipt share one artifact.

## Wedge

- One user: hackathon judge. Proxy buyer: support ops lead at 5,000 to 50,000 tickets a month.
- One job: see a real promise-versus-settlement drift and a repeat-safe fix in 20 seconds.
- One surface: public sample inbox at `./index.html?sample=1`, plus the unedited 20-second capture above the fold.
- One week: by Nov 4, 9:00 PM ET.
- One metric: 5 of 5 fresh viewers can state the gap and the $44 number in 20 seconds; the sample inbox renders the drift and a repeat-safe receipt on mobile and desktop with no API key.
- Kill criterion: if the sample inbox does not render on a fresh mobile browser, or the receipt simulation cannot show the same key and $0 additional movement on repeat, stop and fall back to the live Shopify dev-store proof plus the clone path.
- Test shape: prototype. Frontend-only sample receipt, then a recorded proof.
- What would change the decision: a hosted API key with a spend cap makes a live audit possible; then the sample can call the real API and the video can be live.

## Handoff

- Design risk: `design-research`, then `design-loop` on the sample inbox and the 20-second capture.
- Usefulness risk: `usefulness-gate` with 3 support ops leads and their own transcripts.
- Build risk: `task-decomposition` for the durable promise ledger after the event.
- Open questions:
  - Does the event require the `-1026` pinned model ID, or is the canonical `meta-models/muse-spark-open` the safe default?
  - Is a hosted API key with a spend cap available before the deadline?
  - Can the static sample simulate the receipt without weakening the "recorded live audit" label?

## Rejected

| Thesis | Why rejected | What would revive it |
|---|---|---|
| B as base | Stronger long-term moat, but not visible in 20 seconds and needs a persistence rewrite before freeze | A one-week spike after the event; if the double-run daemon passes, make it the product trust layer |
| C as base | Strong general positioning, but judges score creativity and technical ambition, not ROI; no real merchant data | A real pilot with a support ops lead and a defensible dollar number |
| D as base | Distribution upside, but deployment risk and a mock ledger behind the receipt | A hosted `/audit` with a spend-capped key and a shareable receipt card |
