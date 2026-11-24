import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from analyze import BASE,lines,unpack
def tab(path):return list(csv.DictReader(path.open()))
def run(lang):
    d=BASE/('open-'+lang)
    entries=lines(d/'ledger.jsonl');raw=lines(d/'responses.jsonl')
    rs=tab(d/'scored.csv')
    a={r['key']:r['status'] for r in tab(d/'audit-read.csv')}
    judges={r['job'][6:]:unpack(r) for r in raw if r['job'].startswith('grade/')}
    checks=Counter((a[k],judges[k].get('status','invalid')) for k in a)
    recode={r['key']:r['status'] for r in tab(d/'review-read.csv')}
    primary={}
    pause={}
    pattern=(r"え[えーぇっ〜~]*と|う[ー〜~]+ん|あの[、,…]|…|\.{2,}" if lang=='ja' else
             r"\b(?:um+|uh+|erm+|hmm+|er)\b|\bwell[, …]|…|\.{2,}")
    for arm in ['openA','openB','openF','editB','editF']:
        cases=[r for r in rs if r['model']=='mini' and r['arm']==arm]
        pause[arm]=sum(bool(re.search(pattern,r['reply'],re.I)) for r in cases)
        if arm not in ['openA','openB']:continue
        counter=Counter()
        for r in cases:
            key=hashlib.sha256((r['id']+'\0'+r['reply']).encode()).hexdigest()
            counter[recode.get(key,r['status'])]+=1
        primary[arm]=dict(counter)
    reasons={}
    for cfg in ['none','low']:
        sel=[r for r in raw if not r['job'].startswith('grade/') and r['job'].split('/')[1]==cfg]
        vals=[(r['usage'].get('completion_tokens_details') or {}).get('reasoning_tokens',0) for r in sel]
        reasons[cfg]=dict(n=len(sel),with_reasoning_tokens=sum(v>0 for v in vals),total=sum(vals))
    return dict(usage_USD=sum(e.get('usd',0) for e in entries),ledger_USD=sum(e['delta'] for e in entries),
                charges_by_event=dict(Counter(e['kind'] for e in entries)),grades=len(judges),
                responses=len(raw)-len(judges),judgment_audit={f'{a}->{b}':n for (a,b),n in checks.items()},
                items_checked=len(a),supplemental_reviews=len(recode),rescored=primary,lexical_pauses=pause,reasoning_usage=reasons)
if __name__=='__main__':
    result={l:run(l) for l in ['ja','en']}
    result['translation_USD']=sum(r.get('usd',0) for r in lines(BASE/'open-en/translation/ledger.jsonl'))
    (BASE/'open-ja/diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
