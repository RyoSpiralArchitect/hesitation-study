"""Score all scheduled outputs, with paired inference at the question level."""
import csv
import itertools
import json
import math
import random
import statistics as st
from collections import Counter, defaultdict

import numpy as np
from design import ARMS, ROOT, SEED, SUBJECTS, label, markers, parse_choice, read_lines

OUT = ROOT/"results"
ARMS_ALL = list("ABCDE")
def save_csv(path, fields, rows):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def rate(n,d):
    return n/d if d else None

def avg(values):
    return st.mean(values) if len(values) else None

def gold_outcome(selected,gold):
    if selected in ("invalid","abstain","missing"):
        return selected
    return "correct" if selected == gold else "wrong"

def score():
    items=read_lines(ROOT/"data/manifest.jsonl")
    raw=read_lines(OUT/"responses.jsonl")
    jobmap={r["job"]:r for r in raw}
    if len(jobmap)!=len(raw):
        raise RuntimeError("Duplicate successful request")
    rows=[]
    for item, arm, rep in itertools.product(items,ARMS_ALL,range(2)):
        job=item["item"]+":"+arm+(f":{rep}" if arm=="E" else "")
        if job not in jobmap:
            if arm!="E":
                raise RuntimeError("Study incomplete, missing "+job)
            a=jobmap[item["item"]+":A"]
            a_choice=next(ch for ch in a["choices"] if ch["index"]==rep)
            if parse_choice(a_choice)[0]:
                raise RuntimeError("Missing required rewrite "+job)
            text=""; conf=None; result="missing"
        else:
            request=jobmap[job]
            idx=0 if arm=="E" else rep
            choice=next(ch for ch in request["choices"] if ch["index"]==idx)
            text,conf=parse_choice(choice)
            result=label(text)
        hedge,pause=markers(text)
        rows.append(dict(item=item["item"],subject=item["subject"],gold=item["gold"],arm=arm,
                         rep=rep+1,reply=text,selected=result,outcome=gold_outcome(result,item["gold"]),
                         confidence=conf,hedge=int(hedge),pause=int(pause),chars=len(text)))
    save_csv(OUT/"scored.csv",rows[0],rows)
    return items,raw,rows

def metrics(rs):
    n=len(rs)
    counts=Counter(r["outcome"] for r in rs)
    valid=[r for r in rs if r["outcome"] in ("correct","wrong")]
    wrong=[r for r in valid if r["outcome"]=="wrong"]
    correct=[r for r in valid if r["outcome"]=="correct"]
    conf=[r for r in valid if r["confidence"] is not None]
    bins=defaultdict(list)
    for r in conf:
        bins[min(r["confidence"]//10,9)].append(r)
    ece=0
    for v in bins.values():
        ece+=abs(sum(r["confidence"]/100-(r["outcome"]=="correct") for r in v))
    without=sum(not r["hedge"] for r in wrong)
    return dict(n=n,correct=counts["correct"],wrong=counts["wrong"],abstain=counts["abstain"],
                invalid=counts["invalid"],missing=counts["missing"],answered=len(valid),
                accuracy=counts["correct"]/n,error_rate=counts["wrong"]/n,coverage=len(valid)/n,
                answered_accuracy=rate(counts["correct"],len(valid)),
                wrong_without_hedge=without,without_hedge_given_wrong=rate(without,len(wrong)),
                wrong_and_no_hedge_per_all=without/n,hedge_given_correct=avg([r["hedge"] for r in correct]),
                hedge_given_answer=avg([r["hedge"] for r in valid]),
                pause_given_answer=avg([r["pause"] for r in valid]),
                avg_chars=avg([r["chars"] for r in rs if r["reply"]]),
                n_conf=len(conf),mean_p=avg([r["confidence"]/100 for r in conf]),
                mean_p_wrong=avg([r["confidence"]/100 for r in wrong if r["confidence"] is not None]),
                mean_p_correct=avg([r["confidence"]/100 for r in correct if r["confidence"] is not None]),
                brier=avg([(r["confidence"]/100-(r["outcome"]=="correct"))**2 for r in conf]),
                ece=rate(ece,len(conf)))

def make_blind(rows):
    rng=random.Random(SEED+2)
    audit=[]
    for arm,outcome in itertools.product(ARMS_ALL,["correct","wrong"]):
        pool=[r for r in rows if r["arm"]==arm and r["outcome"]==outcome]
        audit.extend(rng.sample(pool,min(8,len(pool))))
    rng.shuffle(audit)
    ids=[f"T{i:03}" for i in range(1,len(audit)+1)]
    save_csv(OUT/"audit_blind.csv",["id","reply"],[dict(id=i,reply=r["reply"]) for i,r in zip(ids,audit)])
    fields=["item","arm","rep","outcome","hedge","pause"]
    save_csv(OUT/"audit_key.csv",["id",*fields],[{"id":i,**{f:r[f] for f in fields}} for i,r in zip(ids,audit)])

def paired_inference(items,rows,target=OUT/"effects.csv"):
    # Each resampled unit carries both responses and every arm. Ratios keep their own denominators.
    lookup=defaultdict(list)
    for r in rows:
        lookup[(r["item"],r["arm"])].append(r)
    rng=np.random.default_rng(SEED+1)
    weights=np.zeros((10_000,len(items)),dtype=np.int32)
    for subject in SUBJECTS:
        ix=[i for i,item in enumerate(items) if item["subject"]==subject]
        weights[:,ix]=rng.multinomial(len(ix),[1/len(ix)]*len(ix),size=len(weights))
    def vector(rs):
        ok=sum(r["outcome"]=="correct" for r in rs)
        wrong=sum(r["outcome"]=="wrong" for r in rs)
        unhedged=sum(r["outcome"]=="wrong" and not r["hedge"] for r in rs)
        abstain=sum(r["outcome"]=="abstain" for r in rs)
        return [len(rs),ok,wrong,unhedged,abstain]
    measures=[("accuracy",1,0),("error_rate",2,0),("wrong_and_no_hedge_per_all",3,0),
              ("without_hedge_given_wrong",3,2),("abstain_rate",4,0)]
    calc={}
    for arm in ARMS_ALL:
        mat=np.asarray([vector(lookup[item["item"],arm]) for item in items],dtype=np.int32)
        observed=mat.sum(axis=0); boot=weights@mat
        assert np.all(boot[:,0] == observed[0]) and np.all(boot[:,1:] <= boot[:,0,None])
        for metric,i,j in measures:
            calc[arm,metric]=(observed[i]/observed[j],boot[:,i]/boot[:,j])
    out=[]
    for arm in "BCDE":
        for metric,_,_ in measures:
            estimate,dist=calc[arm,metric]; baseline,samples=calc["A",metric]
            lo,hi=np.quantile(dist-samples,[.025,.975])
            out.append(dict(contrast=arm+"-A",metric=metric,delta=estimate-baseline,low95=lo,high95=hi))
    save_csv(target,out[0],out)
    return out

def compare(left,right):
    pairs=list(zip(left,right,strict=True))
    counts=Counter((a["outcome"],b["outcome"]) for a,b in pairs)
    valid=[(a,b) for a,b in pairs if a["selected"] not in ("invalid","missing")
            and b["selected"] not in ("invalid","missing")]
    wrong_both=[(a,b) for a,b in pairs if a["outcome"]==b["outcome"]=="wrong"]
    same_letter_wrong=[(a,b) for a,b in wrong_both if a["selected"]==b["selected"]]
    return {"n":len(pairs),"both_valid":len(valid),"same_choice_or_abstain":sum(a["selected"]==b["selected"] for a,b in valid),
            "same_wrong_letter":len(same_letter_wrong),
            "same_wrong_letter_gained_hedge":sum((not a["hedge"]) and b["hedge"] for a,b in same_letter_wrong),
            "same_wrong_letter_lost_hedge":sum(a["hedge"] and not b["hedge"] for a,b in same_letter_wrong),
            "same_wrong_letter_neither_hedged":sum(not a["hedge"] and not b["hedge"] for a,b in same_letter_wrong),
            "outcomes":{f"{a}_to_{b}":n for (a,b),n in sorted(counts.items())}}

def main():
    items,raw,rows=score()
    groups={a:[r for r in rows if r["arm"]==a] for a in ARMS_ALL}
    save_csv(OUT/"summary.csv",["arm",*metrics(groups["A"])],[dict(arm=a,**metrics(rs)) for a,rs in groups.items()])
    per_subject=[]
    calibration=[]
    transitions={}
    for a,rs in groups.items():
        for subj in SUBJECTS:
            v=[r for r in rs if r["subject"]==subj]
            per_subject.append(dict(arm=a,subject=subj,**metrics(v)))
        for idx in range(10):
            v=[r for r in rs if r["outcome"] in ("correct","wrong") and r["confidence"] is not None
               and min(9,r["confidence"]//10)==idx]
            calibration.append(dict(arm=a,lower=idx*10,upper=(idx+1)*10,n=len(v),
                                    mean_p=avg([r["confidence"]/100 for r in v]),
                                    accuracy=avg([r["outcome"]=="correct" for r in v])))
        transitions[a+"1-"+a+"2"]=compare(rs[::2],rs[1::2])
        if a!="A":
            transitions["A-"+a]=compare(groups["A"],rs)
    save_csv(OUT/"subjects.csv",per_subject[0],per_subject)
    save_csv(OUT/"calibration.csv",calibration[0],calibration)
    (OUT/"transitions.json").write_text(json.dumps(transitions,indent=2)+"\n")
    paired_inference(items,rows)
    make_blind(rows)
    print("Scored",len(rows),"rows. Blinded audit sample available.")

if __name__=="__main__":
    main()
