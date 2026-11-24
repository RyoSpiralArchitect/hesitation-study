"""Item-paired interaction estimates for English minus Japanese, each B minus A."""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/"experiments/en/code"))
from design import label, markers, parse_choice, read_lines, SUBJECTS, SEED
from analyze import gold_outcome

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def records(lang,adjudicate=False):
    d=BASE/"experiments"/lang/"results"
    rows=read(d/"scored.csv")
    if adjudicate:
        readout={r["id"]:r["selected"] for r in read(d/"rescore_read.csv")}
        keys={(r["item"],r["arm"],r["rep"]):readout[r["id"]] for r in read(d/"rescore_key.csv")}
        for r in rows:
            k=(r["item"],r["arm"],r["rep"])
            if k in keys:
                r["selected"]=keys[k]
                r["outcome"]=gold_outcome(keys[k],r["gold"])
    return rows

def corrected(rows):
    d=BASE/"experiments/en/correction"
    item=json.loads((d/"item.json").read_text())
    jobs={r["job"]:r for r in read_lines(d/"responses.jsonl")}
    copy=[]
    for r in rows:
        if r["item"]==item["item"]:
            r=r.copy()
            a,rep=r["arm"],int(r["rep"])-1
            job=r["item"]+":"+a+(f":{rep}" if a=="E" else "")
            ch=next(c for c in jobs[job]["choices"] if c["index"]==(0 if a=="E" else rep))
            reply,p=parse_choice(ch)
            choice=label(reply)
            h,pause=markers(reply)
            r.update(selected=choice,outcome=gold_outcome(choice,r["gold"]),reply=reply,
                     hedge=int(h),pause=int(pause),confidence=p)
        copy.append(r)
    return copy

def interactions(jp,en):
    ids=list(dict.fromkeys(r["item"] for r in jp))
    rng=np.random.default_rng(SEED+1)
    weights=np.zeros((10000,len(ids)),dtype=np.int32)
    for sub in SUBJECTS:
        ix=[i for i,v in enumerate(ids) if v.split("/")[0]==sub]
        weights[:,ix]=rng.multinomial(len(ix),[1/len(ix)]*len(ix),size=10000)
    results={}
    for name,top,den in [("accuracy",1,0),("unhedged_given_wrong",3,2),("unhedged_wrong_per_all",3,0)]:
        estimates=[]
        for rows in [jp,en]:
            groups=defaultdict(list)
            for r in rows:groups[r["item"],r["arm"]].append(r)
            tmp=[]
            for a in "AB":
                matrix=[]
                for i in ids:
                    v=groups[i,a]
                    assert len(v)==2
                    matrix.append([len(v),sum(r["outcome"]=="correct" for r in v),sum(r["outcome"]=="wrong" for r in v),sum(r["outcome"]=="wrong" and not int(r["hedge"]) for r in v)])
                m=np.asarray(matrix,dtype=np.int32)
                boot=weights@m
                tmp.append(np.r_[m[:,top].sum()/m[:,den].sum(),boot[:,top]/boot[:,den]])
            estimates.append(tmp[1]-tmp[0])
        def summary(v):
            return list(map(float,[v[0],*np.quantile(v[1:],[.025,.975])]))
        results[name]={k:summary(v) for k,v in zip(["ja","en","en_minus_ja"],[*estimates,estimates[1]-estimates[0]])}
    return results

if __name__=="__main__":
    out={}
    for mode in ["primary","adjudicated"]:
        jp,en=[records(l,mode=="adjudicated") for l in ["ja","en"]]
        out[mode]=interactions(jp,en)
        out[mode+"_translation_repair"]=interactions(jp,corrected(en))
    d=BASE/"experiments/en"
    ledgers={f:read_lines(d/f/"requests.jsonl") for f in ("results","translation","correction")}
    out["cost_USD"]={f:sum(r.get("charge",0) for r in entries) for f,entries in ledgers.items()}
    out["ledger_reserved_plus_settled_USD"]={f:sum(r["usd_delta"] for r in entries) for f,entries in ledgers.items()}
    (BASE/"comparison.json").write_text(json.dumps(out,indent=2)+"\n")
