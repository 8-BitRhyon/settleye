# Market Importance: Silent Execution Drift

Researched 2026-10-26. Verdict: real problem, early market, worth the build.

## Key facts

1. **Autonomous support is plan of record.** Gartner: 85% of service leaders would explore/pilot customer-facing conversational GenAI in 2025; agentic AI to resolve 80% of common issues without humans by 2029. https://www.gartner.com/en/newsroom/press-releases/2024-12-09-gartner-survey-reveals-85-percent-of-customer-service-leaders-will-explore-or-pilot-customer-facing-conversational-genai-in-2025
2. **Money prices support agents as the durable segment.** Sierra raised $950M at $15B+ valuation with $150M+ ARR; voice passed text as top channel. https://sierra.ai/blog/year-two-in-review
3. **Agents take ledger-touching actions.** Gorgias AI Agent acts directly in Shopify (up to 60% automation claimed); Intercom Fin 3 hits ~67% resolution at $0.99/resolution. https://www.gorgias.com/ai-agent
4. **False-promise incidents are documented and legally load-bearing.** Air Canada tribunal (2024 BCCRT 149) ordered payment after its chatbot invented a bereavement policy. Oct 2025: Priceline "Penny" told a customer a non-refundable booking was fully refundable. https://www.bbc.com/travel/article/20240222-air-canada-chatbot-misinformation-what-travellers-should-know
5. **The cost pool is large.** Chargeback volume +24% 2025-2028 to 324M transactions/yr; global losses $33.79B in 2025, $41.69B by 2028; one chargeback can cost up to 3.4x transaction value. https://www.mastercard.com/sea/en/news-and-trends/Insights/2025/what-s-the-true-cost-of-a-chargeback-in-2025.html
6. **Audit tooling watches traces, not ledgers.** Eval/observability (Braintrust, LangSmith, Arize, Patronus) fight over traces and scores; none reconcile "agent said refund" against money movement. https://devrev.ai/blog/bounded-financial-actions-support-refund-guardrails
7. **Reducto analogy half-validated.** Reducto raised $75M Series B Oct 2025 (~$605M valuation) owning document parsing for vertical agents. Validates owning one enterprise choke point; no funded startup owns agent-to-ledger reconciliation. https://www.vcaonline.com/news/2025101405/reducto-raises-75m-series-b-to-define-the-future-of-ai-document-intelligence/

## Verdict

Real and structurally growing: action-taking agents scale inside Shopify/Stripe stacks, promises already create liability, failures land in a $33B+ dispute pool. Gap: no public source splits AI-caused vs human-caused chargebacks, so the pitch rests on incident precedent plus mechanism, not an AI dispute rate.

## Demo-able pain points

1. Phantom refund: "refund issued", Stripe shows none, customer chargebacks days later.
2. Over-authority refund: above-policy amount, found at month-end close.
3. Silent cancellation gap: subscription stays active, next billing triggers dispute.

## Risks

1. Platform absorption (Intercom/Gorgias/Zendesk ship native action receipts).
2. Unproven willingness to pay for post-hoc audit as a second budget line.
3. No AI-attributable loss dataset; fuzzy promise language risks false positives.

## Prize sizing

One phantom $50 refund/week = ~$2,600/yr leakage; at ~3.4x all-in chargeback cost on escalations, exposure is ~$4,700/yr per merchant. A $49-199/mo auditor catching one incident/month pays for itself 2-10x.
