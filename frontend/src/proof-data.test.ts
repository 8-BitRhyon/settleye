import { describe, expect, it } from "vitest";
import {
  ABCD_GROUNDING_PARAMS,
  FLEET_VOLUME_TIERS,
  FRONTIER_INVARIANTS,
  MICROBENCHMARK_STATS,
  PROOF_TIERS,
} from "./proof-data.ts";

describe("Three-Tier Proof Hierarchy Data", () => {
  it("contains exactly 3 structured proof tiers", () => {
    expect(PROOF_TIERS).toHaveLength(3);
    expect(PROOF_TIERS.map((t) => t.tierNumber)).toEqual([1, 2, 3]);
  });

  it("defines Tier 1 with live read-only dev-store proof", () => {
    const tier1 = PROOF_TIERS[0];
    expect(tier1.badge).toContain("Tier 1");
    expect(tier1.primaryMetric).toBe("$44.00");
    expect(tier1.description).toContain("order #1001");
    expect(tier1.description).toContain("4.07 seconds");
    expect(tier1.highlights.some((h) => h.includes("shpss_"))).toBe(true);
    expect(tier1.highlights.some((h) => h.includes("$6 settled"))).toBe(true);
  });

  it("defines Tier 2 with 12/12 eval replay and zero false clears", () => {
    const tier2 = PROOF_TIERS[1];
    expect(tier2.badge).toContain("Tier 2");
    expect(tier2.primaryMetric).toBe("12 / 12");
    expect(tier2.highlights.some((h) => h.includes("0 false clears"))).toBe(true);
    expect(tier2.highlights.some((h) => h.includes("Argon"))).toBe(true);
    expect(tier2.highlights.some((h) => h.includes("$285.50"))).toBe(true);
  });

  it("defines Tier 3 as a modeled projection", () => {
    const tier3 = PROOF_TIERS[2];
    expect(tier3.badge).toContain("Tier 3");
    expect(tier3.primaryMetric).toBe("$124K to $12.5M");
    expect(tier3.description).toContain("ABCD");
    expect(tier3.highlights.some((h) => h.includes("10.6%"))).toBe(true);
    expect(tier3.badge).toContain("Modeled");
    expect(tier3.highlights.some((h) => h.includes("95k to 122k"))).toBe(true);
    expect(tier3.highlights.some((h) => h.includes("assumption"))).toBe(true);
  });
});

describe("Enterprise Fleet Volume Tiers", () => {
  it("defines 3 volume tiers with exact financial metrics", () => {
    expect(FLEET_VOLUME_TIERS).toHaveLength(3);
    const [mid, large, global] = FLEET_VOLUME_TIERS;

    // Mid-Market (10k tickets/mo)
    expect(mid.name).toBe("Mid-Market");
    expect(mid.monthlyTickets).toBe(10000);
    expect(mid.annualDrifts).toBe(336);
    expect(mid.annualDirectCaught).toBe(17640.0);
    expect(mid.disputePreventionAnnual).toBe(81320.4);
    expect(mid.chargebackSavingsAnnual).toBe(43008.0);
    expect(mid.totalAnnualValue).toBe(124328.4);
    expect(mid.totalAnnualValueStr).toBe("$124,328.40");

    // Large E-Commerce (100k tickets/mo)
    expect(large.name).toBe("Large E-Commerce");
    expect(large.monthlyTickets).toBe(100000);
    expect(large.annualDrifts).toBe(3396);
    expect(large.annualDirectCaught).toBe(178290.0);
    expect(large.disputePreventionAnnual).toBe(821916.96);
    expect(large.chargebackSavingsAnnual).toBe(434688.0);
    expect(large.totalAnnualValue).toBe(1256604.96);
    expect(large.totalAnnualValueStr).toBe("$1,256,604.96");

    // Global Enterprise (1M tickets/mo)
    expect(global.name).toBe("Global Enterprise");
    expect(global.monthlyTickets).toBe(1000000);
    expect(global.annualDrifts).toBe(33936);
    expect(global.annualDirectCaught).toBe(1781640.0);
    expect(global.disputePreventionAnnual).toBe(8213360.4);
    expect(global.chargebackSavingsAnnual).toBe(4343808.0);
    expect(global.totalAnnualValue).toBe(12557168.4);
    expect(global.totalAnnualValueStr).toBe("$12,557,168.40");
  });

  it("verifies mathematical consistency of dispute and fee calculations", () => {
    for (const tier of FLEET_VOLUME_TIERS) {
      // Annual drifts = monthly drifts * 12
      expect(tier.annualDrifts).toBe(tier.monthlyDrifts * 12);

      // Monthly direct = monthly drifts * $52.50
      const expectedMonthlyDirect = Math.round(tier.monthlyDrifts * 52.5 * 100) / 100;
      expect(tier.monthlyDirectCaught).toBe(expectedMonthlyDirect);

      // Annual direct = monthly direct * 12
      const expectedAnnualDirect = Math.round(tier.monthlyDirectCaught * 12 * 100) / 100;
      expect(tier.annualDirectCaught).toBe(expectedAnnualDirect);

      // Dispute prevention = monthly direct * 4.61 * 12
      const monthlyDispute = Math.round(tier.monthlyDirectCaught * 4.61 * 100) / 100;
      const expectedAnnualDispute = Math.round(monthlyDispute * 12 * 100) / 100;
      expect(tier.disputePreventionAnnual).toBe(expectedAnnualDispute);

      // Chargeback savings = monthly drifts * $128 * 12
      const monthlyCb = Math.round(tier.monthlyDrifts * 128.0 * 100) / 100;
      const expectedAnnualCb = Math.round(monthlyCb * 12 * 100) / 100;
      expect(tier.chargebackSavingsAnnual).toBe(expectedAnnualCb);

      // Total annual value = disputePreventionAnnual + chargebackSavingsAnnual
      const expectedTotal = Math.round((tier.disputePreventionAnnual + tier.chargebackSavingsAnnual) * 100) / 100;
      expect(Math.abs(tier.totalAnnualValue - expectedTotal)).toBeLessThan(0.01);
    }
  });
});

describe("Pipeline Microbenchmark Stats", () => {
  it("verifies throughput and latency metrics", () => {
    expect(MICROBENCHMARK_STATS.throughputMin).toBeGreaterThanOrEqual(95000);
    expect(MICROBENCHMARK_STATS.throughputStr).toBe("about 95,000 to 122,000 transcripts/sec");
    expect(MICROBENCHMARK_STATS.p50LatencyStr).toBe("about 0.009 ms");
    expect(MICROBENCHMARK_STATS.batchTranscripts).toBe(1000);
  });
});

describe("ABCD Dialogue Corpus Grounding Parameters", () => {
  it("defines the 6 grounding parameters with verified values", () => {
    expect(ABCD_GROUNDING_PARAMS).toHaveLength(6);
    const paramMap = new Map(ABCD_GROUNDING_PARAMS.map((p) => [p.key, p]));

    expect(paramMap.get("refund-intent")?.valueStr).toBe("10.6%");
    expect(paramMap.get("commitment-rate")?.valueStr).toBe("66.7%");
    expect(paramMap.get("drift-rate")?.valueStr).toBe("4.0%");
    expect(paramMap.get("avg-refund")?.valueStr).toBe("$52.50");
    expect(paramMap.get("dispute-multiplier")?.valueStr).toBe("4.61x");
    expect(paramMap.get("chargeback-fee")?.valueStr).toBe("$128.00");
  });
});

describe("Frontier Invariants", () => {
  it("defines 4 core post-execution refusal invariants", () => {
    expect(FRONTIER_INVARIANTS).toHaveLength(4);
    const titles = FRONTIER_INVARIANTS.map((i) => i.title);
    expect(titles.some((t) => t.includes("Shortfall Clamping"))).toBe(true);
    expect(titles.some((t) => t.includes("Ceilings"))).toBe(true);
    expect(titles.some((t) => t.includes("Append-Only Fsync"))).toBe(true);
    expect(titles.some((t) => t.includes("Two-Party Cryptographic Receipts"))).toBe(true);
  });
});

describe("Style & Convention Compliance", () => {
  it("ensures zero em dashes (U+2014) exist in all exported proof-data structures", () => {
    const rawJson = JSON.stringify({
      PROOF_TIERS,
      FLEET_VOLUME_TIERS,
      MICROBENCHMARK_STATS,
      ABCD_GROUNDING_PARAMS,
      FRONTIER_INVARIANTS,
    });
    expect(rawJson).not.toContain("\u2014");
  });
});
