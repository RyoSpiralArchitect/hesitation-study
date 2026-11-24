"""Plot item-level response proportions for the two short-answer experiments."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
data=json.loads((ROOT/"experiments/open-ja/analysis.json").read_text())
colors={"ja":"#116b67","en":"#aa5922"}
fig,axes=plt.subplots(1,2,figsize=(10,4.5))
fig.subplots_adjust(left=.08,right=.98,bottom=.21,top=.76,wspace=.28)
fig.text(.08,.92,"How does asking for hesitation change a short answer?",size=17,weight="bold")
for ax,metric,title,key_pairs,positions in [
    (axes[0],"wrong","Concrete wrong answers",[("openA","openB"),("mcA","mcB")],[0,1,2.6,3.6]),
    (axes[1],"pause","Utterances with a filled pause or hesitation",[("openB","openF"),("editB","editF")],[0,1,2.6,3.6])]:
    for pair,ii in zip(key_pairs,(0,2)):
        for lang in ["ja","en"]:
            counts=data[lang]["counts"]
            y=[100*counts["mini/"+arm][metric]/128 for arm in pair]
            x=[v+(-.025 if lang=="ja" else .025) for v in positions[ii:ii+2]]
            ax.plot(x,y,"o-",color=colors[lang],label=lang.upper() if ii==0 else None)
    ax.set_title(title,fontsize=11,loc="left")
    ax.set_ylim(-4,104);ax.set_yticks([0,25,50,75,100])
    ax.set_ylabel("% of 128 items");ax.grid(axis="y",alpha=.2)
    ax.set_xticks(positions,["Usual","Optional","Usual","Optional"] if metric=="wrong" else ["Optional","Required","Optional","Required"])
    for x,name in [(0.5,"Open" if metric=="wrong" else "First answer"),(3.1,"Four choices" if metric=="wrong" else "Rewrite")]:
        ax.text(x,-.17,name,transform=ax.get_xaxis_transform(),ha="center",size=10)
    ax.spines[["top","right"]].set_visible(False)
fig.legend(*axes[0].get_legend_handles_labels(),loc="lower left",bbox_to_anchor=(.07,.0),ncol=2,frameon=False)
fig.savefig(ROOT/"research-notes/figures/002-open.png",dpi=180)
