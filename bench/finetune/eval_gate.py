"""Score the local promise gate against the eval set, held-out data, and wild text.

The gate's decision is `needs_extraction`: true when the agent committed to a
financial action (binding, conditional, superseded, or retracted). Policy
explanations and status updates are `info_only` and should be skipped. The
modality head is scored separately, including the info-only case.

Run from this directory:
    .venv/bin/python eval_gate.py --fine-tuned out/laya_gate
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch

from generate_data import MODALITIES, QUESTIONS

THRESHOLDS = (0.20, 0.50)


def format_turns(turns: list[dict]) -> str:
    return "\n".join(f"{turn['role']}: {turn['text']}" for turn in turns)


def load_eval_cases(fixtures: Path) -> list[dict]:
    expected = json.loads((fixtures / "eval_expected.json").read_text())
    cases = []
    for path in sorted((fixtures / "eval").glob("*.json")):
        payload = json.loads(path.read_text())
        manifest = expected[path.name]
        promises = manifest["promises"]
        commitment = [p for p in promises if p["terminal_status"] != "info_only"]
        cases.append(
            {
                "id": path.stem,
                "text": format_turns(payload["turns"]),
                "needs_extraction": bool(commitment),
                "any_entity": bool(promises),
                "modality": promises[0]["terminal_status"] if promises else "info_only",
                "n_entities": len(promises),
                "verdict": manifest["verdict"],
            }
        )
    return cases


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(
            {
                "id": row["case"],
                "text": row["state"],
                "needs_extraction": row["expected"]["needs_extraction"],
                "any_entity": row["expected"]["needs_extraction"],
                "modality": row["expected"]["modality"],
                "n_entities": 1 if row["expected"]["needs_extraction"] else 0,
            }
        )
    return rows


def load_bitext(path: Path) -> list[dict]:
    frame = pd.read_parquet(path, engine="pyarrow")
    refund = frame[frame["intent"].isin(["get_refund", "track_refund", "check_refund_policy"])]
    cancel = frame[frame["intent"] == "cancel_order"]
    other = frame[frame["intent"].isin(["payment_issue", "change_order", "place_order"])]
    sample = pd.concat(
        [
            refund.sample(150, random_state=7),
            cancel.sample(75, random_state=7),
            other.sample(75, random_state=7),
        ]
    )
    rows = []
    for index, row in sample.iterrows():
        rows.append(
            {
                "id": f"bitext-{index}",
                "text": f"customer: {row['instruction']}\nagent: {row['response']}",
                "needs_extraction": False,
                "any_entity": False,
                "modality": "info_only",
                "n_entities": 0,
                "intent": row["intent"],
            }
        )
    return rows


def saved_questions(model_dir: str) -> dict:
    path = Path(model_dir) / "questions.json"
    if path.exists():
        return json.loads(path.read_text())
    return QUESTIONS


def predict(
    model_dir: str, cases: list[dict], device: str, batch_size: int
) -> tuple[list[dict], dict]:
    import laya

    questions = saved_questions(model_dir)
    agent = laya.load(model_dir, device=device)
    started = time.monotonic()
    results = agent.predict_batch(
        [case["text"] for case in cases],
        questions,
        batch_size=batch_size,
    )
    elapsed = time.monotonic() - started
    out = []
    for case, result in zip(cases, results):
        answers = result["answers"]
        out.append(
            {
                **case,
                "p_needs": float(answers["needs_extraction"]["noul"]),
                "pred_modality": str(answers["modality"]["choice"]),
                "modality_probs": {
                    key: float(value)
                    for key, value in answers["modality"]["probabilities"].items()
                },
            }
        )
    del agent
    gc.collect()
    if device == "mps":
        torch.mps.empty_cache()
    timing = {
        "elapsed_s": round(elapsed, 3),
        "ms_per_case": round(elapsed / max(1, len(cases)) * 1000, 2),
        "batch_size": batch_size,
    }
    return out, timing


def ece(pairs: list[tuple[float, int]], bins: int = 10) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    score = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        bucket = [p for p, _ in pairs if low <= p < high or (index == bins - 1 and p == 1.0)]
        if not bucket:
            continue
        labels = [y for p, y in pairs if low <= p < high or (index == bins - 1 and p == 1.0)]
        mean_conf = sum(bucket) / len(bucket)
        accuracy = sum(labels) / len(labels)
        score += (len(bucket) / total) * abs(mean_conf - accuracy)
    return score


def metrics(rows: list[dict], threshold: float) -> dict:
    positives = [row for row in rows if row["needs_extraction"]]
    negatives = [row for row in rows if not row["needs_extraction"]]
    true_positives = sum(1 for row in positives if row["p_needs"] >= threshold)
    false_negatives = len(positives) - true_positives
    true_negatives = sum(1 for row in negatives if row["p_needs"] < threshold)
    false_positives = len(negatives) - true_negatives
    recall = true_positives / len(positives) if positives else None
    skip = true_negatives / len(negatives) if negatives else None
    accuracy = (true_positives + true_negatives) / len(rows) if rows else None
    modality_hits = sum(1 for row in positives if row["pred_modality"] == row["modality"])
    any_entity = [row for row in rows if row["any_entity"]]
    any_entity_hits = sum(1 for row in any_entity if row["pred_modality"] == row["modality"])
    any_entity_kept = sum(1 for row in any_entity if row["p_needs"] >= threshold)
    pairs = [(row["p_needs"], int(row["needs_extraction"])) for row in rows]
    brier = statistics.fmean((p - y) ** 2 for p, y in pairs) if pairs else None
    return {
        "n": len(rows),
        "positives": len(positives),
        "negatives": len(negatives),
        "threshold": threshold,
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "recall": recall,
        "skip_rate": skip,
        "accuracy": accuracy,
        "modality_accuracy_commitment": (modality_hits / len(positives)) if positives else None,
        "modality_correct_commitment": modality_hits,
        "modality_accuracy_any_entity": (any_entity_hits / len(any_entity)) if any_entity else None,
        "any_entity_cases": len(any_entity),
        "any_entity_kept": any_entity_kept,
        "brier": brier,
        "ece": ece(pairs),
        "mean_p": statistics.fmean(row["p_needs"] for row in rows) if rows else None,
    }


def safe_threshold(rows: list[dict]) -> float:
    """Highest threshold with zero false negatives on this split."""
    positives = [row["p_needs"] for row in rows if row["needs_extraction"]]
    if not positives:
        return 0.5
    return max(0.0, min(positives) - 1e-6)


def threshold_curve(rows: list[dict]) -> list[dict]:
    candidates = sorted({0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99})
    return [metrics(rows, threshold) for threshold in candidates]


def table(rows: list[dict], threshold: float) -> str:
    lines = [
        f"{'case':<24}{'p_needs':>9} {'decision':<9}{'pred':<13}{'gold':<13}{'ok':<4}"
    ]
    for row in rows:
        decision = "keep" if row["p_needs"] >= threshold else "skip"
        ok = "yes" if row["pred_modality"] == row["modality"] else "no"
        lines.append(
            f"{row['id']:<24}{row['p_needs']:>9.4f} {decision:<9}"
            f"{row['pred_modality']:<13}{row['modality']:<13}{ok:<4}"
        )
    return "\n".join(lines)


def evaluate_model(
    label: str,
    model_dir: str,
    datasets: dict[str, list[dict]],
    device: str,
    batch_size: int,
) -> dict:
    print(f"\n=== {label}: {model_dir} ===", flush=True)
    report = {"model_dir": model_dir, "datasets": {}, "timing": {}}
    for name, cases in datasets.items():
        print(f"  running {name}: {len(cases)} cases", flush=True)
        scored, timing = predict(model_dir, cases, device, batch_size)
        report["datasets"][name] = scored
        report["timing"][name] = timing
        print(
            f"    {timing['elapsed_s']:.1f}s "
            f"({timing['ms_per_case']:.1f} ms per case)",
            flush=True,
        )
    return report


def summarize(report: dict, threshold: float) -> dict:
    summary = {}
    for name, rows in report["datasets"].items():
        summary[name] = metrics(rows, threshold)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the fine-tuned promise gate.")
    parser.add_argument("--fine-tuned", default="out/laya_gate")
    parser.add_argument("--base-model", default=None)
    parser.add_argument("--fixtures", default="../../fixtures")
    parser.add_argument("--data", default="data")
    parser.add_argument("--bitext", default="/tmp/bitext.parquet")
    parser.add_argument("--out", default="out/eval_report.json")
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--skip-base", action="store_true")
    args = parser.parse_args()

    fixtures = Path(args.fixtures)
    data = Path(args.data)
    datasets = {
        "eval": load_eval_cases(fixtures),
        "val": load_jsonl(data / "val.jsonl"),
        "test": load_jsonl(data / "test.jsonl"),
        "bitext": load_bitext(Path(args.bitext)),
    }
    print(
        "datasets: "
        + ", ".join(f"{name}={len(rows)}" for name, rows in datasets.items()),
        flush=True,
    )

    base_dir = args.base_model
    if base_dir is None and not args.skip_base:
        snapshots = (
            Path.home()
            / ".cache"
            / "huggingface"
            / "hub"
            / "models--convaiinnovations--laya"
            / "snapshots"
        )
        if snapshots.is_dir():
            for candidate in sorted(snapshots.iterdir(), reverse=True):
                if (candidate / "model.safetensors").exists():
                    base_dir = str(candidate)
                    break

    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "models": {}}
    if base_dir and not args.skip_base:
        report["models"]["base"] = evaluate_model(
            "base Laya", base_dir, datasets, args.device, args.batch_size
        )
    report["models"]["fine_tuned"] = evaluate_model(
        "fine-tuned Laya", args.fine_tuned, datasets, args.device, args.batch_size
    )

    eval_rows = report["models"]["fine_tuned"]["datasets"]["eval"]
    val_rows = report["models"]["fine_tuned"]["datasets"]["val"]
    safe = safe_threshold(val_rows)
    report["safe_threshold"] = safe

    for label, model in report["models"].items():
        model["summary"] = {
            f"threshold_{threshold}": summarize(model, threshold) for threshold in THRESHOLDS
        }
        model["summary"]["safe_threshold"] = summarize(model, safe)
        model["threshold_curve"] = {
            name: threshold_curve(rows) for name, rows in model["datasets"].items()
        }
    report["eval_table"] = table(eval_rows, THRESHOLDS[1])

    # Keep committed reports portable: no absolute home paths.
    home = str(Path.home())
    for model in report["models"].values():
        model["model_dir"] = model["model_dir"].replace(home, "~")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== Eval: 12 cases ===")
    print(report["eval_table"])
    print(f"\nsafe threshold from val: {safe:.6f}")

    print("\n=== Summary ===")
    header = (
        f"{'model':<12}{'thr':>6}{'recall':>9}{'skip':>7}{'mod(commit)':>13}"
        f"{'mod(all)':>10}{'brier':>8}{'ece':>7}"
    )
    print(header)
    for label in report["models"]:
        for threshold in (*THRESHOLDS, safe):
            summary = report["models"][label]["summary"][f"threshold_{threshold}"]
            eval_metrics = summary["eval"]
            test_metrics = summary["test"]
            print(
                f"{label:<12}{threshold:>6.2f}{eval_metrics['recall']:>9.3f}"
                f"{eval_metrics['skip_rate']:>7.3f}"
                f"{_fmt(eval_metrics['modality_accuracy_commitment']):>13}"
                f"{_fmt(eval_metrics['modality_accuracy_any_entity']):>10}"
                f"{_fmt(test_metrics['brier']):>8}"
                f"{_fmt(test_metrics['ece']):>7}"
            )
    print(f"\nreport: {out_path}")


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


if __name__ == "__main__":
    main()
