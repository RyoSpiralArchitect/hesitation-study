"""Resume the evaluation using OPENAI_API_KEY; serialize the cost ledger under a lock."""
import asyncio
import fcntl
import json
import os
import random
from datetime import datetime, timezone

import httpx
from design import ROOT, MODELS, answer, grade_id, grading
PRICES={MODELS["mini"]:(.40,.10,1.60),MODELS["full"]:(2,.50,8),MODELS["low"]:(2.50,.25,15)}
BUDGET=5
def read(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
def append(path,row):
    with path.open("a") as f:f.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
def unpack(raw):
    ch=raw["choices"][0]
    if ch["finish_reason"]!="stop" or ch["message"].get("refusal"):return {}
    try:return json.loads(ch["message"]["content"])
    except (ValueError,TypeError):return {}
def cost(model,u):
    price,cached,out=PRICES[model]
    c=(u.get("prompt_tokens_details") or {}).get("cached_tokens",0)
    return ((u["prompt_tokens"]-c)*price+c*cached+u["completion_tokens"]*out)/1e6
class Runner:
    def __init__(self,client):
        self.client=client
        self.raw=ROOT/"responses.jsonl"
        self.events=ROOT/"ledger.jsonl"
        self.done={r["job"]:r for r in read(self.raw)}
        self.balance=sum(e["delta"] for e in read(self.events))
    def record(self,key,kind,delta,**extra):
        append(self.events,dict(job=key,kind=kind,delta=delta,utc=datetime.now(timezone.utc).isoformat(),**extra))
        self.balance+=delta
    async def one(self,key,p):
        model=p["model"]; ip,_,op=PRICES[model]
        upper=((len(json.dumps(p,ensure_ascii=False).encode())+512)*ip+p["max_completion_tokens"]*op)/1e6
        for n in range(6):
            if self.balance+upper>BUDGET:raise RuntimeError("Budget reached")
            self.record(key,"reserve",upper)
            try:resp=await self.client.post("/v1/chat/completions",json=p)
            except httpx.TransportError as err:
                self.record(key,"ambiguous",0,reason=type(err).__name__)
                await asyncio.sleep(2**n);continue
            if resp.status_code!=200:
                code=resp.json().get("error",{}).get("code")
                self.record(key,"http_error",-upper if resp.status_code<500 else 0,status=resp.status_code,code=code)
                if (resp.status_code==429 and code!="insufficient_quota") or resp.status_code>=500:
                    await asyncio.sleep(min(25,2**(n+1)));continue
                raise RuntimeError((key,resp.status_code,code,resp.json().get("error",{}).get("param")))
            raw=resp.json()
            assert raw["model"]==model and len(raw["choices"])==1
            row={k:raw.get(k) for k in ["model","created","usage","choices","id","system_fingerprint"]}
            row["job"]=key
            append(self.raw,row)
            self.done[key]=row
            fee=cost(model,row["usage"])
            self.record(key,"settled",fee-upper,usd=fee)
            if len(self.done)%250==0:print("Completed",len(self.done),"requests",flush=True)
            return
        raise RuntimeError("Retry limit: "+key)
    async def phase(self,tasks):
        todo=iter([(k,p) for k,p in tasks if k not in self.done])
        async def worker():
            for k,p in todo:await self.one(k,p)
        await asyncio.gather(*(worker() for _ in range(32)))
async def main():
    items=read(ROOT/"items.jsonl");rng=random.Random(20261124)
    async with httpx.AsyncClient(base_url="https://api.openai.com",headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]},timeout=100) as client:
        runner=Runner(client)
        jobs=[]
        for item in items:
            for cfg in MODELS:
                arms=["openA","openB","openC"]
                if cfg=="mini":arms+=["openF","mcA","mcB"]
                for arm in arms:jobs.append(("/".join([item["id"],cfg,arm]),answer(cfg,arm,item)))
        rng.shuffle(jobs)
        await runner.phase(jobs)
        edits=[]
        for item in items:
            source=unpack(runner.done[item['id']+"/mini/openA"]).get("reply")
            if source:
                for arm in ["editB","editF"]:
                    edits.append((item['id']+"/mini/"+arm,answer("mini",arm,item,source)))
        rng.shuffle(edits);await runner.phase(edits)
        bank={i["id"]:i for i in items};judges={}
        for k,r in runner.done.items():
            if k.startswith("grade/"):continue
            item=bank[k.split("/")[0]];reply=unpack(r).get("reply")
            if reply:judges["grade/"+grade_id(item,reply)]=grading(item,reply)
        tasks=list(judges.items());rng.shuffle(tasks);await runner.phase(tasks)
        print("Finished",len(runner.done),"requests; ledger USD",round(runner.balance,4),flush=True)
if __name__=="__main__":
    with (ROOT/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        asyncio.run(main())
