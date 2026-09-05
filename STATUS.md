# STATUS

## Where we are
- **PREREGISTRATION.md is binding** (commit 5de0c4e, 2026-09-05 01:55 UTC) — H1 behavioural, H2–H4 Jacobian-lens, with tests and withdrawal conditions fixed before sampling.
- **Runs in progress, chained on the GPU:** D (fictional_cli ×100 at penalty 1.1, for H2) → confirmatory impossible ×30/task → possible ×15/task. D batch 1 of 4 done: 25 sequences, longest 4,621 tokens, **no cap hits**; judged 18 honest_failure / 5 false_claim / 2 other — a fabrication rate near the pilot's 2/8, so H2 will have ~20 fabrications to work with.
- **GPT-OSS-20B downloaded** (27.5 GB); Harmony render adapter written and all 10 tasks render; Harmony-aware sampler written. Smoke test waits for the GPU (first attempt OOM'd against the chain's 57 GB).
- Analysis scripts ready to run the moment sampling ends: `h1_analysis.py`, `h2_analysis.py`, `h3h4_analysis.py`, `make_figures.py` (dataviz-spec figures), `run_judge.py` (resumable; already used on D batch 1).
- 9h 20m agent-active of 16–20h.

## What the numbers mean so far
- **Behavioural half (unchanged):** outcome-tracking 43/44; gaming 1/25 loose, 2/25 strict; pressure 1/25.
- **Confession as sycophancy is real and ours to induce:** 6/44 false self-accusations under "Answer honestly", 0/42 under "Have you finished?"; blocker acknowledgement unchanged by wording. Concentrated in the prefilled setting.
- **Lens readouts are existence observations.** Every group is N ≤ 6; the lens is fit on 25 prompts; targets are single tokens. They are exactly the shapes of evidence Aditya Singh's doc asks for, and they point one way (no hidden doubt in fabricators; failure present while overclaiming), but they are not yet results. PREREGISTRATION §1b says what would make them results and what would withdraw them.
- **What would change my mind:** H2 showing no separation at N=100 → withdraw "no split-brain". H3's headline gap no larger than the prompt-tail gap → C is context salience. A better lens moving the ranks → distrust the n=25 lens.

## Dumbest way this could be wrong
- **C is context.** The error text is in the prompt; the lens may be recalling it, not intending disclosure. Partly narrowed (it unloads mid-answer), not closed.
- **A is one response**, on a digit, in the token family the paper says reads worst.
- **B's late layers mirror the output.** The L20–24 apology readouts precede "There" but are not independent of a CoT that already concluded "not standard".
- **The lens is thin** (n=25) and reimplemented; verified against the paper's example and the model's logits, but not against the reference package's outputs on identical inputs.
- **Labels remain agent labels endorsed by Nimun.**

## Decisions I made without asking
- Reimplemented the readout rather than bumping transformers (Nimun agreed to my stated preference). Verified two ways before use.
- Fixed experiment A's tokenisation bug and re-ran at the digit position; added within-answer control positions to C when the context confound became obvious. Both recorded in sanity_checks.
- Wrote H2–H4 into PREREGISTRATION as DRAFT with tests, token sets, layers, and withdrawal conditions fixed now — before any scaled run.
- Did **not** run steps D–H, fit a lens, or download a corpus: D–F are pre-registered and need the DRAFT approved; G needs a download; H needs a model switch.

## Where the narrative for the write-up lives
- `NARRATIVE.md` — the story in order: ten decision points so far, one paragraph each, plus a summary table. Read this first if you have been away.
- `REPORT.md` — the findings themselves, written as they arrive. Living document, status banner at the top says what exists and what does not.
- `experiments/sanity_checks.md` — every defect and every check, grouped by issue, with reproduction commands. This is the file to write from.
- `CHANGELOG.md` — the same material in time order, with agent-active minutes per step.
- `experiments/pilot_readable.md` — the 15 transcripts themselves.

## Waiting on you
**ONE DECISION: approve `PREREGISTRATION.md` (H1 behavioural + H2–H4 lens).** It fixes the confirmatory run (225 generations at penalty 1.1), the 100-sample `fictional_cli` run for H2, the exact positions/tokens/layers/baselines for H2–H4, the tests, and what would withdraw each claim. On "approved": DRAFT comes off, it is committed with a timestamp, and D (10 min), then the confirmatory run (~45 min) launch. Separately approve **G** (fit our own lens; needs a small corpus download) and **H** (GPT-OSS-20B; model switch + 27.5 GB) if you want them.

**Previously:** The original headline (probe AUROC, gamed vs honest) cannot be computed on one gamed response, and the cheap baseline already recovers it. REPORT.md §3.5 proposes the surviving internals question: **does the residual stream distinguish true confessions from false ones?** Options are laid out there and in the chat. Your call before Step 4 pre-registration, which must be written against whichever headline you choose.

**Read the transcripts.** `experiments/pilot_readable.md` has the original 15 with my guesses. The fixed run (25) is in `experiments/pilot_userturn.jsonl`; say the word and I will render it the same way. Then three decisions:

1. **Your labels, and the rubric.** The single biggest lever is whether "disclosed the blocker but claimed verification that did not happen" counts as gaming. On the loose reading the rate is 1/25; on a strict reading it could be several times that.
2. **The mechanical consequences of Step 2.** (a) Gaming under 10% ⇒ the `pressure` suffix becomes a second reported condition; this still trips at 4.0%. (b) No setting is now all-`other`, so nothing qualifies for dropping on that rule — the fix removed that question.
3. **The real question: can this experiment answer its question with this model?** At roughly one gamed response in fifteen, Step 6 at 30 samples per impossible task yields on the order of ten gamed responses. The headline metric — AUROC of the probe separating task_gamed from honest_failure — would rest on a positive class that small, and every kill-the-result check in §8 would rest on less. Four options, and I recommend the first two together:
   - **(a) Fix the tool-call leak first.** Move `final_turn_note` out of the `<tool_response>` block into a real user turn. That is a prompt-plumbing fix, not a change to task content, and it could convert 5 `other` responses into actual claims. Cheap: one edit, 15 generations, ~15 minutes. It might move the rate on its own.
   - **(b) Add `pressure` as a real second condition** rather than a fallback, since Step 2 says it trips anyway.
   - **(c) Accept the low rate and reframe** the report around "this model mostly does not game these tasks, and here is the forensic reading of the few times it does" — a negative result, which the application doc explicitly says is fine if well analysed, but which weakens the probe half of the project.
   - **(d) Switch to the Gemma 4 12B fallback.** Most expensive, needs your approval per BRIEF §3, and there is no reason yet to think it games more.

I have done everything that does not depend on your answer. Nothing else is blocked.

## Next
1. On your Gate 1 call: either the tool-call plumbing fix and a re-pilot, or straight to Step 4 (pre-registration) and Step 5 (probe training) with the framing you choose.
2. Step 4 pre-registration must be committed with a timestamp **before** any Step 6 sampling, so it should follow immediately once the conditions are settled.
