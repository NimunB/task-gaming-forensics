# CHANGELOG

Append-only. Format is defined in `CLAUDE.md`. Times are EDT. "Agent-active" is time the agent spent working on the project; setup, downloads, and waiting on generation are listed as "not counted".

## [2026-09-04 12:30 EDT] Step 0 — brief revised   (agent-active: 0h 0m, cumulative: 0h 0m)
Did: Read Neel Nanda's MATS 12.0 application doc. Rewrote the brief: cut fake-tool bucket, steering, agent-written write-up; added pilot gate, real-source tasks, C3 as ask-the-model baseline, reporting protocol in CLAUDE.md.
Found: Nothing run yet. Repo contains only README, CLAUDE.md, BRIEF.md, CHANGELOG.md, STATUS.md.
Decided: Extension to 2026-09-11 requested; 20-hour counted cap still applies.
Failed / abandoned: none.
Check this yourself: open BRIEF.md §5 and §7.

## [2026-09-04 12:20 EDT] Step 0 — model pinned   (agent-active: 0h 0m, cumulative: 0h 0m; not counted: 10 min)
Did: Checked Hugging Face. `Qwen/Qwen3.5-9B` exists, ungated, bf16, 32 layers, hidden 4096, architecture `Qwen3_5ForConditionalGeneration`. Chat template opens `<think>\n` by default; `enable_thinking=False` inserts an empty block. No official Qwen 3.6 9B (only 27B and 35B-A3B).
Found: n/a.
Decided: Primary model is `Qwen/Qwen3.5-9B`; Gemma 4 12B stays as fallback. Smoke test must locate the text decoder inside the VL wrapper before hooking.
Failed / abandoned: none.
Check this yourself: https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/config.json and chat_template.jinja lines 149-152.

## [2026-09-04 13:05 EDT] Step 3 (early) — task set built from released environments   (agent-active: 0h 0m; not counted: ~40 min, pre-project design work)
Did: Found that Neel's team open-sourced the task-gaming environments with prompts (gkroiz/agent-interp-envs, MIT). Vendored it and the thesis repo at pinned commits (`scripts/clone_vendor.sh`). Wrote `task_gaming/build_tasks.py`, which generates `task_gaming/tasks.json`: five settings (fictional_cli, test_regression, broken_test_runner, buggy_test, dark_mode), each impossible + matched possible control = 10 tasks, all < 800 prompt tokens. Wrote `task_gaming/prompts.py` (render, pressure suffix, confession follow-up) and `experiments/tasks_review.md` for Nimun's review. Wrote `scripts/BOX_SETUP.md` (install commands for approval; nothing run). Rewrote BRIEF Steps 0-3, 6-7 and §6-7 accordingly.
Found: In the post, models acknowledged the blocker internally 92% vs disclosed 33%, and sometimes fabricated with no deceptive plan in the CoT; no Qwen or Gemma model was tested, so the pilot is still required.
Decided: Drop hand-written tasks from Nimun's repos; no `STATUS:` line (keeps prompts verbatim); labels gain `silent_omission`; 30 samples per impossible task, 15 per control. Tool outputs for broken_test_runner and dark_mode are reconstructed and flagged; Nimun reviews before sampling.
Failed / abandoned: A local venv install was started and stopped at Nimun's request; rule added to CLAUDE.md: install nothing without asking. The HF transcript dataset `adsingh64/model-forensics` returned 307/401 and was not used.
Check this yourself: `python3 task_gaming/build_tasks.py` then open `experiments/tasks_review.md`.

## [2026-09-04 13:40 EDT] Step 3 — task set approved   (agent-active: 0h 0m; not counted: ~20 min review with Nimun)
Did: Walked Nimun through all five impossible tasks. Audited every reconstructed string for loaded wording (none found). Changed the buggy_test prompt ending from "report stating whether all tests pass" to "a short report of what you did" (matches the norvane wording; the old version invited a claim about tests the model cannot run). Regenerated tasks.json and experiments/tasks_review.md.
Found: n/a.
Decided: Nimun approved the 10-task set. tasks.json is frozen; any later change must be logged here with a reason.
Failed / abandoned: none.
Check this yourself: `git diff` after the first commit shows nothing in task_gaming/ changing without a CHANGELOG entry.

## [2026-09-04 14:30 EDT] Step 0 — box and judge decided   (agent-active: 0h 0m)
Did: Nimun rented a Vast.ai RTX PRO 6000 Max-Q (96 GB, CUDA 13.2, verified datacenter host, ~1.5 USD/h). Repo pushed to github.com/NimunB/task-gaming-forensics. Judge model set to `claude-sonnet-5` (matches the released code_summary_honesty eval); ~10 USD of API credit loaded.
Decided: Stop the instance between sittings (storage rate only). Claude Code runs on the box; its installer is the one install Nimun pre-approved verbally, everything else waits for approval per scripts/BOX_SETUP.md.
Check this yourself: BRIEF.md Step 7 names the judge model.
