"""Score the two model arms against the eval manifest.

Arms:
- muse: recorded live output from meta-models/muse-spark-open-1026 (fixtures/eval_live_output.json)
- argon: recorded output from gemini-4-argon with agent scaffolding (bench/argon_output.json)

Both arms get the same manifest, the same order-id normalization, and the same
scoring. Any difference is extraction behavior, not measurement.

Run: python3 bench/score.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / "fixtures" / "eval_expected.json").read_text())
MUSE = json.loads((ROOT / "fixtures" / "eval_live_output.json").read_text())
ARGON = json.loads((ROOT / "bench" / "argon_output.json").read_text())


def norm_order(value):
    if value is None:
        return None
    return str(value).strip().lstrip("#")


def entities(rows):
    return [
        (
            row["action"],
            norm_order(row.get("order_id")),
            row.get("amount"),
            row["terminal_status"],
        )
        for row in rows
    ]


def score(arm, label):
    exact = 0
    hallucinated_order = 0
    false_clear = 0
    rows = []
    for name, want in EXPECTED.items():
        got_rows = arm[name]["entities"] if "entities" in arm[name] else arm[name]
        got = entities(got_rows)
        expected = entities(want["promises"])
        match = got == expected
        exact += match

        # A hallucinated order id is an identifier the transcript never stated.
        for row in got_rows:
            oid = norm_order(row.get("order_id"))
            if oid is not None and oid.startswith("EVAL"):
                hallucinated_order += 1

        # False clear: the arm reported nothing binding where a binding drift exists.
        want_binding = [p for p in want["promises"] if p["terminal_status"] == "binding"]
        got_binding = [r for r in got_rows if r["terminal_status"] == "binding"]
        if want_binding and not got_binding and want["verdict"] == "drift_found":
            false_clear += 1

        rows.append((name, "match" if match else "MISS", got, expected))

    print(f"\n== {label}")
    print(f"exact entity match : {exact} of {len(EXPECTED)}")
    print(f"hallucinated order : {hallucinated_order}")
    print(f"false clears       : {false_clear}")
    for name, status, got, expected in rows:
        if status == "MISS":
            print(f"  MISS {name}")
            print(f"    got      {got}")
            print(f"    expected {expected}")
    return exact, hallucinated_order, false_clear


if __name__ == "__main__":
    muse = score(MUSE, "muse-spark-open-1026 (Baseten, production pipeline)")
    argon = score(ARGON, "gemini-4-argon (OpenCode Go, agent scaffolding)")
    print("\n== summary")
    print(f"{'arm':<44} {'exact':>7} {'halluc':>7} {'falseclear':>11}")
    print(f"{'muse-spark-open-1026':<44} {muse[0]:>7} {muse[1]:>7} {muse[2]:>11}")
    print(f"{'gemini-4-argon':<44} {argon[0]:>7} {argon[1]:>7} {argon[2]:>11}")
