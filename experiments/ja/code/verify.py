"""Cross-check study completeness, costs, matched reports of confidence and the two audits."""
import csv
import hashlib
import json
import statistics
from collections import Counter
from design import ROOT, MODEL, PRICE, COST_LIMIT_USD, read_lines

OUT=ROOT/"results"
def table(name):
    with (OUT/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def main():
    freeze=json.loads((ROOT/"data/freeze.json").read_text())
    for name in ["data/manifest.jsonl","protocol.md","code/design.py","code/prepare.py"]:
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==freeze[name]
    items=read_lines(ROOT/"data/manifest.jsonl")
    assert len({(r["question"],tuple(r["choices"])) for r in items})==640
    assert set(Counter(r["subject"] for r in items).values())=={80}
    raw=read_lines(OUT/"responses.jsonl")
    assert len(raw)==len({r["job"] for r in raw})==len({r["id"] for r in raw})==3840
    assert {r["model"] for r in raw}=={MODEL}
    n=sum(len(r["choices"]) for r in raw)
    assert n==6400
    records=table("scored.csv")
    assert len(records)==len({(r["item"],r["arm"],r["rep"]) for r in records})==n
    groups={a:[r for r in records if r["arm"]==a] for a in "ABCDE"}
    metric_table={r["arm"]:r for r in table("summary.csv")}
    for arm,rs in groups.items():
        assert len(rs)==1280
        vals=Counter(r["outcome"] for r in rs)
        assert all(int(metric_table[arm][c])==vals[c] for c in ["correct","wrong","abstain","invalid","missing"])
        assert abs(float(metric_table[arm]["accuracy"])-vals["correct"]/len(rs))<1e-12
    # Independent reconstruction from keyed records, not zip ordering.
    lookup={(r["item"],r["arm"],r["rep"]):r for r in records}
    identical={}
    for outcome in ("correct","wrong"):
        pairs=[]
        for a in groups["A"]:
            b=lookup[a["item"],"B",a["rep"]]
            if a["outcome"]==b["outcome"]==outcome and a["selected"]==b["selected"]:
                pairs.append((a,b))
        identical[outcome]={"n":len(pairs),"A_conf_percent":statistics.mean(int(a["confidence"]) for a,b in pairs),
                            "B_conf_percent":statistics.mean(int(b["confidence"]) for a,b in pairs),
                            "A_unhedged_B_hedged":sum(a["hedge"]=='0' and b["hedge"]=='1' for a,b in pairs)}
    endings=Counter(ch["finish_reason"] for r in raw for ch in r["choices"])
    events=read_lines(OUT/"requests.jsonl")
    usage={k:sum(r["usage"][k] for r in raw) for k in ["prompt_tokens","completion_tokens"]}
    cached=sum((r["usage"].get("prompt_tokens_details") or {}).get("cached_tokens",0) for r in raw)
    bill=((usage["prompt_tokens"]-cached)*PRICE["input"]+cached*PRICE["cached"]+
          usage["completion_tokens"]*PRICE["output"])/1e6
    assert abs(sum(e["usd_delta"] for e in events)-bill)<1e-8 and bill<COST_LIMIT_USD
    keys={r["id"]:r for r in table("audit_key.csv")}
    audit=table("audit_read.csv")
    fixed=[r for r in audit if r["reader_hedge"]!="ambiguous"]
    matched=sum((r["reader_hedge"]=="yes")==(keys[r["id"]]["hedge"]=="1") for r in fixed)
    matched_pause=sum((r["reader_pause"]=="yes")==(keys[r["id"]]["pause"]=="1") for r in audit)
    info={"items":len(items),"unique_stems":len({r["question"] for r in items}),"requests":len(raw),"outputs":n,
          "provider_fingerprints":len({r["system_fingerprint"] for r in raw}),"received_utc":[raw[0]["received_utc"],raw[-1]["received_utc"]],
          "ends":dict(endings),"requests_by_event":dict(Counter(r["event"] for r in events)),"tokens":{**usage,"cached":cached},
          "estimated_USD":bill,"A_B_same_choice":identical,"blind_read":{"n":len(audit),"hedge_decidable":len(fixed),
          "hedge_matched":matched,"pause_matched":matched_pause}}
    (OUT/"verification.json").write_text(json.dumps(info,indent=2)+"\n")
    print("Verified",n,"outputs; paired confidence, billing and audit counts saved.")

if __name__=="__main__":main()
