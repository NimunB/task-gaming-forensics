"""Figures for the report, static PNG (matplotlib), following the dataviz method:
form = trend over an ordered axis (layers) for two categorical groups -> multi-line; categorical slots in
fixed order (slot 1 blue = refusal/discloser, slot 2 orange = fabrication/control); logit-lens baseline
as the same hue dashed; 2px lines, >=8px end markers with a 2px surface ring; hairline gridlines; legend
always present; direct end-labels; text in ink tokens, never series colour; one axis (log rank).

    python experiments/make_figures.py        # reads h2_results.json / h3h4_results.json if present
"""
from __future__ import annotations
import json, statistics
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; FIG = ROOT/"experiments"/"figures"; FIG.mkdir(exist_ok=True)
S1, S2 = "#2a78d6", "#eb6834"; SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
def load(n): p = ROOT/"experiments"/n; return json.loads(p.read_text()) if p.exists() else None
def style(ax, title, sub):
    ax.set_facecolor(SURF); ax.figure.set_facecolor(SURF)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", color=GRID, linewidth=1, linestyle="-"); ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=11.5, color=INK, pad=34); ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=8.5, color=INK2, va="bottom")
def series(ax, xs, ys, color, label, dashed=False, marker_end=True):
    ax.plot(xs, ys, color=color, linewidth=2, linestyle="--" if dashed else "-", solid_joinstyle="round", solid_capstyle="round", label=label)
    if marker_end: ax.plot([xs[-1]], [ys[-1]], marker="o", markersize=8, markerfacecolor=color, markeredgecolor=SURF, markeredgewidth=2, linestyle="none")

def fig_h2():
    R = load("h2_results.json")
    if not R or not R["rows"]: return print("h2: no data")
    layers = sorted(int(l) for l in R["rows"][0]["at_first_median"])
    fig, ax = plt.subplots(figsize=(9, 5.8), dpi=160)
    for grp, col in (("refusal", S1), ("fabrication", S2)):
        rows = [r for r in R["rows"] if r["group"] == grp]
        if not rows: continue
        for kind, dashed in (("j", False), ("ll", True)):
            med = [statistics.median(r["at_first_median"][str(l)][kind] for r in rows) for l in layers]
            series(ax, layers, med, col, f"{grp} (n={len(rows)}) — {'Jacobian lens' if kind=='j' else 'logit lens'}", dashed=dashed, marker_end=not dashed)
        # individual responses as a faint wash
        for r in rows: ax.plot(layers, [r["at_first_median"][str(l)]["j"] for l in layers], color=col, alpha=0.12, linewidth=1)
    ax.set_yscale("log"); ax.set_xlabel("decoder layer (readout at the first answer token)"); ax.set_ylabel("median rank of 5 doubt tokens (0 = top of 248k)")
    ax.set_xticks(layers); ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    style(ax, "Qwen3.5-9B: doubt words are poised before a refusal, not before a fabrication", "fictional_cli ×100; 74 refusals vs 17 fabrications (judge labels). Solid = Jacobian lens, dashed = plain logit lens.\nFaint lines = individual responses. Lower rank = more poised.")
    fig.tight_layout(); fig.savefig(FIG/"fig_h2_negation_rank.png"); print("wrote", FIG/"fig_h2_negation_rank.png")

def fig_h3():
    R = load("h3h4_results.json")
    if not R or not R["H3"]["rows"]: return print("h3: no data")
    pos = ["prompt_tail", "headline", "ans25", "ans50", "ans75"]; labels = ["prompt tail\n(tool error)", "'Complete'\nheadline", "25% in", "50% in", "75% in"]
    fig, ax = plt.subplots(figsize=(9, 5.6), dpi=160)
    for grp, col, name in (("discloser_candidate", S1, "disclosers"), ("control", S2, "controls")):
        rows = [r for r in R["H3"]["rows"] if r["group"] == grp and (grp != "discloser_candidate" or r["judge_label"] == "honest_failure")]
        if not rows: continue
        med = [statistics.median(r["positions"][p]["20"]["j"][" failed"] if "20" in r["positions"][p] else r["positions"][p][20]["j"][" failed"] for r in rows) for p in pos]
        series(ax, range(len(pos)), med, col, f"{name} (n={len(rows)}) — Jacobian lens L20")
        for r in rows: ax.plot(range(len(pos)), [(r["positions"][p]["20"] if "20" in r["positions"][p] else r["positions"][p][20])["j"][" failed"] for p in pos], color=col, alpha=0.12, linewidth=1)
    ax.set_yscale("log"); ax.set_xticks(range(len(pos))); ax.set_xticklabels(labels); ax.set_ylabel("rank of ' failed' in the lens readout (0 = top)")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    style(ax, "Qwen3.5-9B: ' failed' is no more poised at the Complete headline than at the prompt tail", "dark_mode, layer 20; 15 disclosers vs 2 controls. Pre-registered rule: the headline gap must exceed the prompt-tail gap.\nIt does not — the prompt is what keeps ' failed' poised. Lower rank = more poised.")
    fig.tight_layout(); fig.savefig(FIG/"fig_h3_failed_positions.png"); print("wrote", FIG/"fig_h3_failed_positions.png")

if __name__ == "__main__":
    fig_h2(); fig_h3()
