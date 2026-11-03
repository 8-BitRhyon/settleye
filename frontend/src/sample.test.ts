import { describe, expect, it } from "vitest";
import {
  SAMPLE_AUDIT_RESPONSE,
  SAMPLE_EXPLANATION,
  additionalMovement,
  nextSampleReceipt,
  sampleReceiptKey,
} from "./sample";

describe("sample audit response", () => {
  it("matches the AuditReport shape the inbox renders", () => {
    expect(SAMPLE_AUDIT_RESPONSE.verdict).toBe("drift_found");
    expect(SAMPLE_AUDIT_RESPONSE.total_at_risk_usd).toBe(45.0);
    expect(SAMPLE_AUDIT_RESPONSE.drifts).toHaveLength(1);
    expect(SAMPLE_AUDIT_RESPONSE.drifts[0].amount_at_risk_usd).toBe(45.0);
    expect(SAMPLE_AUDIT_RESPONSE.drifts[0].promise.order_id).toBe("992");
  });

  it("stays consistent between results and drifts", () => {
    expect(SAMPLE_AUDIT_RESPONSE.results).toHaveLength(
      SAMPLE_AUDIT_RESPONSE.promises.length,
    );
    expect(SAMPLE_AUDIT_RESPONSE.drifts[0]).toEqual(
      SAMPLE_AUDIT_RESPONSE.results[0],
    );
  });

  it("models the first fix and the idempotent retry without an API", () => {
    const drift = SAMPLE_AUDIT_RESPONSE.drifts[0];
    const first = nextSampleReceipt(null, drift);
    expect(first.status).toBe("executed");
    expect(first.idempotency_key).toBe("refund:992:45.00");
    expect(first.attempts).toBe(1);
    expect(additionalMovement(first)).toBe(45);

    const second = nextSampleReceipt(first, drift);
    expect(second.status).toBe("already_executed");
    expect(second.idempotency_key).toBe(first.idempotency_key);
    expect(second.attempts).toBe(2);
    expect(additionalMovement(second)).toBe(0);
    expect(sampleReceiptKey(drift)).toBe("refund:992:45.00");
  });

  it("explains the gap with the transcript and the ledger, not the API", () => {
    expect(SAMPLE_EXPLANATION).toContain("$45");
    expect(SAMPLE_EXPLANATION).toContain("$0.00");
  });
});
