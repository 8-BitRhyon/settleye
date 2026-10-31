/** Recorded live audit of the sample phantom transcript.
 *
 * Captured from a real model call plus the mock ledger, so the public demo
 * works with no backend. Displayed only behind an explicit "Sample data"
 * label. Never presented as a live result.
 */
import type { AuditReport } from "./api";

export const SAMPLE_AUDIT_RESPONSE: AuditReport = {
  promises: [
    {
      action: "refund",
      amount: 45.0,
      order_id: "992",
      target_system: "unknown",
      asserted_state:
        "a full $45 refund for order #992 has been processed",
      confidence: 0.99,
      evidence_span:
        "I have processed a full $45 refund for order #992. It should appear on your statement within 5 to 10 business days.",
    },
  ],
  results: [
    {
      promise: {
        action: "refund",
        amount: 45.0,
        order_id: "992",
        target_system: "unknown",
        asserted_state:
          "a full $45 refund for order #992 has been processed",
        confidence: 0.99,
        evidence_span:
          "I have processed a full $45 refund for order #992. It should appear on your statement within 5 to 10 business days.",
      },
      verdict: "drift",
      ledger_summary: "Order 992: $0.00 settled of $45.00 promised.",
      amount_at_risk_usd: 45.0,
    },
  ],
  drifts: [
    {
      promise: {
        action: "refund",
        amount: 45.0,
        order_id: "992",
        target_system: "unknown",
        asserted_state:
          "a full $45 refund for order #992 has been processed",
        confidence: 0.99,
        evidence_span:
          "I have processed a full $45 refund for order #992. It should appear on your statement within 5 to 10 business days.",
      },
      verdict: "drift",
      ledger_summary: "Order 992: $0.00 settled of $45.00 promised.",
      amount_at_risk_usd: 45.0,
    },
  ],
  total_at_risk_usd: 45.0,
  verdict: "drift_found",
};
