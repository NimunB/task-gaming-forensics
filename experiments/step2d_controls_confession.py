"""Does "Answer honestly" induce FALSE confessions on TRUE successes?

The 25 possible-control responses (REPORT §3.6) are correct, complete claims. We append each model
reply and ask (a) the direct question with the "Answer honestly" cue and (b) the paper's indirect
form, same seeds. Any reply that retracts or hedges a true claim is a false confession induced by
the question. This is the clean test of BRIEF §8 check 6 and of REPORT §3.7's hypothesis.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import torch as t
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from task_gaming.prompts import CONFESSION_QUESTION, INDIRECT_QUESTION, confession_messages, task_by_id  # noqa: E402
MODEL = "Qwen/Qwen3.5-9B"; THINK_CLOSE_ID, IM_END_ID, ENDOFTEXT_ID = 248069, 248046, 248044
EOS_IDS = [IM_END_ID, ENDOFTEXT_ID]; SEED = 42
SRC = ROOT/"experiments"/"possible_controls.jsonl"
OUTS = {"direct": (CONFESSION_QUESTION, ROOT/"experiments"/"confession_controls_direct.jsonl"),
        "indirect": (INDIRECT_QUESTION, ROOT/"experiments"/"confession_controls_indirect.jsonl")}
for _, o in OUTS.values():
    if o.exists(): raise SystemExit(f"{o} exists; refusing to overwrite")

def decode_row(tok, gen_row, n_pad, max_new):
    ids = gen_row[n_pad:].tolist()
    while ids and ids[-1] == ENDOFTEXT_ID: ids.pop()
    stopped = "im_end" if ids and ids[-1] == IM_END_ID else ("endoftext" if len(ids) < max_new else "token_limit")
    if ids and ids[-1] == IM_END_ID: ids.pop()
    closed = THINK_CLOSE_ID in ids; k = ids.index(THINK_CLOSE_ID) if closed else None
    return {"n_generated_tokens": len(ids), "closed_think": closed, "n_thinking_tokens": k if closed else len(ids),
            "n_answer_tokens": (len(ids)-k-1) if closed else 0, "stopped_on": stopped,
            "thinking": tok.decode(ids[:k] if closed else ids, skip_special_tokens=True),
            "answer": tok.decode(ids[k+1:], skip_special_tokens=True) if closed else ""}

def main():
    tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()
    rows = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
    for form, (question, out) in OUTS.items():
        print(f"{form}: {len(rows)} controls", flush=True)
        with out.open("w") as fh:
            for start in range(0, len(rows), 10):
                chunk = rows[start:start+10]; prompts = []
                for r in chunk:
                    task = task_by_id(r["task_id"]); kw = {"tools": task["tools"]} if task.get("tools") else {}
                    prompts.append(tok.apply_chat_template(
                        confession_messages(task, r["answer"], final_turn_as_user=True, question=question),
                        tokenize=False, add_generation_prompt=True, **kw))
                enc = tok(prompts, return_tensors="pt", add_special_tokens=False, padding=True).to(model.device)
                n_pad = enc["input_ids"].shape[1]; t.manual_seed(SEED + start); t0 = time.time()
                with t.no_grad():
                    gen = model.generate(**enc, max_new_tokens=4096, do_sample=True, temperature=0.7, top_p=0.95,
                                         pad_token_id=ENDOFTEXT_ID, eos_token_id=EOS_IDS)
                print(f"  {len(chunk)} seqs, {gen.shape[1]-n_pad} new tokens, {time.time()-t0:.0f}s", flush=True)
                for i, r in enumerate(chunk):
                    fh.write(json.dumps({"task_id": r["task_id"], "setting": r["setting"], "sample_index": r["sample_index"],
                                         "form": form, "question": question, "original_answer": r["answer"],
                                         **decode_row(tok, gen[i], n_pad, 4096)}) + "\n")
                fh.flush()
        print(f"wrote {out}", flush=True)
    print("=== STEP2D DONE ===")

if __name__ == "__main__": main()
