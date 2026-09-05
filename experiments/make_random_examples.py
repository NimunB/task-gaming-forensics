"""BRIEF §11: five responses per class, chosen with seed 42, verbatim, thinking and answer separated.
Classes come from the judge labels on the confirmatory run (falls back to the pilot if absent).

    python experiments/make_random_examples.py
"""
from __future__ import annotations
import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; random.seed(42)
def load(n): p = ROOT/"experiments"/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
S = load("samples_impossible.jsonl") + load("samples_possible.jsonl"); J = load("judge__samples_impossible.jsonl") + load("judge__samples_possible.jsonl"); src = "confirmatory run"
if not S: S = load("pilot_userturn.jsonl") + load("possible_controls.jsonl"); J = load("judge__pilot_userturn.jsonl") + load("judge__possible_controls.jsonl"); src = "pilot (confirmatory run not yet sampled)"
lab = {(j["task_id"], j["sample_index"]): j["label"] for j in J}
by = {}
for r in S:
    l = lab.get((r["task_id"], r["sample_index"]))
    if l: by.setdefault(l, []).append(r)
out = [f"# Random examples — five per class, seed 42, verbatim", "", f"Source: {src}. Selection: `random.Random(42).sample` within each judge label. Nothing here was chosen by hand.", ""]
for label in ("false_claim", "silent_omission", "workaround_as_complete", "honest_failure", "genuine_success", "other"):
    pool = by.get(label, [])
    out += [f"## {label} — {len(pool)} available, showing {min(5, len(pool))}", ""]
    for r in random.sample(pool, min(5, len(pool))) if pool else []:
        out += [f"### `{r['task_id']}` #{r['sample_index']}", "", "**Thinking**", "```text", (r["thinking"] or "").strip() or "(empty)", "```", "", "**Answer**", "```text", (r["answer"] or "").strip() or "(none)", "```", ""]
(ROOT/"experiments"/"random_examples.md").write_text("\n".join(out)); print("wrote experiments/random_examples.md from", src, {k: len(v) for k, v in by.items()})
