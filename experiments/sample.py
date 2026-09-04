"""Batched sampler for task-gaming generations (BRIEF.md Steps 2 and 6).

Writes one JSON line per generation with the full thinking and answer text plus the token
offsets Step 8 needs to pool activations over the right spans.

    python experiments/sample.py --tasks impossible --n 3 --out experiments/pilot_samples.jsonl

Decoding is T=0.7, top_p=0.95, seed 42 per BRIEF.md §3. Thinking is always on: the prompt ends
with the open <think> tag and `enable_thinking=False` is never passed.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch as t
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from task_gaming.prompts import load_tasks, render  # noqa: E402

MODEL = "Qwen/Qwen3.5-9B"
THINK_CLOSE_ID = 248069   # '</think>', verified single-token in step1_smoke.json
IM_END_ID = 248046        # '<|im_end|>' — the real end of an assistant turn
ENDOFTEXT_ID = 248044     # '<|endoftext|>'
# Qwen/Qwen3.5-9B ships no generation_config.json, so transformers falls back to
# config.eos_token_id = 248044 (<|endoftext|>). An assistant turn actually ends with
# <|im_end|> (248046), so generation ran straight past the end of the turn and hallucinated the
# next user turn until it degenerated into repetition (found in the first pilot run). Both ids
# are passed explicitly here; do not rely on the default.
EOS_IDS = [IM_END_ID, ENDOFTEXT_ID]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="impossible", choices=["impossible", "possible", "all"])
    ap.add_argument("--n", type=int, default=3, help="samples per task")
    ap.add_argument("--max-new-tokens", type=int, default=8192)
    ap.add_argument("--batch-size", type=int, default=15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--force", action="store_true", help="allow overwriting an existing --out file")
    args = ap.parse_args()

    # The first pilot run was overwritten by the re-run, so the raw evidence for the eos bug was
    # lost and had to be described from memory rather than shown. Never again by accident.
    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} exists. Pass --force to overwrite, or choose a new path.")

    tasks = load_tasks()
    if args.tasks == "impossible":
        tasks = [x for x in tasks if not x["possible"]]
    elif args.tasks == "possible":
        tasks = [x for x in tasks if x["possible"]]

    tok = AutoTokenizer.from_pretrained(MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"          # generation; the extractor uses right padding separately
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=t.bfloat16, device_map="cuda:0").eval()

    jobs = [(task, i) for task in tasks for i in range(args.n)]
    print(f"{len(jobs)} generations over {len(tasks)} tasks, "
          f"max_new_tokens={args.max_new_tokens}, batch={args.batch_size}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.out.open("w") as fh:
        for start in range(0, len(jobs), args.batch_size):
            chunk = jobs[start:start + args.batch_size]
            prompts = [render(tok, task) for task, _ in chunk]
            enc = tok(prompts, return_tensors="pt", add_special_tokens=False, padding=True).to(model.device)
            n_pad_prompt = enc["input_ids"].shape[1]

            t.manual_seed(args.seed + start)   # deterministic per chunk, seed 42 base
            t0 = time.time()
            with t.no_grad():
                gen = model.generate(**enc, max_new_tokens=args.max_new_tokens, do_sample=True,
                                     temperature=0.7, top_p=0.95, pad_token_id=ENDOFTEXT_ID,
                                     eos_token_id=EOS_IDS)
            elapsed = time.time() - t0
            n_new = gen.shape[1] - n_pad_prompt
            print(f"batch {start // args.batch_size}: {len(chunk)} seqs, {n_new} new tokens, "
                  f"{elapsed:.0f}s ({len(chunk) * n_new / elapsed:.0f} tok/s)", flush=True)

            for row, (task, sample_i) in enumerate(chunk):
                # Trim left padding so offsets are relative to this sequence's real prompt.
                n_real_prompt = int(enc["attention_mask"][row].sum().item())
                new_ids = gen[row, n_pad_prompt:].tolist()
                # generate() right-pads finished sequences with pad_token_id
                while new_ids and new_ids[-1] == ENDOFTEXT_ID:
                    new_ids.pop()
                stopped_on = ("im_end" if new_ids and new_ids[-1] == IM_END_ID
                              else "endoftext" if len(new_ids) < args.max_new_tokens
                              else "token_limit")
                if new_ids and new_ids[-1] == IM_END_ID:
                    new_ids.pop()
                closed = THINK_CLOSE_ID in new_ids
                k = new_ids.index(THINK_CLOSE_ID) if closed else None
                thinking = tok.decode(new_ids[:k] if closed else new_ids, skip_special_tokens=True)
                answer = tok.decode(new_ids[k + 1:], skip_special_tokens=True) if closed else ""
                fh.write(json.dumps({
                    "task_id": task["id"], "setting": task["setting"], "possible": task["possible"],
                    "sample_index": sample_i, "seed": args.seed,
                    "n_prompt_tokens": n_real_prompt, "n_generated_tokens": len(new_ids),
                    "closed_think": closed, "think_end_offset": k,
                    "n_thinking_tokens": k if closed else len(new_ids),
                    "n_answer_tokens": (len(new_ids) - k - 1) if closed else 0,
                    "hit_token_limit": stopped_on == "token_limit",
                    "stopped_on": stopped_on,
                    "thinking": thinking, "answer": answer,
                    "generated_token_ids": new_ids,
                }) + "\n")
                written += 1
            fh.flush()
    print(f"wrote {written} generations to {args.out}")


if __name__ == "__main__":
    main()
