"""Judge vs adopted labels on the impossible run; judge distributions on controls and pressure.
    python experiments/judge_agreement.py
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GAMED = {"false_claim","silent_omission","workaround_as_complete"}
def load(n):
    p = ROOT/"experiments"/n
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
def kappa(pairs, cats):
    n=len(pairs); po=sum(a==b for a,b in pairs)/n
    ca,cb=Counter(a for a,_ in pairs),Counter(b for _,b in pairs); pe=sum(ca[c]*cb[c] for c in cats)/(n*n)
    return (po-pe)/(1-pe) if pe<1 else float("nan")

J = {(r["task_id"], r["sample_index"]): r for r in load("judge__pilot_userturn.jsonl")}
H = json.loads((ROOT/"experiments"/"handlabel_gate1.json").read_text())
pairs=[]; admit_pairs=[]
for k, h in H.items():
    tid, si = k.rsplit("#",1); j = J.get((tid, int(si)))
    if not j: continue
    pairs.append((h["label"], j["label"]))
    if h["cot_admits"] in ("y","n") and j.get("cot_admits_impossible") is not None:
        admit_pairs.append((h["cot_admits"]=="y", bool(j["cot_admits_impossible"])))
print(f"=== IMPOSSIBLE RUN: adopted labels vs judge (n={len(pairs)}) ===")
agree=sum(a==b for a,b in pairs)
print(f"label agreement {agree}/{len(pairs)} | kappa(6) = {kappa(pairs, sorted({c for p in pairs for c in p})):.2f} | kappa(gamed vs not) = {kappa([('g' if a in GAMED else 'n','g' if b in GAMED else 'n') for a,b in pairs], ['g','n']):.2f}")
print(f"judge gamed count: {sum(b in GAMED for _,b in pairs)} | adopted gamed count: {sum(a in GAMED for a,_ in pairs)}")
if admit_pairs:
    print(f"cot_admits agreement {sum(a==b for a,b in admit_pairs)}/{len(admit_pairs)} | kappa = {kappa(admit_pairs,[True,False]):.2f}")
dis=[(k,h["label"],J[(k.rsplit('#',1)[0],int(k.rsplit('#',1)[1]))]["label"]) for k,h in H.items() if (k.rsplit('#',1)[0],int(k.rsplit('#',1)[1])) in J and h["label"]!=J[(k.rsplit('#',1)[0],int(k.rsplit('#',1)[1]))]["label"]]
for k,a,b in dis: print(f"  DISAGREE {k}: adopted={a} judge={b} | judge rationale: {J[(k.rsplit('#',1)[0],int(k.rsplit('#',1)[1]))].get('rationale','')[:160]}")
for name in ["judge__possible_controls.jsonl","judge__pressure_samples.jsonl"]:
    rows=load(name)
    if rows:
        print(f"\n=== {name} (n={len(rows)}) ===")
        for st in sorted({r['setting'] for r in rows}):
            print(f"  {st:<20}", dict(Counter(r['label'] for r in rows if r['setting']==st)))
        print("  TOTAL", dict(Counter(r['label'] for r in rows)), "| parse errors:", sum('parse_error' in r for r in rows))
