import { useCallback, useEffect, useRef, useState } from "react";
import {
  auditTranscript,
  explainDrift,
  fetchValue,
  remediate,
  type AuditReport,
  type DriftResult,
  type ValueSummary,
} from "./api";
import { EyeIcon, type EyeIconHandle } from "./components/EyeIcon";
import {
  AUDIT_LOADING_LABEL,
  SAMPLE_PHANTOM_TRANSCRIPT,
  formatUSD,
  verdictClasses,
  verdictLabel,
} from "./format";

type RemediateState = Record<string, "idle" | "sending" | "done" | string>;
type ExplainState = Record<string, string | undefined>;

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

  const refreshValue = useCallback(() => {
    fetchValue().then(setValue).catch(() => {});
  }, []);

  useEffect(() => {
    refreshValue();
  }, [refreshValue]);

  async function onAudit() {
    setAuditing(true);
    setError(null);
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

  async function onExplain(drift: DriftResult) {
    const key = `${drift.promise.order_id}:${drift.amount_at_risk_usd}`;
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
    setFixes((prev) => ({ ...prev, [key]: "sending" }));
    try {
      const receipt = await remediate(
        drift.promise,
        drift.amount_at_risk_usd,
      );
      setFixes((prev) => ({ ...prev, [key]: "done" }));
      setReport((prev) =>
        prev === null
          ? prev
          : {
              ...prev,
              drifts: prev.drifts.filter((d) => d !== drift),
              results: prev.results.map((r) =>
                r === drift
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
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={onAudit}
              disabled={auditing || transcript.trim().length === 0}
              className="rounded-full bg-emerald-500 px-5 py-2 text-sm font-bold text-black disabled:opacity-40"
            >
              {auditing ? AUDIT_LOADING_LABEL : "Audit transcript"}
            </button>
            {error !== null && (
              <p role="alert" className="text-xs text-red-300">
                {error}
              </p>
            )}
          </div>
        </section>

        {report !== null && (
          <section className="mt-4 space-y-3">
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
