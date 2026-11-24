import hashlib
import json
import unicodedata
from datetime import datetime,timezone
from design import ROOT,read_lines

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if __name__=="__main__":
    src=ROOT.parent/"ja/data/manifest.jsonl"
    ja=read_lines(src)
    en=read_lines(ROOT/"data/manifest.jsonl")
    assert len(en)==len(ja)==640
    issues=[]
    for x,y in zip(ja,en):
        assert all(x[k]==y[k] for k in ("item","row","subject","gold"))
        assert len(y["choices"])==4
        normalize=lambda s:" ".join(unicodedata.normalize("NFKC",s).casefold().split())
        if len(set(map(normalize,y["choices"])))!=4:
            issues.append(y["item"])
    files=["code/translate.py","code/design.py","protocol.md","data/manifest.jsonl"]
    lock={f:sha(ROOT/f) for f in files}
    lock.update(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(src), duplicate_translated_options=issues)
    dest=ROOT/"data/freeze.json"
    if dest.exists(): raise SystemExit("Freeze already exists")
    dest.write_text(json.dumps(lock,indent=2)+"\n")
    print("Matched 640 items. Duplicate option sets:",issues)
