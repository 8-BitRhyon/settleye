/** Typed client for the Settleye API. Base URL comes from the environment. */

import type { ExecutionReceipt } from "./receipt";

const BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export interface PromiseEntity {
  action: string;
  amount: number | null;
  order_id: string | null;
  target_system: string;
  asserted_state: string;
  confidence: number;
  evidence_span: string;
}

export interface DriftResult {
  promise: PromiseEntity;
  verdict: "verified" | "drift" | "unverifiable" | "not_binding";
  ledger_summary: string;
  amount_at_risk_usd: number;
}

export interface AuditReport {
  promises: PromiseEntity[];
  results: DriftResult[];
  drifts: DriftResult[];
  total_at_risk_usd: number;
  verdict: "verified_green" | "drift_found";
  transcript_sha256?: string;
  transcript_turns?: number;
  audited_at?: string;
}

export interface RemediationReceipt {
  idempotency_key: string;
  promise: PromiseEntity;
  amount_usd: number;
  status: "executed" | "already_executed";
  receipt?: ExecutionReceipt | null;
}

/** Audit context forwarded so a live remediation can bind a signed receipt. */
export interface RemediateContext {
  transcript_sha256?: string;
  transcript_turns?: number;
  audited_at?: string;
  ledger_summary?: string;
}

export interface ValueSummary {
  total_recovered_usd: number;
  disputes_avoided: number;
  dispute_cost_avoided_usd: number;
  grand_total_usd: number;
}

export interface ReceiptKeyRecord {
  key_id: string;
  public_key: string;
  status: "active" | "retired" | "revoked";
  created_at?: string;
  retired_at?: string | null;
  revoked_at?: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => (body as { detail?: string }).detail ?? response.statusText)
      .catch(() => response.statusText);
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function auditTranscript(transcript: string): Promise<AuditReport> {
  return request<AuditReport>("/audit", {
    method: "POST",
    body: JSON.stringify({ transcript }),
  });
}

export function remediate(
  promise: PromiseEntity,
  amount_usd: number,
  context?: RemediateContext,
): Promise<RemediationReceipt> {
  return request<RemediationReceipt>("/remediate", {
    method: "POST",
    body: JSON.stringify({ promise, amount_usd, ...context }),
  });
}

export function fetchValue(): Promise<ValueSummary> {
  return request<ValueSummary>("/value");
}

/** Public issuer keys only. Never contains private material. */
export function fetchReceiptKeys(): Promise<ReceiptKeyRecord[]> {
  return request<ReceiptKeyRecord[]>("/receipt/keys");
}

export async function explainDrift(
  promise: PromiseEntity,
  ledger_summary: string,
  amount_usd: number,
): Promise<string> {
  const body = await request<{ explanation: string }>("/explain", {
    method: "POST",
    body: JSON.stringify({ promise, ledger_summary, amount_usd }),
  });
  return body.explanation;
}
