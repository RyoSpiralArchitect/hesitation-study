import csv
import hashlib
import json
import random
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from design import ROOT, SUBJECTS, SEED, N_PER_SUBJECT

# Source directory is the CC BY-SA JMMLU/ subdirectory of the pinned upstream checkout.
source = Path(sys.argv[1])
if (ROOT / 'data/manifest.jsonl').exists():
    raise SystemExit("The manifest already exists.")
rng = random.Random(SEED)
seen = set()
selected = []
audit = {}
for subject in SUBJECTS:
    eligible = []
    path = source / f"{subject}.csv"
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row_index, row in enumerate(csv.reader(file), 1):
            if len(row) != 6 or not all(cell.strip() for cell in row) or row[-1].strip() not in list("ABCD"):
                continue
            q, a, b, c, d, gold = (cell.strip() for cell in row)
            choices = [a,b,c,d]
            norm = lambda s: re.sub(r"\s+", "", unicodedata.normalize("NFKC",s))
            if len({norm(c) for c in choices}) != 4:
                continue
            if re.search(r"(下図|図[をに]示|下の図|次の図|以下の図|図中|上の図|次の表|以下の表|下表|図[1１2２])",q):
                continue
            sig=tuple(norm(s) for s in [q, *choices])
            if sig in seen:
                continue
            seen.add(sig)
            eligible.append(dict(item=f"{subject}/{row_index:03d}", subject=subject, row=row_index,
                                 question=q, choices=choices, gold=gold))
    selected.extend(sorted(rng.sample(eligible,N_PER_SUBJECT),key=lambda r:r["row"]))
    audit[subject] = {"eligible":len(eligible),"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
path = ROOT / "data/manifest.jsonl"
path.write_text("".join(json.dumps(i,ensure_ascii=False)+"\n" for i in selected))
lock = {"created_utc":datetime.now(timezone.utc).isoformat(),"subjects":audit}
for rel in ["data/manifest.jsonl", "code/design.py", "code/prepare.py","protocol.md"]:
    lock[rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
(ROOT/"data/freeze.json").write_text(json.dumps(lock,indent=2)+"\n")
print("Manifest frozen",len(selected),"items",lock["data/manifest.jsonl"])
