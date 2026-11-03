"""Turn the full eval report into a small, committable evidence file.

The full report in `out/eval_report.json` holds every per-row probability.
This keeps the eval cases and the headline metrics so the research note can
link to a file that is small enough to review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FIELDS = ("id", "p_needs", "needs_extraction", "any_entity", "pred_modality", "modality")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compact a full gate eval report.")
    parser.add_argument("--report", default="out/tinybert_eval_report.json")
    parser.add_argument("--out", default="results/summary.json")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text())
    summary = {
        "generated_at": report["generated_at"],
        "safe_threshold": report["safe_threshold"],
        "eval_table": report["eval_table"],
        "models": {},
    }
    for label, model in report["models"].items():
        summary["models"][label] = {
            "model_dir": model["model_dir"],
            "timing": model["timing"],
            "summary": model["summary"],
            "eval_cases": [
                {field: row[field] for field in FIELDS}
                for row in model["datasets"]["eval"]
            ],
            "bitext_kept_at_safe_threshold": sum(
                1
                for row in model["datasets"]["bitext"]
                if row["p_needs"] >= report["safe_threshold"]
            ),
            "bitext_n": len(model["datasets"]["bitext"]),
        }

    # Bitext has no labels for our schema. Its Brier and ECE would be computed
    # against an all-negative placeholder, so keep only the discard rate.
    for model in summary["models"].values():
        for threshold_block in model["summary"].values():
            bitext = threshold_block.get("bitext")
            if bitext:
                bitext["brier"] = None
                bitext["ece"] = None
                bitext["label_note"] = "unlabeled; discard rate only"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
