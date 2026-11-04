import {
  ABCD_GROUNDING_PARAMS,
  FLEET_VOLUME_TIERS,
  MICROBENCHMARK_STATS,
} from "../proof-data";

export function FleetImpact() {
  return (
    <section
      id="fleet-impact"
      aria-labelledby="fleet-impact-heading"
      className="rounded-2xl border border-cream/10 bg-cream/[0.02] p-6 sm:p-8 backdrop-blur"
    >
      <div className="mb-6">
        <p className="font-mono text-xs uppercase tracking-widest text-mint">
          Modeled fleet exposure
        </p>
        <h2
          id="fleet-impact-heading"
          className="mt-2 font-display text-2xl sm:text-3xl font-light text-cream"
        >
          Modeled annual exposure across ticket volume tiers
        </h2>
        <p className="mt-2 max-w-2xl text-xs sm:text-sm text-cream/70 leading-relaxed">
          Modeled annual exposure from stated assumptions grounded in the retail
          ABCD dialogue corpus. This is a projection, not a guarantee or a
          merchant result.
        </p>
      </div>

      {/* Fast-scanning tier cards */}
      <div className="grid gap-4 sm:grid-cols-3 mb-6">
        {FLEET_VOLUME_TIERS.map((tier) => (
          <div
            key={tier.name}
            className={`rounded-xl border p-4 transition-colors ${
              tier.highlight
                ? "border-mint/40 bg-mint/[0.06]"
                : "border-cream/10 bg-cream/[0.03]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold text-mint">
                {tier.name}
              </span>
              <span className="font-mono text-[11px] text-cream/60">
                {tier.monthlyTicketsStr}
              </span>
            </div>
            <p className="mt-2 font-display text-2xl font-light text-cream">
              {tier.totalAnnualValueStr}
            </p>
            <p className="mt-1 text-[11px] text-cream/65">
              Modeled annual exposure protected ({tier.annualDrifts.toLocaleString()} drifts/yr)
            </p>
            <div className="mt-3 border-t border-cream/10 pt-2 text-[11px] text-cream/75 space-y-1">
              <div className="flex justify-between">
                <span>Direct exposure:</span>
                <span className="font-mono text-cream/90">{tier.annualDirectCaughtStr}</span>
              </div>
              <div className="flex justify-between">
                <span>Dispute exposure (4.61x):</span>
                <span className="font-mono text-cream/90">{tier.disputePreventionAnnualStr}</span>
              </div>
              <div className="flex justify-between">
                <span>Chargeback fees:</span>
                <span className="font-mono text-cream/90">{tier.chargebackSavingsAnnualStr}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 7-column Comparison Table */}
      <div className="overflow-x-auto rounded-xl border border-cream/10 bg-cream/[0.02]">
        <table className="w-full text-left text-xs text-cream/80 min-w-[760px]">
          <thead className="border-b border-cream/10 bg-cream/[0.04] font-mono text-[11px] text-mint uppercase tracking-wider">
            <tr>
              <th scope="col" className="px-4 py-3">Volume Tier</th>
              <th scope="col" className="px-4 py-3">Monthly Tickets</th>
              <th scope="col" className="px-4 py-3">Annual Drifts</th>
              <th scope="col" className="px-4 py-3">Direct Exposure</th>
              <th scope="col" className="px-4 py-3">Dispute Exposure (4.61x)</th>
              <th scope="col" className="px-4 py-3">Chargeback Fees ($128)</th>
              <th scope="col" className="px-4 py-3">Modeled Annual Exposure</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-cream/5 font-mono text-xs">
            {FLEET_VOLUME_TIERS.map((tier) => (
              <tr
                key={tier.name}
                className={
                  tier.highlight
                    ? "bg-mint/[0.08] text-cream font-medium"
                    : "hover:bg-cream/[0.02]"
                }
              >
                <td className="px-4 py-3 font-sans font-semibold text-cream">
                  {tier.name}
                </td>
                <td className="px-4 py-3 text-cream/75">{tier.monthlyTicketsStr}</td>
                <td className="px-4 py-3 text-cream/75">
                  {tier.annualDrifts.toLocaleString()} drifts/yr
                </td>
                <td className="px-4 py-3 text-cream/90">{tier.annualDirectCaughtStr}</td>
                <td className="px-4 py-3 text-cream/90">{tier.disputePreventionAnnualStr}</td>
                <td className="px-4 py-3 text-cream/90">{tier.chargebackSavingsAnnualStr}</td>
                <td className="px-4 py-3 font-bold text-mint">
                  {tier.totalAnnualValueStr}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ABCD Dialogue Corpus Grounding Parameters */}
      <div className="mt-8 border-t border-cream/10 pt-6">
        <p className="font-mono text-xs uppercase tracking-wider text-mint mb-3">
          Model inputs and assumptions
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ABCD_GROUNDING_PARAMS.map((param) => (
            <div
              key={param.key}
              className="rounded-lg border border-cream/10 bg-cream/[0.03] p-3.5"
            >
              <p className="font-mono text-xl font-semibold text-cream">
                {param.valueStr}
              </p>
              <p className="mt-1 text-xs font-semibold text-cream/90">
                {param.name}
              </p>
              <p className="mt-1 text-[11px] text-cream/65 leading-relaxed">
                {param.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Daemon Audit Throughput Microbenchmark Banner */}
      <div className="mt-6 rounded-xl border border-mint/30 bg-mint/[0.06] p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-baseline gap-3">
            <span className="font-mono text-xl sm:text-2xl font-bold text-mint">
              {MICROBENCHMARK_STATS.throughputStr}
            </span>
            <span className="rounded border border-cream/15 bg-night/70 px-2 py-0.5 font-mono text-xs text-cream/80">
              p50: {MICROBENCHMARK_STATS.p50LatencyStr} &middot; p95: {MICROBENCHMARK_STATS.p95LatencyStr} &middot; p99: {MICROBENCHMARK_STATS.p99LatencyStr}
            </span>
          </div>
          <p className="mt-2 text-xs text-cream/75 max-w-2xl leading-relaxed">
            Pipeline micro-benchmark on {MICROBENCHMARK_STATS.batchTranscripts.toLocaleString()} canned transcripts against a mock ledger. No model or network calls. Model inference is seconds per transcript, not milliseconds.
          </p>
        </div>
        <div className="shrink-0">
          <a
            href="https://github.com/8-BitRhyon/settleye/blob/main/bench/fleet_benchmark.py"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-mono text-xs font-semibold text-mint hover:underline"
          >
            View benchmark script &rarr;
          </a>
        </div>
      </div>
    </section>
  );
}

export default FleetImpact;
