import { describe, expect, it } from "vitest";
import sampleReceipt from "./sample-receipt.json";
import { SAMPLE_KEY_ID, SAMPLE_PUBLIC_KEY } from "./sample-receipt-key";
import {
  tamperAmount,
  verifyExecutionReceipt,
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

  it("fails after a one-digit amount change", async () => {
    const result = await verifyExecutionReceipt(
      tamperAmount(SAMPLE),
      SAMPLE_PUBLIC_KEY,
      SAMPLE_KEY_ID,
    );
    expect(result.valid).toBe(false);
  });
});
