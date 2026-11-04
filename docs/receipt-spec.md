# Execution receipt v1

A signed, portable artifact for an AI agent's promised action and its
remediation. The receipt binds five things:

1. The transcript the promise came from.
2. The extracted promise.
3. The ledger state Settleye observed.
4. The idempotency key used to remediate.
5. The remediation result.

Anyone with the receipt and the pinned issuer key can verify that the payload
was issued by Settleye and was not altered. A merchant can add a second
signature to acknowledge the remediation. The receipt is self-contained for
transport, but trust comes from the pinned keys, not from the keys embedded in
the receipt.

## Envelope

```json
{
  "version": 1,
  "receipt_id": "sha256:...",
  "issued_at": "2026-11-04T12:00:00Z",
  "issuer": {
    "name": "Settleye",
    "key_id": "settleye-demo-2026-12"
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
    "idempotency_key": "refund:992:stripe:45.00",
    "amount_usd": "45.00",
    "status": "executed"
  },
  "signature": {
    "alg": "Ed25519",
    "public_key": "base64url",
    "value": "base64url"
  },
  "countersignatures": [
    {
      "role": "merchant",
      "key_id": "merchant-demo-2026-12",
      "alg": "Ed25519",
      "public_key": "base64url",
      "acknowledged_at": "2026-11-04T12:05:00Z",
      "value": "base64url"
    }
  ]
}
```

`countersignatures` is optional. A v1 receipt with no merchant signature still
verifies. The field is outside the issuer payload, so adding or removing a
merchant signature does not change the issuer signature or the receipt id.

Money is a decimal string with two places. The receipt never stores the full
transcript, only its SHA-256 and the evidence span.

## Canonical bytes

The signed payload is the envelope without `receipt_id`, `signature`, and
`countersignatures`.

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

1. Remove `receipt_id`, `signature`, and `countersignatures` from the envelope.
2. Canonicalize the remaining payload.
3. Recompute the receipt id and compare it.
4. Require `signature.alg == "Ed25519"`.
5. Require `issuer.key_id` and `signature.public_key` to match the pinned key.
6. Verify the signature over the canonical bytes.
7. If merchant countersignatures are present, verify each one.
8. Return a structured result with `valid`, `reason`, `receipt_id`, `key_id`,
   `merchant_valid`, and `merchant_key_id`.

Any failure is a fail-closed result. A tampered amount, order, ledger state,
key id, or receipt id must fail.

## Merchant countersignature

The merchant signs canonical bytes of:

```json
{
  "receipt_id": "sha256:...",
  "role": "merchant",
  "key_id": "merchant-demo-2026-12",
  "acknowledged_at": "2026-11-04T12:05:00Z"
}
```

The message is short on purpose. The amount, promise, and ledger observation
are already bound by `receipt_id`; restating them would create a second place
for the parties to disagree.

Verification rules:

- `role` must be `merchant`; `alg` must be `Ed25519`.
- The key id and public key must match the merchant pin.
- The signature must verify over the countersign message.
- A malformed or invalid present signature fails the receipt.
- Missing countersignatures are a provisional state, not a failure, unless the
  caller requires a merchant signature.
- A merchant signature never makes an invalid issuer payload trusted. The
  issuer check runs first, and the overall result cannot be valid when the
  issuer is invalid.

## Key registry

Issuer keys live in a JSON registry, one record per key id:

```json
{
  "key_id": "settleye-2026-11",
  "public_key": "base64url",
  "status": "active",
  "created_at": "2026-11-04T12:00:00Z",
  "retired_at": null,
  "revoked_at": null
}
```

Statuses:

- `active`: current signing key. Exactly one key should be active.
- `retired`: no new signatures, but historical receipts still verify. The
  verifier reports `retired` as a note, not a failure.
- `revoked`: never trust a receipt from this key. Verification fails.

Rotation generates a new keypair, writes the private key to the issuer key path
with owner-only permissions, marks the old key `retired`, and adds the new key
as `active`. Revocation marks a key `revoked` and keeps the public record so
old receipts can be identified as untrusted rather than unknown.

The public registry is served by `GET /receipt/keys`. It contains public keys
and status only. It never contains a private key or a private key path.

`POST /receipt/verify` uses an explicit pin when `public_key` is supplied.
A `key_id` alone is not a trust anchor: with a registry it is checked against
the published record, and without one the request fails closed. If no public
key or registry is available, verification proves internal consistency only and
does not establish issuer authenticity. A registry file that exists but has no
records fails closed with `registry_error`; it is not treated as "no registry".

A merchant countersignature is only a trust decision when a merchant public key
is supplied. Without one, `merchant_valid` is `null`, not `true`, even if the
signature is internally consistent. `require_merchant=true` without a merchant
pin fails with `merchant_unpinned`.

## Live audit binding

The audit response carries:

- `transcript_sha256`: SHA-256 of the exact transcript bytes.
- `transcript_turns`: non-empty transcript lines.
- `audited_at`: UTC ISO 8601 time of the audit.

The remediation request may forward those fields plus `ledger_summary`. The
server does not trust the client's ledger summary: it re-reads the ledger and
signs its own fresh reconciliation summary. The digest, turns, and audit time
are caller-supplied: the server no longer holds the transcript, so it signs the
binding, not the provenance. A production deployment should persist audit
reports server-side keyed by digest and require `/remediate` to reference the
stored report. When the digest and turns are present and the issuer key is
configured, `/remediate` signs the envelope and persists it with the durable
receipt. When they are absent, the durable receipt is still recorded and
`receipt` is `null`. Money already moved, so a signing failure never fails the
refund; the response states that no signed receipt was produced.

## What the signatures prove

- The payload was signed by the holder of the pinned Settleye key.
- The payload has not changed since signing.
- The promise, transcript digest, ledger observation, remediation key, and
  status are bound together.
- A merchant countersignature proves the holder of the pinned merchant key
  acknowledged this receipt id at `acknowledged_at`.

## What they do not prove

- They do not prove that Stripe or Shopify's state is true. The receipt records
  what Settleye observed at `checked_at`.
- They do not prove the transcript is authentic. It binds a digest; the
  merchant must keep the source transcript.
- In the live path, the transcript digest and audit time are supplied by the
  caller and are not re-derived from a stored audit. The signature binds that
  claim; it does not prove the audit produced it.
- A merchant countersignature does not prove money moved. It proves the
  merchant key holder acknowledged the remediation receipt.
- They are not a third-party audit or a legal attestation.
- They are not a substitute for ledger-side idempotency.

## Sample verification

The public sample receipt is signed by the demo issuer key and countersigned by
the demo merchant key. The browser verifier pins both key ids and checks both
signatures locally. The sample also offers a tamper button: changing the
promised amount changes the canonical issuer bytes and the issuer signature
fails. Changing the merchant acknowledgement time breaks the merchant
signature.
