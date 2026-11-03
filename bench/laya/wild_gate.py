import json, time
import pandas as pd, laya

df = pd.read_parquet('/tmp/bitext.parquet', engine='pyarrow')
refund = df[df['intent'].isin(['get_refund','track_refund','check_refund_policy'])]
cancel = df[df['intent']=='cancel_order']
other  = df[df['intent'].isin(['payment_issue','change_order','place_order'])]
samp = pd.concat([refund.sample(150, random_state=7), cancel.sample(75, random_state=7), other.sample(75, random_state=7)])

Q = {"has_promise": {"type":"choice",
  "instructions":"Did the agent make a financial promise (refund, credit, discount, compensation) that it claims is done or will be done?",
  "criteria":{"yes":"The agent promised or confirmed money movement.","no":"No financial promise was made."}}}

agent = laya.load("convaiinnovations/laya")
t0=time.monotonic(); kept=0; rows=0
for _, r in samp.iterrows():
    text = f"customer: {r['instruction']}\nagent: {r['response']}"
    a = agent.predict(text, Q)["answers"]["has_promise"]["probabilities"]
    if a.get("yes",0.0) >= 0.5: kept += 1
    rows += 1
el=(time.monotonic()-t0)
print(json.dumps({"n":rows,"kept":kept,"discarded":rows-kept,
 "discard_rate":round((rows-kept)/rows*100,1),
 "total_s":round(el,1),"ms_per":round(el/rows*1000)}))
