"""Fine-tune TinyBERT as a local promise gate.

TinyBERT 4-layer (120 MB) is small enough to train on a laptop and to ship
beside a batch worker. The model shares one encoder between two heads:

- `needs_extraction`: a binary gate. Run the extractor only when the agent
  committed to a financial action.
- `modality`: the five-state end state, for comparison with the earlier runs.

Example:
    .venv/bin/python train_tinybert.py \
        --data data --output out/tinybert_gate --epochs 4
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer

from generate_data import MODALITIES, QUESTIONS

ENCODER_ID = "huawei-noah/TinyBERT_General_4L_312D"


class GateModel(nn.Module):
    def __init__(self, encoder: nn.Module, hidden_size: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.encoder = encoder
        self.dropout = nn.Dropout(dropout)
        self.needs_head = nn.Linear(hidden_size, 1)
        self.modality_head = nn.Linear(hidden_size, len(MODALITIES))

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        output = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        pooled = self.dropout(output.last_hidden_state[:, 0])
        return self.needs_head(pooled).squeeze(-1), self.modality_head(pooled)


def read_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows.append(
                {
                    "text": row["state"],
                    "needs": 1.0 if row["expected"]["needs_extraction"] else 0.0,
                    "modality": MODALITIES.index(row["expected"]["modality"]),
                    "case": row["case"],
                }
            )
    return rows


def encode_rows(rows: list[dict], tokenizer, max_len: int) -> dict:
    encoded = tokenizer(
        [row["text"] for row in rows],
        truncation=True,
        max_length=max_len,
        padding=True,
        return_tensors="pt",
    )
    encoded["needs"] = torch.tensor([row["needs"] for row in rows], dtype=torch.float32)
    encoded["modality"] = torch.tensor([row["modality"] for row in rows], dtype=torch.long)
    return encoded


def batches(size: int, batch_size: int, rng: random.Random | None = None):
    order = list(range(size))
    if rng is not None:
        rng.shuffle(order)
    for start in range(0, size, batch_size):
        yield order[start:start + batch_size]


def move(batch: dict, indices: list[int], device: str) -> dict:
    return {
        key: value[indices].to(device)
        for key, value in batch.items()
    }


@torch.no_grad()
def predict_logits(model: nn.Module, batch: dict, device: str, batch_size: int = 32):
    model.eval()
    needs, modality = [], []
    for indices in batches(len(batch["needs"]), batch_size):
        moved = move(batch, indices, device)
        need_logits, modality_logits = model(
            moved["input_ids"],
            moved["attention_mask"],
            moved.get("token_type_ids"),
        )
        needs.append(need_logits.detach().cpu())
        modality.append(modality_logits.detach().cpu())
    return torch.cat(needs), torch.cat(modality)


def fit_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    values = logits.detach().cpu().numpy()
    targets = labels.detach().cpu().numpy()
    best_t, best_nll = 1.0, math.inf
    for temperature in np.linspace(0.5, 5.0, 91):
        p = 1.0 / (1.0 + np.exp(-values / temperature))
        p = np.clip(p, 1e-6, 1.0 - 1e-6)
        nll = -np.mean(targets * np.log(p) + (1.0 - targets) * np.log(1.0 - p))
        if nll < best_nll:
            best_t, best_nll = float(temperature), float(nll)
    return best_t


def sigmoid(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    return torch.sigmoid(logits / temperature)


def evaluate(
    model: nn.Module,
    batch: dict,
    device: str,
    temperature: float = 1.0,
) -> dict:
    need_logits, modality_logits = predict_logits(model, batch, device)
    probabilities = sigmoid(need_logits, temperature)
    predictions = (probabilities >= 0.5).float()
    labels = batch["needs"]
    modality_predictions = modality_logits.argmax(dim=-1)
    modality_labels = batch["modality"]
    positives = labels >= 0.5
    negatives = ~positives
    true_positives = int(((predictions >= 0.5) & positives).sum())
    false_negatives = int(((predictions < 0.5) & positives).sum())
    true_negatives = int(((predictions < 0.5) & negatives).sum())
    false_positives = int(((predictions >= 0.5) & negatives).sum())
    return {
        "n": int(len(labels)),
        "positives": int(positives.sum()),
        "negatives": int(negatives.sum()),
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "recall": true_positives / max(1, int(positives.sum())),
        "skip_rate": true_negatives / max(1, int(negatives.sum())),
        "accuracy": (true_positives + true_negatives) / len(labels),
        "modality_accuracy": int((modality_predictions == modality_labels).sum()) / len(labels),
        "mean_p": float(probabilities.mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune TinyBERT as a local gate.")
    parser.add_argument("--data", default="data")
    parser.add_argument("--output", default="out/tinybert_gate")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    device = args.device
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}", flush=True)

    data = Path(args.data)
    train_rows = read_rows(data / "train.jsonl")
    val_rows = read_rows(data / "val.jsonl")
    test_rows = read_rows(data / "test.jsonl")
    print(
        f"rows: train={len(train_rows)} val={len(val_rows)} test={len(test_rows)}",
        flush=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(ENCODER_ID)
    encoder = AutoModel.from_pretrained(ENCODER_ID)
    model = GateModel(encoder, encoder.config.hidden_size).to(device)

    train_batch = encode_rows(train_rows, tokenizer, args.max_len)
    val_batch = encode_rows(val_rows, tokenizer, args.max_len)
    test_batch = encode_rows(test_rows, tokenizer, args.max_len)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    needs_loss = nn.BCEWithLogitsLoss()
    modality_loss = nn.CrossEntropyLoss()
    rng = random.Random(args.seed)

    best_score = math.inf
    best_state = None
    history = []
    started = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        steps = 0
        for indices in batches(len(train_rows), args.batch_size, rng):
            moved = move(train_batch, indices, device)
            optimizer.zero_grad(set_to_none=True)
            need_logits, modality_logits = model(
                moved["input_ids"],
                moved["attention_mask"],
                moved.get("token_type_ids"),
            )
            loss = needs_loss(need_logits, moved["needs"]) + 0.5 * modality_loss(
                modality_logits, moved["modality"]
            )
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach().cpu())
            steps += 1
        mean_loss = total_loss / max(1, steps)
        val_metrics = evaluate(model, val_batch, device)
        score = (1.0 - val_metrics["recall"]) * 10.0 + (1.0 - val_metrics["skip_rate"]) + (
            1.0 - val_metrics["modality_accuracy"]
        )
        history.append(
            {
                "epoch": epoch,
                "train_loss": round(mean_loss, 6),
                "val": val_metrics,
                "score": round(score, 6),
            }
        )
        print(
            f"epoch {epoch}/{args.epochs} loss {mean_loss:.4f} "
            f"val recall {val_metrics['recall']:.3f} "
            f"skip {val_metrics['skip_rate']:.3f} "
            f"modality {val_metrics['modality_accuracy']:.3f}",
            flush=True,
        )
        if score < best_score:
            best_score = score
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    need_logits, _ = predict_logits(model, val_batch, device)
    temperature = fit_temperature(need_logits, val_batch["needs"])
    val_metrics = evaluate(model, val_batch, device, temperature)
    test_metrics = evaluate(model, test_batch, device, temperature)
    print(f"temperature: {temperature:.4f}", flush=True)
    print(f"val:  {json.dumps(val_metrics)}", flush=True)
    print(f"test: {json.dumps(test_metrics)}", flush=True)
    print(f"elapsed_s: {time.time() - started:.1f}", flush=True)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "encoder_id": ENCODER_ID,
            "hidden_size": encoder.config.hidden_size,
            "max_len": args.max_len,
            "temperature": temperature,
            "modalities": list(MODALITIES),
        },
        output / "model.pt",
    )
    tokenizer.save_pretrained(output / "tokenizer")
    (output / "questions.json").write_text(json.dumps(QUESTIONS, indent=2), encoding="utf-8")
    report = {
        "encoder_id": ENCODER_ID,
        "seed": args.seed,
        "device": device,
        "args": vars(args),
        "history": history,
        "temperature": temperature,
        "val": val_metrics,
        "test": test_metrics,
        "elapsed_s": round(time.time() - started, 1),
    }
    (output / "train_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"saved: {output}", flush=True)


if __name__ == "__main__":
    main()
