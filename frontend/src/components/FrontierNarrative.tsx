import { FRONTIER_INVARIANTS } from "../proof-data";

export function FrontierNarrative() {
  return (
    <section
      id="frontier-narrative"
      aria-labelledby="frontier-narrative-heading"
      className="rounded-2xl border border-cream/10 bg-cream/[0.02] p-6 sm:p-8 backdrop-blur"
    >
      <div className="mb-6">
        <p className="font-mono text-xs uppercase tracking-widest text-mint">
          Frontier Architecture
        </p>
        <h2
          id="frontier-narrative-heading"
          className="mt-2 font-display text-2xl sm:text-3xl font-light text-cream"
        >
          Post-execution refusal and cryptographic receipts
        </h2>
        <p className="mt-2 max-w-2xl text-xs sm:text-sm text-cream/70 leading-relaxed">
          Chatbot words are not money. Unlike pre-send prompt filters or
          retrospective tone QA, Settleye operates post-execution directly
          against financial ledger state with four foundational security
          invariants.
        </p>
      </div>

      {/* 4 Core Invariants */}
      <div className="grid gap-4 sm:grid-cols-2 mb-6">
        {FRONTIER_INVARIANTS.map((inv) => (
          <div
            key={inv.id}
            className="flex flex-col justify-between rounded-xl border border-cream/10 bg-cream/[0.03] p-5 hover:border-mint/30 transition-colors"
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-mint/15 font-mono text-xs font-bold text-mint">
                  {inv.number}
                </span>
                <span className="font-mono text-[11px] uppercase tracking-wider text-cream/60">
                  {inv.mechanism}
                </span>
              </div>
              <h3 className="mt-3 font-display text-base font-medium text-cream">
                {inv.title}
              </h3>
              <p className="mt-2 text-xs text-cream/70 leading-relaxed">
                {inv.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Cryptographic Execution Receipt Callout */}
      <div className="rounded-xl border border-cream/15 bg-cream/[0.03] p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cream/10 pb-4">
          <div>
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-mint">
              Two-Party Cryptographic Receipt Layer
            </span>
            <p className="mt-1 text-xs text-cream/80">
              RFC 8785 Canonical JSON &middot; Ed25519 Dual Signatures &middot; In-Browser Web Crypto Verification
            </p>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="rounded bg-mint/15 px-2 py-0.5 text-mint border border-mint/30">
              Issuer: Ed25519
            </span>
            <span className="rounded bg-mint/15 px-2 py-0.5 text-mint border border-mint/30">
              Merchant: Countersigned
            </span>
          </div>
        </div>

        <p className="mt-4 text-xs text-cream/75 leading-relaxed">
          Every remediation produces a tamper-evident audit receipt binding the transcript SHA-256, extracted promise, ledger state, idempotency key, and settlement status. The interactive verifier below in the Exception Inbox validates signatures locally in the browser using pinned keys. Altering any amount or order ID invalidates the signature immediately.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-4 text-xs">
          <a
            href="https://github.com/8-BitRhyon/settleye/blob/main/docs/receipt-spec.md"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-mint hover:underline"
          >
            View RFC 8785 receipt specification &rarr;
          </a>
          <span className="text-cream/30">&middot;</span>
          <a
            href="#inbox"
            className="font-mono text-cream/80 hover:text-cream hover:underline"
          >
            Try live tamper demo in Exception Inbox &uarr;
          </a>
        </div>
      </div>
    </section>
  );
}

export default FrontierNarrative;
