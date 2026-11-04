import json, time
from pathlib import Path
import torch
from transformers import AutoModel

F = Path(__file__).resolve().parents[2] / 'fixtures'
expected = json.loads((F/'eval_expected.json').read_text())

# Described choice instead of bare noul, per the model card's guidance.
Q = {
 "promise": {"type":"choice","instructions":"Which statement is true of this support conversation?",
   "criteria":{
     "promised":"The agent told the customer money would move or already moved: a refund, credit, discount, or compensation.",
     "none":"The agent promised no money movement. Questions, status updates, or policy explanations only."}},
 "modality": {"type":"choice","instructions":"What is the end state of the agent's promise?",
   "criteria":{"binding":"Unconditional commitment that still stands.",
               "conditional":"Depends on a future customer action.",
               "superseded":"A later turn replaced it with a different amount or action.",
               "retracted":"The agent took it back.",
               "info_only":"Policy explanation, never a commitment."}},
}

model = AutoModel.from_pretrained("LiquidAI/d1-omni-600M", trust_remote_code=True, dtype=torch.float32)
rows=[]
for p in sorted((F/'eval').glob('*.json')):
    payload=json.loads(p.read_text())
    text="\n".join(f"{t.get('role','?')}: {t.get('text','')}" for t in payload['turns'])
    out=model.system_one(text, Q); a=out["answers"]
    probs=a["promise"]["probabilities"]; yes=probs.get("promised",0.0)
    mod=a["modality"]["choice"]; conf=a["modality"]["confidence"]
    want=expected[p.name]["promises"]; wany=len(want)>0
    wmod=want[0]["terminal_status"] if want else "none"
    rows.append((p.name,yes,mod,conf,wany,wmod))

print(f"{'case':<26}{'P(promised)':>12} {'mod':<12}{'conf':>6} {'want':<12}")
agree=0
for n,yes,mod,conf,wany,wmod in rows:
    call=yes>=0.5; ok=(call==wany); agree+=ok
    print(f"{n:<26}{yes:>12.3f} {mod:<12}{conf:>6.2f} {wmod:<12} {'ok' if ok else 'MISS'}")
print(f"\npresence agreement: {agree}/12")
mods=[(m,w) for _,_,m,_,wa,w in rows if wa]
print("modality agreement:", sum(1 for m,w in mods if m==w), "/", len(mods))
