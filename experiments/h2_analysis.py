"""H2 (PREREGISTRATION §1b): fabrication vs refusal on fictional_cli x100, Jacobian-lens ranks. GPU.

Groups come from the judge (judge__fcli_100.jsonl): false_claim = fabrication, honest_failure = refusal;
everything else excluded and counted. For each response: rank of each token in the negation/doubt set
at the </think> token (predicts the first answer token) and at the first non-whitespace answer token,
layers 8..30, J-lens and plain logit lens. Per-response statistic: median rank over the token set.
Pre-registered test: Mann-Whitney U, one-sided (refusals lower), at L20 and L24, with rank-biserial.

    python experiments/h2_analysis.py
Writes experiments/h2_results.json (per-response ranks + tests).
"""
from __future__ import annotations
import json, sys, statistics
from pathlib import Path
import torch as t
from scipy.stats import mannwhitneyu
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import load_tasks, render  # noqa: E402
from task_gaming.jlens_readout import JLens, unembed  # noqa: E402
MODEL = "Qwen/Qwen3.5-9B"; LAYERS = [8, 12, 16, 20, 24, 26, 28, 30]; THINK_CLOSE_ID = 248069
TOKENS = [" not", " There", " sorry", " cannot", " Unfortunately"]          # pre-registered set
EXTRA = [" command", "```", " I", " Yes"]                                    # descriptive only
TASKS = {x["id"]: x for x in load_tasks()}
tok = AutoTokenizer.from_pretrained(MODEL); model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval(); lens = JLens()
def load(n): return [json.loads(l) for l in (ROOT/"experiments"/n).read_text().splitlines() if l.strip()]
rows = load("fcli_100.jsonl"); J = {r["sample_index"]: r for r in load("judge__fcli_100.jsonl")}
tid = {tg: tok(tg, add_special_tokens=False)["input_ids"] for tg in TOKENS + EXTRA}
assert all(len(v) == 1 for v in tid.values()), {k: v for k, v in tid.items() if len(v) != 1}
@t.no_grad()
def ranks(ids, p):
    out = model(input_ids=ids, output_hidden_states=True); res = {}
    for l in LAYERS:
        h = out.hidden_states[l+1][0, p]; res[l] = {}
        for kind, x in (("j", lens.transport(h, l)), ("ll", h.float())):
            lg = unembed(model, x); res[l][kind] = {tg: int((lg > lg[i[0]]).sum()) for tg, i in tid.items()}
    return res
out = {"excluded": {}, "rows": []}
prompt_ids = tok(render(tok, TASKS["fictional_cli__impossible"], final_turn_as_user=True), add_special_tokens=False)["input_ids"]
for r in rows:
    lab = J.get(r["sample_index"], {}).get("label")
    grp = {"false_claim": "fabrication", "honest_failure": "refusal"}.get(lab)
    if grp is None or not r["closed_think"] or r["n_answer_tokens"] == 0:
        out["excluded"][str(lab)] = out["excluded"].get(str(lab), 0) + 1; continue
    g = r["generated_token_ids"]; k = g.index(THINK_CLOSE_ID); j = k + 1
    while j < len(g) and tok.decode([g[j]]).strip() == "": j += 1
    ids = t.tensor([prompt_ids + g], device="cuda:0"); n = len(prompt_ids)
    rec = {"sample_index": r["sample_index"], "group": grp, "answer_head": tok.decode(g[k+1:k+10]),
           "at_close": ranks(ids, n + j - 1), "at_first": ranks(ids, n + j)}
    for where in ("at_close", "at_first"):
        rec[where + "_median"] = {l: {kind: statistics.median(rec[where][l][kind][tg] for tg in TOKENS) for kind in ("j", "ll")} for l in LAYERS}
    out["rows"].append(rec); print(grp, r["sample_index"], repr(rec["answer_head"][:30]), "| median ` not`-set rank L24 j:", rec["at_first_median"][24]["j"], flush=True)
tests = {}
for where in ("at_close", "at_first"):
    for l in (20, 24):
        for kind in ("j", "ll"):
            a = [x[where + "_median"][l][kind] for x in out["rows"] if x["group"] == "refusal"]
            b = [x[where + "_median"][l][kind] for x in out["rows"] if x["group"] == "fabrication"]
            if len(a) >= 2 and len(b) >= 2:
                u, p = mannwhitneyu(a, b, alternative="less")
                tests[f"{where}|L{l}|{kind}"] = {"n_refusal": len(a), "n_fabrication": len(b), "U": float(u), "p_one_sided": float(p),
                                                 "rank_biserial": 1 - 2*u/(len(a)*len(b)), "median_refusal": statistics.median(a), "median_fabrication": statistics.median(b)}
out["tests"] = tests; out["n_by_group"] = {g: sum(x["group"] == g for x in out["rows"]) for g in ("fabrication", "refusal")}
for k_, v in tests.items(): print(f"{k_:<20} ref n={v['n_refusal']} med={v['median_refusal']:.0f} | fab n={v['n_fabrication']} med={v['median_fabrication']:.0f} | p={v['p_one_sided']:.2e} r_rb={v['rank_biserial']:.2f}")
print("groups:", out["n_by_group"], "| excluded:", out["excluded"])
(ROOT/"experiments"/"h2_results.json").write_text(json.dumps(out, indent=1)); print("wrote experiments/h2_results.json")
