# Technical Feasibility

Researched 2026-10-26. One critical correction applied to the original spec.

## Verdicts

### 1. Model `meta-models/muse-spark-open-1026`: RISKY ID, working family

- Real and hosted: yes. 816B MoE / 42B active, 1M context. Day-0 on Baseten Model APIs, Modal Shared Endpoints, plus Fireworks, Groq, Nebius, OpenRouter, Together.
- The exact string `...-1026` exists NOWHERE. Canonical IDs: Baseten `meta-models/muse-spark-open` at `https://inference.baseten.co/v1` (OpenAI-compatible); Modal Shared Endpoint `meta-models/Muse-Spark-Open-816B-A42B` ($1.25/$4.25 per 1M tokens).
- Structured/JSON mode: BLOCKED on Baseten for this model. Baseten accepts `json_schema` but does not enforce it. Do not rely on constrained decoding; use prompt-JSON-only plus Pydantic validation plus bounded retry (max 2).
- Expect cold starts and shared-capacity throttling on serverless tiers during judging.
- Sources: https://www.baseten.co/library/muse-spark-open, https://docs.baseten.co/inference/structured-outputs, https://modal.com/library/meta/muse-spark-open, https://research.meta.ai/blog/muse-spark-open

### 2. Stripe test mode: WORKS

- List refunds: `GET /v1/refunds` with `charge=` or `payment_intent=` filter. Remediate: `POST /v1/refunds` with `charge`/`payment_intent`, optional `amount` for partials.
- Test keys (`sk_test_`) never touch card networks.
- Sources: https://docs.stripe.com/api/refunds/create, https://docs.stripe.com/api/refunds/list, https://docs.stripe.com/testing-use-cases

### 3. Shopify GraphQL Admin on free dev store: WORKS with caveats

- Free partner dev store exposes the full GraphQL Admin API via custom app; auth is Admin API access token in `X-Shopify-Access-Token`.
- `refundCreate(input: RefundInput!)` mutation, `refund(id:)` query, `Order.refunds` connection. Since 2026-04, `refundCreate` REQUIRES `@idempotent(key:...)`.
- Test payments via Bogus gateway; no payouts on dev stores.
- Sources: https://shopify.dev/docs/api/admin-graphql/latest/mutations/refundCreate, https://shopify.dev/docs/apps/build/authentication-authorization

### 4. Modal for FastAPI plus scheduled jobs: WORKS

- FastAPI via `@modal.asgi_app()` or `@modal.fastapi_endpoint()`; scheduled daemon via `@app.function(schedule=modal.Cron(...))`. Free tier covers hackathon scale.
- Sources: https://modal.com/docs/guide/webhooks, https://modal.com/docs/guide/cron

### 5. Pydantic structured extraction: WORKS with layers

- Best practice: constrained decoding where enforced, Pydantic validation as backstop, 1-2 repair retries, never unbounded. Shallow schemas, temperature 0.1-0.3.
- Because Baseten does not enforce schema for this model, extraction must treat model output as untrusted text.

## Ranked risks and fallbacks

1. No enforced JSON schema on Baseten (extraction core). Fallback: validation-retry wrapper; reserve an enforced-schema model for extraction if needed.
2. Wrong model ID ships and breaks all calls. Fallback: `MODEL_ID` constant, startup health check, one-line provider switch.
3. Shopify auth/idempotency friction eats a day. Fallback: mock ledger adapter behind an interface from hour one.
4. Modal cold starts during demo. Fallback: warm ping, generous timeouts, local `uvicorn` runbook.
5. Stripe/Shopify double-refund across rails. Fallback: single remediation service with idempotency keys in our own DB.

## Build order (Oct 27 - Nov 4)

Days 1-2: ledger abstraction plus mock adapter, Stripe test list/create wired. Days 3-4: Shopify dev store read path. Day 5: reconciliation loop, then Modal cron. Day 6: extraction with validate-plus-retry, eval on fixtures. Day 7: remediation behind idempotency guard. Day 8: dashboard plus demo script. Day 9: hardening, key check, offline fallback, submit early.
