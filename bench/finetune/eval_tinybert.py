"""Score the TinyBERT gate on the eval set, held-out data, and wild text."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

from eval_gate import (
    THRESHOLDS,
    _fmt,
    load_bitext,
    load_eval_cases,
    load_jsonl,
    metrics,
    safe_threshold,
    table,
    threshold_curve,
)
from generate_data import MODALITIES
from train_tinybert import GateModel


def load_gate(model_dir: Path, device: str):
    checkpoint = torch.load(model_dir / "model.pt", map_location="cpu", weights_only=False)
    tokenizer = AutoTokenizer.from_pretrained(model_dir / "tokenizer", local_files_only=True)
    encoder = AutoModel.from_pretrained(checkpoint["encoder_id"])
    model = GateModel(encoder, checkpoint["hidden_size"]).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, tokenizer, checkpoint


def predict(
    model,
    tokenizer,
    checkpoint: dict,
    cases: list[dict],
    device: str,
    batch_size: int,
) -> tuple[list[dict], dict]:
    max_len = checkpoint["max_len"]
    temperature = checkpoint["temperature"]
    started = time.monotonic()
    rows = []
    for start in range(0, len(cases), batch_size):
        chunk = cases[start:start + batch_size]
        encoded = tokenizer(
            [case["text"] for case in chunk],
            truncation=True,
            max_length=max_len,
            padding=True,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            need_logits, modality_logits = model(
                encoded["input_ids"],
                encoded["attention_mask"],
                encoded.get("token_type_ids"),
            )
        probabilities = torch.sigmoid(need_logits / temperature).cpu().tolist()
        modality_probabilities = torch.softmax(modality_logits, dim=-1).cpu()
        choices = modality_logits.argmax(dim=-1).cpu().tolist()
        for case, probability, choice, distribution in zip(
            chunk, probabilities, choices, modality_probabilities
        ):
            rows.append(
                {
                    **case,
                    "p_needs": float(probability),
                    "pred_modality": MODALITIES[choice],
                    "modality_probs": {
                        label: float(distribution[index])
                        for index, label in enumerate(MODALITIES)
                    },
                }
            )
    elapsed = time.monotonic() - started
    return rows, {
        "elapsed_s": round(elapsed, 3),
        "ms_per_case": round(elapsed / max(1, len(cases)) * 1000, 2),
        "batch_size": batch_size,
    }


def summarize(rows_by_dataset: dict[str, list[dict]], threshold: float) -> dict:
    return {
        name: metrics(rows, threshold) for name, rows in rows_by_dataset.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the TinyBERT gate.")
    parser.add_argument("--model", default="out/tinybert_gate")
    parser.add_argument("--fixtures", default="../../fixtures")
    parser.add_argument("--data", default="data")
    parser.add_argument("--bitext", default="/tmp/bitext.parquet")
    parser.add_argument("--out", default="out/tinybert_eval_report.json")
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    device = args.device
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"

    datasets = {
        "eval": load_eval_cases(Path(args.fixtures)),
        "val": load_jsonl(Path(args.data) / "val.jsonl"),
        "test": load_jsonl(Path(args.data) / "test.jsonl"),
        "bitext": load_bitext(Path(args.bitext)),
    }
    model, tokenizer, checkpoint = load_gate(Path(args.model), device)
    rows_by_dataset = {}
    timing = {}
    for name, cases in datasets.items():
        print(f"running {name}: {len(cases)} cases", flush=True)
        rows, elapsed = predict(
            model, tokenizer, checkpoint, cases, device, args.batch_size
        )
        rows_by_dataset[name] = rows
        timing[name] = elapsed
        print(f"  {elapsed['elapsed_s']:.1f}s ({elapsed['ms_per_case']:.1f} ms per case)", flush=True)

    safe = safe_threshold(rows_by_dataset["val"])
    summary = {
        f"threshold_{threshold}": summarize(rows_by_dataset, threshold)
        for threshold in THRESHOLDS
    }
    summary["safe_threshold"] = summarize(rows_by_dataset, safe)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safe_threshold": safe,
        "models": {
            "tinybert": {
                "model_dir": args.model,
                "datasets": rows_by_dataset,
                "timing": timing,
                "summary": summary,
                "threshold_curve": {
                    name: threshold_curve(rows)
                    for name, rows in rows_by_dataset.items()
                },
            }
        },
        "eval_table": table(rows_by_dataset["eval"], THRESHOLDS[1]),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== Eval: 12 cases ===")
    print(report["eval_table"])
    print(f"\nsafe threshold from val: {safe:.6f}")
    print("\n=== Summary ===")
    print(
        f"{'thr':>10}{'eval recall':>13}{'eval skip':>11}{'modality':>10}"
        f"{'test recall':>13}{'test skip':>11}{'bitext skip':>13}"
    )
    rows = (
        ("0.20", summary["threshold_0.2"]),
        ("0.50", summary["threshold_0.5"]),
        (f"safe {safe:.4f}", summary["safe_threshold"]),
    )
    for label, row in rows:
        print(
            f"{label:>10}{row['eval']['recall']:>13.3f}"
            f"{row['eval']['skip_rate']:>11.3f}"
            f"{_fmt(row['eval']['modality_accuracy_commitment']):>10}"
            f"{row['test']['recall']:>13.3f}"
            f"{row['test']['skip_rate']:>11.3f}"
            f"{row['bitext']['skip_rate']:>13.3f}"
        )
    print(f"\nreport: {out}")


if __name__ == "__main__":
    main()
