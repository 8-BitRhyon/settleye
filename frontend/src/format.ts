/** Pure display helpers for the exception inbox. No DOM, fully tested. */

export type Verdict = "verified" | "drift" | "unverifiable" | "not_binding";

export function formatUSD(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

export function verdictLabel(verdict: Verdict): string {
  switch (verdict) {
    case "verified":
      return "Verified";
    case "drift":
      return "State drift";
    case "unverifiable":
      return "Needs review";
    case "not_binding":
      return "Not binding";
  }
}

export function verdictClasses(verdict: Verdict): string {
  switch (verdict) {
    case "verified":
      return "pill pill-mint";
    case "drift":
      return "pill pill-red";
    case "unverifiable":
      return "pill pill-gold";
    case "not_binding":
      return "pill pill-dim";
  }
}

/** Placeholder shown while the API works, so the Audit tap always responds. */
export const AUDIT_LOADING_LABEL = "Auditing transcript…";

/** Draft transcript preloaded so judges see the failure case in one click. */
export const SAMPLE_PHANTOM_TRANSCRIPT =
  [
    "Customer: The jacket I ordered (order #992) arrived with a torn seam. I want a refund.",
    "Agent: I am sorry about the torn seam. I have processed a full $45 refund for order #992. It should appear on your statement within 5 to 10 business days.",
    "Customer: Great, thank you for sorting that out so fast.",
  ].join("\n") + "\n";
