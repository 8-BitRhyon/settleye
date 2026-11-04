import { describe, expect, it } from "vitest";
import sampleReceipt from "./sample-receipt.json";
import { SAMPLE_KEY_ID, SAMPLE_PUBLIC_KEY } from "./sample-receipt-key";
import {
  SAMPLE_MERCHANT_KEY_ID,
  SAMPLE_MERCHANT_PUBLIC_KEY,
} from "./sample-receipt-merchant-key";
import {
  tamperAmount,
  verifyExecutionReceipt,
  verifyTwoPartyReceipt,
  type ExecutionReceipt,
} from "./receipt";

const SAMPLE = sampleReceipt as ExecutionReceipt;

describe("signed sample receipt", () => {
  it("verifies the Python-signed payload in the browser verifier", async () => {
    const result = await verifyExecutionReceipt(
      SAMPLE,
      SAMPLE_PUBLIC_KEY,
      SAMPLE_KEY_ID,
    );
    expect(result).toEqual({ valid: true, reason: "Signature valid." });
  });

  it("verifies the issuer and merchant signatures with both pins", async () => {
    const result = await verifyTwoPartyReceipt(
      SAMPLE,
      SAMPLE_PUBLIC_KEY,
      SAMPLE_KEY_ID,
      SAMPLE_MERCHANT_PUBLIC_KEY,
      SAMPLE_MERCHANT_KEY_ID,
    );
    expect(result.issuer.valid).toBe(true);
    expect(result.merchant.status).toBe("valid");
    expect(result.valid).toBe(true);
  });

  it("keeps the frozen receipt id", () => {
    expect(SAMPLE.receipt_id).toBe(
      "sha256:df3f410be43689329b69705c9534f14035a82b32c1b6383986788bf559e4347b",
    );
  });

  it("fails after a one-digit amount change", async () => {
    const result = await verifyExecutionReceipt(
      tamperAmount(SAMPLE),
      SAMPLE_PUBLIC_KEY,
      SAMPLE_KEY_ID,
    );
    expect(result.valid).toBe(false);
  });

  it("fails the merchant signature after a changed acknowledgement time", async () => {
    const entry = SAMPLE.countersignatures?.[0];
    expect(entry).toBeDefined();
    const changed: ExecutionReceipt = {
      ...SAMPLE,
      countersignatures: [
        { ...(entry as NonNullable<typeof entry>), acknowledged_at: "2026-11-04T12:06:00Z" },
      ],
    };
    const result = await verifyTwoPartyReceipt(
      changed,
      SAMPLE_PUBLIC_KEY,
      SAMPLE_KEY_ID,
      SAMPLE_MERCHANT_PUBLIC_KEY,
      SAMPLE_MERCHANT_KEY_ID,
    );
    expect(result.merchant.status).toBe("invalid");
    expect(result.valid).toBe(false);
  });
});
