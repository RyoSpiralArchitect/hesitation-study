"""Run or resume the frozen study. Requires httpx and OPENAI_API_KEY."""
import argparse
import asyncio
import fcntl
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from design import ARMS, COST_LIMIT_USD, MODEL, PRICE, ROOT, SEED, body, parse_choice, read_lines

OUT = ROOT / "results"
RAW, EVENTS = OUT / "responses.jsonl", OUT / "requests.jsonl"
def utc():
    return datetime.now(timezone.utc).isoformat()

def append(path, entry):
    with path.open("a",encoding="utf-8") as file:
        file.write(json.dumps(entry,ensure_ascii=False,separators=(",",":"))+"\n")

def usd(usage):
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens",0)
    tokens = usage["prompt_tokens"]
    return ((tokens-cached)*PRICE["input"] + cached*PRICE["cached"] +
            usage["completion_tokens"]*PRICE["output"])/1_000_000

def reserve_bound(payload):
    # Every UTF-8 byte of the whole serialized request counted as a token, plus framing allowance.
    # n is applied to the full input too, deliberately over-reserving on multi-sample calls.
    possible_input = len(json.dumps(payload,ensure_ascii=False).encode("utf-8")) + 512
    n = payload["n"]
    return n*(possible_input*PRICE["input"] + payload["max_completion_tokens"]*PRICE["output"])/1e6

class Run:
    def __init__(self,client):
        self.client=client
        self.done={r["job"]:r for r in read_lines(RAW)} if RAW.exists() else {}
        self.booked=sum(r["usd_delta"] for r in read_lines(EVENTS)) if EVENTS.exists() else 0.
        self.completed=0
        self.stopping=False
        self.last_print=time.monotonic()
        self.delay_until=0.

    def event(self, kind, job, amount, **extra):
        append(EVENTS,dict(time=utc(),event=kind,job=job,usd_delta=amount,**extra))
        self.booked+=amount

    async def perform(self,job,payload):
        bound=reserve_bound(payload)
        for attempt in range(1,11):
            if self.stopping:
                return
            if self.delay_until>time.monotonic():
                await asyncio.sleep(self.delay_until-time.monotonic())
            if self.stopping:
                return
            if self.booked+bound>COST_LIMIT_USD:
                raise RuntimeError("Local billing ceiling reached")
            self.event("reserve",job,bound,attempt=attempt)
            try:
                res=await self.client.post("/v1/chat/completions",json=payload)
            except httpx.TransportError as exc:
                # Delivery/billing is ambiguous. Keep reservation in force.
                self.event("transport_error",job,0,kind_name=type(exc).__name__)
                await asyncio.sleep(min(2**attempt,18))
                continue
            if res.status_code != 200:
                try:
                    error=res.json()["error"]
                except (ValueError,KeyError,TypeError):
                    error={}
                code=error.get("code"); param=error.get("param")
                self.event("http_error",job,-bound if res.status_code<500 else 0,
                           status=res.status_code,code=code,param=param)
                if res.status_code==429 and code not in ("insufficient_quota","billing_hard_limit_reached"):
                    try:
                        wait=float(res.headers.get("retry-after",min(2**attempt,20)))
                    except ValueError:
                        wait=min(2**attempt,20)
                    self.delay_until=max(self.delay_until,time.monotonic()+min(60,max(1,wait)))
                    await asyncio.sleep(0.3)
                    continue
                if res.status_code>=500:
                    await asyncio.sleep(min(2**attempt,20))
                    continue
                raise RuntimeError(f"Provider rejected {job}: HTTP {res.status_code} code={code} param={param}")
            response=res.json()
            if response.get("model")!=MODEL or len(response.get("choices",[]))!=payload["n"]:
                raise RuntimeError(f"Unexpected model or sample count in {job}")
            charge=usd(response["usage"])
            entry={k:response.get(k) for k in ["id","created","model","system_fingerprint",
                                                "service_tier","choices","usage"]}
            entry.update(job=job,received_utc=utc(),request_id=res.headers.get("x-request-id"))
            append(RAW,entry)
            self.done[job]=entry
            self.event("settle",job,charge-bound,charge=charge)
            self.completed+=1
            if self.completed==1 or time.monotonic()-self.last_print>24:
                print(utc(), "finished requests",len(self.done),"reserved+settled USD",round(self.booked,3),flush=True)
                self.last_print=time.monotonic()
            return
        raise RuntimeError(f"Retry limit reached for {job}")

    async def phase(self,jobs,concurrency):
        todo=[(job,payload) for job,payload in jobs if job not in self.done]
        if not todo:
            return
        # A single actual scheduled job validates each request shape before parallel work starts.
        await self.perform(*todo[0])
        iterator=iter(todo[1:])
        async def worker():
            for job,payload in iterator:
                if self.stopping:
                    return
                try:
                    await self.perform(job,payload)
                except Exception:
                    self.stopping=True
                    raise
        results=await asyncio.gather(*(worker() for _ in range(concurrency)),return_exceptions=True)
        for result in results:
            if isinstance(result,Exception):
                raise result

async def main(concurrency):
    freeze=json.loads((ROOT/"data/freeze.json").read_text())
    for file in ["code/design.py","code/translate.py","protocol.md","data/manifest.jsonl"]:
        if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=freeze[file]:
            raise RuntimeError(f"Frozen file changed: {file}")
    items=read_lines(ROOT/"data/manifest.jsonl")
    rng=random.Random(SEED+8)
    primary=[(f"{item['item']}:{arm}",body(arm,item)) for item in items for arm in ARMS]
    rng.shuffle(primary)
    headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]}
    limits=httpx.Limits(max_connections=concurrency,max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(base_url="https://api.openai.com",headers=headers,
                                 limits=limits,timeout=httpx.Timeout(80,connect=15)) as client:
        run=Run(client)
        print(f"Scheduled {len(primary)} initial requests. Resuming from {len(run.done)} persisted.",flush=True)
        await run.phase(primary,concurrency)
        edits=[]
        for item in items:
            prefix=item["item"]
            for sample in run.done[prefix+":A"]["choices"]:
                source,_=parse_choice(sample)
                if source:
                    edits.append((f"{prefix}:E:{sample['index']}",body("E",None,source)))
        rng.shuffle(edits)
        print("Scheduled",len(edits),"source-linked rewrite requests.",flush=True)
        await run.phase(edits,concurrency)
        print("Completed",len(run.done),"requests; estimated charge",sum(usd(x["usage"]) for x in run.done.values()),flush=True)

if __name__=="__main__":
    args=argparse.ArgumentParser()
    args.add_argument("--concurrency",type=int,default=36)
    options=args.parse_args()
    OUT.mkdir(exist_ok=True)
    with (OUT/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        asyncio.run(main(options.concurrency))
