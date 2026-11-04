import { sha256 } from "@noble/hashes/sha2.js";
import * as nacl from "tweetnacl";

/** A portable, signed proof that Settleye observed and remediated a promise. */
export interface ExecutionReceipt {
  version: number;
  receipt_id: string;
  issued_at: string;
  issuer: { name: string; key_id: string };
  agent: { model_id: string };
  transcript: { sha256: string; turns: number };
  promise: {
    action: string;
    order_id: string | null;
    amount: string;
    target_system: string;
    terminal_status: string;
    evidence_span: string;
  };
  ledger: {
    system: string;
    order_id: string | null;
    shortfall_usd: string;
    summary: string;
    checked_at: string;
  };
  remediation: {
    idempotency_key: string;
    amount_usd: string;
    status: string;
  };
  signature: { alg: string; public_key: string; value: string };
  countersignatures?: Countersignature[];
}

/** A second party's acknowledgement of an issuer receipt. */
export interface Countersignature {
  role: "merchant";
  key_id: string;
  alg: string;
  public_key: string;
  acknowledged_at: string;
  value: string;
}

export interface ReceiptVerification {
  valid: boolean;
  reason: string;
}

export type MerchantStatus = "none" | "valid" | "invalid";

export interface MerchantVerification {
  status: MerchantStatus;
  key_id?: string;
  reason: string;
}

export interface TwoPartyVerification {
  issuer: ReceiptVerification;
  merchant: MerchantVerification;
  /** Issuer valid and no merchant signature is invalid. Missing is provisional. */
  valid: boolean;
}

/** Deterministic JSON: sorted keys, no whitespace, UTF-8. Matches Python. */
export function canonicalize(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalize).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const entries = Object.keys(record)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalize(record[key])}`);
    return `{${entries.join(",")}}`;
  }
  return JSON.stringify(value);
}

export function payloadForSigning(
  receipt: ExecutionReceipt,
): Record<string, unknown> {
  const payload: Record<string, unknown> = { ...receipt };
  delete payload.receipt_id;
  delete payload.signature;
  delete payload.countersignatures;
  return payload;
}

/** The bytes a merchant signs: identity, role, key, and acknowledgement time. */
export function countersignMessage(
  receiptId: string,
  keyId: string,
  acknowledgedAt: string,
): Uint8Array {
  const message = canonicalize({
    receipt_id: receiptId,
    role: "merchant",
    key_id: keyId,
    acknowledged_at: acknowledgedAt,
  });
  return new TextEncoder().encode(message);
}

export function sha256Hex(bytes: Uint8Array): string {
  return Array.from(sha256(bytes))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function base64UrlToBytes(value: string): Uint8Array {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  return Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
}

export function toBase64Url(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export async function verifyExecutionReceipt(
  receipt: ExecutionReceipt,
  pinnedPublicKey: string,
  pinnedKeyId: string,
): Promise<ReceiptVerification> {
  if (receipt.signature.alg !== "Ed25519") {
    return { valid: false, reason: "Unsupported signature algorithm." };
  }
  if (receipt.issuer.key_id !== pinnedKeyId) {
    return { valid: false, reason: "Issuer key id is not pinned." };
  }
  if (receipt.signature.public_key !== pinnedPublicKey) {
    return { valid: false, reason: "Receipt public key does not match the pinned key." };
  }

  const message = new TextEncoder().encode(
    canonicalize(payloadForSigning(receipt)),
  );
  const expectedId = `sha256:${sha256Hex(message)}`;
  if (receipt.receipt_id !== expectedId) {
    return { valid: false, reason: "Receipt id does not match the payload." };
  }

  const signature = base64UrlToBytes(receipt.signature.value);
  const publicKey = base64UrlToBytes(pinnedPublicKey);
  if (!nacl.sign.detached.verify(message, signature, publicKey)) {
    return { valid: false, reason: "Signature does not match the payload." };
  }
  return { valid: true, reason: "Signature valid." };
}

/**
 * Verify every merchant countersignature present. Missing is a provisional
 * state, not a failure. Any malformed or invalid present signature fails.
 */
export function verifyMerchantCountersignatures(
  receipt: ExecutionReceipt,
  merchantPublicKey: string,
  merchantKeyId: string,
): MerchantVerification {
  const signatures = receipt.countersignatures ?? [];
  if (signatures.length === 0) {
    return { status: "none", reason: "No merchant signature yet." };
  }
  if (merchantPublicKey === "" || merchantKeyId === "") {
    return {
      status: "invalid",
      key_id: signatures[0]?.key_id,
      reason: "Merchant key is not pinned.",
    };
  }

  for (const entry of signatures) {
    if (
      entry.role !== "merchant" ||
      entry.alg !== "Ed25519" ||
      typeof entry.key_id !== "string" ||
      typeof entry.public_key !== "string" ||
      typeof entry.acknowledged_at !== "string" ||
      typeof entry.value !== "string"
    ) {
      return {
        status: "invalid",
        key_id: entry.key_id,
        reason: "Malformed merchant signature.",
      };
    }
    if (entry.key_id !== merchantKeyId) {
      return {
        status: "invalid",
        key_id: entry.key_id,
        reason: "Merchant key id is not pinned.",
      };
    }
    if (entry.public_key !== merchantPublicKey) {
      return {
        status: "invalid",
        key_id: entry.key_id,
        reason: "Merchant public key does not match the pinned key.",
      };
    }
    try {
      const message = countersignMessage(
        receipt.receipt_id,
        entry.key_id,
        entry.acknowledged_at,
      );
      const signature = base64UrlToBytes(entry.value);
      const publicKey = base64UrlToBytes(merchantPublicKey);
      if (!nacl.sign.detached.verify(message, signature, publicKey)) {
        return {
          status: "invalid",
          key_id: entry.key_id,
          reason: "Merchant signature does not match the acknowledgement.",
        };
      }
    } catch {
      return {
        status: "invalid",
        key_id: entry.key_id,
        reason: "Malformed merchant signature.",
      };
    }
  }

  return {
    status: "valid",
    key_id: signatures[0]?.key_id,
    reason: "Merchant countersigned.",
  };
}

/** Issuer attribution plus merchant acknowledgement, in one result. */
export async function verifyTwoPartyReceipt(
  receipt: ExecutionReceipt,
  issuerPublicKey: string,
  issuerKeyId: string,
  merchantPublicKey: string,
  merchantKeyId: string,
): Promise<TwoPartyVerification> {
  const issuer = await verifyExecutionReceipt(
    receipt,
    issuerPublicKey,
    issuerKeyId,
  );
  const merchant = verifyMerchantCountersignatures(
    receipt,
    merchantPublicKey,
    merchantKeyId,
  );
  return {
    issuer,
    merchant,
    valid: issuer.valid && merchant.status !== "invalid",
  };
}

/** A demonstration copy with one amount digit changed; the signature stays. */
export function tamperAmount(receipt: ExecutionReceipt): ExecutionReceipt {
  const copy = JSON.parse(JSON.stringify(receipt)) as ExecutionReceipt;
  copy.promise.amount = copy.promise.amount === "45.00" ? "46.00" : "45.00";
  return copy;
}
