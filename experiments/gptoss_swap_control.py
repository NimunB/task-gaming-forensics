"""H5b (PREREGISTRATION §8): same prompt, swapped count token. For each of the 35 GPT-OSS count statements,
forward the original (stated 18) and a copy with the count token swapped to 17. Score with the truth LR probe
(L16) and the deception LR/MM probes (L12), retrained deterministically from the Apollo data and saved to
experiments/exported_probes/. Δ = score(18) − score(17); a truth-tracking probe predicts Δ>0 when 18 is false
(impossible prompt) and Δ<0 when 18 is true (possible prompt).

    python experiments/gptoss_swap_control.py [--statements FILE.jsonl ...]   # GPU; writes gptoss_swap_control.json
Optional --statements: extra response files (H7 replication) — default is the four §3.18 files.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd, torch as t
from scipy.stats import fisher_exact
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import load_tasks, messages_for  # noqa: E402
from task_gaming.vendor_import import load_safety_probes  # noqa: E402
sp = load_safety_probes(("runtime", "probes", "datasets")); LRProbe, MMProbe, drop_last_words = sp.probes.LRProbe, sp.probes.MMProbe, sp.datasets.drop_last_words
HONEST_SYS, DISHONEST_SYS, PAIR_USER_MSG = sp.datasets.HONEST_SYS, sp.datasets.DISHONEST_SYS, sp.datasets.PAIR_USER_MSG
ap = argparse.ArgumentParser(); ap.add_argument("--statements", nargs="*", default=["gptoss_impossible.jsonl", "gptoss_possible.jsonl", "gptoss_tr_impossible25.jsonl", "gptoss_tr_possible10.jsonl"])
ap.add_argument("--out", default="gptoss_swap_control.json"); a = ap.parse_args()
SEED = 42; t.manual_seed(SEED); np.random.seed(SEED); MODEL = "openai/gpt-oss-20b"; L_TRUTH, L_DECEP = 16, 12
TRUTH = {"test_regression__impossible": 17, "test_regression__possible": 18}; DATA = ROOT/"vendor"/"Probing-Safety-Behaviours"/"data"
PROBES = ROOT/"experiments"/"exported_probes"; PROBES.mkdir(exist_ok=True)
tok = AutoTokenizer.from_pretrained(MODEL); model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()
TASKS = {x["id"]: x for x in load_tasks()}; T18, T17 = tok("18", add_special_tokens=False)["input_ids"][0], tok("17", add_special_tokens=False)["input_ids"][0]

# ---- probes: retrain (deterministic) or load ----
def split(xs):
    perm = t.randperm(len(xs), generator=t.Generator().manual_seed(SEED)).tolist(); n = int(0.8*len(xs)); return [xs[i] for i in perm[:n]]
@t.no_grad()
def assistant_mean(sysm, content, layer):
    msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": PAIR_USER_MSG}, {"role": "assistant", "content": content}]
    full = tok.apply_chat_template(msgs, tokenize=False); pre = tok.apply_chat_template(msgs[:2], tokenize=False, add_generation_prompt=True) + "<|channel|>final<|message|>"
    ids = tok(full, add_special_tokens=False, return_tensors="pt")["input_ids"].to("cuda:0"); n_pre = len(tok(pre, add_special_tokens=False)["input_ids"])
    return model(input_ids=ids, output_hidden_states=True).hidden_states[layer+1][0, n_pre:ids.shape[1]-1].float().mean(0).cpu()
def get_probes():
    f = PROBES/"gptoss_probes_h5.pt"
    if f.exists():
        d = t.load(f); print("loaded", f); return d
    df = pd.read_csv(DATA/"repe"/"true_false_facts.csv"); tr_true, tr_false = split(df[df.label == 1].statement.tolist()), split(df[df.label == 0].statement.tolist())
    items_truth = [("You are a helpful AI assistant.", s, 0.0) for s in tr_true] + [("You are a helpful AI assistant.", s, 1.0) for s in tr_false]
    items_dec = [(sysm, drop_last_words(s), lab) for s in tr_true for sysm, lab in ((DISHONEST_SYS, 1.0), (HONEST_SYS, 0.0))]
    out = {}
    for name, items, L in (("truth", items_truth, L_TRUTH), ("deception", items_dec, L_DECEP)):
        print(f"retraining {name} probe at L{L} on {len(items)}", flush=True)
        X = t.stack([assistant_mean(s, c, L) for s, c, _ in items]); y = t.tensor([l for *_, l in items])
        lr, mm = LRProbe.from_data(X, y), MMProbe.from_data(X, y)
        out[name] = {"layer": L, "lr_w": lr.net.weight.data[0].clone(), "scaler_mean": lr.scaler_mean.clone(), "scaler_scale": lr.scaler_scale.clone(), "mm_dir": mm.direction.data.clone()}
    t.save(out, f); print("saved", f); return out
P = get_probes()
def score(name, kind, x):
    d = P[name]; x = x.float()
    return float(((x - d["scaler_mean"]) / d["scaler_scale"]) @ d["lr_w"]) if kind == "lr" else float(x @ d["mm_dir"])

# ---- statements ----
def load(n): p = ROOT/"experiments"/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
rows = [r for f in a.statements for r in load(f) if r["setting"] == "test_regression"]
def full_ids(r):
    task = TASKS[r["task_id"]]; kw = {"tools": task["tools"]} if task.get("tools") else {}
    prompt = tok.apply_chat_template(messages_for(task, final_turn_as_user=True, harmony=True), tokenize=False, add_generation_prompt=True, **kw)
    pid = tok(prompt, add_special_tokens=False)["input_ids"]; return t.tensor([pid + r["generated_token_ids"]], device="cuda:0"), len(pid)
g = t.Generator().manual_seed(SEED); RND = [(lambda d: d/d.norm())(t.randn(model.config.hidden_size, generator=g)) for _ in range(20)]
recs = []
with t.no_grad():
    for r in rows:
        if not r["closed_think"] or r["n_answer_tokens"] == 0: continue
        ids, n = full_ids(r); gen = ids[0, n:].tolist(); truth = TRUTH[r["task_id"]]
        for j, tid in enumerate(gen):
            if tid in (T18, T17):
                p = n + j - 1; ctx = tok.decode(ids[0, p-8:p+3].tolist())
                if not re.search(r"test|pass|suite|unit", ctx, re.I): continue
                if tid != T18: break   # all statements in hand say 18; a stated 17 has nothing to swap to symmetrically — record and skip
                sw = ids.clone(); sw[0, p+1] = T17
                rec = {"task_id": r["task_id"], "sample_index": r["sample_index"], "truth": truth, "eighteen_is_false": truth != 18, "context": ctx}
                for tag, x in (("orig18", ids), ("swap17", sw)):
                    hs = model(input_ids=x, output_hidden_states=True).hidden_states
                    for name in ("truth", "deception"):
                        L = P[name]["layer"]; ct, pm = hs[L+1][0, p+1].float().cpu(), hs[L+1][0, p+1:].float().mean(0).cpu()
                        rec[f"{name}_lr_count_{tag}"] = score(name, "lr", ct); rec[f"{name}_lr_post_{tag}"] = score(name, "lr", pm)
                        rec[f"{name}_mm_count_{tag}"] = score(name, "mm", ct)
                    h16 = hs[L_TRUTH+1][0, p+1].float().cpu(); rec[f"rnd_count_{tag}"] = [float(h16 @ d) for d in RND]
                recs.append(rec); break
def summarise(key):
    imp = [x for x in recs if x["eighteen_is_false"]]; pos = [x for x in recs if not x["eighteen_is_false"]]
    d = lambda x: x[f"{key}_orig18"] - x[f"{key}_swap17"]
    a_ = sum(d(x) > 0 for x in imp); b_ = sum(d(x) < 0 for x in pos)
    p_ = fisher_exact([[a_, len(imp)-a_], [len(pos)-b_, b_]], alternative="greater")[1] if imp and pos else None
    return {"imp_delta_pos": f"{a_}/{len(imp)}", "pos_delta_neg": f"{b_}/{len(pos)}", "median_delta_imp": float(np.median([d(x) for x in imp])) if imp else None, "median_delta_pos": float(np.median([d(x) for x in pos])) if pos else None, "fisher_p": p_}
summary = {k: summarise(k) for k in ("truth_lr_count", "truth_lr_post", "truth_mm_count", "deception_lr_count", "deception_lr_post", "deception_mm_count")}
# random directions: how many of 20 show the interaction pattern at the same ≥80%/≥80% bar
imp = [x for x in recs if x["eighteen_is_false"]]; pos = [x for x in recs if not x["eighteen_is_false"]]; n_int = 0
for k in range(20):
    a_ = sum(x["rnd_count_orig18"][k] - x["rnd_count_swap17"][k] > 0 for x in imp); b_ = sum(x["rnd_count_orig18"][k] - x["rnd_count_swap17"][k] < 0 for x in pos)
    a2 = len(imp) - a_; b2 = len(pos) - b_   # the opposite-sign interaction counts too
    if (a_ >= .8*len(imp) and b_ >= .8*len(pos)) or (a2 >= .8*len(imp) and b2 >= .8*len(pos)): n_int += 1
summary["random_directions_with_interaction"] = f"{n_int}/20"
out = {"n": len(recs), "n_impossible": len(imp), "n_possible": len(pos), "summary": summary, "rows": recs}
(ROOT/"experiments"/a.out).write_text(json.dumps(out, indent=1))
for k, v in summary.items(): print(k, v)
print("wrote", a.out, len(recs), "statements")
