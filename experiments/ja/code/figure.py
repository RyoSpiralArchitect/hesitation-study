"""Plot the question-paired effects and the lexical outcome from the scored data."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, MaxNLocator
from design import ROOT

def read_csv(name):
    with (ROOT/"results"/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def main():
    candidates=[Path("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")]
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"]=font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams.update({"axes.unicode_minus":False,"savefig.facecolor":"#FFFFFF","figure.facecolor":"#FFFFFF"})
    summary=read_csv("summary.csv")
    eff={r["contrast"][0]:r for r in read_csv("effects.csv") if r["metric"]=="accuracy"}
    names=["A   通常回答","B   事前に言い淀む","C   不確かなときだけ留保","D   断定する","E   A を事後に書き換える"]
    fig,(left,right)=plt.subplots(1,2,figsize=(11.2,4.7),gridspec_kw={"width_ratios":[1,1]})
    fig.subplots_adjust(left=.225,right=.95,top=.78,bottom=.21,wspace=.25)
    fig.text(.047,.94,"言い淀むよう頼むと、答えの正しさと言い方はどう変わるか",fontsize=16,color="#1e293b")
    left.set_title("全出力の正答率差（対 A、ポイント）",loc="left",fontsize=11,pad=16)
    right.set_title("誤答のうち、留保語がない割合（%）",loc="left",fontsize=11,pad=16)
    max_extent=max(4.0,max(max(abs(float(r[k])*100) for k in ("low95","high95")) for r in eff.values())+1.1)
    left.set_xlim(-max_extent,max_extent);left.axvline(0,color="#78889a",lw=1)
    left.xaxis.set_major_locator(MaxNLocator(nbins=6,integer=True))
    left.xaxis.set_major_formatter(FuncFormatter(lambda v,pos:f"{v:+g}" if v else "0"))
    right.set_xlim(-5,115);right.set_xticks([0,25,50,75,100])
    left.set_yticks(range(5),names);right.set_yticks([])
    for i,r in enumerate(summary):
        a=r["arm"]
        v,lo,hi=(0,0,0) if a=="A" else [float(eff[a][k])*100 for k in ("delta","low95","high95")]
        color="#00786c" if a=="B" else "#394c62"
        left.errorbar(v,i,xerr=[[max(0,v-lo)],[max(0,hi-v)]],fmt="o",ms=7,capsize=3,lw=1.6,color=color)
        pct=100*float(r["without_hedge_given_wrong"])
        right.hlines(i,0,pct,lw=3,color="#d2dce2")
        right.plot(pct,i,"o",color=color,ms=7)
        right.text(pct+3,i,f"{pct:.1f}",va="center",color=color,fontsize=10)
    for ax in (left,right):
        ax.set_ylim(4.55,-.55)
        ax.set_axisbelow(True)
        ax.grid(axis="x",lw=.6,color="#e0e6eb")
        ax.tick_params(axis="both",which="both",length=0,labelsize=10,pad=8,colors="#394c62")
        for spine in ax.spines.values():spine.set_visible(False)
    fig.text(.047,.073,"JMMLU 8科目・640問 × 各条件2回。左の線は設問単位で対応を保った95%区間。",fontsize=9,color="#485b6a")
    fig.text(.047,.027,"留保の有無は固定した語形辞書で判定。「ええと」や「……」などのためらいだけでは留保に数えない。",fontsize=9,color="#485b6a")
    fig.savefig(ROOT/"results/figure.png",dpi=180)
    plt.close(fig)
if __name__=="__main__":
    main()
