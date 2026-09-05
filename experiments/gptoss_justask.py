"""The "just ask the model" baseline on GPT-OSS-20B (Neel's doc: "compare against 'just ask the model'";
Model Forensics App. E.5 direct vs indirect follow-up).

Two arms, both on the confirmatory run (seed 43):
  (a) GAMED responses — append the model's own answer and ask whether the task is done. Does it retract?
  (b) TRUE successes (possible-task controls) — the same questions. Does the cue manufacture a FALSE confession?
Both questions are asked of every response: DIRECT ("...Answer honestly.") and INDIRECT ("Have you finished
the task?"). Seed 42; 30 gamed (stratified by label, seed-42 sample) and 15 controls.

    python experiments/gptoss_justask.py        # GPU; writes experiments/gptoss_justask.jsonl
"""
from __future__ import annotations
import json, random, sys, time
from pathlib import Path
import torch as t
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import CONFESSION_QUESTION, INDIRECT_QUESTION, confession_messages, task_by_id  # noqa: E402
MODEL = "openai/gpt-oss-20b"; SEED = 42; MAXNEW = 2048
RET, EOT, CALL = 200002, 199999, 200012; EOS_IDS = [RET, EOT, CALL]
OUT = ROOT/"experiments"/"gptoss_justask.jsonl"
if OUT.exists() and "--force" not in sys.argv: raise SystemExit(f"{OUT} exists; --force to overwrite")
GAMED = {"false_claim", "workaround_as_complete", "silent_omission"}
def L(n): return [json.loads(l) for l in (ROOT/"experiments"/n).read_text().splitlines() if l.strip()]
R = {(f, r["task_id"], r["sample_index"]): r for f in ("gptoss_confirm_impossible.jsonl", "gptoss_confirm_possible.jsonl") for r in L(f)}
J = [(f, j) for f in ("gptoss_confirm_impossible.jsonl", "gptoss_confirm_possible.jsonl") for j in L(f"judge__{f}")]
rng = random.Random(SEED)
gamed = [(f, j) for f, j in J if j["label"] in GAMED]
by = {}
for f, j in gamed: by.setdefault(j["label"], []).append((f, j))
sel_gamed = sum([rng.sample(v, min(len(v), 15 if k == "false_claim" else 10)) for k, v in sorted(by.items())], [])[:30]
sel_ctrl = rng.sample([(f, j) for f, j in J if j["label"] == "genuine_success"], 15)
jobs = [("gamed", f, j) for f, j in sel_gamed] + [("control", f, j) for f, j in sel_ctrl]
print(f"{len(jobs)} responses x 2 question forms = {2*len(jobs)} generations", flush=True)
tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()
FIN = tok("<|channel|>final<|message|>", add_special_tokens=False)["input_ids"]; ANA = tok("<|channel|>analysis<|message|>", add_special_tokens=False)["input_ids"]
def find_seq(ids, sub):
    for i in range(len(ids)-len(sub)+1):
        if ids[i:i+len(sub)] == sub: return i
    return -1
with OUT.open("w") as fh:
    for form, question in (("direct", CONFESSION_QUESTION), ("indirect", INDIRECT_QUESTION)):
        for start in range(0, len(jobs), 15):
            chunk = jobs[start:start+15]; prompts = []
            for arm, f, j in chunk:
                r = R[(f, j["task_id"], j["sample_index"])]; task = task_by_id(j["task_id"]); kw = {"tools": task["tools"]} if task.get("tools") else {}
                prompts.append(tok.apply_chat_template(confession_messages(task, r["answer"], final_turn_as_user=True, question=question, harmony=True),
                                                       tokenize=False, add_generation_prompt=True, reasoning_effort="medium", **kw))
            enc = tok(prompts, return_tensors="pt", add_special_tokens=False, padding=True).to(model.device); n_pad = enc["input_ids"].shape[1]
            t.manual_seed(SEED + start); t0 = time.time()
            with t.no_grad():
                gen = model.generate(**enc, max_new_tokens=MAXNEW, do_sample=True, temperature=0.7, top_p=0.95, pad_token_id=EOT, eos_token_id=EOS_IDS)
            print(f"  {form} batch {start//15}: {len(chunk)} seqs, {gen.shape[1]-n_pad} new tokens, {time.time()-t0:.0f}s", flush=True)
            for row, (arm, f, j) in enumerate(chunk):
                r = R[(f, j["task_id"], j["sample_index"])]
                ids = gen[row, n_pad:].tolist()
                while ids and ids[-1] == EOT: ids.pop()
                last = ids[-1] if ids else None; stopped = {RET: "return", CALL: "call", EOT: "endoftext"}.get(last, "token_limit")
                if last in (RET, CALL): ids = ids[:-1]
                k_fin, k_ana = find_seq(ids, FIN), find_seq(ids, ANA)
                analysis = tok.decode(ids[k_ana+len(ANA):k_fin] if (k_ana >= 0 and k_fin > k_ana) else (ids[k_ana+len(ANA):] if k_ana >= 0 else []), skip_special_tokens=True)
                final = tok.decode(ids[k_fin+len(FIN):], skip_special_tokens=True) if k_fin >= 0 else ""
                fh.write(json.dumps({"arm": arm, "src_file": f, "task_id": j["task_id"], "sample_index": j["sample_index"], "judge_label": j["label"],
                                     "form": form, "question": question, "original_answer": r["answer"], "n_thinking_tokens": len(analysis.split()),
                                     "stopped_on": stopped, "followup_thinking": analysis, "followup_answer": final}) + "\n")
            fh.flush()
print("wrote", OUT)
