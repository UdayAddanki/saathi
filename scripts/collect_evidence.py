"""Build evidence artifacts from the local SQLite usage and feedback records.

This script does not call the model and does not modify application data.
"""
from __future__ import annotations
import csv, json, sqlite3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.config import DB_PATH, PRICE_INPUT_PER_M, PRICE_CACHED_INPUT_PER_M, PRICE_OUTPUT_PER_M
EVIDENCE=ROOT/'evidence'

def query(db, sql, args=()):
    db.row_factory=sqlite3.Row; return [dict(row) for row in db.execute(sql,args)]

def tokenomics(db):
    calls=query(db,'select * from llm_calls')
    groups={}
    for row in calls:
        kind=(query(db,'select kind from runs where id=?',(row['run_id'],)) or [{'kind':'unknown'}])[0]['kind']; item=groups.setdefault(kind,{'runs':set(),'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'cost_usd':0,'provider_cost_usd':0})
        item['runs'].add(row['run_id'])
        for key in ('input_tokens','cached_input_tokens','output_tokens','cost_usd','provider_cost_usd'): item[key]+=row[key] or 0
    output={}
    for kind,item in groups.items():
        count=max(1,len(item['runs'])); output[kind]={key:(round(value/count,8) if key not in ('runs',) else count) for key,value in item.items() if key != 'runs'}; output[kind]['runs']=count
    EVIDENCE.joinpath('tokenomics.json').write_text(json.dumps({'source':'saathi.db llm_calls and runs','run_types':output,'prices':{'input_per_m':PRICE_INPUT_PER_M,'cached_input_per_m':PRICE_CACHED_INPUT_PER_M,'output_per_m':PRICE_OUTPUT_PER_M}},indent=2))
    lines=['# Tokenomics','',f'Source: `llm_calls` and `runs` in `{DB_PATH}`. No records are fabricated.','']
    for kind,data in output.items(): lines.append(f'## {kind}\n\n{json.dumps(data,indent=2)}')
    lines.append('\n## Scale assumptions\n\nPer-teacher monthly projections are not produced until a verified full-loop dataset exists; placeholders are intentional.')
    EVIDENCE.joinpath('tokenomics.md').write_text('\n'.join(lines)+'\n')

def pilot(db):
    rows=query(db,'select * from feedback order by created_at')
    with EVIDENCE.joinpath('pilot_feedback.csv').open('w',newline='') as handle:
        if rows:
            writer=csv.DictWriter(handle,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        else: handle.write('PLACEHOLDER: no teacher feedback recorded yet\n')
    if rows:
        avg=sum(row['rating'] for row in rows)/len(rows); text=f'{len(rows)} feedback responses; average rating {avg:.2f}. Quotes are included only in pilot_feedback.csv.'
    else: text='PLACEHOLDER: no teacher feedback recorded yet. Do not infer teacher satisfaction or time saved.'
    EVIDENCE.joinpath('pilot_summary.md').write_text('# Pilot summary\n\n'+text+'\n')

def main():
    EVIDENCE.mkdir(exist_ok=True); db=sqlite3.connect(DB_PATH); tokenomics(db); pilot(db); db.close()
if __name__=='__main__': main()
