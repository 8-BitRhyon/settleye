import json, time
from pathlib import Path
import torch
from transformers import AutoModel

F = Path('/Users/rhyon/Downloads/Self Curated CS Curriculum/Projects/promise-check/fixtures')
expected = json.loads((F/'eval_expected.json').read_text())

Q = {
 "promise": {"type":"noul","instructions":"The agent made a financial promise to the customer: a refund, credit, discount, or compensation that it claims is done or will be done."},
 "modality": {"type":"choice","instructions":"What is the end state of the agent's promise?",
   "criteria":{"binding":"Unconditional commitment that still stands.",
               "conditional":"Depends on a future customer action.",
               "superseded":"A later turn replaced it.",
               "retracted":"The agent took it back.",
               "info_only":"Policy explanation, never a commitment."}},
}

model = AutoModel.from_pretrained("LiquidAI/d1-omni-600M", trust_remote_code=True, dtype=torch.float32)
rows=[]
for p in sorted((F/'eval').glob('*.json')):
    payload=json.loads(p.read_text())
    text="\n".join(f"{t.get('role','?')}: {t.get('text','')}" for t in payload['turns'])
    t0=time.monotonic(); out=model.system_one(text, Q); ms=(time.monotonic()-t0)*1000
    a=out["answers"]
    yes=a["promise"]["noul"]; mod=a["modality"]["choice"]; conf=a["modality"]["confidence"]
    want=expected[p.name]["promises"]; wany=len(want)>0
    wmod=want[0]["terminal_status"] if want else "none"
    rows.append((p.name,yes,mod,conf,wany,wmod,ms))

print(f"{'case':<26}{'P(yes)':>8} {'mod':<12}{'conf':>6} {'want':<12}{'ms':>7}")
agree=0
for n,yes,mod,conf,wany,wmod,ms in rows:
    call=yes>=0.5; ok=(call==wany); agree+=ok
    print(f"{n:<26}{yes:>8.3f} {mod:<12}{conf:>6.2f} {wmod:<12}{ms:>7.0f} {'ok' if ok else 'MISS'}")
print(f"\npresence agreement: {agree}/12")
mods=[(m,w) for _,_,m,_,wa,w,_ in rows if wa]
print("modality agreement:", sum(1 for m,w in mods if m==w), "/", len(mods))
