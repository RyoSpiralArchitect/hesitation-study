"""Run the prospectively identified single translation repair as a companion experiment."""
import asyncio
import fcntl
import json
import os
import httpx
import run
from design import ROOT, ARMS, body, parse_choice, read_lines

async def main():
    out=ROOT/"correction"
    run.RAW,run.EVENTS=out/"responses.jsonl",out/"requests.jsonl"
    item=next(i for i in read_lines(ROOT/"data/manifest.jsonl") if i["item"]=="sociology/024")
    assert item["choices"][1]==item["choices"][2]=="Cultural capital"
    item["choices"][1]="Culture of capital"
    (out/"item.json").write_text(json.dumps(item,indent=2)+"\n")
    async with httpx.AsyncClient(base_url="https://api.openai.com",headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]},timeout=80) as c:
        r=run.Run(c)
        await r.phase([(item["item"]+":"+a,body(a,item)) for a in ARMS],1)
        tasks=[]
        for ch in r.done[item["item"]+":A"]["choices"]:
            source,_=parse_choice(ch)
            if source:tasks.append((item["item"]+":E:"+str(ch["index"]),body("E",None,source)))
        await r.phase(tasks,1)
if __name__=="__main__":
    with (ROOT/"correction/.run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        asyncio.run(main())
