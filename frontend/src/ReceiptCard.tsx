import { useEffect, useId, useState } from "react";
import { formatUSD } from "./format";
import {
  tamperAmount,
  verifyTwoPartyReceipt,
  type ExecutionReceipt,
  type TwoPartyVerification,
} from "./receipt";
import {
  describeReceiptCard,
  type ReceiptRowDisplay,
  type ReceiptRowKind,
} from "./receipt-display";

export interface ReceiptCardProps {
  receipt: ExecutionReceipt;
  issuerPublicKey: string;
  issuerKeyId: string;
  merchantPublicKey: string;
  merchantKeyId: string;
  originNote?: string;
  statusLine?: string;
  attemptsNote?: string;
  onRetry?: () => void;
  retryLabel?: string;
  onReload?: () => void;
  reloadLabel?: string;
  allowTamper?: boolean;
}

function amountLabel(raw: string): string {
  const parsed = Number.parseFloat(raw);
  return Number.isNaN(parsed) ? raw : formatUSD(parsed);
}

const ROW_TEXT: Record<ReceiptRowKind, string> = {
  valid: "text-mint",
  neutral: "text-cream/70",
  invalid: "text-alarm",
};

const ROW_ICON: Record<ReceiptRowKind, string> = {
  valid: "✓",
  neutral: "–",
  invalid: "✕",
};

function SignatureRow({ row }: { row: ReceiptRowDisplay }) {
  return (
    <li className={`flex items-start gap-2 text-xs ${ROW_TEXT[row.kind]}`}>
      <span aria-hidden="true" className="font-bold">
        {ROW_ICON[row.kind]}
      </span>
      <span>
        <span className="font-semibold">{row.title}. </span>
        {row.detail !== "" && (
          <span className="text-cream/45">{row.detail}</span>
        )}
      </span>
    </li>
  );
}

/**
 * One signed receipt card for the static sample and live remediations.
 * Auto-verifies on arrival and whenever the envelope changes. The tamper
 * demo only verifies an altered in-memory copy; the saved receipt is kept.
 */
export default function ReceiptCard({
  receipt,
  issuerPublicKey,
  issuerKeyId,
  merchantPublicKey,
  merchantKeyId,
  originNote,
  statusLine,
  attemptsNote,
  onRetry,
  retryLabel = "Retry",
  onReload,
  reloadLabel = "Reload",
  allowTamper = false,
}: ReceiptCardProps) {
  const [verification, setVerification] =
    useState<TwoPartyVerification | null>(null);
  const [tampered, setTampered] = useState(false);
  const [nonce, setNonce] = useState(0);
  const tamperNoteId = useId();

  useEffect(() => {
    let cancelled = false;
    setVerification(null);
    const target = tampered ? tamperAmount(receipt) : receipt;
    verifyTwoPartyReceipt(
      target,
      issuerPublicKey,
      issuerKeyId,
      merchantPublicKey,
      merchantKeyId,
    )
      .then((result) => {
        if (!cancelled) setVerification(result);
      })
      .catch(() => {
        if (!cancelled) {
          setVerification({
            issuer: {
              valid: false,
              reason: "Verification failed. The receipt could not be read.",
            },
            merchant: {
              status: "invalid",
              reason: "Verification failed. The receipt could not be read.",
            },
            valid: false,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [
    receipt,
    tampered,
    nonce,
    issuerPublicKey,
    issuerKeyId,
    merchantPublicKey,
    merchantKeyId,
  ]);

  function onReverify() {
    setTampered(false);
    setNonce((value) => value + 1);
  }

  const display =
    verification === null
      ? null
      : describeReceiptCard(receipt, verification);
  const fallbackStatusLine =
    receipt.remediation.status === "executed"
      ? `${amountLabel(receipt.remediation.amount_usd)} refunded.`
      : "Already executed. No additional movement.";
  const verificationFailed = display !== null && !display.trusted;
  const verificationPending = display === null;

  return (
    <section
      className={`mt-4 rounded-2xl border bg-cream/[0.04] p-5 backdrop-blur md:p-6 ${
        verificationPending
          ? "border-cream/10"
          : verificationFailed
            ? "border-alarm/40"
            : "border-mint/30"
      }`}
    >
      <p
        className={`font-mono text-[11px] font-semibold uppercase tracking-[0.16em] ${
          verificationPending
            ? "text-cream/50"
            : verificationFailed
              ? "text-alarm"
              : "text-mint"
        }`}
      >
        {verificationPending
          ? "Verifying receipt"
          : verificationFailed
            ? "Receipt not verified"
            : "Remediation receipt"}
      </p>
      {originNote !== undefined && originNote !== "" && (
        <p className="mt-2 font-mono text-[11px] leading-relaxed text-cream/45">{originNote}</p>
      )}
      <p className="mt-2 break-all font-mono text-[11px] text-cream/60">
        {receipt.receipt_id}
      </p>
      <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-cream/40">
        issuer key {issuerKeyId}
      </p>
      <p className="mt-3 font-display text-xl font-light" aria-live="polite">
        Durable receipt: {statusLine ?? fallbackStatusLine}
      </p>
      <p className="mt-1 break-all font-mono text-xs text-cream/60">
        {receipt.remediation.idempotency_key}
      </p>
      {attemptsNote !== undefined && attemptsNote !== "" && (
        <p className="mt-1 font-mono text-[11px] text-cream/45">{attemptsNote}</p>
      )}
      {(onRetry !== undefined || onReload !== undefined) && (
        <div className="mt-4 flex flex-wrap items-center gap-3">
          {onRetry !== undefined && (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-full border border-mint/50 px-4 py-1.5 font-mono text-xs font-semibold text-mint transition hover:bg-mint/10"
            >
              {retryLabel}
            </button>
          )}
          {onReload !== undefined && (
            <button
              type="button"
              onClick={onReload}
              className="text-xs font-semibold text-cream/60 underline decoration-mint/60 underline-offset-4"
            >
              {reloadLabel}
            </button>
          )}
        </div>
      )}

      <div
        role="status"
        aria-live="polite"
        className="mt-4 rounded-xl border border-cream/10 bg-night p-4"
      >
        {display === null ? (
          <p className="font-mono text-xs text-cream/45">Verifying receipt…</p>
        ) : (
          <ul className="space-y-2">
            <SignatureRow row={display.issuer} />
            <SignatureRow row={display.merchant} />
          </ul>
        )}
        <button
          type="button"
          onClick={onReverify}
          className="mt-3 text-xs font-semibold text-mint underline underline-offset-4"
        >
          Re-verify
        </button>
      </div>

      {allowTamper && (
        <div className="mt-3">
          {tampered ? (
            <button
              type="button"
              onClick={() => setTampered(false)}
              className="text-xs font-semibold text-cream underline underline-offset-4"
            >
              Reset
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setTampered(true)}
              aria-describedby={tamperNoteId}
              className="text-xs font-semibold text-cream/60 underline underline-offset-4"
            >
              Try tamper demo
            </button>
          )}
          <p id={tamperNoteId} className="mt-1 font-mono text-[11px] leading-relaxed text-cream/40">
            Local demo: tampers a copy of the amount in your browser. The
            saved receipt is unchanged.
          </p>
        </div>
      )}

      <p className="mt-3 font-mono text-[11px] leading-relaxed text-cream/40">
        The signature proves the pinned key issued these bytes and they did
        not change. It does not independently prove Stripe or Shopify state.
      </p>
    </section>
  );
}
