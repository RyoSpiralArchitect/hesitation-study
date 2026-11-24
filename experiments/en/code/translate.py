"""Translate each prompt without exposing the key; resume through the study ledger."""
import asyncio
import fcntl
import json
import os
import httpx
import run
from design import MODEL, ROOT, read_lines

SOURCE = ROOT.parent / "ja/data/manifest.jsonl"
INSTRUCTION = ("Translate this Japanese multiple-choice question and its four options into faithful, natural English. Preserve each option's position, numbers, quotation scope, mathematical notation, ambiguity, names and dates. Do not solve, correct, explain, add clues or indicate an answer. Transliterate Japanese names or terms when appropriate. Return the translated question and exactly four choices in their original order.")

async def main():
    run.OUT = ROOT / "translation"
    run.RAW, run.EVENTS = run.OUT/"responses.jsonl", run.OUT/"requests.jsonl"
    run.COST_LIMIT_USD = 1
    items = read_lines(SOURCE)
    schema = {"type":"object","properties":{"question":{"type":"string"},"choices":{"type":"array","items":{"type":"string"}}},"required":["question","choices"],"additionalProperties":False}
    jobs=[]
    for item in items:
        content=json.dumps({k:item[k] for k in ["question","choices"]},ensure_ascii=False)
        jobs.append((item["item"],dict(model=MODEL, messages=[{"role":"system","content":INSTRUCTION},{"role":"user","content":content}],temperature=0,n=1,max_completion_tokens=1100,store=False,service_tier="default",response_format={"type":"json_schema","json_schema":{"name":"translation","strict":True,"schema":schema}})))
    async with httpx.AsyncClient(base_url="https://api.openai.com",headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]},timeout=80) as client:
        runner=run.Run(client)
        await runner.phase(jobs,28)
        translated=[]
        for item in items:
            choice=runner.done[item["item"]]["choices"][0]
            assert choice["finish_reason"]=="stop"
            obj=json.loads(choice["message"]["content"])
            assert len(obj["choices"])==4 and all(s.strip() for s in [obj["question"],*obj["choices"]])
            translated.append({**item,**obj})
    target=ROOT/"data/manifest.jsonl"
    data="".join(json.dumps(i,ensure_ascii=False)+"\n" for i in translated)
    if target.exists() and target.read_text()!=data:
        raise RuntimeError("Translation differs from saved manifest")
    target.write_text(data)
    print("Finished translations",len(translated))
if __name__=="__main__":
    with (ROOT/"translation/.run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        asyncio.run(main())
