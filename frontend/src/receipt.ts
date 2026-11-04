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
}

export interface ReceiptVerification {
  valid: boolean;
  reason: string;
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
  return payload;
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

/** A demonstration copy with one amount digit changed; the signature stays. */
export function tamperAmount(receipt: ExecutionReceipt): ExecutionReceipt {
  const copy = JSON.parse(JSON.stringify(receipt)) as ExecutionReceipt;
  copy.promise.amount = copy.promise.amount === "45.00" ? "46.00" : "45.00";
  return copy;
}
