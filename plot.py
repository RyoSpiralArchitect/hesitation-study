"""Render the paired language contrasts with separate scales."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
summary=json.loads((ROOT/"comparison.json").read_text())
fig,axes=plt.subplots(1,2,figsize=(9.5,3.4))
fig.subplots_adjust(left=.18,right=.97,top=.72,bottom=.29,wspace=.40)
fig.text(.04,.92,"What changes when the model is asked to hesitate?",fontsize=16,weight="bold")
for ax,key,title in zip(axes,["accuracy","unhedged_given_wrong"],["Accuracy, all responses","Errors without a hedge, among errors"]):
    for y,lang in enumerate(["ja","en","en_minus_ja"]):
        for name,offset,color in [("primary",-.11,"#137c80"),("adjudicated",.11,"#91501c")]:
            value,lo,hi=[100*x for x in summary[name][key][lang]]
            ax.errorbar(value,y+offset,xerr=[[value-lo],[hi-value]],fmt="o",ms=5,color=color,capsize=2,lw=1.4,
                        label=("Frozen scoring" if name=="primary" else "After reading invalids") if y==0 else None)
    ax.axvline(0,lw=.8,c="#8c98a1")
    ax.set_title(title,loc="left",fontsize=10)
    ax.set_yticks([0,1,2],["Japanese","English","EN minus JA"] if ax==axes[0] else [])
    ax.set_ylim(2.5,-.5)
    ax.grid(axis="x",alpha=.17)
    ax.set_xlabel("B minus A (percentage points)",fontsize=9)
    for s in ax.spines.values():s.set_visible(False)
fig.legend(*axes[0].get_legend_handles_labels(),loc="lower left",bbox_to_anchor=(.03,.08),ncol=2,frameon=False,fontsize=9)
fig.text(.04,.045,"640 paired items, two samples per condition. Bars show stratified question-bootstrap 95% intervals.",fontsize=8)
fig.savefig(ROOT/"comparison.png",dpi=180)
