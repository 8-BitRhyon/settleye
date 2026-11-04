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
  valid: "text-emerald-200",
  neutral: "text-zinc-300",
  invalid: "text-red-300",
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
          <span className="text-zinc-400">{row.detail}</span>
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
        if (!cancelled) setVerification(null);
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

  return (
    <section className="mt-4 rounded-xl border border-emerald-800 bg-zinc-900 p-4">
      <p className="text-xs font-semibold tracking-widest text-emerald-400 uppercase">
        Remediation receipt
      </p>
      {originNote !== undefined && originNote !== "" && (
        <p className="mt-1 text-[11px] text-amber-200">{originNote}</p>
      )}
      <p className="mt-1 break-all font-mono text-[11px] text-zinc-300">
        {receipt.receipt_id}
      </p>
      <p className="mt-1 font-mono text-[10px] text-zinc-500">
        pinned key {receipt.issuer.key_id}
      </p>
      <p className="mt-2 text-sm text-zinc-100" aria-live="polite">
        {statusLine ?? fallbackStatusLine}
      </p>
      <p className="mt-1 font-mono text-xs text-zinc-300">
        {receipt.remediation.idempotency_key}
      </p>
      {attemptsNote !== undefined && attemptsNote !== "" && (
        <p className="mt-1 text-xs text-zinc-500">{attemptsNote}</p>
      )}
      {(onRetry !== undefined || onReload !== undefined) && (
        <div className="mt-3 flex items-center gap-3">
          {onRetry !== undefined && (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-full border border-emerald-600 px-4 py-1.5 text-xs font-bold text-emerald-300"
            >
              {retryLabel}
            </button>
          )}
          {onReload !== undefined && (
            <button
              type="button"
              onClick={onReload}
              className="text-xs font-semibold text-zinc-400 underline underline-offset-2"
            >
              {reloadLabel}
            </button>
          )}
        </div>
      )}

      <div
        role="status"
        aria-live="polite"
        className="mt-3 rounded-lg bg-zinc-950 p-3"
      >
        {display === null ? (
          <p className="text-xs text-zinc-400">Verifying receipt…</p>
        ) : (
          <ul className="space-y-2">
            <SignatureRow row={display.issuer} />
            <SignatureRow row={display.merchant} />
          </ul>
        )}
        <button
          type="button"
          onClick={onReverify}
          className="mt-2 text-xs font-semibold text-emerald-300 underline underline-offset-2"
        >
          Re-verify
        </button>
      </div>

      {allowTamper && (
        <div className="mt-2">
          {tampered ? (
            <button
              type="button"
              onClick={() => setTampered(false)}
              className="text-xs font-semibold text-zinc-200 underline underline-offset-2"
            >
              Reset
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setTampered(true)}
              aria-describedby={tamperNoteId}
              className="text-xs font-semibold text-zinc-400 underline underline-offset-2"
            >
              Try tamper demo
            </button>
          )}
          <p id={tamperNoteId} className="mt-1 text-[11px] text-zinc-500">
            Local demo: tampers a copy of the amount in your browser. The
            saved receipt is unchanged.
          </p>
        </div>
      )}

      <p className="mt-2 text-[11px] text-zinc-500">
        The signature proves the pinned key issued these bytes and they did
        not change. It does not independently prove Stripe or Shopify state.
      </p>
    </section>
  );
}
