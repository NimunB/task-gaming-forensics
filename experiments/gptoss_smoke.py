"""Step-1-style smoke test for openai/gpt-oss-20b (PREREGISTRATION step H; Concrete Problems doc's
recommended internals model). Same five questions as experiments/step1_smoke.py, for a new model with a
different (Harmony) chat format:

  1. Loads in bf16 (MXFP4 MoE weights dequantized by transformers; no `kernels` package)?
  2. Decoder path, layer count, hidden size; hook vs output_hidden_states agreement.
  3. All 10 tasks render? Tool calls / tool results render? Prompt ends with `<|start|>assistant`?
  4. Thinking/answer split: Harmony puts reasoning in `<|channel|>analysis<|message|>...<|end|>` and the
     reply in `<|channel|>final<|message|>...<|return|>`; tool calls go to the commentary channel and end
     with `<|call|>`. Stop ids from generation_config: [200002 <|return|>, 199999, 200012 <|call|>].
  5. One sample on fictional_cli__impossible at T=0.7: does it close analysis and produce a final?

Writes experiments/gptoss_smoke.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import torch as t
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import load_tasks, messages_for  # noqa: E402
MODEL = "openai/gpt-oss-20b"; OUT = ROOT/"experiments"/"gptoss_smoke.json"
CH, MSG, START, END, RET, CALL = 200005, 200008, 200006, 200007, 200002, 200012
rep = {"model": MODEL}
tok = AutoTokenizer.from_pretrained(MODEL)
t0 = time.time(); model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()
rep["load"] = {"seconds": round(time.time()-t0), "vram_GB": round(t.cuda.memory_allocated()/1e9, 1), "dtype": str(next(model.parameters()).dtype)}
cfg = model.config; rep["config"] = {"layers": cfg.num_hidden_layers, "hidden": cfg.hidden_size, "experts": getattr(cfg, "num_local_experts", None), "arch": cfg.architectures}
layers = model.model.layers; rep["decoder_path"] = "model.model.layers"; rep["n_layers_found"] = len(layers)
print(json.dumps({k: rep[k] for k in ("load", "config")}), flush=True)
# hook check
cap = {}; h = layers[12].register_forward_hook(lambda m, i, o: cap.__setitem__("x", (o[0] if isinstance(o, tuple) else o).detach()))
enc = tok("The capital of France is", return_tensors="pt").to("cuda:0")
with t.no_grad(): out = model(**enc, output_hidden_states=True)
h.remove(); rep["hook_check"] = {"layer": 12, "max_abs_diff_vs_hidden_states[13]": float((cap["x"].float()-out.hidden_states[13].float()).abs().max()), "n_hidden_states": len(out.hidden_states),
                                 "lm_head(hs[-1])==logits": float((model.lm_head(out.hidden_states[-1])[0].float()-out.logits[0].float()).abs().max())}
print("hook:", rep["hook_check"], flush=True)
# render all tasks (arguments must be a dict? try both; the Qwen dictify is applied by messages_for's caller — here we pass raw then dictified)
rows = []
for task in load_tasks():
    for variant in ("dictified",):
        msgs = messages_for(task, final_turn_as_user=True, harmony=True)  # dictify args + Harmony None-content fix
        kw = {"tools": task["tools"]} if task.get("tools") else {}
        try:
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kw)
            ids = tok(text, add_special_tokens=False)["input_ids"]
            rows.append({"id": task["id"], "ok": True, "n_tokens": len(ids), "tail": text[-60:], "ends_start_assistant": text.rstrip().endswith("<|start|>assistant"),
                         "has_tool_msgs": any(m["role"] == "tool" for m in msgs)})
        except Exception as e:
            rows.append({"id": task["id"], "ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})
    print(rows[-1], flush=True)
rep["render"] = rows; rep["render_all_ok"] = all(r["ok"] for r in rows)
# one generation
task = next(x for x in load_tasks() if x["id"] == "fictional_cli__impossible")
text = tok.apply_chat_template(messages_for(task, final_turn_as_user=True, harmony=True), tokenize=False, add_generation_prompt=True)
enc = tok(text, return_tensors="pt", add_special_tokens=False).to("cuda:0"); n = enc["input_ids"].shape[1]
t.manual_seed(42)
with t.no_grad():
    gen = model.generate(**enc, max_new_tokens=2048, do_sample=True, temperature=0.7, top_p=0.95, eos_token_id=[RET, 199999, CALL], pad_token_id=199999)
ids = gen[0, n:].tolist(); raw = tok.decode(ids, skip_special_tokens=False)
def find_seq(seq, sub):
    for i in range(len(seq)-len(sub)+1):
        if seq[i:i+len(sub)] == sub: return i
    return -1
fin = tok("<|channel|>final<|message|>", add_special_tokens=False)["input_ids"]; k = find_seq(ids, fin)
rep["generation"] = {"n_new": len(ids), "stopped_on": tok.decode([ids[-1]]) if ids else None, "has_final_channel": k >= 0,
                     "n_analysis_tokens": k if k >= 0 else None, "n_final_tokens": (len(ids)-k-len(fin)) if k >= 0 else None,
                     "raw_head": raw[:400], "final_text": tok.decode(ids[k+len(fin):], skip_special_tokens=True)[:600] if k >= 0 else None}
print(json.dumps(rep["generation"], indent=1)[:1500], flush=True)
OUT.write_text(json.dumps(rep, indent=1)); print("wrote", OUT)
