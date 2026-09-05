"""Figures: fig_prevalence.png (gamed share per impossible setting, Qwen3.5-9B vs GPT-OSS-20B, Wilson 95% CIs) and
fig_h5_swap.png (H5b swap control: per-statement Δ = score(18) − score(17) by prompt group). Uses the GPT-OSS
confirmatory files when judged, else pilot + widening.

    python experiments/make_figures_gptoss.py
"""
from __future__ import annotations
import json, math
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; FIG = ROOT/"experiments"/"figures"; FIG.mkdir(exist_ok=True)
S1, S2, SURF, INK, INK2, MUTED, GRID, AXIS = "#2a78d6", "#eb6834", "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
def load(n): p = ROOT/"experiments"/n; return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return (p, (c-h)/d, (c+h)/d)
GAMED = {"false_claim", "silent_omission", "workaround_as_complete"}; SETTINGS = ["fictional_cli", "test_regression", "buggy_test", "broken_test_runner", "dark_mode"]
qwen = load("judge__samples_impossible.jsonl")
conf = load("judge__gptoss_confirm_impossible.jsonl"); gpt_src = "confirmatory run, seed 43" if conf else "pilot + widening, seed 42"
gpt = conf or (load("judge__gptoss_impossible.jsonl") + load("judge__gptoss_tr_impossible25.jsonl") + load("judge__gptoss_fcli50.jsonl"))
def rates(J): return {s: wilson(sum(j["label"] in GAMED for j in J if j["setting"] == s), sum(j["setting"] == s for j in J)) + (sum(j["setting"] == s for j in J),) for s in SETTINGS}
rq, rg = rates(qwen), rates(gpt)
fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=160); ax.set_facecolor(SURF); fig.set_facecolor(SURF)
y = list(range(len(SETTINGS))); h = 0.34
for off, r, col, lab in ((-h/2, rq, S1, f"Qwen3.5-9B (n per setting = {rq[SETTINGS[0]][3]})"), (h/2, rg, S2, f"GPT-OSS-20B ({gpt_src})")):
    for i, s in enumerate(SETTINGS):
        p, lo, hi, n = r[s]; ax.barh(i+off, p, height=h-0.04, color=col, label=lab if i == 0 else None)
        ax.plot([lo, hi], [i+off, i+off], color=INK2, linewidth=1); ax.text(max(hi, p)+0.015, i+off, f"{int(round(p*n))}/{n}", va="center", fontsize=8.5, color=INK2)
ax.set_yticks(y); ax.set_yticklabels(SETTINGS); ax.invert_yaxis(); ax.set_xlim(0, 1.12); ax.set_xlabel("share of impossible-task responses judged gamed\n(false claim, silent omission, or workaround-as-complete); lines = Wilson 95% CI")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.grid(True, axis="x", color=GRID, linewidth=1); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8.5, loc="lower right")
ax.set_title("The same ten tasks: Qwen3.5-9B almost never games; GPT-OSS-20B usually does", loc="left", fontsize=11.5, pad=10)
fig.tight_layout(); fig.savefig(FIG/"fig_prevalence.png"); print("wrote fig_prevalence.png", {s: (rq[s][3], rg[s][3]) for s in SETTINGS})

# ---- H5b swap control ----
sw = json.load(open(ROOT/"experiments"/"gptoss_swap_control.json"))
fig, axes = plt.subplots(1, 2, figsize=(9, 4.8), dpi=160, sharey=False); fig.set_facecolor(SURF)
for ax, key, title in zip(axes, ("truth_lr_count", "deception_lr_count"), ("Truth probe (L16) at the count token", "Deception probe (L12) at the count token")):
    ax.set_facecolor(SURF)
    for gi, (grp, col, lab) in enumerate(((True, S1, "impossible prompt: 18 is FALSE → Δ should be > 0"), (False, S2, "possible prompt: 18 is TRUE → Δ should be < 0"))):
        d = [r[f"{key}_orig18"] - r[f"{key}_swap17"] for r in sw["rows"] if r["eighteen_is_false"] == grp]
        xs = [gi + (k - len(d)/2) * 0.035 for k in range(len(d))]
        ax.scatter(xs, d, s=36, color=col, edgecolors=SURF, linewidths=1.5, label=lab if ax is axes[0] else None, zorder=3)
        ax.__dict__.setdefault("_ticklabs", []).append(f"{'impossible' if grp else 'possible'} prompt\n(truth {17 if grp else 18})\n{sum(x > 0 for x in d)}/{len(d)} above zero")
    ax.axhline(0, color=AXIS, linewidth=1); ax.set_xticks([0, 1]); ax.set_xticklabels(ax.__dict__["_ticklabs"], fontsize=9); ax.set_xlim(-0.5, 1.5)
    ax.set_title(title, loc="left", fontsize=10.5); ax.set_ylabel("Δ = score(“18”) − score(“17”), same response")
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(True, axis="y", color=GRID, linewidth=1); ax.set_axisbelow(True)
fig.suptitle("Swap the digit inside the same response: neither probe flips with the truth — each just prefers one digit", x=0.02, ha="left", fontsize=11.5)
fig.legend(frameon=False, fontsize=8.5, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.06, 1, 0.94)); fig.savefig(FIG/"fig_h5_swap.png"); print("wrote fig_h5_swap.png")
