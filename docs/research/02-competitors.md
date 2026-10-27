# Competitive Landscape

Researched 2026-10-26. White space confirmed: everyone audits the conversation OR the money, never the join.

## Competitor matrix

| Name | What they do | Gap vs PromiseCheck |
|---|---|---|
| Sierra | Enterprise autonomous agent, outcome billing | Executes actions; no post-hoc promise-vs-ledger diff |
| Decagon | Enterprise agent, audit trail of tool calls/approvals | Log of what the agent saw/did, never checked against external ledger truth |
| Intercom Fin | Helpdesk agent, $0.99/outcome, refund/cancel actions | Logs actions taken; no verification against live ledger state |
| Zendesk AI Agents | Conversation logs with action boxes | Intra-platform manual trace review, no cross-system reconciliation |
| Ada / Gorgias / Yuma | Shopify-native agents, pre-send guardrails | Prevention before send, not post-promise auditing; no exception inbox |
| LangSmith / Langfuse / Braintrust | Traces, evals, scorers | Score text quality, never claims vs system of record |
| Patronus / Vellum / Humanloop | Hallucination/policy judges, eval gates | Grade text against policy, not live ledger balance |
| Chargeflow / Chargeblast / Justt | Post-dispute automation, evidence packs | Reactive (after chargeback filed); never ingest transcripts proactively |
| Fincile / A2X / Synder | Ledger-to-ledger reconciliation (orders vs payouts) | Never parse unstructured promises as inputs |
| Open source | Langfuse, Agenta, forum scripts | No transcript-to-ledger reconciler found |

Sources: https://decagon.ai/glossary/what-is-an-ai-audit-trail, https://support.zendesk.com/hc/en-us/articles/8357749580186-Reviewing-conversation-logs-for-AI-agents, https://yuma.ai/blogs/ai-hallucinations-in-customer-service-why-quality-control-architecture-matters, https://apps.shopify.com/fincile

Context raising urgency: Air Canada 2024 plus May 2026 German appeals rulings make chatbot promises legally binding; EU AI Act disclosure deadline Aug 2026.

## Adjacent validator: Collar (YC F26)

Collar (https://www.ycombinator.com/companies/collar, https://usecollarai.com) builds AI-native investor relations: earnings prep, investor targeting, citation-backed live teleprompters, Q&A bots, and cross-department reconciliation ("reconciles conflicting information, checks freshness, so management can use an answer without manually verifying it"). Founders Kazel Koh En Yang (CEO) and Jamie Yau (COO), Singaporean, second-time founders ex-GIC/military intelligence; 7-figure ARR, 8 paying clients.

Relationship to PromiseCheck: adjacent, not overlapping. Different buyer (IR teams and CFOs at public companies vs e-commerce support ops), different ledger (filings and consensus vs Stripe/Shopify money movement), no remediation loop. What it validates: citation-backed verification plus a live answer surface is fundable product language, and a teleprompter surfacing a wrong figure is the same drift liability in another domain. A warm founder connection here is a design-pattern reference (evidence spans, freshness checks) and a potential future design partner, not a competitor to outrun.

## White-space verdict

Agent platforms own prevention, recon tools own ledger-to-ledger, eval tools own text quality. The named failure ("promising actions the system never takes") has no vendor owning detection plus remediation. PromiseCheck sits above the agent platforms and beside Stripe/Shopify: integration partners, not direct competitors.

## Demo differentiators

1. Show the lie live: transcript quote vs live ledger row, red MISMATCH badge.
2. Money-sorted exception inbox with evidence chain, not trace search.
3. One-click remediation that writes back to the ledger and flips the card to RESOLVED.
