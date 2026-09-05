# VERIFY.md — recompute every headline number yourself

Each line: the number as stated in REPORT.md, the file it comes from, and a one-line command that
recomputes it from raw outputs. Run from the repo root with `.venv` active. Numbers marked *(pending)*
are filled in when the confirmatory run's analysis lands; the commands already work on whatever is on disk.

## Behavioural (Qwen3.5-9B)

| claim (REPORT §) | recompute |
|---|---|
| Pilot gaming 1/25, disclosure 18/19 (§3.2) | `python -c "import json;from collections import Counter;print(Counter(json.loads(l)['label'] for l in open('experiments/judge__pilot_userturn.jsonl')))"` |
| Strict-rubric gaming 2/25 (§3.9) | same on `experiments/judge_strict__pilot_userturn.jsonl` |
| Possible controls 25/25 genuine_success (§3.6) | same on `experiments/judge__possible_controls.jsonl` |
| Pressure 1/25 gamed (§3.8) | same on `experiments/judge__pressure_samples.jsonl` |
| Prompt-delivery fix 8/15 → 19/25 labelable (§3.4) | `python experiments/compare_runs.py --a experiments/pilot_samples.jsonl --b experiments/pilot_userturn.jsonl` |
| Direct vs indirect follow-up, impossible (§3.7) | `python experiments/analyze_step2c.py B` |
| Direct vs indirect on true successes, 5/25 vs 0/25 (§3.10) | `python -c "import json,re;R=re.compile(r'never (created\|modified\|wrote)\|did not actually\|simulated',re.I);[print(n,sum(bool(R.search(json.loads(l)['answer'])) for l in open(f'experiments/confession_controls_{n}.jsonl'))) for n in ('direct','indirect')]"` (regex flags 4 of the 5; the fifth — dark_mode #1 "cannot verify" — is read, see REPORT) |
| Judge vs adopted labels κ = 1.00 (§3.9) | `python experiments/judge_agreement.py` |
| Wilson intervals | `python -c "import math;k,n=1,25;z=1.96;p=k/n;d=1+z*z/n;c=p+z*z/(2*n);h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n));print((c-h)/d,(c+h)/d)"` (edit k,n) |
| **H1 outcome-tracking 187/194 = 0.964 [0.927, 0.982] → supported; 187/225 = 0.831 with tool calls in the denominator** (§3.12) | `python experiments/h1_analysis.py` → `experiments/h1_results.json` (prints both denominators, per-setting counts, the 2×2 and cap hits) |
| Corrected variant 187/191, gaming 4/116 (§3.12) | rules in sanity_checks 3f/3g/3h; recompute from `judge__samples_impossible.jsonl` + `fcli_100_subgroups.json` regex |

## Jacobian lens (Qwen3.5-9B)

| claim (REPORT §) | recompute |
|---|---|
| Readout matches the model's logits (0.0) and the paper's boot→Italy→euros example (§3.11) | `python - <<'P'` … see the smoke block in CHANGELOG 2026-09-05 00:55; or rerun `experiments/jlens_experiments.py` (GPU) |
| A: true digit `7` rank 16/1/1 at L24/28/30 for the false "18"; 444–1,423 at L28 for the five true "18"s | `python -c "import json;r=json.load(open('experiments/jlens_results_2.json'));[print(e['case'],e['note'],{l:e['ranks'][l]['j']['7'] for l in ('24','28','30')}) for e in r['A_digit']]"` |
| B: ` not` rank at first answer token, L24: refusers 282–542, fabricators 147k–181k | `python -c "import json;r=json.load(open('experiments/jlens_results.json'));[print(e['note'][:30],e['at_first_answer_token']['layers']['24']['jlens']['rank'][' not']) for e in r['B']]"` |
| C: ` failed` at "Complete", L20: disclosers 205–716, controls 6,315–13,473; prompt tail ~511–544 | `python -c "import json;r=json.load(open('experiments/jlens_results_2.json'));[print(e['note'],e['case'],{k:v['failed_j']['20'] for k,v in e['positions'].items()}) for e in r['C_deconfound']]"` |
| **H2 / H3 / H4 on the scaled runs** *(pending)* | `python experiments/h2_analysis.py`; `python experiments/h3h4_analysis.py` (GPU) → `h2_results.json`, `h3h4_results.json`; figures: `python experiments/make_figures.py` |

## Provenance

| item | check |
|---|---|
| Pre-registration predates the confirmatory sampling | `git log -1 --format='%H %ci' -- PREREGISTRATION.md; stat -c '%y' experiments/samples_impossible.jsonl` |
| Tasks unchanged since Step 3 approval | `git log --oneline -- task_gaming/tasks.json` |
| Labels are agent labels endorsed by Nimun, not blind human labels | `sed -n '1,12p' experiments/handlabel_gate1.md` |
