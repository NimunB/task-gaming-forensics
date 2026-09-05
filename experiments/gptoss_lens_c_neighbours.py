"""Per-layer summary of a gptoss_lens_c*.json with the pre-registered neighbour baseline (PREREGISTRATION §8, H7):
for false "18 passed" statements, the share where 17 / 16 / 19 outrank 18 (J-lens and logit lens), the same for
true statements, Fisher test on the frozen 17-vs-18 rule, and which of {16,17,18,19} ranks best at each layer.

    python experiments/gptoss_lens_c_neighbours.py --in gptoss_lens_c_confirm.json --out gptoss_lens_c_confirm_summary.json --fig fig_c_confirm.png
"""
from __future__ import annotations
import argparse, json, statistics as st
from collections import Counter
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import fisher_exact
ROOT = Path(__file__).resolve().parents[1]; E = ROOT/"experiments"
ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", default="gptoss_lens_c_confirm.json"); ap.add_argument("--out", default="gptoss_lens_c_confirm_summary.json"); ap.add_argument("--fig", default="fig_c_confirm.png"); ap.add_argument("--title", default="Replication (seed 43)"); a = ap.parse_args()
d = json.load(open(E/a.inp)); rows = [r for r in d["rows"] if r["stated"] == 18]; F = [r for r in rows if r["false"]]; T = [r for r in rows if not r["false"]]
layers = sorted(int(k) for k in rows[0]["count_pos"]); has16 = "j16" in rows[0]["count_pos"][str(layers[0])]
out = {"source": a.inp, "n_false": len(F), "n_true": len(T), "per_layer": {}}
for L in layers:
    c = lambda r: r["count_pos"][str(L)]; row = {}
    for kind in ("j", "ll"):
        f17 = sum(c(r)[kind+"17"] < c(r)[kind+"18"] for r in F); t18 = sum(c(r)[kind+"18"] < c(r)[kind+"17"] for r in T)
        row[kind] = {"false_17_ahead": f"{f17}/{len(F)}", "true_18_ahead": f"{t18}/{len(T)}", "fisher_p": fisher_exact([[f17, len(F)-f17], [len(T)-t18, t18]], alternative="greater")[1] if F and T else None}
        if has16:
            row[kind].update({"false_16_ahead": f"{sum(c(r)[kind+'16'] < c(r)[kind+'18'] for r in F)}/{len(F)}", "false_19_ahead": f"{sum(c(r)[kind+'19'] < c(r)[kind+'18'] for r in F)}/{len(F)}",
                              "true_16_ahead": f"{sum(c(r)[kind+'16'] < c(r)[kind+'18'] for r in T)}/{len(T)}", "true_19_ahead": f"{sum(c(r)[kind+'19'] < c(r)[kind+'18'] for r in T)}/{len(T)}",
                              "false_best_of_four": dict(Counter(min(("16", "17", "18", "19"), key=lambda k: c(r)[kind+k]) for r in F)), "true_best_of_four": dict(Counter(min(("16", "17", "18", "19"), key=lambda k: c(r)[kind+k]) for r in T)),
                              "false_17_ahead_of_16": f"{sum(c(r)[kind+'17'] < c(r)[kind+'16'] for r in F)}/{len(F)}"})
    row["median_rank_false"] = {k: st.median(c(r)["j"+k] for r in F) for k in (("16", "17", "18", "19") if has16 else ("17", "18"))}
    row["median_rank_true"] = {k: st.median(c(r)["j"+k] for r in T) for k in (("16", "17", "18", "19") if has16 else ("17", "18"))}
    out["per_layer"][L] = row
    print(f"L{L:<2} J: false 17>18 {row['j']['false_17_ahead']:>6}  true 18>17 {row['j']['true_18_ahead']:>6}  p={row['j']['fisher_p']:.1e} | logit {row['ll']['false_17_ahead']:>6} {row['ll']['true_18_ahead']:>6}" + (f" | false 16>18 {row['j']['false_16_ahead']} 19>18 {row['j']['false_19_ahead']} | true 16>18 {row['j']['true_16_ahead']} | best-of-4 false {row['j']['false_best_of_four']} true {row['j']['true_best_of_four']}" if has16 else ""))
(E/a.out).write_text(json.dumps(out, indent=1)); print("wrote", a.out)
# ---- figure: share of statements where each neighbour outranks 18, false vs true, J-lens ----
S1, S2, S3, SURF, INK, INK2, MUTED, GRID, AXIS = "#2a78d6", "#eb6834", "#1baf7a", "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), dpi=160, sharey=True); fig.set_facecolor(SURF)
for ax, G, name in zip(axes, (F, T), (f"false statements: wrote 18, truth 17 (n={len(F)})", f"true statements: wrote 18, truth 18 (n={len(T)})")):
    ax.set_facecolor(SURF)
    for tokn, col, ls in ((("17", S1, "-"), ("16", S2, "-"), ("19", S3, "-")) if has16 else (("17", S1, "-"),)):
        ys = [sum(r["count_pos"][str(L)]["j"+tokn] < r["count_pos"][str(L)]["j18"] for r in G)/len(G) for L in layers]
        ax.plot(layers, ys, color=col, linewidth=2, linestyle=ls, label=f"“{tokn}” ranked ahead of “18”"); ax.plot([layers[-1]], [ys[-1]], "o", color=col, markersize=8, markeredgecolor=SURF, markeredgewidth=2)
    ax.set_title(name, loc="left", fontsize=10.5); ax.set_xticks(layers); ax.set_xlabel("decoder layer"); ax.set_ylim(0, 1.05)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(True, axis="y", color=GRID, linewidth=1); ax.set_axisbelow(True)
axes[0].set_ylabel("share of statements"); axes[0].legend(frameon=False, fontsize=8.5, loc="lower left")
fig.suptitle(f"{a.title}: before a false “18 passed”, lower counts (16 and 17) outrank 18 — not 17 alone", x=0.02, ha="left", fontsize=11.5)
fig.text(0.02, 0.905, "gpt-oss-20b, test_regression, Jacobian lens at the position predicting the count token. The pre-registered rule was “17 ahead of 18 at layer 20”; the neighbour check asks whether 16 and 19 behave the same.", fontsize=8.3, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.88)); fig.savefig(E/"figures"/a.fig); print("wrote figures/" + a.fig)
