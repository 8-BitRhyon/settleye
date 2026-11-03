/** Recorded live audit of the sample phantom transcript.
 *
 * Captured from a real model call plus the mock ledger, so the public demo
 * works with no backend. Displayed only behind an explicit "Sample data"
 * label. Never presented as a live result.
 */
import type { AuditReport, DriftResult } from "./api";

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

export const SAMPLE_EXPLANATION =
  "The transcript says the $45 refund was processed. The ledger shows $0.00 settled. That gap is the money at risk.";

export interface SampleReceiptState {
  idempotency_key: string;
  amount_usd: number;
  status: "executed" | "already_executed";
  attempts: number;
}

export function sampleReceiptKey(drift: DriftResult): string {
  return `${drift.promise.action}:${drift.promise.order_id ?? "unknown"}:${drift.amount_at_risk_usd.toFixed(2)}`;
}

export function nextSampleReceipt(
  current: SampleReceiptState | null,
  drift: DriftResult,
): SampleReceiptState {
  const key = sampleReceiptKey(drift);
  if (current === null) {
    return {
      idempotency_key: key,
      amount_usd: drift.amount_at_risk_usd,
      status: "executed",
      attempts: 1,
    };
  }
  return {
    ...current,
    status: "already_executed",
    attempts: current.attempts + 1,
  };
}

export function additionalMovement(receipt: SampleReceiptState): number {
  return receipt.status === "already_executed" ? 0 : receipt.amount_usd;
}
