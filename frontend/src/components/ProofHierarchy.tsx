import { PROOF_TIERS } from "../proof-data";

export function ProofHierarchy() {
  return (
    <section
      id="proof-hierarchy"
      aria-labelledby="proof-hierarchy-heading"
      className="rounded-2xl border border-cream/10 bg-cream/[0.02] p-6 sm:p-8 backdrop-blur"
    >
      <div className="mb-6">
        <p className="font-mono text-xs uppercase tracking-widest text-mint">
          Three-tier proof
        </p>
        <h2
          id="proof-hierarchy-heading"
          className="mt-2 font-display text-2xl sm:text-3xl font-light text-cream"
        >
          Tier 1 is live. Tier 2 is labeled.{" "}
          <span className="italic text-mint">Tier 3 is modeled.</span>
        </h2>
        <p className="mt-2 max-w-2xl text-xs sm:text-sm text-cream/70 leading-relaxed">
          The first two tiers are measured on this build. The third is a
          projection from stated assumptions. We keep the border between them
          visible.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {PROOF_TIERS.map((tier) => (
          <article
            key={tier.id}
            className="flex flex-col justify-between rounded-xl border border-cream/10 bg-cream/[0.03] p-5 hover:border-mint/30 transition-colors"
          >
            <div>
              <div className="mb-3 inline-block rounded-full border border-mint/30 bg-mint/10 px-2.5 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wider text-mint">
                {tier.badge}
              </div>
              <h3 className="font-display text-lg text-cream font-medium">
                {tier.title}
              </h3>
              <p className="mt-3 font-display text-3xl font-light text-mint">
                {tier.primaryMetric}
              </p>
              <p className="mt-2 text-xs font-medium text-cream/90">
                {tier.summary}
              </p>
              <p className="mt-2 text-xs text-cream/70 leading-relaxed">
                {tier.description}
              </p>
            </div>

            <ul className="mt-5 space-y-2 border-t border-cream/10 pt-4 text-xs text-cream/75">
              {tier.highlights.map((highlight, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-mint font-bold" aria-hidden="true">
                    •
                  </span>
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

export default ProofHierarchy;
