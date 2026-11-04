import { describe, expect, it } from "vitest";
import * as nacl from "tweetnacl";
import {
  canonicalize,
  countersignMessage,
  sha256Hex,
  toBase64Url,
  verifyExecutionReceipt,
  verifyMerchantCountersignatures,
  verifyTwoPartyReceipt,
  type Countersignature,
  type ExecutionReceipt,
} from "./receipt";

const ISSUER_KEY_ID = "issuer-test-key";
const MERCHANT_KEY_ID = "merchant-test-key";

function payload(): Omit<ExecutionReceipt, "receipt_id" | "signature"> {
  return {
    version: 1,
    issued_at: "2026-11-04T12:00:00Z",
    issuer: { name: "Settleye", key_id: ISSUER_KEY_ID },
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
  };
}

interface Fixture {
  receipt: ExecutionReceipt;
  issuerPublicKey: string;
  merchantPublicKey: string;
}

function fixture(): Fixture {
  const issuer = nacl.sign.keyPair();
  const merchant = nacl.sign.keyPair();
  const issuerPublicKey = toBase64Url(issuer.publicKey);
  const merchantPublicKey = toBase64Url(merchant.publicKey);
  const body = payload();
  const message = new TextEncoder().encode(canonicalize(body));
  const receiptId = `sha256:${sha256Hex(message)}`;
  const issuerSignature = nacl.sign.detached(message, issuer.secretKey);
  const acknowledgedAt = "2026-11-04T12:05:00Z";
  const counterMessage = countersignMessage(
    receiptId,
    MERCHANT_KEY_ID,
    acknowledgedAt,
  );
  const countersignature: Countersignature = {
    role: "merchant",
    key_id: MERCHANT_KEY_ID,
    alg: "Ed25519",
    public_key: merchantPublicKey,
    acknowledged_at: acknowledgedAt,
    value: toBase64Url(
      nacl.sign.detached(counterMessage, merchant.secretKey),
    ),
  };
  return {
    issuerPublicKey,
    merchantPublicKey,
    receipt: {
      ...body,
      receipt_id: receiptId,
      signature: {
        alg: "Ed25519",
        public_key: issuerPublicKey,
        value: toBase64Url(issuerSignature),
      },
      countersignatures: [countersignature],
    },
  };
}

describe("merchant countersignature", () => {
  it("verifies a two-party receipt with both keys pinned", async () => {
    const { receipt, issuerPublicKey, merchantPublicKey } = fixture();
    const result = await verifyTwoPartyReceipt(
      receipt,
      issuerPublicKey,
      ISSUER_KEY_ID,
      merchantPublicKey,
      MERCHANT_KEY_ID,
    );
    expect(result.issuer.valid).toBe(true);
    expect(result.merchant.status).toBe("valid");
    expect(result.valid).toBe(true);
  });

  it("keeps the issuer signature valid after countersigning", async () => {
    const { receipt, issuerPublicKey } = fixture();
    const result = await verifyExecutionReceipt(
      receipt,
      issuerPublicKey,
      ISSUER_KEY_ID,
    );
    expect(result.valid).toBe(true);
  });

  it("reports no merchant signature as provisional, not invalid", async () => {
    const { receipt, merchantPublicKey } = fixture();
    const unsigned = { ...receipt, countersignatures: [] };
    const result = verifyMerchantCountersignatures(
      unsigned,
      merchantPublicKey,
      MERCHANT_KEY_ID,
    );
    expect(result.status).toBe("none");
  });

  it("rejects a changed acknowledgement time", async () => {
    const { receipt, merchantPublicKey } = fixture();
    const changed: ExecutionReceipt = {
      ...receipt,
      countersignatures: [
        {
          ...(receipt.countersignatures?.[0] as Countersignature),
          acknowledged_at: "2026-11-04T12:06:00Z",
        },
      ],
    };
    const result = verifyMerchantCountersignatures(
      changed,
      merchantPublicKey,
      MERCHANT_KEY_ID,
    );
    expect(result.status).toBe("invalid");
  });

  it("rejects a merchant key id that is not pinned", async () => {
    const { receipt, merchantPublicKey } = fixture();
    const result = verifyMerchantCountersignatures(
      receipt,
      merchantPublicKey,
      "other-merchant-key",
    );
    expect(result.status).toBe("invalid");
  });

  it("rejects a different merchant public key", async () => {
    const { receipt } = fixture();
    const other = nacl.sign.keyPair();
    const result = verifyMerchantCountersignatures(
      receipt,
      toBase64Url(other.publicKey),
      MERCHANT_KEY_ID,
    );
    expect(result.status).toBe("invalid");
  });

  it("rejects a malformed countersignature", async () => {
    const { receipt } = fixture();
    const malformed = {
      ...receipt,
      countersignatures: [{ role: "merchant" }],
    } as unknown as ExecutionReceipt;
    expect(() =>
      verifyMerchantCountersignatures(
        malformed,
        "not-a-key",
        MERCHANT_KEY_ID,
      ),
    ).not.toThrow();
    expect(
      verifyMerchantCountersignatures(malformed, "not-a-key", MERCHANT_KEY_ID)
        .status,
    ).toBe("invalid");
  });

  it("never accepts a valid merchant signature over a broken issuer payload", async () => {
    const { receipt, issuerPublicKey, merchantPublicKey } = fixture();
    const tampered: ExecutionReceipt = {
      ...receipt,
      promise: { ...receipt.promise, amount: "46.00" },
    };
    const result = await verifyTwoPartyReceipt(
      tampered,
      issuerPublicKey,
      ISSUER_KEY_ID,
      merchantPublicKey,
      MERCHANT_KEY_ID,
    );
    expect(result.merchant.status).toBe("valid");
    expect(result.issuer.valid).toBe(false);
    expect(result.valid).toBe(false);
  });
});
