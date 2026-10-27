# Gemini Deep Research Prompt: The Reducto Play for PromiseCheck (v3)

Foundation research completed by our team (Oct 27-28): Reducto/Collar/Global Citizens surface work, plus round-2 tracks on adjacent vendors, complaint data, eval benchmarks, BNPL/dispute rails, incident UX, and regulation. This prompt asks Gemini only what surface work could NOT answer. Paste everything below the line into Gemini Deep Research.

---

Research the following for a startup called PromiseCheck: an execution auditor for AI customer-support agents. It reads support transcripts, extracts binding promises the agent made (refunds, cancellations, reships: action, amount, order ID, evidence quote), and reconciles each promise against live Stripe/Shopify ledger state, flagging mismatches in an exception inbox with one-click remediation. Stack: `meta-models/muse-spark-open-1026` via Baseten for extraction, Pydantic validation plus bounded retry, FastAPI backend, React dashboard. Target buyers: e-commerce merchants and support ops leads running AI agents.

## What we already know (do not re-research; build on it)

- Reducto (reducto.ai): API-first document intelligence (Parse, Split, Extract, Classify, Edit, Studio), public per-1,000-page pricing (Parse $10, Extract $20, Deep Extract $40), r-1 single-pass parsing model (Sept 2026, claimed 20% error reduction, 1c/page), $75M Series B Oct 2025 (a16z), first Fortune 10 deal started as a $200/mo playground signup. Accuracy claims are largely vendor-commissioned; one independent bench (Hanji, 400 pages) ranks Reducto 3rd at 75.2% text accuracy. Architecture, training data, margins, and real ACVs are undisclosed.
- Global Citizens (globalcitizens.ai): hybrid tech-co plus law firm selling fixed-fee US immigration services (O-1 $10,500, EB-1A $11,500, H-1B $4,500), internal "Loki" 4-sub-agent system, attorneys hand-review before filing, seed stage, self-reported 1,560+ cases and 99.5% approval. AI stack, error rates, and round size undisclosed.
- Collar (usecollarai.com, YC F26): AI investor-relations suite (targeting, CRM, simulators, coworking sign-offs, Q&A bank, live teleprompter, front desk), sales-led with a free wedge, no public pricing, no named customers, self-reported "~40 hours/month saved." Adjacent (verification-flavored) but non-overlapping: different buyer, different ledger, no remediation loop.

## Core strategic question

Reducto won enterprise deals by doing ONE narrow function extremely well and expanding into everything around it. For PromiseCheck:

1. What is our equivalent "one function"? Candidates: (a) extracting structured promises from messy multi-turn support dialogue with near-perfect precision/recall, (b) the transcript-to-ledger reconciliation join itself, (c) something else. Which one, and what accuracy bar makes it enterprise-grade?
2. Build vs borrow: should we fine-tune an open-weight model for this narrow extraction task, or keep prompting a frontier model? Compare on expected accuracy lift with numbers from published fine-tuning studies on structured extraction, training and serving cost, latency, and whether a fine-tuned model is a real moat or a feature. Budget frame: under $5k compute, under 3 months.
3. What is technically replicable from Reducto's r-1 approach (single-pass vision-language parsing, agentic verify-and-correct loops like their Deep Extract) for OUR input type (dialogue transcripts, not PDFs)? What is not transferable?
4. What transfers from Global Citizens' hybrid model (fixed-scope packages, human sign-off ritual, SLA dashboard) to selling an auditor to support ops?

## What we already know, round 2 (do not re-research; build on it)

- Adjacent vendors mapped: Loop/Redo/Corso/Extend/Appriss decide claims pre-money; Klaus/MaestroQA/EvaluAgent score chats. None reconciles promises against ledgers. Boundary: they decide claims or score chats; we prove money moved. Steals adopted: money-sorted queue, cited-factors trail, performance pricing, promised-but-unsettled flag.
- Pain quantified: FTC Sentinel $12.5B fraud losses 2024 (+25%), 38% of reporters lost money; negative-option complaints 42 to ~70/day 2021-2024. CFPB narratives FROZE Aug 14, 2026 (pin the FOIA archive now). No published promised-but-unissued refund rate exists.
- Eval gap confirmed: tau-bench grounds actions against DB state (copy its DB-plus-verifier pattern, not frozen tasks); AgentDojo is the adversarial template; ABCD is the best dialogue seed; nothing extracts promises AND reconciles them against ledgers. Our harness: 300-500 cases, deterministic-first grader, false-all-clear rate as the lead metric, open dataset plus leaderboard.
- Rails ranked: Affirm, Adyen, PayPal, Klarna, Afterpay last. Merchant eats phantom refunds on every BNPL rail. Visa CE3.0 exact field bar known; export schema specified.
- Inbox rules adopted from incident.io/Rootly/PagerDuty: money sort, fixed card order, Open/Acked/Resolved only, ack and resolve timers, triage hold, append-only export pack.
- Regulation: EU AI Act Art 50 live Aug 2026 (fines to EUR 15M/3%); CA AB 2863 live; click-to-cancel dead but UDAP alive; Air Canada persuasive-not-binding; SOC 2 budget $25-60k first year. Trap noted: no PAN, minimization only.

## Questions our surface research could not answer (priority, updated)

5. Reducto: what are r-1's actual training data, failure modes, unit economics per page, real ACVs and discount curves, and how defensible is it vs hyperscalers and Docling/Unstructured once single-pass parsing commoditizes?
6. Global Citizens: what is Loki technically (models, retrieval corpus, generation vs templates), what are measured error controls, is there any paying law-firm software customer, and how is privilege handled across vendors and offshore staff?
7. Collar: what is the real commercial model, who are the design partners behind the "$300B market cap" claim, what grounds the teleprompter ("never invents a number" is unproven), and does their reconciliation engine persist an auditable trail or is it ephemeral?
8. Buyer research: for e-commerce merchants ($10K+/mo GMV), what evidence do they require before paying (pilot structure, ROI proof format, SOC 2)? How do chargeback representment teams evaluate evidence packs today, field by field against Visa CE3.0? Name 5-10 merchant profiles that feel phantom-refund pain most acutely, with reasons. Note our constraint: CFPB narratives froze Aug 2026, so where should fresh promise-failure evidence come from?
9. BNPL adjudication: who eats phantom refunds on Klarna/Affirm/Afterpay rails in practice, and what would a cross-rail auditor need to prove for a merchant to trust it over the lender's own dashboard?

## Deliverable format

Return: (1) verdict on fine-tune vs prompt with costed numbers, (2) the single function to own with its accuracy bar and eval plan (note: we intend to open-source our eval harness, Reducto-style, so advise on its design), (3) packaging and pricing recommendation with buyer evidence requirements, (4) ranked list of the 5 strongest facts a founder should know before selling this, each with a source URL. Be skeptical of vendor marketing; prefer primary docs, filings, and measured benchmarks. Mark anything unverifiable as UNVERIFIED.
