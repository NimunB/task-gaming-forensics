"""Summarise option (c): does the workspace rank the TRUE count above the STATED count when the statement is false?
Per statement and layer: sign of (rank_17 - rank_18). False statements (truth 17, wrote 18) should have 17 ahead;
true statements (truth 18, wrote 18) should have 18 ahead. Fisher exact at each layer; logit-lens twin; also the
rank of ' failed' at the position after the count. Writes gptoss_lens_c_summary.json and figures/fig_c_true_count.png.
"""
import json, statistics
from pathlib import Path
from scipy.stats import fisher_exact
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; R=json.loads((ROOT/"experiments"/"gptoss_lens_c.json").read_text()); rows=R["rows"]
layers=sorted(int(l) for l in rows[0]["count_pos"]); F=[r for r in rows if r["false"]]; T=[r for r in rows if not r["false"]]
out={"n_false":len(F),"n_true":len(T),"lens":R["lens"],"per_layer":{}}
for l in layers:
    L=str(l)
    for kind in ("j","ll"):
        f_true_ahead=sum(r["count_pos"][L][f"{kind}17"] < r["count_pos"][L][f"{kind}18"] for r in F)   # false stmt: truth(17) ranked above stated(18)
        t_true_ahead=sum(r["count_pos"][L][f"{kind}18"] < r["count_pos"][L][f"{kind}17"] for r in T)   # true stmt: truth(18) ranked above 17
        # 2x2: rows = false/true statement; cols = "17 ahead" / "18 ahead"
        table=[[f_true_ahead, len(F)-f_true_ahead],[len(T)-t_true_ahead, t_true_ahead]]
        odds,p=fisher_exact(table)
        out["per_layer"].setdefault(L,{})[kind]={"false_stmts_with_17_ahead":f"{f_true_ahead}/{len(F)}","true_stmts_with_18_ahead":f"{t_true_ahead}/{len(T)}","fisher_p":p,
            "median_rank17_false":statistics.median(r["count_pos"][L][f"{kind}17"] for r in F),"median_rank18_false":statistics.median(r["count_pos"][L][f"{kind}18"] for r in F),
            "median_rank17_true":statistics.median(r["count_pos"][L][f"{kind}17"] for r in T),"median_rank18_true":statistics.median(r["count_pos"][L][f"{kind}18"] for r in T)}
    out["per_layer"][L]["failed_after_count_median"]={"false":statistics.median(r["after_count_pos"][L]["failed"] for r in F),"true":statistics.median(r["after_count_pos"][L]["failed"] for r in T)}
print(f"n false={len(F)} true={len(T)} | lens anchor L{R['lens']['anchor_layer']} dist {R['lens']['anchor_dist']:.2f}")
print(f"{'layer':>5} | J-lens: false w/17 ahead | true w/18 ahead | Fisher p   || logit lens: same | same | p        || median r17,r18 false | true")
for l in layers:
    L=str(l); j=out["per_layer"][L]["j"]; ll=out["per_layer"][L]["ll"]
    print(f"{l:>5} | {j['false_stmts_with_17_ahead']:>8} | {j['true_stmts_with_18_ahead']:>8} | {j['fisher_p']:.1e} || {ll['false_stmts_with_17_ahead']:>8} | {ll['true_stmts_with_18_ahead']:>8} | {ll['fisher_p']:.1e} || {j['median_rank17_false']:.0f},{j['median_rank18_false']:.0f} | {j['median_rank17_true']:.0f},{j['median_rank18_true']:.0f}")
print("' failed' rank at the position after the count (median, J-lens L20): false", out["per_layer"]["20"]["failed_after_count_median"]["false"], "| true", out["per_layer"]["20"]["failed_after_count_median"]["true"])
(ROOT/"experiments"/"gptoss_lens_c_summary.json").write_text(json.dumps(out,indent=1))
# ---- figure: per-layer fraction of statements where the TRUE count is ranked ahead, false vs true statements ----
S1,S2="#2a78d6","#eb6834"; SURF,INK,INK2,MUTED,GRID,AXIS="#fcfcfb","#0b0b0b","#52514e","#898781","#e1e0d9","#c3c2b7"
plt.rcParams.update({"font.family":"sans-serif","font.size":10,"axes.edgecolor":AXIS,"axes.labelcolor":INK2,"xtick.color":MUTED,"ytick.color":MUTED,"text.color":INK})
fig,ax=plt.subplots(figsize=(9,5.6),dpi=160); ax.set_facecolor(SURF); fig.set_facecolor(SURF)
for grp,col,label,key,n in (("false",S1,"false statements: wrote 18, truth 17 — share with 17 ranked ahead","false_stmts_with_17_ahead",len(F)),("true",S2,"true statements: wrote 18, truth 18 — share with 18 ranked ahead","true_stmts_with_18_ahead",len(T))):
    for kind,dashed in (("j",False),("ll",True)):
        ys=[int(out["per_layer"][str(l)][kind][key].split("/")[0])/n for l in layers]
        ax.plot(layers,ys,color=col,linewidth=2,linestyle="--" if dashed else "-",label=f"{'False' if grp=='false' else 'True'} statements (n={n}) — {'Jacobian lens' if kind=='j' else 'logit lens'}")
        if not dashed: ax.plot([layers[-1]],[ys[-1]],marker="o",markersize=8,markerfacecolor=col,markeredgecolor=SURF,markeredgewidth=2,linestyle="none")
ax.set_ylim(0,1.05); ax.set_xticks(layers); ax.set_xlabel("decoder layer"); ax.set_ylabel("share where the TRUE count outranks the other")
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.grid(True,axis="y",color=GRID,linewidth=1); ax.set_axisbelow(True); ax.legend(frameon=False,fontsize=8.5,loc="upper center",bbox_to_anchor=(0.5,-0.16),ncol=2)
ax.set_title("Before GPT-OSS writes a false '18 passed', its workspace ranks the true count ahead", loc="left", fontsize=11.5, pad=38)
ax.text(0,1.025,"gpt-oss-20b, test_regression, readout at the position predicting the count token. False statements: wrote 18, truth 17 (share with 17 ahead).\nTrue statements: wrote 18, truth 18 (share with 18 ahead). At layer 20: 19/20 vs 15/15, Fisher p = 4.9e-9. Lens: Neuronpedia (457 prompts).",transform=ax.transAxes,fontsize=8.2,color=INK2,va="bottom")
fig.tight_layout(); (ROOT/"experiments"/"figures").mkdir(exist_ok=True); fig.savefig(ROOT/"experiments"/"figures"/"fig_c_true_count.png"); print("wrote figures/fig_c_true_count.png")
