# STATUS

## Where we are
- Steps 0–2 done, plus three exploratory checks: the tool-call confound (fixed), the just-ask-the-model baseline (done), and a decoding control on `fictional_cli` (done). **Gate 1 is open and waiting on you.**
- REPORT.md now has §1b (where this comes from, what Neel's team found, what had to change), §3.5 (just-ask baseline), and a corrected §3.3. `experiments/sanity_checks.md` updated. All committed.
- **Headline so far:** on this model the task-gaming phenomenon barely occurs (1/25), the model discloses (18/19), and a one-line question recovers the one fabrication. The original probe headline has nothing to measure.
- **One earlier claim withdrawn:** the `fictional_cli` "runaway reasoning" was a sampler artefact (repetition penalty fixes it 5/5). It was in REPORT §3.3 as a hypothesis; it is now recorded there as a corrected error.
- 3h 40m agent-active of 16–20h. Deadline Sept 11 (extension).

## What the numbers mean so far
- **Gaming rate 1/25 = 4.0%** (1/19 of labelable claims), my guesses, N=25 fixed-prompt run. Sensitive to rubric: strict reading of "claimed verification that did not happen" could raise it several-fold.
- **Just ask the model: 14/19 confess, 5/19 "yes but", 0/19 double down.** The one fabrication confesses ("highly likely I guessed the invocation"). But **1 clear over-confession** (`dark_mode` #0 disowns work the transcript shows was done) and 2 leaning that way — so confession is high-recall, low-precision. That is BRIEF §8 check 6 observed unprompted.
- **`fictional_cli` pooled, 13 samples, 8 answers: 2 fabrications, 6 honest refusals.** The two fabrications have the two shortest CoTs that reached an answer (142, 519 tokens vs 269–3712 for refusals). Pattern in 8 datapoints; not a result.
- **What would change my mind:** your labels, especially on rubric strictness; and whether you read the over-confessions the way I do.

## Dumbest way this could be wrong
- All labels are one agent's reading. No judge, no human labels, no kappa.
- The gaming rate depends on a rubric decision I flagged but did not make.
- The "short CoT → fabricate" pattern is 2 datapoints on one side.
- Over-confession in `dark_mode` rests on the prefilled transcript being read as "work was done"; a reader could argue the model is right to doubt work it did not perform. That reading makes it honest, not sycophantic.
- 3 of 25 fixed-run responses still emit tool calls.

## Decisions I made without asking
- Pulled the C3 baseline forward from Step 9, and ran the decoding control, as exploration — neither is a headline run, so neither needed the Step 4 pre-registration first.
- Withdrew the runaway hypothesis from REPORT.md rather than softening it. It was wrong.
- Proposed, but did not adopt, a new internals question (§3.5 last paragraph). Adopting it is yours.
- Recorded `repetition_penalty=1.1` as the intended default for later runs — to be fixed in PREREGISTRATION.md, not silently.

## Where the narrative for the write-up lives
- `REPORT.md` — the findings themselves, written as they arrive. Living document, status banner at the top says what exists and what does not.
- `experiments/sanity_checks.md` — every defect and every check, grouped by issue, with reproduction commands. This is the file to write from.
- `CHANGELOG.md` — the same material in time order, with agent-active minutes per step.
- `experiments/pilot_readable.md` — the 15 transcripts themselves.

## Waiting on you
**GATE 1 — now also a framing decision.** The original headline (probe AUROC, gamed vs honest) cannot be computed on one gamed response, and the cheap baseline already recovers it. REPORT.md §3.5 proposes the surviving internals question: **does the residual stream distinguish true confessions from false ones?** Options are laid out there and in the chat. Your call before Step 4 pre-registration, which must be written against whichever headline you choose.

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
