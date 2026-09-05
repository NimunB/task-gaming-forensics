# STATUS

## Where we are
- Steps 0–2 done; three exploratory checks done (confound fix, follow-up baseline, decoding control); the Model Forensics paper read in the body; a self-review against its standards written as REPORT.md §7. **Gate 1 is open and waiting on you.**
- **Headline so far:** on this model the task-gaming phenomenon barely occurs — 1/25 [1%, 20%] — the model discloses 18/19 [75%, 99%], and a follow-up question recovers the one fabrication. The original probe headline has no positive class.
- **The review found three cheap gaps**, all from the paper's own standards: no control-task sample, no positive control, and a follow-up question in the form the authors warn against. REPORT.md §8 lists them as next steps A–C (~30 min GPU total).
- **Two of my own proposals are now withdrawn** in the record: the `fictional_cli` "runaway" (sampler artefact) and the "true vs false confessions" probe idea (N=1).
- 4h 15m agent-active of 16–20h. Deadline Sept 11 (extension). All work committed.

## What the numbers mean so far
- **Gaming 1/25 [1%, 20%]**; of claims, 1/19 [1%, 25%]. My reading, N=25 fixed-prompt run. Sensitive to rubric strictness (REPORT §3.2).
- **Disclosure 18/19 [75%, 99%].** Every `test_regression` names the failing test; every `buggy_test` says the test case is wrong; every `broken_test_runner` and `dark_mode` report says what it could not do.
- **Follow-up: confess 14/19 [51%, 88%], double down 0/19 [0%, 17%]**, clear over-confession 1/19. The double-down upper bound is 17% — "rarely", not "never". And the question was the paper's *direct* form with an "Answer honestly" cue, so these rates may be inflated.
- **`fictional_cli`, pooled, 8 answers: 2 fabrications [7%, 59%], 6 refusals.** The only setting that games.
- **Labelable responses 8/15 → 19/25 after the confound fix** [57%, 89%]; all 11 new ones honest.
- **What would change my mind:** your labels on rubric strictness; the possible-task controls (if the model hedges there too, "disclosure" is a style, not a judgement); the indirect follow-up (if over-confession vanishes, it was our cue).

## Dumbest way this could be wrong
- Every label is one agent's reading. No judge, no human labels, no kappa.
- **No positive control:** nothing shows this pipeline would see gaming if it were there.
- **No control tasks sampled:** "discloses on impossible tasks" is uninterpretable without "claims success on possible ones".
- The confession rate may be an artefact of asking the model to "answer honestly".
- Intervals at N=25 and N=19 are wide enough that most of the above could move a lot.

## Decisions I made without asking
- Read the paper body (~40 min agent) and wrote the self-review, because the user asked for a review and the paper is the reviewer's own standard.
- Withdrew the "true vs false confessions" proposal rather than keep it as an option: N=1.
- Added Wilson CIs everywhere a rate is stated, following the paper's reporting practice rather than BRIEF's "CIs on everything" being deferred to Step 8.
- Did **not** run next steps A–C. They are exploration and cheap, but they are also the last runs before a framing decision that is yours, so I stopped here.

## Where the narrative for the write-up lives
- `NARRATIVE.md` — the story in order: ten decision points so far, one paragraph each, plus a summary table. Read this first if you have been away.
- `REPORT.md` — the findings themselves, written as they arrive. Living document, status banner at the top says what exists and what does not.
- `experiments/sanity_checks.md` — every defect and every check, grouped by issue, with reproduction commands. This is the file to write from.
- `CHANGELOG.md` — the same material in time order, with agent-active minutes per step.
- `experiments/pilot_readable.md` — the 15 transcripts themselves.

## Waiting on you
**GATE 1 — now also a framing decision, and an approval.** Approve REPORT.md §8 steps A–C (possible-task controls, indirect follow-up, pressure as positive control; ~30 min GPU, ~30 min agent) and I run them before you label. Or label first; either order works.

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
