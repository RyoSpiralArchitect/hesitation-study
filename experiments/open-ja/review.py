"""Supplemental masked review of every non-correct primary A/B response."""
import csv
import hashlib
import json
import random
from pathlib import Path
from analyze import BASE,csvout,lines
def key(r):
    return hashlib.sha256((r['id']+'\0'+r['reply']).encode()).hexdigest()
def packet(lang):
    d=BASE/('open-'+lang)
    records=list(csv.DictReader((d/'scored.csv').open()))
    items={x['id']:x for x in lines(d/'items.jsonl')}
    review={}
    for r in records:
        if r['model']=='mini' and r['arm'] in ['openA','openB'] and r['status']!='correct':
            i=items[r['id']]
            review[key(r)]={'key':key(r),'q':i['q'],'gold':i['gold'],'reply':r['reply']}
    rows=list(review.values());random.Random(23497).shuffle(rows)
    csvout(d/'review-blind.csv',rows)
if __name__=='__main__':
    import sys
    packet(sys.argv[1])
