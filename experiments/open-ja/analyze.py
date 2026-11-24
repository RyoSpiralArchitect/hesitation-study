"""Reproduce the two matched experiments, including paired percentile intervals."""
import csv
import hashlib
import json
import random
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parents[1]
def lines(path):return [json.loads(l) for l in path.read_text().splitlines()]
def csvout(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def unpack(r):
    if r and r['choices'][0]['finish_reason']=='stop' and not r['choices'][0]['message'].get('refusal'):
        return json.loads(r['choices'][0]['message']['content'])
    return {}
def load(lang):
    d=BASE/('open-'+lang)
    items=lines(d/'items.jsonl');raw=lines(d/'responses.jsonl');jobs={r['job']:r for r in raw}
    assert len(jobs)==len(raw) and len(items)==128
    rows=[];unique={}
    for i in items:
        for cf in ['mini','full','none','low']:
            arms=['openA','openB','openC']
            if cf=='mini':arms+=['openF','mcA','mcB','editB','editF']
            for arm in arms:
                key='/'.join([i['id'],cf,arm])
                if key not in jobs:
                    assert arm.startswith('edit') and not unpack(jobs[i['id']+'/mini/openA'])
                reply=unpack(jobs.get(key)).get('reply','')
                h=hashlib.sha256((i['id']+'\0'+reply).encode()).hexdigest()
                if reply:assert 'grade/'+h in jobs
                g=unpack(jobs.get('grade/'+h)) if reply else {}
                rec=dict(id=i['id'],model=cf,arm=arm,reply=reply,status=g.get('status','invalid'),
                         candidate=g.get('candidate',''),hedge=int(g.get('hedge',False)),
                         pause=int(g.get('pause',False)),extra=int(g.get('extra',False)))
                rows.append(rec)
                if g:unique[h]=dict(question=i["q"],reference=i["gold"],reply=reply)
    csvout(d/'scored.csv',rows)
    ids=random.Random(20261126).sample(sorted(unique),64)
    csvout(d/'audit-blind.csv',[dict(key=k,**unique[k]) for k in ids])
    return rows
def aggregate(rs):
    c=Counter(r['status'] for r in rs)
    ok=c['correct'];err=c['wrong']
    wh=sum(r['hedge'] for r in rs if r['status']=='wrong')
    ch=sum(r['hedge'] for r in rs if r['status']=='correct')
    return dict(n=len(rs),**{k:c[k] for k in ['correct','wrong','vague','abstain','unresolved','invalid']},
                wrong_hedged=wh,correct_hedged=ch,hedge=sum(r['hedge'] for r in rs),
                pause=sum(r['pause'] for r in rs),extra=sum(r['extra'] for r in rs),
                error_given_specific=err/(ok+err) if ok+err else None)
def interval(vals):
    valid=vals[1:][np.isfinite(vals[1:])]
    lo,hi=np.quantile(valid,[.025,.975]) if len(valid) else (float('nan'),float('nan'))
    return [float(v) if np.isfinite(v) else None for v in (vals[0],lo,hi)]+[len(valid)]
def main(langs,exclude=frozenset(),filename=None):
    n=128-len(exclude)
    rng=np.random.default_rng(20261125)
    w=np.vstack([np.ones(n,dtype=int),rng.multinomial(n,[1/n]*n,size=10000)]).astype(np.int32)
    compiled={};anchor=None;result={}
    for lang in langs:
        rows=load(lang); groups=defaultdict(list)
        for r in rows:
            if r["id"] not in exclude:groups[r['model'],r['arm']].append(r)
        metrics={}; counts={}
        for (cfg,a),rs in groups.items():
            ids=[r['id'] for r in rs]
            if anchor is None:anchor=ids
            assert ids==anchor and len(ids)==n
            counts[cfg+'/'+a]=aggregate(rs)
            m=np.array([[r['status']=='wrong',r['status']=='correct',r['hedge'],r['pause'],r['hedge']*(r['status']=='wrong'),r['hedge']*(r['status']=='correct')] for r in rs],dtype=np.int32)
            err,ok,hedge,pause,wh,ch=(w@m).T
            with np.errstate(invalid='ignore',divide='ignore'):
                metrics[cfg,a]={'error':err/n,'correct':ok/n,'hedge':hedge/n,'pause':pause/n,'select':wh/err-ch/ok}
        effects={}
        for cfg in ['mini','full','none','low']:
            key=lambda arm,metric:metrics[cfg,arm][metric]
            for m in ['error','correct','hedge']:
                effects[cfg+'/open_B-A/'+m]=key('openB',m)-key('openA',m)
            for a in 'AC':
                effects[cfg+'/'+a+'/selectivity']=key('open'+a,'select')
            effects[cfg+'/C-A/selectivity']=key('openC','select')-key('openA','select')
        effects['reasoning_C_selectivity_interaction']=effects['low/C-A/selectivity']-effects['none/C-A/selectivity']
        effects['size_C_selectivity_interaction']=effects['full/C-A/selectivity']-effects['mini/C-A/selectivity']
        for m in ['error','correct']:
            effects['mini/mc_B-A/'+m]=metrics['mini','mcB'][m]-metrics['mini','mcA'][m]
            effects['format_interaction/'+m]=effects['mini/open_B-A/'+m]-effects['mini/mc_B-A/'+m]
        for m in ['pause','hedge']:
            b,f,eb,ef=[metrics['mini',arm][m] for arm in ['openB','openF','editB','editF']]
            for name,vals in [('initial_mandatory_minus_optional',f-b),('edit_mandatory_minus_optional',ef-eb),('optional_edit_minus_initial',eb-b),('mandatory_edit_minus_initial',ef-f),('interaction',(ef-eb)-(f-b))]:
                effects[name+'/'+m]=vals
        transitions={}
        for arm in ['openB','editB','editF']:
            t=Counter();pres=Counter()
            for x,y in zip(groups['mini','openA'],groups['mini',arm]):
                t[x['status']+'->'+y['status']]+=1
                if x['status']==y['status']=='wrong':
                    pres['same' if x['candidate']==y['candidate'] else 'different']+=1
            transitions[arm]=dict(status=dict(t),wrong_names=dict(pres))
        result[lang]=dict(counts=counts,effects={k:interval(v) for k,v in effects.items()},transitions=transitions)
        compiled[lang]=effects
    if len(langs)==2:
        result['en_minus_ja']={k:interval(compiled['en'][k]-v) for k,v in compiled['ja'].items()}
    dest=(BASE/'open-ja'/'analysis.json') if len(langs)==2 else BASE/'open-ja'/'ja-only.json'
    if filename:dest=BASE/"open-ja"/filename
    dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':
    import sys
    langs=sys.argv[1:] or ['ja','en']
    main(langs)
    if len(langs)==2:
        overlap={'QA20CAPR-0295','QA20CAPR-0347','QA20QBIK-0559','QA20QBIK-0599','QA20QBIK-0989'}
        main(langs,overlap,'sensitivity-123.json')
        main(langs,overlap | {'QA20CAPR-0683','QA20CAPR-0897','QA20QBIK-0839'},'sensitivity-120.json')
