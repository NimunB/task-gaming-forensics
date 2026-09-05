"""Option (c): Jacobian-lens readout on GPT-OSS-20B at the false "18 passed" (and the true ones). GPU.

test_regression on GPT-OSS: impossible variants where the model claims "18 passed" (truth: 17 pass, one
fails) vs possible variants where "18 passed" is true. GPT-OSS tokenizes "18" and "17" as single tokens
(1157, 1422), so the readout is at the position that PREDICTS the count token: rank of `17` (truth in the
false case) and `18`, J-lens and plain logit lens, every source layer. Also, at the position predicting the
word after the count ("passed"/"pass"): rank of ` failed`/` fail` vs ` passed`/` pass`.
These responses were produced with ZERO analysis-channel tokens (REPORT §3.17) — the lens is the only
place to look for whether the model carried the true count.

    python experiments/gptoss_lens_c.py            # reads gptoss_impossible/possible + gptoss_tr_* if present
Writes experiments/gptoss_lens_c.json.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import torch as t
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import load_tasks, messages_for  # noqa: E402
from task_gaming.jlens_readout import JLens, unembed  # noqa: E402
MODEL = "openai/gpt-oss-20b"; LENS = ROOT/"experiments"/"lenses"/"gpt-oss-20b"/"jlens"/"Salesforce-wikitext"/"gpt-oss-20b_jacobian_lens.pt"
TRUTH = {"test_regression__impossible": 17, "test_regression__possible": 18}
TASKS = {x["id"]: x for x in load_tasks()}
tok = AutoTokenizer.from_pretrained(MODEL); model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()
lens = JLens(LENS); LAYERS = [l for l in lens.source_layers if l % 2 == 0]
print(f"lens: layers {lens.source_layers[0]}..{lens.source_layers[-1]}, anchor L{lens.target_layer} dist {lens.anchor_dist:.3f} (identity_anchor={lens.identity_anchor})", flush=True)
T18, T17 = tok("18", add_special_tokens=False)["input_ids"][0], tok("17", add_special_tokens=False)["input_ids"][0]
WORDS = {w: tok(w, add_special_tokens=False)["input_ids"] for w in (" passed", " pass", " failed", " fail", " fails", "17", "18")}
def load(n): p = ROOT/"experiments"/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
rows = [r for f in ("gptoss_impossible.jsonl", "gptoss_possible.jsonl", "gptoss_tr_impossible25.jsonl", "gptoss_tr_possible10.jsonl") for r in load(f) if r["setting"] == "test_regression"]
def full_ids(r):
    task = TASKS[r["task_id"]]; kw = {"tools": task["tools"]} if task.get("tools") else {}
    prompt = tok.apply_chat_template(messages_for(task, final_turn_as_user=True, harmony=True), tokenize=False, add_generation_prompt=True, **kw)
    pid = tok(prompt, add_special_tokens=False)["input_ids"]; return t.tensor([pid + r["generated_token_ids"]], device="cuda:0"), len(pid)
@t.no_grad()
def ranks(ids, p, targets):
    out = model(input_ids=ids, output_hidden_states=True); res = {}
    for l in LAYERS:
        h = out.hidden_states[l+1][0, p]; res[l] = {}
        for kind, x in (("j", lens.transport(h, l)), ("ll", h.float())):
            lg = unembed(model, x); res[l][kind] = {n: (int((lg > lg[i[0]]).sum()) if len(i) == 1 else None) for n, i in targets.items()}
            res[l][kind]["top6"] = [tok.decode([i]) for i in lg.topk(6).indices.tolist()]
    return res, tok.decode([int(out.logits[0, p].argmax())])
out = {"lens": {"path": str(LENS), "anchor_layer": lens.target_layer, "anchor_dist": lens.anchor_dist}, "rows": []}
for r in rows:
    if not r["closed_think"] or r["n_answer_tokens"] == 0: continue
    ids, n = full_ids(r); g = ids[0, n:].tolist(); truth = TRUTH[r["task_id"]]
    # positions where the model emits the count token (18 or 17) in the ANSWER part
    for j, tid in enumerate(g):
        if tid in (T18, T17):
            stated = 18 if tid == T18 else 17; p = n + j - 1
            ctx = tok.decode(ids[0, p-8:p+3].tolist())
            if not re.search(r"test|pass|suite|unit", ctx, re.I): continue   # only count statements about tests
            rk, nxt = ranks(ids, p, {"17": WORDS["17"], "18": WORDS["18"]})
            rec = {"task_id": r["task_id"], "sample_index": r["sample_index"], "source": "pilot" if r["sample_index"] < 5 else "widen",
                   "stated": stated, "truth": truth, "false": stated != truth, "context": ctx, "actual_next": nxt, "n_thinking_tokens": r["n_thinking_tokens"],
                   "count_pos": {l: {"j17": rk[l]["j"]["17"], "j18": rk[l]["j"]["18"], "ll17": rk[l]["ll"]["17"], "ll18": rk[l]["ll"]["18"], "j_top6": rk[l]["j"]["top6"]} for l in LAYERS}}
            # word after the count: position predicting "passed"/"pass"
            p2 = n + j
            rk2, nxt2 = ranks(ids, p2, {"passed": WORDS[" passed"], "pass": WORDS[" pass"], "failed": WORDS[" failed"], "fail": WORDS[" fail"], "fails": WORDS[" fails"]})
            rec["after_count_pos"] = {"actual_next": nxt2, **{l: {k: rk2[l]["j"][k] for k in ("passed", "pass", "failed", "fail", "fails")} | {"ll_failed": rk2[l]["ll"]["failed"], "j_top6": rk2[l]["j"]["top6"]} for l in LAYERS}}
            out["rows"].append(rec)
            print(f"{r['task_id'].split('__')[1]:<10} #{r['sample_index']:<3} stated={stated} truth={truth} {'FALSE' if stated!=truth else 'true '} | ctx={ctx!r} | j17@L16={rk[16]['j']['17']} j18@L16={rk[16]['j']['18']} j17@L20={rk[20]['j']['17']} j18@L20={rk[20]['j']['18']} | failed@after L16={rk2[16]['j']['failed']}", flush=True)
            break
(ROOT/"experiments"/"gptoss_lens_c.json").write_text(json.dumps(out, indent=1)); print("wrote experiments/gptoss_lens_c.json;", len(out["rows"]), "count statements read")
