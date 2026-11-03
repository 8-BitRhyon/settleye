"""Run the TinyBERT gate over ABCD, a public human-human retail support corpus.

ABCD has no merchant transcript labels for our schema, but its scenario
subflows include refund initiation, refund updates, status checks, returns, and
cancellations. This script measures the gate's discard rate by subflow before
any extractor calls. A skip on `refund_initiate`, `refund_update`, or a return
that the agent approves is the dangerous direction.

ABCD: https://github.com/asappresearch/abcd (10,042 dialogues).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import torch

from eval_tinybert import load_gate
from generate_data import MODALITIES

REFUND_SUBFLOWS = (
    "refund_initiate",
    "refund_update",
    "refund_status",
    "return_size",
    "return_color",
    "return_stain",
)
ACTION_SUBFLOWS = (
    "refund_initiate",
    "refund_update",
    "return_size",
    "return_color",
    "return_stain",
)


def transcript(row: dict) -> str:
    return "\n".join(
        f"{role}: {text}"
        for role, text in row["original"]
        if role in ("customer", "agent")
    )


def load_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for split in ("train", "dev", "test"):
        for row in payload[split]:
            text = transcript(row)
            rows.append(
                {
                    "id": f"abcd-{row['convo_id']}",
                    "text": text,
                    "flow": row["scenario"]["flow"],
                    "subflow": row["scenario"]["subflow"],
                }
            )
    return rows


@torch.no_grad()
def score(
    model,
    tokenizer,
    checkpoint: dict,
    rows: list[dict],
    device: str,
    batch_size: int,
    max_len: int,
) -> list[dict]:
    temperature = checkpoint["temperature"]
    scored = []
    for start in range(0, len(rows), batch_size):
        chunk = rows[start:start + batch_size]
        encoded = tokenizer(
            [row["text"] for row in chunk],
            truncation=True,
            max_length=max_len,
            padding=True,
            return_tensors="pt",
        ).to(device)
        need_logits, modality_logits = model(
            encoded["input_ids"],
            encoded["attention_mask"],
            encoded.get("token_type_ids"),
        )
        probabilities = torch.sigmoid(need_logits / temperature).cpu().tolist()
        choices = modality_logits.argmax(dim=-1).cpu().tolist()
        for row, probability, choice in zip(chunk, probabilities, choices):
            scored.append(
                {
                    **row,
                    "p_needs": float(probability),
                    "pred_modality": MODALITIES[choice],
                    "truncated": len(tokenizer(row["text"])["input_ids"]) > max_len,
                }
            )
    return scored


def summarize(rows: list[dict], threshold: float) -> dict:
    def block(subset: list[dict]) -> dict:
        n = len(subset)
        skipped = sum(1 for row in subset if row["p_needs"] < threshold)
        return {
            "n": n,
            "skipped": skipped,
            "discard_rate": skipped / n if n else None,
            "mean_p": sum(row["p_needs"] for row in subset) / n if n else None,
        }

    by_subflow = defaultdict(list)
    for row in rows:
        by_subflow[row["subflow"]].append(row)
    refund = [row for row in rows if row["subflow"] in REFUND_SUBFLOWS]
    action = [row for row in rows if row["subflow"] in ACTION_SUBFLOWS]
    return {
        "all": block(rows),
        "refund_subflows": block(refund),
        "action_subflows": block(action),
        "by_subflow": {
            name: block(subset) for name, subset in sorted(by_subflow.items())
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score ABCD with the TinyBERT gate.")
    parser.add_argument("--model", default="out/tinybert_gate")
    parser.add_argument("--abcd", default="data/abcd/abcd_v1.1.json")
    parser.add_argument("--out", default="results/abcd_gate.json")
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-len", type=int, default=512)
    parser.add_argument("--threshold", type=float, default=0.20)
    args = parser.parse_args()

    device = args.device
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"

    rows = load_rows(Path(args.abcd))
    model, tokenizer, checkpoint = load_gate(Path(args.model), device)
    scored = score(
        model, tokenizer, checkpoint, rows, device, args.batch_size, args.max_len
    )
    thresholds = {
        str(threshold): summarize(scored, threshold) for threshold in (0.2, 0.5)
    }
    summary = thresholds[str(args.threshold)]
    refund_rows = [row for row in scored if row["subflow"] in REFUND_SUBFLOWS]
    lowest_refund = sorted(refund_rows, key=lambda row: row["p_needs"])[:20]
    skipped_refund = [
        row for row in refund_rows if row["p_needs"] < args.threshold
    ]
    result = {
        "corpus": "ABCD v1.1",
        "source": "https://github.com/asappresearch/abcd",
        "threshold": args.threshold,
        "max_len": args.max_len,
        "n_rows": len(scored),
        "truncated": sum(1 for row in scored if row["truncated"]),
        "summary": summary,
        "thresholds": thresholds,
        "lowest_refund_rows": lowest_refund,
        "skipped_refund_rows": skipped_refund,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"rows: {len(scored)}  truncated: {result['truncated']}")
    for label, block in sorted(thresholds.items()):
        print(
            f"threshold {label}: all {block['all']['discard_rate']:.3f}  "
            f"refund {block['refund_subflows']['discard_rate']:.3f}  "
            f"action {block['action_subflows']['discard_rate']:.3f}"
        )
    print(f"skipped refund rows at {args.threshold}: {len(skipped_refund)}")
    print("\nby subflow (n, discard):")
    for name, block in summary["by_subflow"].items():
        print(f"  {name:<28}{block['n']:>5}  {block['discard_rate']:.3f}")
    print(f"\nreport: {out}")


if __name__ == "__main__":
    main()
