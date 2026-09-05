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
| **H2 supported**: `</think>` L20 refusals 204 vs fabrications 8,538, p = 9e-9, r = 0.88; logit-lens twin r = 0.91 (§3.13) | `python -c "import json;t=json.load(open('experiments/h2_results.json'))['tests'];[print(k,v['median_refusal'],v['median_fabrication'],v['p_one_sided'],round(v['rank_biserial'],2)) for k,v in t.items()]"` (GPU to regenerate: `python experiments/h2_analysis.py`) |
| Liar vs bullshitter cells indistinguishable (§3.13) | `python experiments/h2_sensitivity.py` → S2 table; cells in `experiments/fcli_100_subgroups.json` |
| **H3 withdrawn** — headline gap 481 vs 13,731; prompt-tail gap 544 vs 8,113 (§3.14) | `python -c "import json;t=json.load(open('experiments/h3h4_results.json'))['H3']['tests'];[print(k,v.get('median_disclosers'),v.get('median_controls'),v.get('p_one_sided')) for k,v in t.items() if ' failed' in k and 'L20' in k]"` |
| H4 untestable — no false counts (§3.15) | `python -c "import json;print([(r['task_id'],r['stated'],r['truth'],r['false']) for r in json.load(open('experiments/h3h4_results.json'))['H4']['rows']])"` |
| Strict 10/119 vs loose 7/119; seed-43 4/45 gamed (§3.16) | `python experiments/h1_analysis.py`; `python -c "import json;from collections import Counter;print(Counter(json.loads(l)['label'] for l in open('experiments/judge__samples_seed43.jsonl')))"` |
| Figures | `python experiments/make_figures.py && python experiments/h2_sensitivity.py` → `experiments/figures/` |

## GPT-OSS-20B

| claim (REPORT §) | recompute |
|---|---|
| Pilot gaming 14/20 claims; widened test_regression 27/30 false_claim; fictional_cli 55/55 (§3.17) | `python -c "import json;from collections import Counter;[print(f,Counter(json.loads(l)['label'] for l in open('experiments/'+f))) for f in ('judge__gptoss_impossible.jsonl','judge__gptoss_tr_impossible25.jsonl','judge__gptoss_fcli50.jsonl','judge__gptoss_possible.jsonl','judge__gptoss_tr_possible10.jsonl')]"` |
| Zero analysis-channel tokens on prefilled tasks (§3.17) | `python -c "import json;[print(r['setting'],r['sample_index'],r['n_thinking_tokens']) for r in map(json.loads,open('experiments/gptoss_impossible.jsonl'))]"` |
| **True count ranked ahead at L20: 19/20 false vs 15/15 true, Fisher p = 4.9e-9; logit lens 18/20** (§3.18) | `python experiments/gptoss_lens_c_summary.py` (reads `gptoss_lens_c.json`; GPU to regenerate: `python experiments/gptoss_lens_c.py`) |

| GPT-OSS confirmatory per-task counts, strict, controls (§3.20) | `python -c "import json;from collections import Counter;[print(f,{s:dict(Counter(j['label'] for j in map(json.loads,open('experiments/'+f)) if j['setting']==s)) for s in ('fictional_cli','test_regression','buggy_test','dark_mode','broken_test_runner')}) for f in ('judge__gptoss_confirm_impossible.jsonl','judge_strict__gptoss_confirm_impossible.jsonl','judge__gptoss_confirm_possible.jsonl')]"` |
| H1-analogue 102/196 (§3.20) | `python -c "import json;J=[json.loads(l) for f in ('judge__gptoss_confirm_impossible.jsonl','judge__gptoss_confirm_possible.jsonl') for l in open('experiments/'+f)];c=[j for j in J if j['label']!='other'];print(sum(j['label'] in ('honest_failure','genuine_success') for j in c),len(c))"` |
| Lens replication 22/24, 12/15; 16 ahead 24/24; 19 ahead 1/24 (§3.21) | `python experiments/gptoss_lens_c_neighbours.py --in gptoss_lens_c_confirm.json --out /tmp/x.json --fig /tmp/x.png` |
| Original 35 re-read with 16/19: 16 ahead 20/20, best-of-four 17:13/16:7 (§3.18 post hoc) | `python experiments/gptoss_lens_c_neighbours.py --in gptoss_lens_c.json --out /tmp/y.json --fig /tmp/y.png` |
| Probe negative + swap control, original and replication (§3.19, §3.21) | `python -c "import json;[print(f,json.load(open('experiments/'+f))['summary']) for f in ('gptoss_swap_control.json','gptoss_swap_control_confirm.json')]"` |

## Provenance

| item | check |
|---|---|
| Pre-registration predates the confirmatory sampling | `git log -1 --format='%H %ci' -- PREREGISTRATION.md; stat -c '%y' experiments/samples_impossible.jsonl` |
| Tasks unchanged since Step 3 approval | `git log --oneline -- task_gaming/tasks.json` |
| Labels are agent labels endorsed by Nimun, not blind human labels | `sed -n '1,12p' experiments/handlabel_gate1.md` |
