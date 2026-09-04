# CLAUDE.md — standing rules for every session in this repo

Read `BRIEF.md` fully before doing anything. Then read `STATUS.md` and the last three entries of `CHANGELOG.md`.

## Reporting protocol (non-negotiable)

Nimun is not watching the terminal. Everything they know about this project comes from the files below. Write for a reader who did not see the tool calls.

1. **`STATUS.md`** — overwritten, always current. Rewrite it at every checkpoint (see 3). Sections, in order:
   - **Where we are:** current step, what is running, what is done. Five bullets max.
   - **What the numbers mean so far:** plain English, every number with its N. Say what would change your mind.
   - **Dumbest way this could be wrong:** for each result reported above, one line.
   - **Decisions I made without asking:** and why.
   - **Waiting on you:** questions or gates that need Nimun. If none, say "nothing".
   - **Next:** the next two actions.
2. **`CHANGELOG.md`** — append-only history. Entry format:
   ```
   ## [YYYY-MM-DD HH:MM EDT] Step N — short title   (agent-active: Xh Ym, cumulative: Xh Ym)
   Did: ...
   Found: ... (numbers, N, CI)
   Decided: ... because ...
   Failed / abandoned: ... (so later sessions do not retry)
   Check this yourself: <one-line command or file to open>
   ```
3. **Checkpoints** happen (a) at the end of every step, (b) every 45 minutes of agent-active work regardless, (c) immediately before starting any job longer than 5 minutes, and (d) whenever a result contradicts the pre-registration or a previous entry. At each checkpoint: append to CHANGELOG, rewrite STATUS, commit both with message `checkpoint: step N — title`.
4. **Explain, do not just record.** When you report a result, say in one or two sentences what it means for the liar-versus-bullshitter question and what it does not mean. Define any term the first time it appears (AUROC, kappa, difference-of-means, detection mask).
5. **Track time.** Log agent-active minutes per step in CHANGELOG headers. Setup, downloads, and waiting on generation are logged separately as "not counted".
6. **Gates.** At the four gates in BRIEF.md §5, write the decision question to STATUS.md under "Waiting on you", do every piece of work that does not depend on the answer, then stop.

## Hard rules

- **Install nothing without asking.** No pip, venv, apt, brew, or model download, on the Mac or the box. Write the exact command to STATUS.md under "Waiting on you" and stop. `scripts/BOX_SETUP.md` is the approved list format.
- Never fabricate a number. If something did not run, write "did not run" and why.
- Do not write prose for the executive summary, the application form, or the final Google Doc. Produce `REPORT.md`, `VERIFY.md`, `experiments/random_examples.md`, figures, and `results.json`. Nimun writes the doc.
- Do not expand scope: no SAEs, no extra models, no extra behaviours, no fake-tool bucket, no steering.
- Do not generate tasks with an LLM. Tasks come from Nimun or from real repos with a source URL.
- Stop at time boxes. Over budget means write what you have to CHANGELOG and move on.
- Ask (via STATUS.md) before changing the model, the dataset provenance, or the framing.
- Random examples are selected with a fixed seed, never cherry-picked.
- Seed 42 everywhere; seed 43 only for the robustness row.
