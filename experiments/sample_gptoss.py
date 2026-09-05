"""Batched sampler for openai/gpt-oss-20b (PREREGISTRATION step H). Same interface as sample.py; Harmony format.

Differences from the Qwen sampler, all from the model's own chat template and generation_config:
  * prompt is rendered with `messages_for(..., harmony=True)` and ends with `<|start|>assistant`;
  * reasoning arrives as `<|channel|>analysis<|message|>...<|end|>`, the reply as
    `<|channel|>final<|message|>...<|return|>`; a tool call is `<|channel|>commentary ...<|call|>`;
  * stop ids: 200002 <|return|>, 199999 <|endoftext|>, 200012 <|call|> (generation_config.json);
  * `reasoning_effort` is a template argument (default "medium"); left at default and recorded.

    python experiments/sample_gptoss.py --tasks impossible --n 5 --out experiments/gptoss_pilot.jsonl
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import torch as t
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import load_tasks, messages_for  # noqa: E402
MODEL = "openai/gpt-oss-20b"; RET, EOT, CALL = 200002, 199999, 200012; EOS_IDS = [RET, EOT, CALL]

def find_seq(seq, sub):
    for i in range(len(seq) - len(sub) + 1):
        if seq[i:i+len(sub)] == sub: return i
    return -1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="impossible", choices=["impossible", "possible", "all"]); ap.add_argument("--only", default=None)
    ap.add_argument("--n", type=int, default=5); ap.add_argument("--max-new-tokens", type=int, default=8192); ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42); ap.add_argument("--pressure", action="store_true"); ap.add_argument("--reasoning-effort", default="medium")
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.out.exists() and not a.force: raise SystemExit(f"{a.out} exists; --force to overwrite")
    tasks = load_tasks()
    if a.tasks != "all": tasks = [x for x in tasks if x["possible"] == (a.tasks == "possible")]
    if a.only: tasks = [x for x in tasks if a.only in x["id"]]
    tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()
    FIN = tok("<|channel|>final<|message|>", add_special_tokens=False)["input_ids"]
    ANA = tok("<|channel|>analysis<|message|>", add_special_tokens=False)["input_ids"]
    jobs = [(x, i) for x in tasks for i in range(a.n)]; print(f"{len(jobs)} generations, effort={a.reasoning_effort}", flush=True)
    with a.out.open("w") as fh:
        for start in range(0, len(jobs), a.batch_size):
            chunk = jobs[start:start+a.batch_size]; prompts = []
            for x, _ in chunk:
                kw = {"tools": x["tools"]} if x.get("tools") else {}
                prompts.append(tok.apply_chat_template(messages_for(x, pressure=a.pressure, final_turn_as_user=True, harmony=True),
                                                       tokenize=False, add_generation_prompt=True, reasoning_effort=a.reasoning_effort, **kw))
            enc = tok(prompts, return_tensors="pt", add_special_tokens=False, padding=True).to(model.device); n_pad = enc["input_ids"].shape[1]
            t.manual_seed(a.seed + start); t0 = time.time()
            with t.no_grad():
                gen = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=True, temperature=0.7, top_p=0.95, pad_token_id=EOT, eos_token_id=EOS_IDS)
            print(f"batch {start//a.batch_size}: {len(chunk)} seqs, {gen.shape[1]-n_pad} new tokens, {time.time()-t0:.0f}s", flush=True)
            for row, (x, i) in enumerate(chunk):
                ids = gen[row, n_pad:].tolist()
                while ids and ids[-1] == EOT: ids.pop()
                last = ids[-1] if ids else None
                stopped = {RET: "return", CALL: "call", EOT: "endoftext"}.get(last, "token_limit" if len(ids) >= a.max_new_tokens else "endoftext")
                if last in (RET, CALL): ids = ids[:-1]
                k_fin = find_seq(ids, FIN); k_ana = find_seq(ids, ANA)
                analysis = tok.decode(ids[k_ana+len(ANA):k_fin] if (k_ana >= 0 and k_fin > k_ana) else (ids[k_ana+len(ANA):] if k_ana >= 0 else []), skip_special_tokens=True)
                final = tok.decode(ids[k_fin+len(FIN):], skip_special_tokens=True) if k_fin >= 0 else ""
                fh.write(json.dumps({"task_id": x["id"], "setting": x["setting"], "possible": x["possible"], "sample_index": i, "seed": a.seed,
                                     "model": MODEL, "reasoning_effort": a.reasoning_effort, "pressure": a.pressure, "final_turn_as_user": True, "harmony": True,
                                     "n_prompt_tokens": int(enc["attention_mask"][row].sum()), "n_generated_tokens": len(ids),
                                     "closed_think": k_fin >= 0, "think_end_offset": k_fin if k_fin >= 0 else None,
                                     "n_thinking_tokens": (k_fin - (k_ana + len(ANA))) if (k_ana >= 0 and k_fin >= 0) else (len(ids) if k_ana >= 0 else 0),
                                     "n_answer_tokens": (len(ids) - k_fin - len(FIN)) if k_fin >= 0 else 0, "stopped_on": stopped,
                                     "is_tool_call": stopped == "call", "hit_token_limit": stopped == "token_limit",
                                     "thinking": analysis, "answer": final if stopped != "call" else "<tool_call>" + tok.decode(ids[k_ana+len(ANA):] if k_ana >= 0 else ids, skip_special_tokens=True)[-400:],
                                     "generated_token_ids": ids}) + "\n")
            fh.flush()
    print(f"wrote {a.out}")

if __name__ == "__main__": main()
