"""Metric checks for the gate evaluator. Run with `python -m unittest`."""

from __future__ import annotations

import unittest

from eval_gate import metrics, safe_threshold


def row(case_id: str, p: float, needs: bool, modality: str = "binding") -> dict:
    return {
        "id": case_id,
        "text": "",
        "needs_extraction": needs,
        "any_entity": needs,
        "modality": modality,
        "n_entities": 1 if needs else 0,
        "p_needs": p,
        "pred_modality": modality,
    }


class MetricsTest(unittest.TestCase):
    def test_perfect_split(self) -> None:
        rows = [row("a", 0.9, True), row("b", 0.1, False, "info_only")]
        result = metrics(rows, 0.5)
        self.assertEqual(result["true_positives"], 1)
        self.assertEqual(result["false_negatives"], 0)
        self.assertEqual(result["true_negatives"], 1)
        self.assertEqual(result["false_positives"], 0)
        self.assertEqual(result["recall"], 1.0)
        self.assertEqual(result["skip_rate"], 1.0)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["modality_accuracy_commitment"], 1.0)
        self.assertAlmostEqual(result["brier"], 0.01)

    def test_false_negative_is_counted(self) -> None:
        rows = [row("a", 0.4, True), row("b", 0.1, False, "info_only")]
        result = metrics(rows, 0.5)
        self.assertEqual(result["false_negatives"], 1)
        self.assertEqual(result["recall"], 0.0)
        self.assertEqual(result["skip_rate"], 1.0)

    def test_safe_threshold_keeps_every_positive(self) -> None:
        rows = [row("a", 0.4, True), row("b", 0.8, True), row("c", 0.1, False, "info_only")]
        threshold = safe_threshold(rows)
        self.assertLessEqual(threshold, 0.4)
        result = metrics(rows, threshold)
        self.assertEqual(result["false_negatives"], 0)

    def test_modality_is_scored_on_positives_only(self) -> None:
        rows = [
            row("a", 0.9, True, "binding"),
            row("b", 0.8, True, "conditional"),
            row("c", 0.1, False, "info_only"),
        ]
        for item in rows:
            item["pred_modality"] = "binding"
        result = metrics(rows, 0.5)
        self.assertEqual(result["modality_accuracy_commitment"], 0.5)


if __name__ == "__main__":
    unittest.main()
