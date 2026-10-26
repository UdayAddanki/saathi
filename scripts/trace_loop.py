"""Run the redacted demo full-loop evidence trace.

This intentionally performs the real model calls. Run it from the repository
root with a valid PORTKEY_API_KEY in .env or its parent directory.
"""
from __future__ import annotations
import argparse, json, os, shutil, sqlite3, subprocess, tempfile, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]

def wait_for(url):
    for _ in range(120):
        try:
            if requests.get(url + '/api/health', timeout=2).ok: return
        except requests.RequestException: pass
        time.sleep(.5)
    raise RuntimeError('App did not start')

def call(session, method, base, path, **kwargs):
    started=time.perf_counter(); response=session.request(method, base+path, timeout=300, **kwargs); elapsed=round(time.perf_counter()-started,3)
    if not response.ok: raise RuntimeError(f'{method} {path} -> {response.status_code}: {response.text[:500]}')
    try: body=response.json()
    except ValueError: body={}
    return body, elapsed

def db_details(db_path, since):
    db=sqlite3.connect(db_path); db.row_factory=sqlite3.Row
    calls=[dict(x) for x in db.execute('select agent_name,input_tokens,cached_input_tokens,output_tokens,cost_usd,provider_cost_usd,duration_ms from llm_calls where created_at>=?',(since,))]
    run_ids=[x['id'] for x in db.execute('select id from runs where created_at>=?',(since,))]
    tools=[]
    for x in db.execute('select agent_name,tool_name,arguments_json,duration_ms from tool_calls where created_at>=?',(since,)):
        tools.append({'agent':x[0],'tool':x[1],'arguments':x[2],'duration_ms':x[3]})
    db.close(); return calls,tools,run_ids

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,default=8765); args=ap.parse_args()
    tmp=Path(tempfile.mkdtemp(prefix='saathi-trace-')); db_path=tmp/'trace.db'; base=f'http://127.0.0.1:{args.port}'
    env=os.environ.copy(); env.update({'PORT':str(args.port),'DEMO_MODE':'true','SAATHI_DB_PATH':str(db_path)})
    proc=subprocess.Popen(['python3','run.py'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    records=[]
    try:
        wait_for(base)
        s=requests.Session(); started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        body,elapsed=call(s,'POST',base,'/api/auth/login',json={'username':'demo','password':'saathi-demo'}); records.append({'step':'login','duration_s':elapsed,'detail':'demo session established'})
        body,elapsed=call(s,'POST',base,'/api/classes',json={'grade':3,'section':'A','board':'TS_SCERT','class_size':38,'period_minutes':40,'resources':[]}); class_id=body['id']; records.append({'step':'create class','duration_s':elapsed,'detail':'Grade 3 Telangana class'})
        roll=ROOT/'tests/fixtures/class_roll/class_roll_3A_valid.xlsx'
        with roll.open('rb') as f: body,elapsed=call(s,'POST',base,f'/api/classes/{class_id}/roll/upload',files={'file':(roll.name,f,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
        rows=body['rows']; call(s,'POST',base,f'/api/classes/{class_id}/roll/save',json=rows); records.append({'step':'class roll','duration_s':elapsed,'detail':f'{len(rows)} rows saved'})
        since=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); payload={'class_id':class_id,'subject':'Mathematics','chapter':'Place value','topic':'place value','chapter_or_topic':'place value','lesson_type':'5-step','teacher_note':'Grade 3 Telangana classroom; use clear local examples.','differentiated':True,'differentiation_types':['process']}
        body,elapsed=call(s,'POST',base,'/api/plans',json=payload); plan_id=body.get('id') or body.get('plan_id'); check_id=body.get('check_id'); records.append({'step':'plan','duration_s':elapsed,'detail':'Grade 3 place value 5-step lesson','plan_id':plan_id,'check_id':check_id})
        if not check_id:
            lesson,_=call(s,'GET',base,f'/api/lessons/recent?class_id={class_id}'); check_id=lesson[0]['check_id']
        paper,elapsed=call(s,'POST',base,f'/api/papers/from-check/{check_id}'); paper_id=paper['id']; records.append({'step':'print answer sheet','duration_s':elapsed,'detail':'answer key created for printable sheet','paper_id':paper_id})
        files=[]
        for path in sorted((ROOT/'tests/fixtures/submissions/grade3').glob('*')): files.append(('files',(path.name,path.open('rb'),'image/png')))
        body,elapsed=call(s,'POST',base,f'/api/checks/{check_id}/submissions',files=files); records.append({'step':'upload five sheets','duration_s':elapsed,'detail':f"{len(body.get('files',[]))} fixture sheets uploaded"})
        body,elapsed=call(s,'POST',base,f'/api/papers/{paper_id}/read-submissions'); records.append({'step':'read sheets','duration_s':elapsed,'detail':body.get('message','batch complete')})
        grid,_=call(s,'GET',base,f'/api/papers/{paper_id}/review-grid'); confirm_payload=grid.get('cells',[]); body,elapsed=call(s,'POST',base,f'/api/papers/{paper_id}/results/confirm',json=confirm_payload); records.append({'step':'confirm','duration_s':elapsed,'detail':f"{body.get('count',0)} results confirmed"})
        body,elapsed=call(s,'GET',base,f'/api/checks/{check_id}/insight'); records.append({'step':'analysis','duration_s':elapsed,'detail':'code diagnosis loaded'})
        body,elapsed=call(s,'POST',base,f'/api/checks/{check_id}/next-steps'); records.append({'step':'next steps','duration_s':elapsed,'detail':'Coach output generated'})
        body,elapsed=call(s,'POST',base,f'/api/checks/{check_id}/resources/worksheets'); records.append({'step':'worksheet','duration_s':elapsed,'detail':'worksheet generated'})
        body,elapsed=call(s,'POST',base,f'/api/checks/{check_id}/use-warmup'); records.append({'step':'use in next lesson','duration_s':elapsed,'detail':'warm-up saved'})
        calls,tools,runs=db_details(db_path,since); out={'source':'demo fixture trace; no real classroom data','records':records,'llm_calls':calls,'tool_calls':tools,'run_ids':runs,'diagnosis_experiment':{'status':'not run','reason':'Run separately only if the course model is available; no comparison is fabricated.'}}
        ev=ROOT/'evidence'; ev.mkdir(exist_ok=True)
        # Screens with real data come from scripts/capture_real_screens.py, which
        # drives the same loop in a logged-in browser. This script records the
        # run itself (steps, model calls, tools, tokens, cost, timing).
        (ev/'run_trace.json').write_text(json.dumps(out,indent=2)+'\n')
        md=['# Full-loop trace','', 'Source: demo account and committed fixtures; no real classroom data.', '']
        for r in records: md.append(f"- **{r['step']}** — {r['detail']} ({r['duration_s']}s)")
        md += ['', '## Model calls', '','| Agent | Input | Cached | Output | Cost | Duration |','|---|---:|---:|---:|---:|---:|']
        for c in calls: md.append(f"| {c['agent_name']} | {c['input_tokens']} | {c['cached_input_tokens']} | {c['output_tokens']} | ${c['cost_usd']:.6f} | {c['duration_ms']} ms |")
        md += ['', '## Tools', '']+[f"- {t['agent']}: `{t['tool']}` ({t['duration_ms']} ms)" for t in tools]
        (ev/'run_trace.md').write_text('\n'.join(md)+'\n'); print('Trace complete; evidence/run_trace.json and evidence/run_trace.md written.')
    finally:
        proc.terminate(); proc.wait(timeout=10); shutil.rmtree(tmp,ignore_errors=True)

if __name__=='__main__': main()
