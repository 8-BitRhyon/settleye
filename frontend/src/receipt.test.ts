import { describe, expect, it } from "vitest";
import * as nacl from "tweetnacl";
import {
  canonicalize,
  sha256Hex,
  tamperAmount,
  toBase64Url,
  verifyExecutionReceipt,
  type ExecutionReceipt,
} from "./receipt";

const KEY_ID = "test-issuer-key";

async function signedReceipt(): Promise<{
  receipt: ExecutionReceipt;
  publicKey: string;
}> {
  const keyPair = nacl.sign.keyPair();
  const publicKey = toBase64Url(keyPair.publicKey);
  const payload: Omit<ExecutionReceipt, "receipt_id" | "signature"> = {
    version: 1,
    issued_at: "2026-11-04T12:00:00Z",
    issuer: { name: "Settleye", key_id: KEY_ID },
    agent: { model_id: "meta-models/muse-spark-open-1026" },
    transcript: { sha256: "abc123", turns: 3 },
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
  const message = new TextEncoder().encode(canonicalize(payload));
  const receiptId = `sha256:${await sha256Hex(message)}`;
  const signature = nacl.sign.detached(message, keyPair.secretKey);
  return {
    publicKey,
    receipt: {
      ...payload,
      receipt_id: receiptId,
      signature: {
        alg: "Ed25519",
        public_key: publicKey,
        value: toBase64Url(signature),
      },
    },
  };
}

describe("execution receipt verification", () => {
  it("canonicalizes with sorted keys and no whitespace", () => {
    expect(canonicalize({ b: 2, a: { d: 4, c: 3 } })).toBe(
      '{"a":{"c":3,"d":4},"b":2}',
    );
  });

  it("accepts a valid Ed25519 receipt with the pinned key", async () => {
    const { receipt, publicKey } = await signedReceipt();
    const result = await verifyExecutionReceipt(receipt, publicKey, KEY_ID);
    expect(result).toEqual({ valid: true, reason: "Signature valid." });
  });

  it("rejects a changed amount", async () => {
    const { receipt, publicKey } = await signedReceipt();
    const result = await verifyExecutionReceipt(
      tamperAmount(receipt),
      publicKey,
      KEY_ID,
    );
    expect(result.valid).toBe(false);
  });

  it("rejects a different pinned key", async () => {
    const { receipt } = await signedReceipt();
    const other = nacl.sign.keyPair();
    const result = await verifyExecutionReceipt(
      receipt,
      toBase64Url(other.publicKey),
      KEY_ID,
    );
    expect(result.valid).toBe(false);
  });

  it("rejects a different key id", async () => {
    const { receipt, publicKey } = await signedReceipt();
    const result = await verifyExecutionReceipt(receipt, publicKey, "other-key");
    expect(result.valid).toBe(false);
  });

  it("rejects a changed receipt id", async () => {
    const { receipt, publicKey } = await signedReceipt();
    const result = await verifyExecutionReceipt(
      { ...receipt, receipt_id: "sha256:00" },
      publicKey,
      KEY_ID,
    );
    expect(result.valid).toBe(false);
  });

  it("rejects a non-Ed25519 algorithm", async () => {
    const { receipt, publicKey } = await signedReceipt();
    const result = await verifyExecutionReceipt(
      { ...receipt, signature: { ...receipt.signature, alg: "HMAC" } },
      publicKey,
      KEY_ID,
    );
    expect(result.valid).toBe(false);
  });
});
