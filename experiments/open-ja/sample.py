"""Build the frozen JAQKET dev2 subset from the official JSONL."""
import hashlib
import json
import random
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE_SHA="ec4938b0bb19455b69c8770a57f4f5b2baf32311295b3d1557a8bca4152189d9"
def main(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==SOURCE_SHA
    rng=random.Random(20261124)
    items=[]
    seen=set()
    for row in map(json.loads,path.read_text().splitlines()):
        q=row["question"]
        gold=row["answer_entity"]
        options=sorted(set(row["answer_candidates"])-{gold})
        if q in seen or len(options)<3 or gold not in row["answer_candidates"] or any(w in q for w in ["現在","現時点","今年","昨年","最新"]):
            continue
        seen.add(q)
        items.append((row["qid"],q,gold,options))
    sample=[]
    for i,q,g,opts in sorted(rng.sample(items,128)):
        choices=rng.sample(opts,3)+[g]
        rng.shuffle(choices)
        sample.append(dict(id=i,q=q,gold=g,choices=choices))
    (ROOT/"items.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in sample))
if __name__=="__main__":main(Path(sys.argv[1]))
