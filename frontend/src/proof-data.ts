export interface ProofTier {
  id: string;
  tierNumber: number;
  badge: string;
  title: string;
  primaryMetric: string;
  summary: string;
  description: string;
  highlights: string[];
}

export interface FleetVolumeTier {
  name: string;
  monthlyTickets: number;
  monthlyTicketsStr: string;
  annualTickets: number;
  monthlyDrifts: number;
  annualDrifts: number;
  monthlyDirectCaught: number;
  annualDirectCaught: number;
  annualDirectCaughtStr: string;
  disputePreventionAnnual: number;
  disputePreventionAnnualStr: string;
  chargebackSavingsAnnual: number;
  chargebackSavingsAnnualStr: string;
  totalAnnualValue: number;
  totalAnnualValueStr: string;
  highlight?: boolean;
}

export interface MicrobenchmarkStats {
  throughputStr: string;
  throughputMin: number;
  p50LatencyStr: string;
  p95LatencyStr: string;
  p99LatencyStr: string;
  batchTranscripts: number;
  totalWallTimeStr: string;
  driftsDetected: number;
  liabilityCaught: number;
  liabilityCaughtStr: string;
  inferenceOverheadPercent: string;
}

export interface AbcdGroundingParam {
  key: string;
  name: string;
  valueStr: string;
  numericValue: number;
  unit: string;
  description: string;
  source: string;
}

export interface FrontierInvariant {
  id: string;
  number: number;
  title: string;
  mechanism: string;
  description: string;
}

export const PROOF_TIERS: ProofTier[] = [
  {
    id: "tier-1",
    tierNumber: 1,
    badge: "Tier 1: Live, Read-Only",
    title: "Real Shopify dev store",
    primaryMetric: "$44.00",
    summary: "live read-only dev-store proof: $44.00 at risk in 4.07s on order #1001",
    description:
      "Audited live in read-only mode against Shopify Admin GraphQL on test-mode order #1001. The customer was promised a $50.00 refund on a damaged jacket, but the store ledger only settled $6.00. Settleye detected the $44.00 shortfall in 4.07 seconds. One order, no money moved.",
    highlights: [
      "Live, read-only audit against the Shopify GraphQL API",
      "Caught a $44.00 shortfall on one test-mode order ($6 settled of $50 promised)",
      "Strict credential boundary: secret app tokens (shpss_) refused locally; only short-lived OAuth tokens accepted",
      "No money moved; one order, not a fleet sample",
    ],
  },
  {
    id: "tier-2",
    tierNumber: 2,
    badge: "Tier 2: Labeled Eval Replay",
    title: "Ground-truth eval replay",
    primaryMetric: "12 / 12",
    summary: "verdicts correct across labeled adversarial benchmark",
    description:
      "Deterministic eval suite across 12 adversarial support tickets. 12/12 verdicts correct, 11/12 exact entity extractions, 0 false clears (0/8 binding missed), and $285.50 unledgered liability caught across 5 drifts.",
    highlights: [
      "12 of 12 verdicts correct (100% verdict accuracy) on complex transcripts",
      "0 false clears: zero missed binding customer commitments",
      "0 of 4 non-binding promises reached drift",
      "0 hallucinated orders vs Gemini 4 Argon (Argon fabricated non-existent order EVAL09)",
      "$285.50 unledgered liability caught across 5 drifts",
    ],
  },
  {
    id: "tier-3",
    tierNumber: 3,
    badge: "Tier 3: Modeled, Not Measured",
    title: "Modeled fleet exposure",
    primaryMetric: "$124K to $12.5M",
    summary: "modeled annual exposure protected from 10k to 1M tickets per month",
    description:
      "Modeled projections built from stated assumptions grounded in the ABCD retail dialogue corpus, covering drift volume, direct exposure, dispute exposure, and card network chargeback fees. This is a projection, not a guarantee or a merchant result.",
    highlights: [
      "Mid-Market (10k tickets/mo): $124,328.40 modeled annual exposure protected",
      "Large E-Commerce (100k tickets/mo): $1,256,604.96 modeled annual exposure protected",
      "Global Enterprise (1M tickets/mo): $12,557,168.40 modeled annual exposure protected",
      "Assumptions: 10.6% refund intent, 66.7% binding commitment, 4.0% execution failure. The 4.0% rate is an assumption, not a merchant measurement",
      "Pipeline micro-benchmark: about 95k to 122k audits/sec, p50 about 0.009 ms, canned extraction and mock ledger, no model calls",
    ],
  },
];

export const FLEET_VOLUME_TIERS: FleetVolumeTier[] = [
  {
    name: "Mid-Market",
    monthlyTickets: 10000,
    monthlyTicketsStr: "10,000/mo",
    annualTickets: 120000,
    monthlyDrifts: 28,
    annualDrifts: 336,
    monthlyDirectCaught: 1470.0,
    annualDirectCaught: 17640.0,
    annualDirectCaughtStr: "$17,640.00",
    disputePreventionAnnual: 81320.4,
    disputePreventionAnnualStr: "$81,320.40",
    chargebackSavingsAnnual: 43008.0,
    chargebackSavingsAnnualStr: "$43,008.00",
    totalAnnualValue: 124328.4,
    totalAnnualValueStr: "$124,328.40",
    highlight: false,
  },
  {
    name: "Large E-Commerce",
    monthlyTickets: 100000,
    monthlyTicketsStr: "100,000/mo",
    annualTickets: 1200000,
    monthlyDrifts: 283,
    annualDrifts: 3396,
    monthlyDirectCaught: 14857.5,
    annualDirectCaught: 178290.0,
    annualDirectCaughtStr: "$178,290.00",
    disputePreventionAnnual: 821916.96,
    disputePreventionAnnualStr: "$821,916.96",
    chargebackSavingsAnnual: 434688.0,
    chargebackSavingsAnnualStr: "$434,688.00",
    totalAnnualValue: 1256604.96,
    totalAnnualValueStr: "$1,256,604.96",
    highlight: false,
  },
  {
    name: "Global Enterprise",
    monthlyTickets: 1000000,
    monthlyTicketsStr: "1,000,000/mo",
    annualTickets: 12000000,
    monthlyDrifts: 2828,
    annualDrifts: 33936,
    monthlyDirectCaught: 148470.0,
    annualDirectCaught: 1781640.0,
    annualDirectCaughtStr: "$1,781,640.00",
    disputePreventionAnnual: 8213360.4,
    disputePreventionAnnualStr: "$8,213,360.40",
    chargebackSavingsAnnual: 4343808.0,
    chargebackSavingsAnnualStr: "$4,343,808.00",
    totalAnnualValue: 12557168.4,
    totalAnnualValueStr: "$12,557,168.40",
    highlight: true,
  },
];

export const MICROBENCHMARK_STATS: MicrobenchmarkStats = {
  throughputStr: "about 95,000 to 122,000 transcripts/sec",
  throughputMin: 95000,
  p50LatencyStr: "about 0.009 ms",
  p95LatencyStr: "about 0.010 ms",
  p99LatencyStr: "about 0.013 ms",
  batchTranscripts: 1000,
  totalWallTimeStr: "0.008s to 0.011s",
  driftsDetected: 350,
  liabilityCaught: 27000.0,
  liabilityCaughtStr: "$27,000.00",
  inferenceOverheadPercent: "pipeline only",
};

export const ABCD_GROUNDING_PARAMS: AbcdGroundingParam[] = [
  {
    key: "refund-intent",
    name: "Refund Intent Rate",
    valueStr: "10.6%",
    numericValue: 0.106,
    unit: "%",
    description: "Retail support ticket baseline from the ABCD dialogue corpus.",
    source: "ABCD retail dialogue corpus empirical frequency",
  },
  {
    key: "commitment-rate",
    name: "Binding Commitment Rate",
    valueStr: "66.7%",
    numericValue: 0.667,
    unit: "%",
    description:
      "Proportion of refund inquiries resulting in unconditional agent commitments.",
    source: "ABCD dialogue commitment analysis",
  },
  {
    key: "drift-rate",
    name: "Execution Failure Drift",
    valueStr: "4.0%",
    numericValue: 0.04,
    unit: "%",
    description:
      "Agent tool-call execution failure or silent payment rail omission rate.",
    source: "Assumption used in the projection model, not a merchant measurement",
  },
  {
    key: "avg-refund",
    name: "Average Refund Commitment",
    valueStr: "$52.50",
    numericValue: 52.5,
    unit: "USD",
    description: "Mean unfulfilled refund amount modeled per drift incident.",
    source: "Assumption used in the projection model",
  },
  {
    key: "dispute-multiplier",
    name: "Dispute Cost Multiplier",
    valueStr: "4.61x",
    numericValue: 4.61,
    unit: "ratio",
    description:
      "LexisNexis true cost of fraud and disputes (goods, labor, investigation, churn).",
    source: "LexisNexis 2025 True Cost of Fraud Study (N=569)",
  },
  {
    key: "chargeback-fee",
    name: "Chargeback Admin Fee",
    valueStr: "$128.00",
    numericValue: 128.0,
    unit: "USD",
    description:
      "Standard Mastercard/card network dispute filing fee per formal merchant dispute.",
    source: "Mastercard Card Brand Dispute Schedule",
  },
];

export const FRONTIER_INVARIANTS: FrontierInvariant[] = [
  {
    id: "inv-1",
    number: 1,
    title: "Server-Side Ledger Reconcile & Shortfall Clamping",
    mechanism: "Post-execution audit against Shopify and Stripe rails",
    description:
      "Unlike pre-send prompt filters or retrospective tone QA, Settleye operates post-execution directly against financial ledgers. Unfulfilled refund amounts are clamped strictly to unledgered shortfall ($44.00 on order #1001 when $6.00 settled of $50.00 promise).",
  },
  {
    id: "inv-2",
    number: 2,
    title: "Original Charge Ceilings & Non-Binding Filtering",
    mechanism: "Financial bounds enforcement (HTTP 422 refusal)",
    description:
      "Refuses refund requests exceeding the original captured transaction amount with HTTP 422, halting balance drain attacks. Gating rules enforce 100% refutation on conditional, retracted, and info-only promises with zero ledger touches.",
  },
  {
    id: "inv-3",
    number: 3,
    title: "Append-Only Fsync Ledger & Idempotent Settlement",
    mechanism: "Deterministic JSONL store keyed by action:order_id:rail:amount",
    description:
      "Remediation actions are atomically journaled to an append-only store with immediate fsync. Idempotent retries move exactly $0.00 and return the existing signed execution receipt.",
  },
  {
    id: "inv-4",
    number: 4,
    title: "Two-Party Cryptographic Receipts & Browser Verifier",
    mechanism: "RFC 8785 canonical JSON + Ed25519 dual signatures",
    description:
      "Emits portable tamper-evident receipts signed by the Settleye issuer key and countersigned by the merchant key. Pinned Web Crypto verifier validates signatures locally in the browser; any single-digit modification invalidates the receipt.",
  },
];
