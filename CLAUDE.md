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
3. **`experiments/sanity_checks.md`** — the lab record, grouped by issue and never by date. Update it at every checkpoint, alongside STATUS and CHANGELOG. **Record what worked as well as what broke** — a record of only the failures is as misleading as a record of only the successes. Four sections:
   - **Issues found:** each with expected / observed (quote the raw output, do not paraphrase it) / how it was caught / root cause / fix / what it changed / a reproduction command. Mark `FIXED` or `OPEN`.
   - **Checks that passed:** the check, why the result could have been false without it, and the outcome. A check is only evidence if it was specified before the answer was known and reported whichever way it came out. Never quietly drop one because it passed.
   - **What worked first time:** decisions and methods that paid off, and why. This is where the reasoning behind a good call gets preserved instead of vanishing into a result that looks obvious in hindsight.
   - **Not yet checked:** so that untested is never mistaken for passed.
   Own errors go in under my name, not in the passive voice. If evidence is lost, say it is lost rather than describing it from memory as though it survived.
4. **`REPORT.md`** — the findings, written as they arrive rather than reconstructed at the end. Update it at every checkpoint where a result changed. It is a living document with a status banner naming what exists and what does not; mark any number that has not been human-labelled or verified as provisional, and say plainly when a result is negative. Every number carries its N. Structure by finding, not by chronology. This is the file the write-up is built from; per the hard rules below, it is not itself the write-up.
5. **`NARRATIVE.md`** — the story of the project for a reader with no context: what we set out to do, what we found, where the plan changed and why, what each change cost. One paragraph per beat plus a decision-point table at the top. Add a beat at every checkpoint where something changed direction, was found, or was withdrawn. This is where a reviewer sees *why* decisions were made; CHANGELOG records *that* they were.
6. **Checkpoints** happen (a) at the end of every step, (b) every 45 minutes of agent-active work regardless, (c) immediately before starting any job longer than 5 minutes, and (d) whenever a result contradicts the pre-registration or a previous entry. At each checkpoint: append to CHANGELOG, rewrite STATUS, update `experiments/sanity_checks.md` if anything was found or checked, update `REPORT.md` if a result changed, add a beat to `NARRATIVE.md` if direction changed, and commit with message `checkpoint: step N — title`.
7. **Explain, do not just record.** When you report a result, say in one or two sentences what it means for the liar-versus-bullshitter question and what it does not mean. Define any term the first time it appears (AUROC, kappa, difference-of-means, detection mask).
8. **Track time.** Log agent-active minutes per step in CHANGELOG headers. Setup, downloads, and waiting on generation are logged separately as "not counted".
9. **Gates.** At the four gates in BRIEF.md §5, write the decision question to STATUS.md under "Waiting on you", do every piece of work that does not depend on the answer, then stop.

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
