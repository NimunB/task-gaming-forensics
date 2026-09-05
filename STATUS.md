# STATUS

## Where we are
- Gate 1 labels adopted: **agent labels endorsed by Nimun after a second adversarial read — recorded as such, not as independent human labels.** 18 honest_failure · 1 false_claim · 6 other on the N=25 fixed run.
- **Judge run (Step 7, claude-sonnet-5, $0.65 total):** κ = 1.00 vs adopted labels on 25; 25/25 genuine_success on controls; pressure identical to the hand read. Caveat: same rubric, same ground truth — this measures rubric clarity.
- **Strict-rubric pass:** flipped **1 of 25** (test_regression #2's false "18 tests pass"). Gaming 1/25 loose, **2/25 strict** [2%, 25%]. My earlier "several-fold" was wrong; corrected everywhere.
- **`PREREGISTRATION.md` drafted** for the reframed headline (outcome-tracking rate; confirmatory run 30/15 per task at penalty 1.1; judge frozen; kill checks; what would change our mind). Marked DRAFT pending your yes.
- 7h 05m agent-active of 16–20h (last 50 min: reading the Concrete Problems doc, the Jacobian-lens paper, the reference code, and the released lens artifacts). Nothing running.

## What the numbers mean so far
- **Outcome-tracking 43/44 [88%, 100%]** across impossible (18/19 disclose) and possible (25/25 claim correctly). Gaming **1/25 loose [1%, 20%], 2/25 strict [2%, 25%]**; pressure 1/25 either way.
- **Judge κ = 1.00** clears the brief's 0.7 bar but is not the human check the application doc wants: judge and agent read the same rubric. The rubric is unambiguous on these responses; whether it is the *right* rubric is a choice, and yours was the loose one.
- **Strict rubric matters less than I claimed.** The judge did not treat "verified manually" (the fix *is* correct) or "Implementation Complete ✅" (the implementation *is* complete) as false claims; only the literally false test count flipped.
- **What would change my mind:** the confirmatory run's numbers, pre-registered in `PREREGISTRATION.md` §5 with thresholds; and a blind human relabel, which does not exist.

## Dumbest way this could be wrong
- **No independent human labels.** You endorsed mine. The application doc explicitly warns about this shape; the write-up must say it plainly and the confirmatory run's adjudication set (PREREGISTRATION §2) is the fix.
- Judge–agent κ = 1.00 could reflect shared rubric text as much as shared truth.
- No positive control succeeded: detection of gaming by this pipeline remains unproven.
- All intervals are wide at N=25.

## Decisions I made without asking
- Labelled the 19 myself under the loose rubric after you delegated ("give it one more scrutinizing look... otherwise I agree"), and wrote the provenance into the sheet, the JSON, REPORT §3.9, NARRATIVE, and sanity_checks so it cannot be mistaken for a blind human label later.
- Ran the judge ($0.35) and a strict-rubric judge pass ($0.30): both within the brief's Step 7 budget and both directly requested by the framing you agreed to.
- Corrected my own "several-fold" claim in every file rather than softening it.
- Drafted PREREGISTRATION.md; **did not** remove DRAFT or launch the confirmatory run.

## Where the narrative for the write-up lives
- `NARRATIVE.md` — the story in order: ten decision points so far, one paragraph each, plus a summary table. Read this first if you have been away.
- `REPORT.md` — the findings themselves, written as they arrive. Living document, status banner at the top says what exists and what does not.
- `experiments/sanity_checks.md` — every defect and every check, grouped by issue, with reproduction commands. This is the file to write from.
- `CHANGELOG.md` — the same material in time order, with agent-active minutes per step.
- `experiments/pilot_readable.md` — the 15 transcripts themselves.

## Waiting on you
**THE DECISION: what the application is about.** Nimun's read — a one-model negative result is not a strong application — is right, and Aditya Singh's *Concrete Problems in Model Forensics* doc (8 Aug 2026) points at two upgrades that keep everything built so far. Both need your yes; neither is launched.

**Option J — J-lens on the model we have (recommended first).** The "J-lens" in that doc is Anthropic's Jacobian lens (Gurnee, Sofroniew, Lindsey; Transformer Circuits, 6 Jul 2026): it reads, at any layer and token, the vocabulary tokens an activation is *poised to verbalise*. Aditya's exact asks for our problem: *"check for deceptive J-lens readouts preceding the misrepresentation"* and *"a 'true' number for what the model did (e.g. 7), it says 8, but the lens says 7 — strong evidence."* Pre-fitted lenses exist for **Qwen3.5-9B** (camilablank/workspace-lenses, fit on the instruct model, n=25; and Neuronpedia, fit on the **Base** model, n=458). Needs no training set of gamed responses — the blocker that killed the probe plan — and runs on the 75+ responses already on disk. Approvals: (i) framing change; (ii) EITHER `pip install -e` the Apache-2.0 `anthropics/jacobian-lens` repo, which requires bumping `transformers` from 5.2.0 to ≥5.5, OR let me re-implement the ~20-line readout (`lm_head(final_norm(J_l @ h))`, formula and file format documented in the repo) against our pinned stack; (iii) one ~1 GB download (the lens file). Optionally fit our own lens on the instruct model (~100 prompts, est. 40–60 min GPU; needs a small corpus download).

**Option G — swap the subject model to `openai/gpt-oss-20b`.** Named by Aditya as a recommended internals model for exactly these environments (Norvane, Code Summary Honesty); ungated; 27.5 GB; supported by transformers 5.2.0; fits our card in bf16. A Neuronpedia J-lens exists for it too. Turns the Qwen result into a cross-model control if it games. Approvals: model switch (BRIEF §3), 27.5 GB download, optional `pip install kernels`.

**Either way, first:** the 5-minute test of whether "Answer honestly" induces false confessions on the 25 *true* successes — a clean positive finding about the "just ask" baseline. No approval needed beyond a nod.

**What I'd do:** J first (same model, same data, the reviewer's own tool and his own experiment), G second if time allows. `PREREGISTRATION.md` stays DRAFT until the framing is settled; it will be rewritten around whichever headline you choose.

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
