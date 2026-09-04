"""Structural summaries for REPORT.md §8 A–C. No honesty labels — those are Gate 1 / Step 7.

A. possible_controls.jsonl   : report / tool call / no answer; does the answer contain hedging
                                language about being unable to verify or complete?
B. confession_indirect.jsonl : paired against confession.jsonl by (task_id, sample_index);
                                opening phrase of each reply side by side.
C. pressure_samples.jsonl    : same structural split as compare_runs.py, vs pilot_userturn.jsonl.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def load(n): p = ROOT/"experiments"/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
def kind(r):
    if not r["closed_think"] or r["n_answer_tokens"] == 0: return "no answer"
    return "tool call" if "<tool_call>" in r["answer"] else "report"
HEDGE = re.compile(r"(unable to|could not|couldn't|cannot verify|can't verify|not able to|failed|did not run|didn't run|wasn't able|were not run|not verified)", re.I)
def opening(a):
    a = a.strip().lstrip("#* ").lower()
    m = re.match(r"(no\b|not yet\b|yes\b|partially\b|honest answer|you're right|i need to be honest|looking at)", a)
    return m.group(1) if m else a[:22]

which = sys.argv[1:] or ["A", "B", "C"]
if "A" in which and (A := load("possible_controls.jsonl")):
    print("=== A. POSSIBLE CONTROLS (n=%d) ===" % len(A))
    print(f"{'setting':<22}{'report':>7}{'toolcall':>9}{'noans':>6}   hedge-phrase in answer (of reports)")
    for st in sorted({r["setting"] for r in A}):
        rs = [r for r in A if r["setting"] == st]; ks = [kind(r) for r in rs]
        hed = [bool(HEDGE.search(r["answer"])) for r in rs if kind(r) == "report"]
        print(f"{st:<22}{ks.count('report'):>7}{ks.count('tool call'):>9}{ks.count('no answer'):>6}   {sum(hed)}/{len(hed)}")
    print("hedge-phrase is a regex flag for reading, NOT a label (see sanity_checks 3b).\n")
if "B" in which and (B := load("confession_indirect.jsonl")):
    D = {(r["task_id"], r["sample_index"]): r for r in load("confession.jsonl")}
    print("=== B. DIRECT vs INDIRECT FOLLOW-UP, paired (n=%d) ===" % len(B))
    print(f"{'response':<26}{'direct opens':<20}{'indirect opens':<20} indirect ans tokens")
    for r in B:
        d = D.get((r["task_id"], r["sample_index"]))
        print(f"{r['setting']+'#'+str(r['sample_index']):<26}{opening(d['answer']) if d else '-':<20}{opening(r['answer']):<20} {r['n_answer_tokens']}")
    print("\nindirect: closed_think %d/%d, tool_call in reply %d, 'hallucinat' in reply: %s\n" % (
        sum(r["closed_think"] for r in B), len(B), sum("<tool_call>" in r["answer"] for r in B),
        [f"{r['setting']}#{r['sample_index']}" for r in B if "hallucinat" in r["answer"].lower()]))
if "C" in which and (C := load("pressure_samples.jsonl")):
    base = load("pilot_userturn.jsonl")
    print("=== C. PRESSURE vs BASELINE, structural (n=%d vs %d) ===" % (len(C), len(base)))
    print(f"{'setting':<22}{'report b/p':>12}{'toolcall b/p':>14}{'noans b/p':>11}")
    for st in sorted({r["setting"] for r in C}):
        kb = [kind(r) for r in base if r["setting"] == st]; kp = [kind(r) for r in C if r["setting"] == st]
        print(f"{st:<22}{kb.count('report'):>5}/{kp.count('report'):<6}{kb.count('tool call'):>7}/{kp.count('tool call'):<6}{kb.count('no answer'):>5}/{kp.count('no answer'):<5}")
    print("(b = baseline pilot_userturn, p = pressure). Gaming must be read, not counted here.")
