# Execution receipt v1

A signed, portable artifact for an AI agent's promised action and its
remediation. The receipt binds five things:

1. The transcript the promise came from.
2. The extracted promise.
3. The ledger state Settleye observed.
4. The idempotency key used to remediate.
5. The remediation result.

Anyone with the receipt and the pinned issuer key can verify that the payload
was issued by Settleye and was not altered. The receipt is self-contained for
transport, but trust comes from the pinned key, not from the key embedded in
the receipt.

## Envelope

```json
{
  "version": 1,
  "receipt_id": "sha256:...",
  "issued_at": "2026-11-04T12:00:00Z",
  "issuer": {
    "name": "Settleye",
    "key_id": "settleye-demo-2026-11"
  },
  "agent": {
    "model_id": "meta-models/muse-spark-open-1026"
  },
  "transcript": {
    "sha256": "...",
    "turns": 3
  },
  "promise": {
    "action": "refund",
    "order_id": "992",
    "amount": "45.00",
    "target_system": "stripe",
    "terminal_status": "binding",
    "evidence_span": "I have processed a full $45 refund for order #992."
  },
  "ledger": {
    "system": "stripe",
    "order_id": "992",
    "shortfall_usd": "45.00",
    "summary": "Order 992: $0.00 settled of $45.00 promised.",
    "checked_at": "2026-11-04T12:00:00Z"
  },
  "remediation": {
    "idempotency_key": "refund:992:45.00",
    "amount_usd": "45.00",
    "status": "executed"
  },
  "signature": {
    "alg": "Ed25519",
    "public_key": "base64url",
    "value": "base64url"
  }
}
```

Money is a decimal string with two places. The receipt never stores the full
transcript, only its SHA-256 and the evidence span.

## Canonical bytes

The signed payload is the envelope without `receipt_id` and `signature`.

Canonical bytes are UTF-8 JSON with:

- object keys sorted lexicographically at every level,
- no insignificant whitespace,
- separators `,` and `:`,
- `ensure_ascii=False`.

The same bytes must be produced by the backend and the browser verifier.

## Receipt id

```
receipt_id = "sha256:" + hex(SHA-256(canonical_bytes))
```

The id is a content address, not a signature. It lets a merchant deduplicate
receipts and reference one without including the full payload.

## Signing

```
signature.value = base64url(Ed25519_sign(canonical_bytes))
signature.public_key = base64url(Ed25519_public_key)
signature.alg = "Ed25519"
```

The private key never leaves the issuer. The public key is pinned by key id in
the verifier.

## Verification

1. Remove `receipt_id` and `signature` from the envelope.
2. Canonicalize the remaining payload.
3. Recompute the receipt id and compare it.
4. Require `signature.alg == "Ed25519"`.
5. Require `issuer.key_id` and `signature.public_key` to match the pinned key.
6. Verify the signature over the canonical bytes.
7. Return a structured result with `valid`, `reason`, `receipt_id`, and
   `key_id`.

Any failure is a fail-closed result. A tampered amount, order, ledger state,
key id, or receipt id must fail.

## What the signature proves

- The payload was signed by the holder of the pinned Settleye key.
- The payload has not changed since signing.
- The promise, transcript digest, ledger observation, remediation key, and
  status are bound together.

## What it does not prove

- It does not prove that Stripe or Shopify's state is true. It records what
  Settleye observed at `checked_at`.
- It does not prove the transcript is authentic. It binds a digest; the
  merchant must keep the source transcript.
- It is not a third-party audit or a legal attestation.
- It is not a substitute for ledger-side idempotency.

The next steps are ledger countersignatures, a public key registry, and a
merchant countersignature on the same payload.

## Sample verification

The public sample receipt is signed by the demo key. The browser verifier pins
`settleye-demo-2026-11` and checks the signature locally. The sample also
offers a tamper button: changing the promised amount changes the canonical
bytes and the signature fails.
