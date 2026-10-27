# Gemini Deep Research Prompt: The Reducto Play for PromiseCheck

Paste everything below the line into Gemini Deep Research.

---

Research the following for a startup called PromiseCheck: an execution auditor for AI customer-support agents. It reads support transcripts, extracts binding promises the agent made (refunds, cancellations, reships: action, amount, order ID, evidence quote), and reconciles each promise against live Stripe/Shopify ledger state, flagging mismatches in an exception inbox with one-click remediation. Stack: `meta-models/muse-spark-open` via Baseten for extraction, Pydantic validation plus bounded retry, FastAPI backend, React dashboard. Target buyers: e-commerce merchants and support ops leads running AI agents.

## Core strategic question

Reducto won multi-million-dollar enterprise deals by doing ONE narrow function extremely well (their R1 model parsing messy documents at near-100% vs ~50% for general models) and then expanding into everything around that function. Global Citizens F.ai did the same for immigration law workflows. For PromiseCheck:

1. What is our equivalent "one function"? Candidates: (a) extracting structured promises from messy multi-turn support dialogue with near-perfect precision/recall, (b) the transcript-to-ledger reconciliation join itself, (c) something else. Which one, and what accuracy bar makes it enterprise-grade?
2. Build vs borrow: should we fine-tune an open-weight model (e.g. a small Qwen/Llama-class extractor, or Meta's open models) for this narrow extraction task, or keep prompting a frontier model? Compare on: expected accuracy lift with numbers from published fine-tuning studies on structured extraction; training and serving cost; latency; and whether a fine-tuned model constitutes a real moat or just a feature.
3. What did Reducto actually do technically with their R1 model (architecture, training data, eval methodology)? What is replicable for us in under 3 months with under $5k in compute?
4. What does Global Citizens F.ai's stack and packaging look like, and what transfers to a support-ops auditor?

## Buyer and packaging research

5. For e-commerce merchants ($10K+/mo GMV) and support ops leads: what exactly would they buy — per-seat, per-audit, per-dollar-recovered, or flat monthly? Cite how adjacent tools (Gorgias, Chargeflow at 25% of recovered, Shopify fraud apps, Ethoca/RDR alert fees) price, with current numbers and URLs.
6. What evidence do these buyers require before paying (pilot structure, ROI proof format, security/compliance checkboxes like SOC 2)? How do chargeback representment teams evaluate evidence packs today?
7. Who are 5-10 specific companies or merchant profiles that feel phantom-refund pain most acutely, and why?

## Frontier vs problem framing

8. Is "AI execution verification layer" better positioned as frontier-pushing infrastructure or as a fix for a known firsthand support-ops pain? Which framing has won enterprise deals historically for analogous auditor products, with examples?

## Deliverable format

Return: (1) a verdict on fine-tune vs prompt with costed numbers, (2) the single function to own with its accuracy bar and eval plan, (3) a packaging and pricing recommendation with buyer evidence requirements, (4) a ranked list of the 5 strongest facts a founder should know before selling this, each with a source URL. Be skeptical of vendor marketing; prefer primary docs, filings, and measured benchmarks.
