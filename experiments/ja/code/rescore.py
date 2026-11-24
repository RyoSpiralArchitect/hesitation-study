"""Post hoc sensitivity analysis. Keep all frozen primary scores."""
import argparse
import csv
import json
import random
from collections import Counter
from design import ROOT, SEED, read_lines
from analyze import compare, metrics, paired_inference, save_csv, OUT

def load(name):
    with (OUT/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def packet(items,rows):
    cases=[r for r in rows if r["outcome"]=="invalid"]
    random.Random(SEED+173).shuffle(cases)
    questions={r["item"]:r for r in items}
    ids=[f"R{i:03d}" for i in range(1,len(cases)+1)]
    packet=[dict(id=i,reply=r["reply"],choices=json.dumps(questions[r["item"]]["choices"],ensure_ascii=False))
            for i,r in zip(ids,cases)]
    key=[dict(id=i,item=r["item"],arm=r["arm"],rep=r["rep"]) for i,r in zip(ids,cases)]
    save_csv(OUT/"rescore_blind.csv",packet[0],packet)
    save_csv(OUT/"rescore_key.csv",key[0],key)

def finish(rows):
    original=load("rescore_read.csv")
    decisions={r["id"]:r["selected"] for r in original}
    key=load("rescore_key.csv")
    if len(original)!=len(key) or set(decisions)!={r["id"] for r in key}:
        raise ValueError("Incomplete readings")
    mapping={(r["item"],r["arm"],r["rep"]):decisions[r["id"]] for r in key}
    for r in rows:
        if r["outcome"]=="invalid":
            picked=mapping[r["item"],r["arm"],r["rep"]]
            if picked not in ["A","B","C","D","invalid","abstain"]:
                raise ValueError(picked)
            r["selected"]=picked
            r["outcome"]=("correct" if picked==r["gold"] else "wrong") if picked in list("ABCD") else picked
        for k in ["hedge","pause","chars"]:
            r[k]=int(r[k])
        r["confidence"]=int(r["confidence"]) if r["confidence"] else None
    out=[]
    for arm in "ABCDE":
        rs=[r for r in rows if r["arm"]==arm]
        out.append({"arm":arm,**metrics(rs)})
    save_csv(OUT/"sensitivity.csv",out[0],out)
    baseline=[r for r in rows if r["arm"]=="A"]
    transfers={"A-"+a:compare(baseline,[r for r in rows if r["arm"]==a]) for a in "BCDE"}
    (OUT/"sensitivity_transitions.json").write_text(json.dumps(transfers,indent=2)+"\n")
    # Reuse exactly the primary resampling algorithm. Write to a separate table.
    items=read_lines(ROOT/"data/manifest.jsonl")
    paired_inference(items,rows,target=OUT/"sensitivity_effects.csv")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["packet","score"])
    mode=parser.parse_args().mode
    rows=load("scored.csv")
    if mode=="packet":
        packet(read_lines(ROOT/"data/manifest.jsonl"),rows)
    else:
        finish(rows)
