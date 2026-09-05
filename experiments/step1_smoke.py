"""Step 1 smoke test .

Answers five questions and writes experiments/step1_smoke.json:
  1. Does the model load in bf16 on one card, and with which Auto class?
  2. Where are the text decoder layers inside the VL wrapper, and how many?
  3. Does a forward hook on a decoder layer give the residual stream, and does it agree with
     output_hidden_states (a cross-check, so later steps trust one hook point)?
  4. Do all 10 tasks render through the chat template — tool_calls and role:tool included —
     and does every prompt end with the open thinking tag? What are the token counts?
  5. On a real generation, can thinking tokens and answer tokens be separated by token offset,
     and do the two pools give different activations?

Run: python experiments/step1_smoke.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch as t
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from task_gaming.prompts import load_tasks, render  # noqa: E402

MODEL = "Qwen/Qwen3.5-9B"
SEED = 42
HOOK_LAYER = 16          # arbitrary mid-stack layer, per the brief; the sweep happens in Step 5
MAX_NEW_TOKENS = 4096   # 1024 was not enough: the model was still inside <think> (first run)
OUT = ROOT / "experiments" / "step1_smoke.json"

report: dict = {"model": MODEL, "seed": SEED}


def section(msg: str) -> None:
    print(f"\n{'=' * 70}\n{msg}\n{'=' * 70}", flush=True)


# ---------------------------------------------------------------- 1. load
section("1. Load model in bf16")
tok = AutoTokenizer.from_pretrained(MODEL)

load_errors = {}
model = None
for cls_name in ("AutoModelForCausalLM", "AutoModelForImageTextToText", "Qwen3_5ForConditionalGeneration"):
    try:
        import transformers

        cls = getattr(transformers, cls_name)
        model = cls.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0")
        report["auto_class"] = cls_name
        print(f"loaded with {cls_name}")
        break
    except Exception as e:  # noqa: BLE001 — we want the reason logged, then try the next class
        load_errors[cls_name] = f"{type(e).__name__}: {e}"
        print(f"{cls_name} failed: {type(e).__name__}: {e}")
if model is None:
    report["load_errors"] = load_errors
    OUT.write_text(json.dumps(report, indent=2))
    raise SystemExit("no Auto class could load the model — see experiments/step1_smoke.json")
report["load_errors"] = load_errors
model.eval()

cfg = model.config
text_cfg = getattr(cfg, "text_config", cfg)
report["config"] = {
    "architectures": cfg.architectures,
    "num_hidden_layers": text_cfg.num_hidden_layers,
    "hidden_size": text_cfg.hidden_size,
    "dtype": str(next(model.parameters()).dtype),
    "device": str(next(model.parameters()).device),
    "vram_allocated_GB": round(t.cuda.memory_allocated() / 1e9, 2),
}
print(json.dumps(report["config"], indent=2))

# ---------------------------------------------------------------- 2. find decoder layers
section("2. Locate the text decoder inside the VL wrapper")
candidates = [
    "model.language_model.layers",
    "model.model.language_model.layers",
    "model.layers",
    "language_model.model.layers",
]


def resolve(root, path: str):
    obj = root
    for part in path.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


layers, layers_path = None, None
for path in candidates:
    got = resolve(model, path)
    if got is not None and hasattr(got, "__len__"):
        layers, layers_path = got, path
        break
if layers is None:
    report["decoder_search"] = {"tried": candidates, "top_level_children": [n for n, _ in model.named_children()]}
    OUT.write_text(json.dumps(report, indent=2))
    raise SystemExit("could not find decoder layers — see experiments/step1_smoke.json")

report["decoder_layers_path"] = layers_path
report["n_decoder_layers"] = len(layers)
report["decoder_layer_class"] = type(layers[0]).__name__
print(f"decoder layers at model.{layers_path}  (n={len(layers)}, {type(layers[0]).__name__})")
assert len(layers) == text_cfg.num_hidden_layers, "layer count disagrees with config"

# ---------------------------------------------------------------- 3. hook == hidden_states?
section("3. Forward hook on one layer vs output_hidden_states")
captured = {}


def grab(_mod, _inp, out):
    captured["resid"] = (out[0] if isinstance(out, tuple) else out).detach().float().cpu()


probe_text = "The capital of France is Paris, and the capital of Japan is Tokyo."
enc = tok(probe_text, return_tensors="pt").to(model.device)
h = layers[HOOK_LAYER].register_forward_hook(grab)
with t.no_grad():
    out = model(**enc, output_hidden_states=True)
h.remove()

hs = out.hidden_states[HOOK_LAYER + 1].float().cpu()
max_abs_diff = (captured["resid"] - hs).abs().max().item()
report["hook_check"] = {
    "layer": HOOK_LAYER,
    "hook_shape": list(captured["resid"].shape),
    "hidden_states_index": HOOK_LAYER + 1,
    "max_abs_diff": max_abs_diff,
    "agree": max_abs_diff < 1e-3,
    "n_hidden_states": len(out.hidden_states),
}
print(json.dumps(report["hook_check"], indent=2))

# ---------------------------------------------------------------- 4. render all tasks
section("4. Render all 10 tasks through the chat template")
tasks = load_tasks()
think_open = "<think>"
rows = []
for task in tasks:
    row = {"id": task["id"], "setting": task["setting"], "possible": task["possible"],
           "n_messages": len(task["messages"]), "has_tools": bool(task.get("tools"))}
    try:
        text = render(tok, task)
        ids = tok(text, add_special_tokens=False)["input_ids"]
        row.update(
            rendered_ok=True,
            n_prompt_tokens=len(ids),
            tail_repr=repr(text[-40:]),
            ends_with_open_think=text.rstrip("\n").endswith(think_open) or text.endswith("<think>\n"),
            n_tool_role_msgs=sum(1 for m in task["messages"] if m["role"] == "tool"),
            n_tool_call_msgs=sum(1 for m in task["messages"] if m.get("tool_calls")),
        )
    except Exception as e:  # noqa: BLE001
        row.update(rendered_ok=False, error=f"{type(e).__name__}: {e}")
    rows.append(row)
    print(f"{row['id']:<34} ok={row['rendered_ok']}  tokens={row.get('n_prompt_tokens')}  "
          f"tool_msgs={row.get('n_tool_role_msgs')}/{row.get('n_tool_call_msgs')}  "
          f"ends_open_think={row.get('ends_with_open_think')}  tail={row.get('tail_repr')}")
report["render"] = rows
report["render_all_ok"] = all(r["rendered_ok"] for r in rows)
report["render_all_end_open_think"] = all(r.get("ends_with_open_think") for r in rows)

# thinking-tag token ids, for the offset bookkeeping later steps depend on
report["think_tags"] = {
    tag: {"ids": tok(tag, add_special_tokens=False)["input_ids"], "single_token": len(tok(tag, add_special_tokens=False)["input_ids"]) == 1}
    for tag in ("<think>", "</think>", "\n</think>")
}
print("\nthink tag token ids:", json.dumps(report["think_tags"]))

# ---------------------------------------------------------------- 5. thinking vs answer split
section("5. Generate once, split thinking from answer, pool activations separately")
task = next(x for x in tasks if x["id"] == "fictional_cli__impossible")
prompt = render(tok, task)
enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
n_prompt = enc["input_ids"].shape[1]

t.manual_seed(SEED)
with t.no_grad():
    gen = model.generate(**enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=True, temperature=0.7,
                         top_p=0.95, pad_token_id=tok.eos_token_id)
new_ids = gen[0, n_prompt:].tolist()
gen_text = tok.decode(new_ids, skip_special_tokens=False)

close_ids = tok("</think>", add_special_tokens=False)["input_ids"]
close_id = close_ids[0] if len(close_ids) == 1 else None
think_end = new_ids.index(close_id) if (close_id is not None and close_id in new_ids) else None

report["generation"] = {
    "task": task["id"], "n_prompt_tokens": n_prompt, "n_generated_tokens": len(new_ids),
    "closed_think": think_end is not None,
    "think_end_offset_in_generation": think_end,
    "n_thinking_tokens": think_end if think_end is not None else None,
    "n_answer_tokens": (len(new_ids) - think_end - 1) if think_end is not None else None,
    "generated_text_head": gen_text[:600],
    "generated_text_tail": gen_text[-600:],
}
print(json.dumps({k: v for k, v in report["generation"].items() if not k.startswith("generated_text")}, indent=2))

if think_end is not None:
    # absolute positions in the full sequence
    think_slice = slice(n_prompt, n_prompt + think_end)
    answer_slice = slice(n_prompt + think_end + 1, gen.shape[1])
    h = layers[HOOK_LAYER].register_forward_hook(grab)
    with t.no_grad():
        model(input_ids=gen)
    h.remove()
    resid = captured["resid"][0]                      # [seq, d_model]
    pools = {
        "prompt": resid[:n_prompt].mean(0),
        "thinking": resid[think_slice].mean(0),
        "answer": resid[answer_slice].mean(0),
    }
    report["pooled_activations"] = {
        "layer": HOOK_LAYER,
        "d_model": int(resid.shape[1]),
        "n_tokens": {k: int(v) for k, v in
                     {"prompt": n_prompt, "thinking": think_end, "answer": gen.shape[1] - (n_prompt + think_end + 1)}.items()},
        "norms": {k: round(v.norm().item(), 3) for k, v in pools.items()},
        "cosine_thinking_vs_answer": round(t.nn.functional.cosine_similarity(
            pools["thinking"], pools["answer"], dim=0).item(), 4),
        "cosine_prompt_vs_answer": round(t.nn.functional.cosine_similarity(
            pools["prompt"], pools["answer"], dim=0).item(), 4),
        "any_nan": bool(t.isnan(resid).any().item()),
    }
    print(json.dumps(report["pooled_activations"], indent=2))
else:
    report["pooled_activations"] = (
        f"did not run — generation never closed </think> within {MAX_NEW_TOKENS} new tokens")

# ---------------------------------------------------------------- 6. batched generation
# Step 2 samples each task 3 times and Step 6 samples 30 times; batching is what keeps those
# inside their time boxes. Generation needs LEFT padding (the thesis extractor sets right padding
# for pooling, so the two must never share a tokenizer setting without being explicit).
section("6. Batched generation with left padding, and throughput")
import time  # noqa: E402

if tok.pad_token is None:
    tok.pad_token = tok.eos_token
tok.padding_side = "left"
batch_prompts = [render(tok, task)] * 3
benc = tok(batch_prompts, return_tensors="pt", add_special_tokens=False, padding=True).to(model.device)
t.manual_seed(SEED)
start = time.time()
with t.no_grad():
    bgen = model.generate(**benc, max_new_tokens=512, do_sample=True, temperature=0.7, top_p=0.95,
                          pad_token_id=tok.pad_token_id)
elapsed = time.time() - start
n_new = bgen.shape[1] - benc["input_ids"].shape[1]
texts = [tok.decode(bgen[i, benc["input_ids"].shape[1]:], skip_special_tokens=False) for i in range(3)]
report["batched_generation"] = {
    "batch_size": 3,
    "padding_side": tok.padding_side,
    "new_tokens_each": int(n_new),
    "seconds": round(elapsed, 1),
    "tokens_per_second_total": round(3 * n_new / elapsed, 1),
    "all_three_differ": len(set(texts)) == 3,
    "first_80_chars_each": [x[:80] for x in texts],
}
print(json.dumps(report["batched_generation"], indent=2))

OUT.write_text(json.dumps(report, indent=2))
print(f"\nwrote {OUT}")
