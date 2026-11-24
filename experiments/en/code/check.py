"""Verify provenance and compute blinded audit and same-wrong-choice readouts."""
import csv
import hashlib
import json
from collections import Counter
from statistics import mean
from design import ROOT,MODEL,read_lines
OUT=ROOT/"results"
def tab(name):
    with (OUT/name).open(encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def main():
    for file,sha in json.loads((ROOT/"data/freeze.json").read_text()).items():
        if "/" in file:assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==sha
    observed=tab("scored.csv")
    assert len(observed)==len({(r['item'],r['arm'],r['rep']) for r in observed})==6400
    jobs=read_lines(OUT/"responses.jsonl")
    assert len(jobs)==len({r["job"] for r in jobs})
    assert {r["model"] for r in jobs}=={MODEL}
    keys={r['id']:r for r in tab('audit_key.csv')}
    blind=tab('audit_read.csv')
    assert len(keys)==len(blind)==80
    dec=[r for r in blind if r["reader_hedge"]!="ambiguous"]
    lookup={(r['item'],r['arm'],r['rep']):r for r in observed}
    wrong=[]
    for a in observed:
        if a['arm']!='A' or a['outcome']!='wrong':continue
        b=lookup[a['item'],'B',a['rep']]
        if b['selected']==a['selected']:wrong.append((a,b))
    result=dict(n_calls=len(jobs),n_replies=sum(len(j["choices"]) for j in jobs),
                termination=dict(Counter(c["finish_reason"] for j in jobs for c in j["choices"])),
                same_wrong=len(wrong),same_wrong_probs=[mean(int(p[i]["confidence"]) for p in wrong if p[i]["confidence"]) for i in [0,1]],
                newly_hedged=sum(a["hedge"]=="0" and b["hedge"]=="1" for a,b in wrong),
                audit_hedge_n=len(dec),audit_hedge_match=sum((r["reader_hedge"]=="yes")==(keys[r['id']]['hedge']=='1') for r in dec),
                audit_pause_match=sum((r["reader_pause"]=="yes")==(keys[r['id']]['pause']=='1') for r in blind))
    (OUT/"verification.json").write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__": main()
