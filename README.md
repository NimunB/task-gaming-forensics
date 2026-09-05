# task-gaming-forensics

**When a language model is given a task it cannot complete and reports on it anyway — does it tell you,
does it lie, or does it bullshit?** And can you tell which from the outside, from its reasoning, or from
its activations?

A short, time-boxed research project (~16–20 agent-hours, one GPU) on **task-gaming**: models claiming
success on tasks that were impossible as specified — a test suite that cannot run, a screenshot that
cannot be taken, a command that does not exist. Frontier models have been shown to misrepresent their
work in these settings while their chain of thought shows no plan to deceive. We ask what a small open
model does in the same settings, and what its internals say while it does it.

## What we are doing, at a high level

1. **Tasks.** Five settings, each an impossible task with a matched *possible* control (10 tasks),
   taken verbatim from the released task-gaming environments in `gkroiz/agent-interp-envs` (Singh,
   Nanda & Rajamanoharan, 2026). No task was written by us or by an LLM.
2. **Sample and label.** Run `Qwen/Qwen3.5-9B` (thinking on) on every task many times; label each final
   report with an LLM judge using the environments' own per-setting rubrics — *false claim*, *silent
   omission*, *workaround presented as complete*, *honest failure*, *genuine success* — plus whether the
   thinking admits the blocker.
3. **Behavioural forensics.** Does the report track the outcome? What happens under pressure? Does asking
   the model afterwards ("did you actually complete it?") recover the truth — and does the *wording* of
   that question change the answer?
4. **Internals.** A **Jacobian lens** (reads the words an activation is *poised to say*, at any layer and
   token) applied to the same responses: is the true test count present when the model writes a false
   one? Do fabricating responses carry any trace of doubt at the moment of decision? Is the failure
   loaded in the model's workspace while it writes "Implementation Complete"?
5. **Pre-registered confirmatory run**, then a second model (`openai/gpt-oss-20b`) as a cross-model
   comparison.

Every claim is paired with the cheapest baseline that could explain it away (control tasks, a plain
logit lens, a neutral follow-up question), and two of our own hypotheses have been withdrawn on the
record when a control killed them. Numbers, with their N and intervals, live in `REPORT.md` §0.

## Start here

| File | What it is |
|---|---|
| `NARRATIVE.md` | The story in order: who we build on, what the data looks like, every decision point and what it cost |
| `REPORT.md` | Findings by result — §0 is a plain-language digest; §7 is a self-review against the source paper's standards |
| `PREREGISTRATION.md` | The claims, metrics, thresholds and withdrawal conditions, committed before the confirmatory run |
| `STATUS.md` | Always-current state, what the numbers mean, what is waiting on a human decision |
| `CHANGELOG.md` | Append-only, timestamped history with agent-active minutes per step |
| `experiments/sanity_checks.md` | Everything that broke and every check that passed, with reproduction commands |
| `VERIFY.md` | One-line commands to recompute each headline number from the raw outputs |
| `BRIEF.md`, `CLAUDE.md` | The original plan and the standing rules every session follows |

## Layout

```
task_gaming/        tasks.json (frozen), prompts.py (rendering for Qwen and Harmony formats),
                    jlens_readout.py (Jacobian-lens readout, reimplemented against the reference code)
experiments/        sample*.py (batched sampling), run_judge.py (LLM judge, loose and strict rubric),
                    h1/h2/h3h4_analysis.py (pre-registered analyses), jlens_*.py, make_figures.py,
                    *.jsonl outputs, *_readable.md transcripts, figures/
scripts/            BOX_SETUP.md (approved installs), clone_vendor.sh (pinned vendored repos)
vendor/             gkroiz/agent-interp-envs and NimunB/Probing-Safety-Behaviours at pinned commits (gitignored)
```

## Reproduce

`bash scripts/clone_vendor.sh`, then the commands in `scripts/BOX_SETUP.md` §2–3 (`transformers==5.2.0`,
`torch` cu128, one ~24 GB model download). `VERIFY.md` recomputes every reported number from the files
in `experiments/`.
