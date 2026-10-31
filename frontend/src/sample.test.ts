import { describe, expect, it } from "vitest";
import { SAMPLE_AUDIT_RESPONSE } from "./sample";

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
});
