/** Pure display mapping for the two-signature receipt card. No DOM. */

import type { ReceiptKeyRecord } from "./api";
import type { ExecutionReceipt, TwoPartyVerification } from "./receipt";

export type ReceiptRowKind = "valid" | "neutral" | "invalid";

export interface ReceiptRowDisplay {
  kind: ReceiptRowKind;
  title: string;
  detail: string;
}

export interface ReceiptCardDisplay {
  issuer: ReceiptRowDisplay;
  merchant: ReceiptRowDisplay;
  /** Issuer valid and no merchant signature invalid. Missing is provisional. */
  trusted: boolean;
}

export const MERCHANT_PENDING_DETAIL =
  "Issuer only; merchant acceptance pending.";

/**
 * First published key with active status, or null when no key can
 * attribute a live receipt in this browser. Never throws.
 */
/**
 * Select the registry record that signed a receipt. Active and retired keys
 * are acceptable; a revoked key is not. The key id must match exactly, so a
 * rotation cannot make an old receipt look like a new-key receipt.
 */
export function selectIssuerKey(
  keys: ReceiptKeyRecord[] | null | undefined,
  keyId: string,
): ReceiptKeyRecord | null {
  if (keys === null || keys === undefined) return null;
  const record = keys.find((candidate) => candidate.key_id === keyId);
  if (record === undefined || record.status === "revoked") return null;
  return record;
}

export function selectActiveIssuerKey(
  keys: ReceiptKeyRecord[] | null | undefined,
): ReceiptKeyRecord | null {
  if (keys === null || keys === undefined) return null;
  return keys.find((key) => key.status === "active") ?? null;
}

/**
 * Map a two-party verification to card rows. Returns null when there is
 * nothing to show yet (missing live receipt, or verification still running).
 * A merchant row is never green when the issuer is invalid.
 */
export function describeReceiptCard(
  receipt: ExecutionReceipt | null | undefined,
  verification: TwoPartyVerification | null,
): ReceiptCardDisplay | null {
  if (receipt === null || receipt === undefined || verification === null) {
    return null;
  }
  const issuer: ReceiptRowDisplay = verification.issuer.valid
    ? {
        kind: "valid",
        title: "Issuer signature valid",
        detail: receipt.issuer.key_id,
      }
    : {
        kind: "invalid",
        title: "Issuer signature invalid",
        detail: verification.issuer.reason,
      };
  let merchant: ReceiptRowDisplay;
  if (verification.merchant.status === "none") {
    merchant = {
      kind: "neutral",
      title: "No merchant signature yet",
      detail: MERCHANT_PENDING_DETAIL,
    };
  } else if (
    verification.merchant.status === "valid" &&
    verification.issuer.valid
  ) {
    merchant = {
      kind: "valid",
      title: "Merchant countersigned",
      detail: verification.merchant.key_id ?? "",
    };
  } else if (verification.merchant.status === "valid") {
    merchant = {
      kind: "invalid",
      title: "Merchant signature invalid",
      detail:
        "Issuer signature is invalid, so merchant acceptance cannot be trusted.",
    };
  } else {
    merchant = {
      kind: "invalid",
      title: "Merchant signature invalid",
      detail: verification.merchant.reason,
    };
  }
  return { issuer, merchant, trusted: verification.valid };
}
