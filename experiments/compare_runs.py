"""Compare two sampling runs on the structural question: did the model produce a report at all?

Used for the final-turn-note A/B (sanity_checks.md issue 3). Deliberately does not label honesty —
that is Gate 1 and Step 7. It answers only: did the response contain a claim we could label?

    python experiments/compare_runs.py --a experiments/pilot_samples.jsonl \
        --b experiments/pilot_userturn.jsonl --label-a "note in tool result" --label-b "note as user turn"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def classify(r: dict) -> str:
    """Structural classification only — no honesty judgement."""
    if not r["closed_think"] or r["n_answer_tokens"] == 0:
        return "no answer"
    if "<tool_call>" in r["answer"]:
        return "tool call"
    return "report"


def summarise(rows: list[dict]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["setting"], {}).setdefault(classify(r), 0)
        out[r["setting"]][classify(r)] += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path, required=True)
    ap.add_argument("--b", type=Path, required=True)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    sa, sb = summarise(A), summarise(B)
    kinds = ("report", "tool call", "no answer")

    print(f"A = {args.label_a}  (n={len(A)}, {args.a.name})")
    print(f"B = {args.label_b}  (n={len(B)}, {args.b.name})\n")
    print(f"{'setting':<22}" + "".join(f"{k+' A':>13}{k+' B':>13}" for k in kinds))
    for setting in sorted(set(sa) | set(sb)):
        row = f"{setting:<22}"
        for k in kinds:
            na = sa.get(setting, {}).get(k, 0)
            nb = sb.get(setting, {}).get(k, 0)
            row += f"{na:>13}{nb:>13}"
        print(row)

    ta = {k: sum(v.get(k, 0) for v in sa.values()) for k in kinds}
    tb = {k: sum(v.get(k, 0) for v in sb.values()) for k in kinds}
    print(f"\n{'TOTAL':<22}" + "".join(f"{ta[k]:>13}{tb[k]:>13}" for k in kinds))
    print(f"\nresponses containing a claim we can label: "
          f"A {ta['report']}/{len(A)} ({100*ta['report']/len(A):.0f}%), "
          f"B {tb['report']}/{len(B)} ({100*tb['report']/len(B):.0f}%)")
    print("\nThe two affected settings are broken_test_runner and dark_mode; the other three have "
          "identical prompts in both runs and are a sanity check that nothing else moved.")


if __name__ == "__main__":
    main()
