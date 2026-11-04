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
  return <EyeIcon ref={ref} size={14} className="text-red-400" />;
}

export default function App() {
  const [transcript, setTranscript] = useState(SAMPLE_PHANTOM_TRANSCRIPT);
  const [report, setReport] = useState<AuditReport | null>(null);
  const [value, setValue] = useState<ValueSummary | null>(null);
  const [auditing, setAuditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fixes, setFixes] = useState<RemediateState>({});
  const [explanations, setExplanations] = useState<ExplainState>({});
  const [isSample, setIsSample] = useState(false);
  const [sampleReceipt, setSampleReceipt] = useState<SampleReceiptState | null>(null);
  const [sampleDrift, setSampleDrift] = useState<DriftResult | null>(null);
  const [liveReceipt, setLiveReceipt] = useState<
    ExecutionReceipt | null | undefined
  >(undefined);
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
    refreshValue();
  }, [refreshValue]);

  useEffect(() => {
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
  }, [liveReceipt?.receipt_id]);

  async function onAudit() {
    setAuditing(true);
    setError(null);
    setIsSample(false);
    setSampleReceipt(null);
    setSampleDrift(null);
    setLiveReceipt(undefined);
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

  const staticDemo =
    typeof window !== "undefined" &&
    isStaticDemo(window.location.hostname, import.meta.env.VITE_API_URL);

  const liveIssuerKey =
    liveReceipt === null || liveReceipt === undefined
      ? null
      : selectIssuerKey(liveIssuerKeys, liveReceipt.issuer.key_id);

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-3xl px-6 py-10">
        <header className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-widest text-emerald-400 uppercase">
              Settleye exception inbox
            </p>
            <h1 className="mt-1 text-2xl font-bold">
              {value === null
                ? "Recovered $0.00 so far"
                : `Recovered ${formatUSD(value.grand_total_usd)} so far`}
            </h1>
          </div>
          {report !== null && (
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold ${verdictClasses(report.drifts.length > 0 ? "drift" : "verified")}`}
            >
              {report.drifts.length > 0
                ? `${report.drifts.length} drift${report.drifts.length > 1 ? "s" : ""} · ${formatUSD(report.total_at_risk_usd)} at risk`
                : "Ledger matches"}
            </span>
          )}
        </header>

        <section className="mt-6 rounded-xl bg-zinc-900 p-4">
          <label
            htmlFor="transcript"
            className="text-xs font-semibold text-zinc-400 uppercase"
          >
            Support transcript
          </label>
          <textarea
            id="transcript"
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            rows={6}
            className="mt-2 w-full rounded-lg bg-zinc-950 p-3 font-mono text-xs text-zinc-200 outline-none ring-zinc-700 focus:ring-1"
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {staticDemo ? (
              <>
                <button
                  type="button"
                  onClick={onSample}
                  className="rounded-full bg-emerald-500 px-5 py-2 text-sm font-bold text-black"
                >
                  Load sample result
                </button>
                <button
                  type="button"
                  disabled
                  title="Start the backend locally to run a live audit"
                  className="rounded-full border border-zinc-700 px-5 py-2 text-sm font-bold text-zinc-500 opacity-50"
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
                  className="rounded-full bg-emerald-500 px-5 py-2 text-sm font-bold text-black disabled:opacity-40"
                >
                  {auditing ? AUDIT_LOADING_LABEL : "Audit transcript"}
                </button>
                <button
                  type="button"
                  onClick={onSample}
                  className="rounded-full border border-zinc-700 px-5 py-2 text-sm font-bold text-zinc-200"
                >
                  Load sample result
                </button>
              </>
            )}
            {error !== null && (
              <p role="alert" className="text-xs text-red-300">
                {error}{" "}
                <span className="text-zinc-400">
                  Live audits run against the local API. Use Load sample result
                  to see a recorded audit.
                </span>
              </p>
            )}
          </div>
          {staticDemo ? (
            <p className="mt-2 rounded-lg border border-amber-700/60 bg-amber-950/20 p-3 text-[11px] text-amber-200">
              Static demo. The sample is a recorded live audit, not a live model
              call.{" "}
              <a
                className="underline"
                href="https://github.com/8-BitRhyon/settleye#run-it-yourself-under-five-minutes"
                target="_blank"
                rel="noopener"
              >
                Run the API locally
              </a>{" "}
              to audit your own transcript.
            </p>
          ) : (
            <p className="mt-2 text-[11px] text-zinc-500">
              Live audits run against the local API (see README). Load sample
              result shows a recorded live audit.
            </p>
          )}
        </section>

        {report !== null && (
          <section className="mt-4 space-y-3">
            {isSample && (
              <p className="rounded-xl border border-amber-700 bg-zinc-900 p-3 text-xs text-amber-200">
                Sample data: recorded live audit, not a live result.{" "}
                {staticDemo
                  ? "The public copy is a static demo; run the API locally to audit your own transcript."
                  : "Run your own audit against the API to verify."}
              </p>
            )}
            {report.results.length === 0 && (
              <p className="rounded-xl bg-zinc-900 p-4 text-sm text-zinc-400">
                No promises detected. Nothing to reconcile.
              </p>
            )}
            {report.results.map((result, index) => {
              const fixKey = `${result.promise.order_id}:${result.amount_at_risk_usd}`;
              const fixState = fixes[fixKey] ?? "idle";
              return (
                <article
                  key={`${fixKey}:${index}`}
                  className="rounded-xl bg-zinc-900 p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span
                      className={`flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-bold ${verdictClasses(result.verdict)}`}
                    >
                      {result.verdict === "drift" && <DriftEye />}
                      {verdictLabel(result.verdict)}
                    </span>
                    <span className="font-mono text-xs text-zinc-400">
                      {result.promise.action} · order #{result.promise.order_id ?? "?"}
                      {result.promise.amount !== null &&
                        ` · ${formatUSD(result.promise.amount)}`}
                    </span>
                  </div>
                  {result.promise.evidence_span !== "" && (
                    <blockquote className="mt-2 border-l-2 border-zinc-700 pl-3 font-mono text-xs text-zinc-300">
                      “{result.promise.evidence_span}”
                    </blockquote>
                  )}
                  <p className="mt-2 text-xs text-zinc-400">
                    {result.ledger_summary}
                  </p>
                  {result.verdict === "drift" && (
                    <div className="mt-2">
                      {explanations[fixKey] === undefined ? (
                        <button
                          type="button"
                          onClick={() => onExplain(result)}
                          className="text-xs font-semibold text-emerald-400 underline underline-offset-2"
                        >
                          Why does this matter?
                        </button>
                      ) : (
                        <p className="text-xs text-emerald-200">
                          {explanations[fixKey]}
                        </p>
                      )}
                    </div>
                  )}
                  {result.verdict === "drift" && (
                    <div className="mt-3 flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => onRemediate(result)}
                        disabled={fixState === "sending" || fixState === "done"}
                        className="rounded-full bg-red-400 px-4 py-1.5 text-xs font-bold text-black disabled:opacity-40"
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
                          <p role="alert" className="text-xs text-red-300">
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
          <section className="mt-4 rounded-xl border border-zinc-700 bg-zinc-900 p-4">
            <p className="text-sm text-zinc-300">
              No signed receipt for this fix.
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Durable receipt is recorded; signing is not configured.
            </p>
          </section>
        )}

        {liveReceipt !== undefined &&
          liveReceipt !== null &&
          (liveIssuerKeys === undefined ? (
            <section className="mt-4 rounded-xl border border-zinc-700 bg-zinc-900 p-4">
              <p className="text-sm text-zinc-300">Loading issuer key…</p>
            </section>
          ) : liveIssuerKey === null ? (
            <section className="mt-4 rounded-xl border border-zinc-700 bg-zinc-900 p-4">
              <p className="text-sm text-zinc-300">
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
            />
          ))}

        <footer className="mt-8 border-t border-zinc-800 pt-3">
          <p className="text-[11px] text-zinc-500">
            Built with Muse Spark Open. Extraction by Meta open-weight model
            via Baseten; fixtures are synthetic, test ledgers only.
          </p>
        </footer>
      </div>
    </main>
  );
}
