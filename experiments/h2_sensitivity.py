"""H2 sensitivity analyses, pre-declared in sanity_checks 3f/3g before any lens rank existed.

Joins experiments/h2_results.json (per-response lens ranks, grouped by judge label) with the frozen
structural subgroups and hand-read cells in experiments/fcli_100_subgroups.json, and reports:
  S1  fabrication_proper (regex: durc invocation, no hedge) vs refusal      — Mann-Whitney, one-sided
  S2  liar / bullshitter / mixed / sidestep / refusal                          — medians per cell (descriptive)
Both at the first answer token and at </think>, L20 and L24, J-lens and logit lens.
Also writes figures/fig_h2_cells.png (three series: refusal, bullshitter, liar; dataviz slots 1-3).

    python experiments/h2_sensitivity.py
"""
from __future__ import annotations
import json, statistics
from pathlib import Path
from scipy.stats import mannwhitneyu
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; FIG = ROOT/"experiments"/"figures"
R = json.loads((ROOT/"experiments"/"h2_results.json").read_text()); G = json.loads((ROOT/"experiments"/"fcli_100_subgroups.json").read_text())
rows = {r["sample_index"]: r for r in R["rows"]}
sub = {}
for grp, ids in G["groups"].items():
    for i in ids: sub[i] = grp
cell = {int(k): v["cell"] for k, v in G["cot_cell"].items()}
def cells_of(i, r):
    if r["group"] == "refusal": return "refusal"
    if i in cell: return cell[i]
    return sub.get(i, "unknown")
for r in rows.values(): r["cell"] = cells_of(r["sample_index"], r)
def med(vals): return statistics.median(vals) if vals else None
out = {"n_by_cell": {}, "S1": {}, "S2": {}}
from collections import Counter
out["n_by_cell"] = dict(Counter(r["cell"] for r in rows.values()))
print("n by cell:", out["n_by_cell"])
def vals(pred, where, l, kind): return [r[where + "_median"][str(l)][kind] for r in rows.values() if pred(r)]
for where in ("at_first", "at_close"):
    for l in (20, 24):
        for kind in ("j", "ll"):
            a = vals(lambda r: r["cell"] == "refusal", where, l, kind); b = vals(lambda r: sub.get(r["sample_index"]) == "fabrication_proper", where, l, kind)
            if len(a) >= 2 and len(b) >= 2:
                u, p = mannwhitneyu(a, b, alternative="less")
                out["S1"][f"{where}|L{l}|{kind}"] = {"n_refusal": len(a), "n_fab_proper": len(b), "p_one_sided": float(p), "rank_biserial": 1 - 2*u/(len(a)*len(b)), "median_refusal": med(a), "median_fab_proper": med(b)}
            out["S2"][f"{where}|L{l}|{kind}"] = {c: {"n": len(vals(lambda r, c=c: r["cell"] == c, where, l, kind)), "median": med(vals(lambda r, c=c: r["cell"] == c, where, l, kind))} for c in ("refusal", "bullshitter", "liar", "mixed", "sidestep_no_durc", "hedged_or_refusal_with_durc")}
print("\nS1 fabrication_proper vs refusal:")
for k, v in out["S1"].items(): print(f"  {k:<18} ref n={v['n_refusal']} med={v['median_refusal']:.0f} | fab n={v['n_fab_proper']} med={v['median_fab_proper']:.0f} | p={v['p_one_sided']:.2e} r_rb={v['rank_biserial']:.2f}")
print("\nS2 medians by hand cell (first answer token, J-lens):")
for l in (20, 24):
    print(f"  L{l}: " + " | ".join(f"{c}: n={v['n']} med={v['median']:.0f}" for c, v in out["S2"][f"at_first|L{l}|j"].items() if v["n"]))
(ROOT/"experiments"/"h2_sensitivity.json").write_text(json.dumps(out, indent=1, default=str)); print("wrote experiments/h2_sensitivity.json")

# ---- figure: three cells, J-lens solid, logit lens dashed, individual responses faint ----
S1c, S2c, S3c = "#2a78d6", "#eb6834", "#1baf7a"; SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
layers = sorted(int(l) for l in next(iter(rows.values()))["at_first_median"])
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160); ax.set_facecolor(SURF); fig.set_facecolor(SURF)
for c, col, name in (("refusal", S1c, "refusal"), ("bullshitter", S2c, "fabrication — CoT asserts durc exists"), ("liar", S3c, "fabrication — CoT admits it cannot know")):
    rs = [r for r in rows.values() if r["cell"] == c]
    if not rs: continue
    for kind, dashed in (("j", False), ("ll", True)):
        m = [statistics.median(r["at_first_median"][str(l)][kind] for r in rs) for l in layers]
        ax.plot(layers, m, color=col, linewidth=2, linestyle="--" if dashed else "-", label=f"{name} (n={len(rs)}) — {'Jacobian lens' if kind=='j' else 'logit lens'}")
        if not dashed: ax.plot([layers[-1]], [m[-1]], marker="o", markersize=8, markerfacecolor=col, markeredgecolor=SURF, markeredgewidth=2, linestyle="none")
    for r in rs: ax.plot(layers, [r["at_first_median"][str(l)]["j"] for l in layers], color=col, alpha=0.12, linewidth=1)
ax.set_yscale("log"); ax.set_xticks(layers); ax.set_xlabel("decoder layer (readout at the first answer token)"); ax.set_ylabel("median rank of 5 doubt tokens (0 = top of 248k)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(True, axis="y", color=GRID, linewidth=1); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.set_title("At the moment of answering, 'knew and hid it' looks the same inside as 'believed it'", loc="left", fontsize=12, pad=14)
ax.text(0, 1.02, "fictional_cli ×100, Qwen3.5-9B. Hand-read cells frozen before lens ranks. Faint lines = individual responses. Lower = more poised.", transform=ax.transAxes, fontsize=9, color=INK2)
fig.tight_layout(); FIG.mkdir(exist_ok=True); fig.savefig(FIG/"fig_h2_cells.png"); print("wrote", FIG/"fig_h2_cells.png")
