"""experiments/results.json — every headline number in REPORT.md, pulled from the analysis outputs (never typed in).
Re-run after any analysis changes.    python experiments/make_results_json.py
"""
from __future__ import annotations
import json, math
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; E = ROOT/"experiments"
def J(n): p = E/n; return json.load(open(p)) if p.exists() else None
def L(n): p = E/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
def wilson(k, n, z=1.96):
    if n == 0: return None
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return {"k": k, "n": n, "rate": p, "wilson95": [(c-h)/d, (c+h)/d]}
GAMED = {"false_claim", "silent_omission", "workaround_as_complete"}
def counts(files):
    rows = [r for f in files for r in L(f)]; c = Counter(r["label"] for r in rows)
    return {"n": len(rows), "labels": dict(c), "gamed": wilson(sum(c[k] for k in GAMED), len(rows)),
            "per_setting": {s: {"n": sum(r["setting"] == s for r in rows), "labels": dict(Counter(r["label"] for r in rows if r["setting"] == s))} for s in sorted({r["setting"] for r in rows})}}
h1, h2, h34, lc, pr, sw = J("h1_results.json"), J("h2_results.json"), J("h3h4_results.json"), J("gptoss_lens_c_summary.json"), J("gptoss_probe.json"), J("gptoss_swap_control.json")
out = {
 "qwen3.5-9b": {"confirmatory_impossible": counts(["judge__samples_impossible.jsonl"]), "confirmatory_possible": counts(["judge__samples_possible.jsonl"]),
                "strict_impossible": counts(["judge_strict__samples_impossible.jsonl"]), "seed43_impossible": counts(["judge__samples_seed43.jsonl"]),
                "H1": h1 and h1["H1"], "H2": h2 and h2["tests"], "H3_H4": h34},
 "gpt-oss-20b": {"pilot_widening_impossible": counts(["judge__gptoss_impossible.jsonl", "judge__gptoss_tr_impossible25.jsonl", "judge__gptoss_fcli50.jsonl"]),
                 "pilot_widening_possible": counts(["judge__gptoss_possible.jsonl", "judge__gptoss_tr_possible10.jsonl"]),
                 "confirmatory_impossible_seed43": counts(["judge__gptoss_confirm_impossible.jsonl"]), "confirmatory_possible_seed43": counts(["judge__gptoss_confirm_possible.jsonl"]),
                 "confirmatory_strict_impossible_seed43": counts(["judge_strict__gptoss_confirm_impossible.jsonl"]),
                 "zero_analysis_tokens_among_false_claims": None,
                 "lens_true_count_L20": lc and {"n_false": lc["n_false"], "n_true": lc["n_true"], **lc["per_layer"].get("20", {})},
                 "lens_neighbours_original35": (lambda d: d and {"n_false": d["n_false"], "n_true": d["n_true"], "L20": d["per_layer"].get("20")})(J("gptoss_lens_c_summary_neighbours.json")),
                 "lens_true_count_confirm": (lambda d: d and {"n_false": d["n_false"], "n_true": d["n_true"], **d["per_layer"].get("20", {})})(J("gptoss_lens_c_confirm_summary.json")),
                 "H5_probe": pr and {n: {"chosen_layer": p["chosen_layer"], "heldout_auroc_lr": p["per_layer"][str(p["chosen_layer"])]["heldout_auroc_lr"],
                                        **{k: p["per_layer"][str(p["chosen_layer"])][k] for k in ("pred_pos_lr", "count_tok_lr", "answer_mean_lr", "prompt_mean_lr")}, "random_directions_p95": p["random_directions_p95"]} for n, p in pr["probes"].items()},
                 "H5b_swap_control": sw and sw["summary"], "H5b_swap_control_confirm": (lambda d: d and d["summary"])(J("gptoss_swap_control_confirm.json"))}}
# zero-analysis-token share among judged false claims (GPT-OSS)
resp = {(r["task_id"], r["sample_index"], f): r for f in ("gptoss_impossible.jsonl", "gptoss_tr_impossible25.jsonl", "gptoss_fcli50.jsonl", "gptoss_confirm_impossible.jsonl") for r in L(f)}
fc = [(j["task_id"], j["sample_index"], f) for f in ("gptoss_impossible.jsonl", "gptoss_tr_impossible25.jsonl", "gptoss_fcli50.jsonl", "gptoss_confirm_impossible.jsonl") for j in L(f"judge__{f}") if j["label"] == "false_claim"]
z = [resp[k]["n_thinking_tokens"] == 0 for k in fc if k in resp]
out["gpt-oss-20b"]["zero_analysis_tokens_among_false_claims"] = wilson(sum(z), len(z))
(E/"results.json").write_text(json.dumps(out, indent=1)); print("wrote experiments/results.json")
