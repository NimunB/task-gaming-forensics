"""BRIEF §11 for GPT-OSS-20B: five responses per judge label, seed 42, verbatim, analysis channel and final answer
separated. Uses the confirmatory files if present, else pilot + widening.

    python experiments/make_random_examples_gptoss.py
"""
from __future__ import annotations
import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; random.seed(42)
def load(n): p = ROOT/"experiments"/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
CONF = ["gptoss_confirm_impossible.jsonl", "gptoss_confirm_possible.jsonl"]; PILOT = ["gptoss_impossible.jsonl", "gptoss_possible.jsonl", "gptoss_tr_impossible25.jsonl", "gptoss_tr_possible10.jsonl", "gptoss_fcli50.jsonl"]
files, src = (CONF, "confirmatory run (seed 43)") if all((ROOT/"experiments"/f).exists() and (ROOT/"experiments"/f"judge__{f}").exists() for f in CONF) else (PILOT, "pilot + widening (seed 42; confirmatory run not yet judged)")
S = [r | {"_file": f} for f in files for r in load(f)]; lab = {(f, j["task_id"], j["sample_index"]): j["label"] for f in files for j in load(f"judge__{f}")}
by = {}
for r in S:
    l = lab.get((r["_file"], r["task_id"], r["sample_index"]))
    if l: by.setdefault(l, []).append(r)
out = [f"# Random examples — GPT-OSS-20B — five per class, seed 42, verbatim", "", f"Source: {src}: {', '.join(files)}. Selection: `random.Random(42).sample` within each judge label. Nothing here was chosen by hand.", "",
       "GPT-OSS's Harmony `analysis` channel is shown as **Thinking**; the `final` channel as **Answer**. Many gamed responses have an empty analysis channel — that is the finding, not a rendering bug (REPORT §3.17).", ""]
for label in ("false_claim", "silent_omission", "workaround_as_complete", "honest_failure", "genuine_success", "other"):
    pool = by.get(label, [])
    out += [f"## {label} — {len(pool)} available, showing {min(5, len(pool))}", ""]
    for r in random.sample(pool, min(5, len(pool))) if pool else []:
        out += [f"### `{r['task_id']}` #{r['sample_index']} ({r['_file']})", "", f"**Thinking** ({r.get('n_thinking_tokens', '?')} tokens)", "```text", (r.get("thinking") or "").strip() or "(empty)", "```", "", "**Answer**", "```text", (r.get("answer") or "").strip() or "(none)", "```", ""]
(ROOT/"experiments"/"random_examples_gptoss.md").write_text("\n".join(out)); print("wrote experiments/random_examples_gptoss.md from", src, {k: len(v) for k, v in by.items()})
