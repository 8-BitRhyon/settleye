import { useCallback, useEffect, useRef, useState } from "react";
import {
  auditTranscript,
  explainDrift,
  fetchReceiptKeys,
  fetchValue,
  remediate,
  type AuditReport,
  type DriftResult,
  type ReceiptKeyRecord,
  type ValueSummary,
} from "./api";
import { EyeIcon, type EyeIconHandle } from "./components/EyeIcon";
import { isStaticDemo } from "./runtime";
import sampleReceipt from "./sample-receipt.json";
import { SAMPLE_KEY_ID, SAMPLE_PUBLIC_KEY } from "./sample-receipt-key";
import {
  SAMPLE_MERCHANT_KEY_ID,
  SAMPLE_MERCHANT_PUBLIC_KEY,
} from "./sample-receipt-merchant-key";
import type { ExecutionReceipt } from "./receipt";
import { selectIssuerKey } from "./receipt-display";
import ReceiptCard from "./ReceiptCard";
import ProofHierarchy from "./components/ProofHierarchy";
import FleetImpact from "./components/FleetImpact";
import FrontierNarrative from "./components/FrontierNarrative";
import {
  SAMPLE_AUDIT_RESPONSE,
  SAMPLE_EXPLANATION,
  additionalMovement,
  nextSampleReceipt,
  type SampleReceiptState,
} from "./sample";
import {
  AUDIT_LOADING_LABEL,
  SAMPLE_PHANTOM_TRANSCRIPT,
  formatUSD,
  verdictClasses,
  verdictLabel,
} from "./format";

type RemediateState = Record<string, "idle" | "sending" | "done" | string>;
type ExplainState = Record<string, string | undefined>;

const SIGNED_SAMPLE = sampleReceipt as ExecutionReceipt;

function DriftEye() {
  const ref = useRef<EyeIconHandle | null>(null);
  useEffect(() => {
    ref.current?.startAnimation();
  }, []);
  return <EyeIcon ref={ref} size={14} className="text-[#f0837f]" />;
}

export default function App() {
  const [transcript, setTranscript] = useState(SAMPLE_PHANTOM_TRANSCRIPT);
  const [report, setReport] = useState<AuditReport | null>(null);
  const [value, setValue] = useState<ValueSummary | null>(null);
  const [auditing, setAuditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fixes, setFixes] = useState<RemediateState>({});
  const [explanations, setExplanations] = useState<ExplainState>({});
  const [isSample, setIsSample] = useState(() => {
    if (typeof window === "undefined") return false;
    return new URLSearchParams(window.location.search).get("sample") === "1";
  });
  const staticDemo =
    typeof window !== "undefined" &&
    isStaticDemo(window.location.hostname, import.meta.env.VITE_API_URL);
  const [sampleReceipt, setSampleReceipt] = useState<SampleReceiptState | null>(null);
  const [sampleDrift, setSampleDrift] = useState<DriftResult | null>(null);
  const [liveReceipt, setLiveReceipt] = useState<
    ExecutionReceipt | null | undefined
  >(undefined);
  const [liveReceiptStatus, setLiveReceiptStatus] = useState<string | null>(
    null,
  );
  const [liveIssuerKeys, setLiveIssuerKeys] = useState<
    ReceiptKeyRecord[] | null | undefined
  >(undefined);

  // Deep link from the landing page: ?sample=1 opens the recorded audit
  // immediately so a visitor sees a drift without a single click.
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (new URLSearchParams(window.location.search).get("sample") === "1") {
      setReport(SAMPLE_AUDIT_RESPONSE);
      setIsSample(true);
    }
  }, []);

  const refreshValue = useCallback(() => {
    fetchValue().then(setValue).catch(() => {});
  }, []);

  useEffect(() => {
    if (isSample || staticDemo) return;
    refreshValue();
  }, [isSample, staticDemo, refreshValue]);

  useEffect(() => {
    if (isSample || staticDemo) {
      setLiveIssuerKeys(null);
      return;
    }
    let cancelled = false;
    fetchReceiptKeys()
      .then((keys) => {
        if (!cancelled) setLiveIssuerKeys(keys);
      })
      .catch(() => {
        if (!cancelled) setLiveIssuerKeys(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isSample, staticDemo, liveReceipt?.receipt_id]);

  async function onAudit() {
    setAuditing(true);
    setError(null);
    setIsSample(false);
    setSampleReceipt(null);
    setSampleDrift(null);
    setLiveReceipt(undefined);
    setLiveReceiptStatus(null);
    try {
      const next = await auditTranscript(transcript);
      setReport(next);
      setFixes({});
      setExplanations({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audit failed.");
    } finally {
      setAuditing(false);
    }
  }

  function onSample() {
    setError(null);
    setIsSample(true);
    setReport(SAMPLE_AUDIT_RESPONSE);
    setFixes({});
    setExplanations({});
    setSampleReceipt(null);
    setSampleDrift(null);
    setLiveReceipt(undefined);
    setLiveReceiptStatus(null);
  }

  async function onExplain(drift: DriftResult) {
    const key = `${drift.promise.order_id}:${drift.amount_at_risk_usd}`;
    if (isSample) {
      setExplanations((prev) => ({ ...prev, [key]: SAMPLE_EXPLANATION }));
      return;
    }
    setExplanations((prev) => ({ ...prev, [key]: "…" }));
    try {
      const text = await explainDrift(
        drift.promise,
        drift.ledger_summary,
        drift.amount_at_risk_usd,
      );
      setExplanations((prev) => ({ ...prev, [key]: text }));
    } catch (err) {
      setExplanations((prev) => ({
        ...prev,
        [key]: err instanceof Error ? `Explain failed: ${err.message}` : "Explain failed.",
      }));
    }
  }

  async function onRemediate(drift: DriftResult) {
    const key = `${drift.promise.order_id}:${drift.amount_at_risk_usd}`;
    const matches = (candidate: DriftResult) =>
      `${candidate.promise.order_id}:${candidate.amount_at_risk_usd}` === key;
    if (isSample) {
      const next = nextSampleReceipt(sampleReceipt, drift);
      setSampleReceipt(next);
      setSampleDrift(drift);
      setFixes((prev) => ({ ...prev, [key]: "done" }));
      if (next.status === "executed") {
        setValue((prev) => ({
          total_recovered_usd:
            (prev?.total_recovered_usd ?? 0) + next.amount_usd,
          disputes_avoided: prev?.disputes_avoided ?? 0,
          dispute_cost_avoided_usd: prev?.dispute_cost_avoided_usd ?? 0,
          grand_total_usd: (prev?.grand_total_usd ?? 0) + next.amount_usd,
        }));
        setReport((prev) =>
          prev === null
            ? prev
            : {
                ...prev,
                drifts: prev.drifts.filter((d) => !matches(d)),
                results: prev.results.map((r) =>
                  matches(r)
                    ? { ...r, verdict: "verified" as const, amount_at_risk_usd: 0 }
                    : r,
                ),
                total_at_risk_usd: Math.max(
                  0,
                  prev.total_at_risk_usd - next.amount_usd,
                ),
              },
        );
      }
      return;
    }
    setFixes((prev) => ({ ...prev, [key]: "sending" }));
    try {
      const receipt = await remediate(
        drift.promise,
        drift.amount_at_risk_usd,
        {
          transcript_sha256: report?.transcript_sha256,
          transcript_turns: report?.transcript_turns,
          audited_at: report?.audited_at,
          ledger_summary: drift.ledger_summary,
        },
      );
      setLiveReceipt(receipt.receipt ?? null);
      setLiveReceiptStatus(
        receipt.status === "executed"
          ? `${formatUSD(receipt.amount_usd)} refunded.`
          : "Already executed. $0.00 additional movement.",
      );
      setFixes((prev) => ({ ...prev, [key]: "done" }));
      setReport((prev) =>
        prev === null
          ? prev
          : {
              ...prev,
              drifts: prev.drifts.filter((d) => !matches(d)),
              results: prev.results.map((r) =>
                matches(r)
                  ? { ...r, verdict: "verified" as const, amount_at_risk_usd: 0 }
                  : r,
              ),
              total_at_risk_usd: Math.max(
                0,
                prev.total_at_risk_usd - receipt.amount_usd,
              ),
            },
      );
      refreshValue();
    } catch (err) {
      setFixes((prev) => ({
        ...prev,
        [key]: err instanceof Error ? err.message : "Fix failed.",
      }));
    }
  }

  function onSampleRetry() {
    if (sampleDrift === null) return;
    setSampleReceipt((prev) => nextSampleReceipt(prev, sampleDrift));
  }

  const liveIssuerKey =
    liveReceipt === null || liveReceipt === undefined
      ? null
      : selectIssuerKey(liveIssuerKeys, liveReceipt.issuer.key_id);

  return (
    <main className="min-h-screen bg-night font-body text-cream">
      <div className="mx-auto max-w-5xl px-5 py-12 md:px-8 md:py-16">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-mint">
              Settleye exception inbox
            </p>
            <h1 className="mt-3 font-display text-[clamp(2.5rem,6vw,3.75rem)] leading-[1.02] font-light tracking-[-0.02em]">
              {value === null
                ? "Recovered $0.00 so far"
                : `Recovered ${formatUSD(value.grand_total_usd)} so far`}
            </h1>
          </div>
          {report !== null && (
            <span
              className={`${verdictClasses(report.drifts.length > 0 ? "drift" : "verified")} mb-2`}
            >
              {report.drifts.length > 0
                ? `${report.drifts.length} drift${report.drifts.length > 1 ? "s" : ""} · ${formatUSD(report.total_at_risk_usd)} at risk`
                : "Ledger matches"}
            </span>
          )}
        </header>

        <nav aria-label="Section navigation" className="mt-6 flex flex-wrap items-center gap-2">
          <a
            href="#inbox"
            className="rounded-full border border-cream/15 bg-cream/[0.04] px-3.5 py-1 text-xs font-mono text-cream/80 hover:border-mint/50 hover:text-mint transition-colors"
          >
            Exception Inbox
          </a>
          <a
            href="#proof-hierarchy"
            className="rounded-full border border-cream/15 bg-cream/[0.04] px-3.5 py-1 text-xs font-mono text-cream/80 hover:border-mint/50 hover:text-mint transition-colors"
          >
            Three-Tier Proof
          </a>
        </nav>

        <section id="inbox" className="mt-10 rounded-2xl border border-cream/10 bg-cream/[0.04] p-5 backdrop-blur md:p-7">
          <label
            htmlFor="transcript"
            className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-cream/55"
          >
            Support transcript
          </label>
          <textarea
            id="transcript"
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            rows={6}
            className="mt-3 w-full rounded-xl border border-cream/10 bg-night p-4 font-mono text-[13px] leading-relaxed text-cream/90 outline-none focus:border-mint/60"
          />
          <div className="mt-5 flex flex-wrap items-center gap-3">
            {staticDemo ? (
              <>
                <button
                  type="button"
                  onClick={onSample}
                  className="rounded-full bg-mint px-6 py-2.5 text-sm font-bold text-night transition hover:brightness-110"
                >
                  Load sample result
                </button>
                <button
                  type="button"
                  disabled
                  title="Start the backend locally to run a live audit"
                  className="rounded-full border border-cream/20 px-6 py-2.5 text-sm font-bold text-cream/35 opacity-60"
                >
                  Audit transcript (local API)
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={onAudit}
                  disabled={auditing || transcript.trim().length === 0}
                  className="rounded-full bg-mint px-6 py-2.5 text-sm font-bold text-night transition hover:brightness-110 disabled:opacity-40"
                >
                  {auditing ? AUDIT_LOADING_LABEL : "Audit transcript"}
                </button>
                <button
                  type="button"
                  onClick={onSample}
                  className="rounded-full border border-cream/25 px-6 py-2.5 text-sm font-bold text-cream transition hover:border-cream/60"
                >
                  Load sample result
                </button>
              </>
            )}
            {error !== null && (
              <p role="alert" className="text-xs text-alarm">
                {error}{" "}
                <span className="text-cream/50">
                  Live audits run against the local API. Use Load sample result
                  to see a recorded audit.
                </span>
              </p>
            )}
          </div>
          {staticDemo ? (
            <p className="mt-4 font-mono text-[11px] leading-relaxed text-cream/45">
              Static demo. The sample is a recorded live audit, not a live model
              call.{" "}
              <a
                className="text-cream underline decoration-mint/60 underline-offset-2"
                href="https://github.com/8-BitRhyon/settleye#run-it-yourself-under-five-minutes"
                target="_blank"
                rel="noopener"
              >
                Run the API locally
              </a>{" "}
              to audit your own transcript.
            </p>
          ) : (
            <p className="mt-4 font-mono text-[11px] leading-relaxed text-cream/45">
              Live audits run against the local API (see README). Load sample
              result shows a recorded live audit.
            </p>
          )}
        </section>

        {report !== null && (
          <section className="mt-6 space-y-4">
            {isSample && (
              <p className="border-l border-gold/50 pl-3 font-mono text-[11px] leading-relaxed text-cream/50">
                Sample data: recorded live audit, not a live result.{" "}
                {staticDemo
                  ? "The public copy is a static demo; run the API locally to audit your own transcript."
                  : "Run your own audit against the API to verify."}
              </p>
            )}
            {report.results.length === 0 && (
              <p className="rounded-2xl border border-cream/10 bg-cream/[0.03] p-6 text-sm text-cream/60">
                No promises detected. Nothing to reconcile.
              </p>
            )}
            {report.results.map((result, index) => {
              const fixKey = `${result.promise.order_id}:${result.amount_at_risk_usd}`;
              const fixState = fixes[fixKey] ?? "idle";
              const isDrift = result.verdict === "drift";
              return (
                <article
                  key={`${fixKey}:${index}`}
                  className={`rounded-2xl border bg-cream/[0.04] p-5 backdrop-blur md:p-7 ${
                    isDrift ? "border-alarm/30" : "border-cream/10"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span
                      className={verdictClasses(result.verdict)}
                    >
                      {result.verdict === "drift" && <DriftEye />}
                      {verdictLabel(result.verdict)}
                    </span>
                    <span className="font-mono text-[11px] text-cream/50">
                      {result.promise.action} · order #{result.promise.order_id ?? "?"}
                      {result.promise.amount !== null &&
                        ` · ${formatUSD(result.promise.amount)}`}
                    </span>
                  </div>
                  {result.promise.evidence_span !== "" && (
                    <blockquote
                      className={`mt-4 border-l-2 pl-4 font-mono text-[13px] leading-relaxed text-cream/85 ${
                        isDrift ? "border-alarm/60" : "border-cream/25"
                      }`}
                    >
                      “{result.promise.evidence_span}”
                    </blockquote>
                  )}
                  <p className="mt-3 text-[13px] leading-relaxed text-cream/60">
                    {result.ledger_summary}
                  </p>
                  {isDrift && (
                    <p className="mt-4 font-display text-[2rem] leading-none font-light">
                      <span className="tabular-nums">
                        {formatUSD(result.amount_at_risk_usd)}
                      </span>{" "}
                      <span className="text-lg text-cream/60">at risk</span>
                    </p>
                  )}
                  {result.verdict === "drift" && (
                    <div className="mt-3">
                      {explanations[fixKey] === undefined ? (
                        <button
                          type="button"
                          onClick={() => onExplain(result)}
                          className="text-[13px] font-semibold text-mint underline underline-offset-4"
                        >
                          Why does this matter?
                        </button>
                      ) : (
                        <p className="text-[13px] leading-relaxed text-mint/90">
                          {explanations[fixKey]}
                        </p>
                      )}
                    </div>
                  )}
                  {result.verdict === "drift" && (
                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={() => onRemediate(result)}
                        disabled={fixState === "sending" || fixState === "done"}
                        className="rounded-full bg-mint px-5 py-2 text-[13px] font-bold text-night transition hover:brightness-110 disabled:opacity-40"
                      >
                        {fixState === "sending"
                          ? "Fixing…"
                          : fixState === "done"
                            ? "Fixed"
                            : `Issue ${formatUSD(result.amount_at_risk_usd)} refund`}
                      </button>
                      {fixState !== "idle" &&
                        fixState !== "sending" &&
                        fixState !== "done" && (
                          <p role="alert" className="text-xs text-alarm">
                            {fixState}
                          </p>
                        )}
                    </div>
                  )}
                </article>
              );
            })}
          </section>
        )}

        {isSample && sampleReceipt !== null && (
          <ReceiptCard
            key={SIGNED_SAMPLE.receipt_id}
            receipt={SIGNED_SAMPLE}
            issuerPublicKey={SAMPLE_PUBLIC_KEY}
            issuerKeyId={SAMPLE_KEY_ID}
            merchantPublicKey={SAMPLE_MERCHANT_PUBLIC_KEY}
            merchantKeyId={SAMPLE_MERCHANT_KEY_ID}
            originNote="Sample data: recorded live audit, not a live result."
            statusLine={
              sampleReceipt.status === "executed"
                ? `${formatUSD(sampleReceipt.amount_usd)} refunded.`
                : `Already executed. ${formatUSD(additionalMovement(sampleReceipt))} additional movement.`
            }
            attemptsNote={`Attempt ${sampleReceipt.attempts}. Same key on every retry; no second refund.`}
            onRetry={onSampleRetry}
            retryLabel="Retry the same fix"
            onReload={onSample}
            reloadLabel="Reload sample"
            allowTamper
          />
        )}

        {liveReceipt === null && (
          <section className="mt-4 rounded-2xl border border-cream/10 bg-cream/[0.03] p-5">
            <p className="text-sm text-cream/70">
              No signed receipt for this fix.
            </p>
            <p className="mt-1 font-mono text-[11px] text-cream/45">
              Durable receipt is recorded; signing is not configured.
            </p>
          </section>
        )}

        {liveReceipt !== undefined &&
          liveReceipt !== null &&
          (liveIssuerKeys === undefined ? (
            <section className="mt-4 rounded-2xl border border-cream/10 bg-cream/[0.03] p-5">
              <p className="text-sm text-cream/70">Loading issuer key…</p>
            </section>
          ) : liveIssuerKey === null ? (
            <section className="mt-4 rounded-2xl border border-cream/10 bg-cream/[0.03] p-5">
              <p className="text-sm text-cream/70">
                No active or retired issuer key matches this receipt. It cannot
                be attributed in this browser.
              </p>
            </section>
          ) : (
            <ReceiptCard
              key={liveReceipt.receipt_id}
              receipt={liveReceipt}
              issuerPublicKey={liveIssuerKey.public_key}
              issuerKeyId={liveIssuerKey.key_id}
              merchantPublicKey=""
              merchantKeyId=""
              statusLine={liveReceiptStatus ?? undefined}
            />
          ))}

        <div className="mt-14 space-y-6">
          <ProofHierarchy />
          <details className="rounded-2xl border border-cream/10 bg-cream/[0.02] p-5 sm:p-6">
            <summary className="cursor-pointer font-mono text-xs uppercase tracking-widest text-mint">
              Modeled fleet exposure (optional detail)
            </summary>
            <p className="mt-2 max-w-2xl text-xs leading-relaxed text-cream/60">
              Tier 3 is a projection from stated assumptions, not a merchant
              result. The table and assumptions are here for judges who want
              the full model.
            </p>
            <div className="mt-6">
              <FleetImpact />
            </div>
          </details>
          <details className="rounded-2xl border border-cream/10 bg-cream/[0.02] p-5 sm:p-6">
            <summary className="cursor-pointer font-mono text-xs uppercase tracking-widest text-mint">
              Frontier architecture and receipt invariants
            </summary>
            <div className="mt-6">
              <FrontierNarrative />
            </div>
          </details>
        </div>

        <footer className="mt-14 border-t border-cream/10 pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-[11px] text-cream/45">
            <p>
              Built for Meta Global AI Developer Hackathon (Indie track). Model: meta-models/muse-spark-open-1026 via Baseten.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/8-BitRhyon/settleye"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-cream hover:underline"
              >
                GitHub Repository
              </a>
              <span>&middot;</span>
              <a
                href="landing.html"
                className="hover:text-cream hover:underline"
              >
                Landing Page
              </a>
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
