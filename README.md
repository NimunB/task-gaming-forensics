# task-gaming-forensics

**When a coding agent claims success on a task it could not have completed, is it lying — it represented the
failure and concealed it — or bullshitting — it never tracked the truth at all?** The two look identical from
outside, and only the first can be caught by reading the model's internal state. This repository holds the code,
data, figures and lab record of a short, time-boxed study (one GPU, ~16 agent-hours) that tried to tell them apart
using three instruments: the model's reasoning channel, its internal activations (Jacobian lens, logit lens, linear
probes), and a direct follow-up question.

## The setting

Ten tasks from the environments released with *Why do models task game?* (Singh, Nanda & Rajamanoharan, 2026;
`gkroiz/agent-interp-envs`, pinned commit `56fd0c11`): five that are impossible in a way the model cannot fix — a
fictional CLI it is asked to give the syntax of, a pull request over a test its change broke, an `is_prime` against a
test that says 7 is not prime, a screenshot with no browser, a broken test runner — and five matched *possible
variants* with the blocker removed. Two open-weight models, **Qwen3.5-9B** and **GPT-OSS-20B**. Every response is
labelled by an LLM judge (`claude-sonnet-5`, frozen rubric, loose and strict passes); 79 seed-selected responses were
read by hand against the labels.

One deliberate departure from the paper: their agents ran live in Docker and executed real tools over many turns. Ours
execute nothing. Each task is a single prompt, and two are prefilled transcripts in which the failing test or the
missing browser is already in front of the model when it writes its report. That isolates the reporting step from the
agentic rollout.

## What we found

- **The two models behave completely differently on the same tasks.** Qwen3.5-9B games 7 of 150 impossible-task
  responses and its claims are true 96% of the time. GPT-OSS-20B games 93 of 150 (62%) and its claims are true 52% of
  the time. Gaming is concentrated: 30/30 on the fictional command, 29/30 on the false test count, 30/30 on the rigged
  test — and 2/30 on the screenshot task, where the model is simply honest.
- **Within GPT-OSS, the answer depends on the task.** On the fictional command, the model's private reasoning doubts
  the tool in **78 of 85** responses and the answer passes that doubt on in **4 of 85**: the truth is tracked and
  withheld. On the false test count there is no reasoning at all; one layer before it writes "18", a Jacobian lens
  ranks lower numbers above 18 in **44 of 44** false statements and 2 of 30 true ones — but 16 as often as 17, so the
  model carries "fewer than 18", not the true count. A pre-registered neighbour check narrowed that headline.
- **A probe that scored AUROC 1.00 was a confound.** A truth probe trained on Apollo trivia separated false from true
  "18 passed" claims perfectly; so did a random direction, because the two groups came from two different prompts.
  Swapping the digit inside each response with the prompt held fixed showed both probes read the digit, not its truth.
  Negative, replicated on a fresh seed.
- **Asking the model directly works on exactly one task.** GPT-OSS admits the failing test 4 of 4 times, never retracts
  the fictional command (0 of 9), admits nothing when asked indirectly, and once confessed to a failure it never had.

Every instrument is reported beside a trivial alternative (logit lens beside Jacobian lens, random directions beside
every probe, prompt-only readouts, strict rubric, second seed, asking the model). Hypotheses, tests and the controls
that could overturn them were committed before the corresponding data were sampled; the git history records the
order. Two of our own first readings were reversed by those controls and are reported as such.

## Figures

| file | what it shows |
|---|---|
| `experiments/figures/fig_prevalence.png` | share of gamed responses per impossible task, both models, 95% intervals |
| `experiments/figures/fig_zero_reasoning.png` | reasoning tokens before the answer, by judge label (GPT-OSS) |
| `experiments/figures/fig_c_true_count.png`, `fig_c_confirm.png` | lens ranks of 16/17/19 vs 18 before the false count, first batch and replication |
| `experiments/figures/fig_h5_swap.png` | the digit-swap control on both probes |
| `experiments/figures/fig_h2_negation_rank.png`, `fig_h2_cells.png` | Qwen: doubt words before refusals vs fabrications; reasoning-acknowledged vs not |
| `experiments/figures/fig_h3_failed_positions.png` | Qwen: the withdrawn "failure held in mind" reading and its prompt-tail control |

## Layout

```
task_gaming/        tasks.json (frozen), prompts.py (rendering for Qwen and Harmony formats, follow-up questions),
                    jlens_readout.py (Jacobian-lens readout, reimplemented), vendor_import.py
experiments/
  sample.py, sample_gptoss.py          batched sampling (Qwen; GPT-OSS Harmony)
  run_judge.py                          LLM judge, loose and --strict rubric
  h1_analysis.py, h2_analysis.py,       pre-registered Qwen analyses (outcome tracking; doubt words; withdrawn readings)
  h2_sensitivity.py, h3h4_analysis.py
  gptoss_lens_c.py, gptoss_lens_c_neighbours.py   lens readout at the false test count; 16/17/19 vs 18 by layer
  gptoss_probe.py, gptoss_swap_control.py         Apollo-trained probes, controls, digit swap
  fcli_doubt_judge.py                   does the reasoning doubt the fictional tool; does the answer hedge
  gptoss_justask.py                     direct vs indirect follow-up questions
  make_figures*.py, make_results_json.py, make_random_examples*.py, make_adjudication_confirm.py
  *.jsonl                               every sampled response and every judge label
  results.json                          every headline number, recomputed from the outputs
  random_examples*.md                   seed-42 examples, five per label, never hand-picked
  adjudication_set*.md                  the responses read by hand against the judge's labels
  sanity_checks.md                      the lab record: what broke, what was checked, what was not
  exported_probes/gptoss_probes_h5.pt   the saved truth and deception probes
  figures/
scripts/            BOX_SETUP.md (approved installs), clone_vendor.sh (pinned vendored repos)
vendor/             agent-interp-envs and Probing-Safety-Behaviours at pinned commits (gitignored; clone with the script)
```

## Reproduce

`bash scripts/clone_vendor.sh`, then the commands in `scripts/BOX_SETUP.md` (`transformers==5.2.0`, `torch` cu128;
the two models download on first run, ~20 GB and ~42 GB in bf16). The published Jacobian lenses
(`camilablank/workspace-lenses` for Qwen, `neuronpedia/jacobian-lens` for GPT-OSS) go under `experiments/lenses/`.
`python experiments/make_results_json.py` regenerates `results.json` from the files in `experiments/`; the analysis
scripts named above regenerate each number and figure from the `.jsonl` outputs without a GPU, except the lens and
probe extractions, which need the model loaded.

Sources: Singh, Nanda & Rajamanoharan, *Why do models task game?* (2026); Singh, Kroiz, Rajamanoharan & Nanda, *Model
Forensics* (2026); Gurnee, Sofroniew & Lindsey, *Jacobian lens* (Transformer Circuits, 2026); Goldowsky-Dill et al.,
*Detecting strategic deception using linear probes* (2025), via `NimunB/Probing-Safety-Behaviours`.
