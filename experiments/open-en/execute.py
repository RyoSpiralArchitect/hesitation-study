"""Run translation, then evaluation. Share the total cap with the finished Japanese study."""
import argparse
import asyncio
import fcntl
import json
import os
import sys
import httpx
import design
from design import ROOT,SHARED
sys.path.insert(1,str(SHARED))
import run
def spend(path):
    return sum(r["delta"] for r in run.read(path/"ledger.jsonl"))
async def translate():
    source=run.read(SHARED/"items.jsonl")
    folder=ROOT/"translation"
    folder.mkdir(exist_ok=True)
    run.ROOT=folder
    async with httpx.AsyncClient(base_url="https://api.openai.com",headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]},timeout=90) as client:
        runner=run.Runner(client); tasks=[]
        for i in source:
            specs={"q":{"type":"string"},"choices":{"type":"array","items":{"type":"string"}}}
            p=design.ja.payload(design.MODELS["mini"],"Translate this Japanese quiz question and each of its four options into English, keeping order, distinct entities, specificity, clues and quotations. Do not solve it or add information. Use conventional English names or transliteration. Return q and exactly four choices.",json.dumps({k:i[k] for k in ["q","choices"]},ensure_ascii=False),800,specs,temp=0)
            tasks.append((i["id"],p))
        await runner.phase(tasks)
        out=[]
        for i in source:
            v=run.unpack(runner.done[i["id"]])
            assert len(v["choices"])==4 and all(v["choices"]) and v["q"]
            out.append(dict(id=i["id"],**v,gold=v["choices"][i["choices"].index(i["gold"])]))
        data="".join(json.dumps(i,ensure_ascii=False)+"\n" for i in out)
        path=ROOT/"items.jsonl"
        if path.exists() and path.read_text()!=data:raise RuntimeError("Translation drift")
        path.write_text(data)
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=["translate","evaluate"])
    args=parser.parse_args()
    with (ROOT/".run.lock").open("a") as lock, (SHARED/".run.lock").open("a") as ja_lock:
        for f in [lock,ja_lock]:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run.BUDGET=5-spend(SHARED)
        if args.mode=="translate":
            run.BUDGET-=spend(ROOT)
            asyncio.run(translate())
        else:
            run.BUDGET-=spend(ROOT/"translation")
            asyncio.run(run.main())
