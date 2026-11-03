import json, time
from pathlib import Path
import laya

F = Path('/Users/rhyon/Downloads/Self Curated CS Curriculum/Projects/promise-check/fixtures')
expected = json.loads((F/'eval_expected.json').read_text())

QUESTIONS = {
    "has_promise": {"type": "choice",
        "instructions": "Did the agent make a financial promise (refund, credit, discount, compensation) that it claims is done or will be done?",
        "criteria": {"yes": "The agent promised or confirmed money movement.",
                     "no": "No financial promise was made."}},
    "modality": {"type": "choice",
        "instructions": "What is the end state of the agent's promise?",
        "criteria": {"binding": "Unconditional commitment that still stands.",
                     "conditional": "Depends on a future customer action.",
                     "superseded": "A later turn replaced it.",
                     "retracted": "The agent took it back.",
                     "info_only": "Policy explanation, never a commitment."}},
}

agent = laya.load("convaiinnovations/laya")
rows = []
for p in sorted((F/'eval').glob('*.json')):
    payload = json.loads(p.read_text())
    text = "\n".join(f"{t.get('role','?')}: {t.get('text','')}" for t in payload['turns'])
    t0 = time.monotonic()
    r = agent.predict(text, QUESTIONS)
    ms = (time.monotonic()-t0)*1000
    a = r["answers"]
    yes = a["has_promise"]["probabilities"].get("yes", 0.0)
    mod = a["modality"]["choice"]
    conf = a["modality"]["confidence"]
    want = expected[p.name]["promises"]
    want_any = len(want) > 0
    want_mod = want[0]["terminal_status"] if want else "none"
    rows.append((p.name, yes, mod, conf, want_any, want_mod, ms))

print(f"{'case':<26}{'P(yes)':>8} {'mod':<12}{'conf':>6} {'want':<12}{'ms':>7}")
agree = 0
for n, yes, mod, conf, wany, wmod, ms in rows:
    call = yes >= 0.5
    ok = call == wany
    agree += ok
    print(f"{n:<26}{yes:>8.3f} {mod:<12}{conf:>6.2f} {wmod:<12}{ms:>7.0f} {'ok' if ok else 'MISS'}")
print(f"\npromise-presence agreement: {agree}/12")
mods = [(m, w) for _,_,m,_,wa,w,_ in rows if wa]
print("modality agreement on promise cases:", sum(1 for m,w in mods if m==w), "/", len(mods))
