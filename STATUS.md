# STATUS

## Where we are
- Step 3 done and approved by Nimun (2026-09-04): `task_gaming/tasks.json` holds 10 tasks (5 settings x impossible/possible) built from Neel's team's released environments.
- No model, no GPU, no installs yet. Nothing has been sampled.
- The brief (BRIEF.md) and standing rules (CLAUDE.md) are updated; the four files plus scripts/ and task_gaming/ are uncommitted.

## What the numbers mean so far
- No experimental numbers yet. Prompt sizes: 115 to 785 estimated tokens per task, so 225 generations at ~1,500 thinking+answer tokens each is a few GPU-hours in the background.

## Dumbest way this could be wrong
- The reconstructed tool outputs were audited for loaded wording and reviewed by Nimun; residual risk is subtle realism, not nudging.
- The Qwen chat template might not render assistant `tool_calls` / `role: tool` messages the way the OpenAI-format transcripts assume. Step 1 checks this before any sampling.
- Two settings (broken_test_runner, dark_mode) assume prior work "already done" by the model; the generated turn is off-policy relative to the real agentic run. Reported as a limitation.

## Decisions I made without asking
- Used the released environments instead of hand-written tasks (Nimun said yes to building on existing work).
- Added `silent_omission` as a third gamed label because two settings' released rubrics distinguish silent from affirmative claims.
- Did not add a `STATUS:` line to prompts, to keep them verbatim; the judge extracts the claim sentence instead.

## Waiting on you
1. Rent an 80GB pod. Then approve and run the commands in `scripts/BOX_SETUP.md` sections 2 and 3 (installs and model download). Nothing is installed until you say so.
2. Decide the GitHub remote: tell me to push, or create the repo and give me the URL.
3. Whether to commit the current files now as `checkpoint: step 3 — task set drafted`.

## Next
1. Commit (on your word), push, clone on the box, run `scripts/clone_vendor.sh`.
2. Step 1 smoke test: load Qwen3.5-9B bf16, hook the text decoder, render all 10 tasks through the chat template.
3. Step 2 pilot: 5 impossible tasks x 3 samples, written to `experiments/pilot_readable.md` for you to read.
