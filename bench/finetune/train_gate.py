"""Fine-tune Laya as a local promise gate on the generated dataset.

This is a thin, reproducible wrapper around `laya.train.finetune`, the same
recipe the model authors publish for Apple Silicon. The output checkpoint loads
with `laya.load(output_dir)`.

Example:
    .venv/bin/python train_gate.py \
        --data data/train.jsonl --eval-data data/test.jsonl \
        --output out/laya_gate --epochs 4
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from huggingface_hub import snapshot_download

from laya.train import TrainConfig, finetune

MODEL_ID = "convaiinnovations/laya"


def cached_model_dir() -> str | None:
    """Use the English checkpoint already in the Hugging Face cache.

    The repo also holds the multilingual and typed-decisions checkpoints, so a
    plain snapshot download fetches files this run never reads. Prefer the local
    snapshot and fall back to an allowlisted download only when it is absent.
    """
    snapshots = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "models--convaiinnovations--laya"
        / "snapshots"
    )
    if not snapshots.is_dir():
        return None
    for candidate in sorted(snapshots.iterdir(), reverse=True):
        if (candidate / "model.safetensors").exists() and (candidate / "rl_agent_config.json").exists():
            return str(candidate)
    return None


def skip_intermediate_checkpoints() -> None:
    """Do not keep an epoch snapshot beside the final checkpoint.

    `laya.train.finetune` writes `checkpoint_latest/` after every epoch. That
    doubles the disk footprint of an 421M-parameter model for a run whose final
    artifact is the only thing we evaluate. The final save still runs normally.
    """
    import laya.train as train_module

    original = train_module.save_checkpoint

    def save_final_only(model, tok, cfg, path):
        if Path(path).name == "checkpoint_latest":
            return
        original(model, tok, cfg, path)

    train_module.save_checkpoint = save_final_only


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune the local promise gate.")
    parser.add_argument("--data", default="data/train.jsonl")
    parser.add_argument("--eval-data", default="data/test.jsonl")
    parser.add_argument("--output", default="out/laya_gate")
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--micro-batch", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--calib-max", type=int, default=400)
    parser.add_argument("--calib-frac", type=float, default=0.2)
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--head-max-len", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--loss", choices=("rlcd", "soft_ce"), default="rlcd")
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    parser.add_argument(
        "--freeze-encoder",
        action="store_true",
        help="Train the decision head only. Much smaller memory footprint.",
    )
    parser.add_argument(
        "--no-eval",
        action="store_true",
        help="Skip the trainer's internal before/after eval; score separately.",
    )
    parser.add_argument("--no-checkpointing", action="store_true")
    parser.add_argument("--keep-intermediate", action="store_true")
    args = parser.parse_args()

    torch.set_float32_matmul_precision("high")
    if not args.keep_intermediate:
        skip_intermediate_checkpoints()
    model_dir = args.model_dir or cached_model_dir()
    if model_dir is None:
        model_dir = snapshot_download(
            MODEL_ID,
            allow_patterns=("encoder/*", "tokenizer/*", "model.safetensors", "rl_agent_config.json"),
        )
    eval_data = None if args.no_eval else args.eval_data
    config = TrainConfig(
        epochs=args.epochs,
        micro_batch=args.micro_batch,
        grad_accum=args.grad_accum,
        calib_max=args.calib_max,
        calib_frac=args.calib_frac,
        max_len=args.max_len,
        head_max_len=args.head_max_len,
        seed=args.seed,
        loss=args.loss,
        freeze_encoder=args.freeze_encoder,
        gradient_checkpointing=not args.no_checkpointing,
        amp=False,
        eval_data=eval_data,
        log_every=100,
    )

    print(f"model: {model_dir}", flush=True)
    print(f"data: {args.data}  eval: {eval_data}", flush=True)
    print(f"output: {args.output}", flush=True)
    started = time.time()
    summary = finetune(
        data=args.data,
        model_dir=model_dir,
        output_dir=args.output,
        config=config,
        device=args.device,
    )
    elapsed = round(time.time() - started, 1)
    print(f"elapsed_s: {elapsed}", flush=True)
    print(
        "summary:",
        json.dumps(
            {key: summary.get(key) for key in ("train_items", "calibration_items", "temperature")},
            default=str,
        ),
        flush=True,
    )

    run_config = {
        "model_id": MODEL_ID,
        "model_dir": model_dir,
        "data": args.data,
        "eval_data": eval_data,
        "output": args.output,
        "elapsed_s": elapsed,
        "args": vars(args),
        "config": {key: value for key, value in vars(config).items()},
        "summary": summary,
    }
    Path(args.output).mkdir(parents=True, exist_ok=True)
    (Path(args.output) / "run_config.json").write_text(
        json.dumps(run_config, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
