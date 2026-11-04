import { describe, expect, it } from "vitest";
import {
  describeReceiptCard,
  MERCHANT_PENDING_DETAIL,
  selectActiveIssuerKey,
  selectIssuerKey,
} from "./receipt-display";
import type { ReceiptKeyRecord } from "./api";
import type { ExecutionReceipt, TwoPartyVerification } from "./receipt";

function receipt(): ExecutionReceipt {
  return {
    version: 1,
    issued_at: "2026-11-04T12:00:00Z",
    issuer: { name: "Settleye", key_id: "settleye-demo-2026-11" },
    agent: { model_id: "meta-models/muse-spark-open-1026" },
    transcript: { sha256: "a".repeat(64), turns: 3 },
    promise: {
      action: "refund",
      order_id: "992",
      amount: "45.00",
      target_system: "stripe",
      terminal_status: "binding",
      evidence_span: "I have processed a full $45 refund for order #992.",
    },
    ledger: {
      system: "stripe",
      order_id: "992",
      shortfall_usd: "45.00",
      summary: "Order 992: $0.00 settled of $45.00 promised.",
      checked_at: "2026-11-04T12:00:00Z",
    },
    remediation: {
      idempotency_key: "refund:992:45.00",
      amount_usd: "45.00",
      status: "executed",
    },
    receipt_id: "sha256:abc",
    signature: { alg: "Ed25519", public_key: "issuer-pin", value: "sig" },
  };
}

function verification(
  issuerValid: boolean,
  merchant: TwoPartyVerification["merchant"],
): TwoPartyVerification {
  return {
    issuer: {
      valid: issuerValid,
      reason: issuerValid
        ? "Signature valid."
        : "Receipt id does not match the payload.",
    },
    merchant,
    valid: issuerValid && merchant.status !== "invalid",
  };
}

describe("describeReceiptCard", () => {
  it("shows issuer valid plus merchant pending when no countersignature", () => {
    const display = describeReceiptCard(
      receipt(),
      verification(true, {
        status: "none",
        reason: "No merchant signature yet.",
      }),
    );
    expect(display?.trusted).toBe(true);
    expect(display?.issuer).toEqual({
      kind: "valid",
      title: "Issuer signature valid",
      detail: "settleye-demo-2026-11",
    });
    expect(display?.merchant).toEqual({
      kind: "neutral",
      title: "No merchant signature yet",
      detail: MERCHANT_PENDING_DETAIL,
    });
  });

  it("shows both rows green when the merchant countersigned", () => {
    const display = describeReceiptCard(
      receipt(),
      verification(true, {
        status: "valid",
        key_id: "merchant-demo-2026-11",
        reason: "Merchant countersigned.",
      }),
    );
    expect(display?.trusted).toBe(true);
    expect(display?.issuer.kind).toBe("valid");
    expect(display?.merchant).toEqual({
      kind: "valid",
      title: "Merchant countersigned",
      detail: "merchant-demo-2026-11",
    });
  });

  it("never shows a green merchant row when the issuer is invalid", () => {
    const display = describeReceiptCard(
      receipt(),
      verification(false, {
        status: "valid",
        key_id: "merchant-demo-2026-11",
        reason: "Merchant countersigned.",
      }),
    );
    expect(display?.trusted).toBe(false);
    expect(display?.issuer.kind).toBe("invalid");
    expect(display?.issuer.title).toBe("Issuer signature invalid");
    expect(display?.merchant.kind).not.toBe("valid");
    expect(display?.merchant.kind).toBe("invalid");
  });

  it("surfaces the merchant reason when the merchant signature is invalid", () => {
    const display = describeReceiptCard(
      receipt(),
      verification(true, {
        status: "invalid",
        key_id: "merchant-demo-2026-11",
        reason: "Merchant key is not pinned.",
      }),
    );
    expect(display?.trusted).toBe(false);
    expect(display?.merchant).toEqual({
      kind: "invalid",
      title: "Merchant signature invalid",
      detail: "Merchant key is not pinned.",
    });
  });

  it("returns null for a missing live receipt", () => {
    expect(
      describeReceiptCard(
        null,
        verification(true, {
          status: "none",
          reason: "No merchant signature yet.",
        }),
      ),
    ).toBeNull();
    expect(
      describeReceiptCard(
        undefined,
        verification(true, {
          status: "none",
          reason: "No merchant signature yet.",
        }),
      ),
    ).toBeNull();
  });

  it("returns null while verification is still running", () => {
    expect(describeReceiptCard(receipt(), null)).toBeNull();
  });
});

describe("selectActiveIssuerKey", () => {
  function key(
    keyId: string,
    status: ReceiptKeyRecord["status"],
  ): ReceiptKeyRecord {
    return { key_id: keyId, public_key: `pub-${keyId}`, status };
  }

  it("returns the first active key", () => {
    expect(
      selectActiveIssuerKey([
        key("retired-1", "retired"),
        key("active-1", "active"),
        key("active-2", "active"),
      ]),
    ).toEqual(key("active-1", "active"));
  });

  it("returns null when no key is active", () => {
    expect(
      selectActiveIssuerKey([key("old", "retired"), key("bad", "revoked")]),
    ).toBeNull();
    expect(selectActiveIssuerKey([])).toBeNull();
  });

  it("returns null for a missing or failed key list", () => {
    expect(selectActiveIssuerKey(null)).toBeNull();
    expect(selectActiveIssuerKey(undefined)).toBeNull();
  });
});


describe("selectIssuerKey", () => {
  function key(
    keyId: string,
    status: ReceiptKeyRecord["status"],
  ): ReceiptKeyRecord {
    return { key_id: keyId, public_key: `pub-${keyId}`, status };
  }

  it("selects the key that actually signed the receipt", () => {
    expect(
      selectIssuerKey(
        [key("new-active", "active"), key("old-retired", "retired")],
        "old-retired",
      ),
    ).toEqual(key("old-retired", "retired"));
  });

  it("does not select a revoked key", () => {
    expect(selectIssuerKey([key("bad", "revoked")], "bad")).toBeNull();
  });

  it("does not select a different key id", () => {
    expect(selectIssuerKey([key("other", "active")], "signed-by-me")).toBeNull();
  });

  it("returns null for a missing or failed key list", () => {
    expect(selectIssuerKey(null, "any")).toBeNull();
    expect(selectIssuerKey(undefined, "any")).toBeNull();
    expect(selectIssuerKey([], "any")).toBeNull();
  });
});
