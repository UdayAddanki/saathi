from __future__ import annotations

import json
import datetime
import logging
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from .config import ACCESS_CODE, DAILY_BUDGET_USD, DEMO_MODE, KEY_FOUND
from .db import init_db, rows, one, conn
from .models import PlanRequest, ClassRequest
from .pipeline import generate_plan, generate_next_steps
from .config import ROOT
from .diagnosis import analyze_results
from .models import ResultsRequest

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Saathi", lifespan=lifespan)
logger = logging.getLogger(__name__)
REQUESTS: dict[str, list[float]] = {}
INJECTION_PATTERNS = re.compile(r"ignore\s+(all\s+)?previous\s+instructions|system\s+prompt|you\s+are\s+now|reveal\s+your\s+instructions|disregard\s+the", re.I)

@app.get('/api/health')
def health():
    return {'ok': True, 'key_found': KEY_FOUND, 'access_required': bool(ACCESS_CODE), 'demo_mode': DEMO_MODE, 'message': None if KEY_FOUND else 'PORTKEY_API_KEY not found'}

def authorize(request):
    if not ACCESS_CODE:
        return None
    if request.headers.get('X-Saathi-Access-Code') != ACCESS_CODE:
        raise HTTPException(401, 'Enter the Saathi access code to continue.')
    return None

def enforce_rate_limit(request):
    key = request.headers.get('X-Saathi-Access-Code') or (request.client.host if request.client else 'unknown')
    now = time.time()
    REQUESTS[key] = [stamp for stamp in REQUESTS.get(key, []) if now - stamp < 3600]
    if len(REQUESTS[key]) >= 10:
        raise HTTPException(429, 'This access code has reached the limit of 10 lesson runs per hour.')
    REQUESTS[key].append(now)

def guard_request(request):
    authorize(request)

def budget_remaining() -> bool:
    today = datetime.date.today().isoformat()
    total = sum(item['cost_usd'] for item in rows("select cost_usd from llm_calls where created_at like ?", (today + '%',)))
    return total < DAILY_BUDGET_USD

def check_injection(run_id: str, topic: str, note: str | None) -> None:
    if INJECTION_PATTERNS.search(f'{topic}\n{note or ""}'):
        logger.warning('Blocked prompt injection attempt for run %s', run_id)
        raise HTTPException(400, 'That topic or note contains text that Saathi cannot treat as classroom context.')
@app.get('/api/boards')
def boards(request: Request): authorize(request); return json.loads((ROOT / "data/boards.json").read_text())
@app.get('/api/classes')
def classes(request: Request): authorize(request); return rows('select * from classes')
@app.get('/api/classes/{class_id}')
def get_class(class_id: str, request: Request):
 authorize(request)
 x=one('select * from classes where id=?',(class_id,))
 if not x: raise HTTPException(404,'Class not found')
 return x
@app.post('/api/classes')
def create_class(req: ClassRequest, request: Request):
 authorize(request)
 import uuid,json
 cid=str(uuid.uuid4()); c=conn(); c.execute('insert into classes values(?,?,?,?,?,?,?,?)',(cid,f'{req.grade}{req.section}',req.board,req.grade,req.section,req.class_size,req.period_minutes,json.dumps(req.resources))); c.executemany('insert into students values(?,?,?)',[(cid,i,None) for i in range(1,req.class_size+1)]); c.commit(); c.close(); return {'id':cid}
@app.post('/api/plans')
def plan(req: PlanRequest, request: Request):
 authorize(request)
 if not KEY_FOUND: raise HTTPException(503,'PORTKEY_API_KEY not found')
 if not budget_remaining(): raise HTTPException(429, 'Today’s lesson budget has been reached. Please try again tomorrow.')
 run_id = 'preflight-' + str(time.time_ns())
 check_injection(run_id, req.chapter_or_topic, req.teacher_note)
 enforce_rate_limit(request)
 return generate_plan(req.class_id,req.subject,req.chapter_or_topic,req.teacher_note)
@app.get('/api/plans/{plan_id}')
def saved(plan_id: str, request: Request):
 authorize(request)
 x=one('select * from lesson_plans where id=?',(plan_id,))
 if not x: raise HTTPException(404,'Plan not found')
 return x

@app.get('/api/lessons/recent')
def recent_lessons(request: Request):
    authorize(request)
    return rows('''select lp.id, lp.chapter_or_topic, lp.created_at, c.name as class_name, c.grade, ch.id as check_id, ch.check_type
                   from lesson_plans lp join classes c on c.id=lp.class_id join checks ch on ch.lesson_plan_id=lp.id
                   order by lp.created_at desc limit 20''')

@app.get('/api/checks/{check_id}')
def get_check(check_id: str, request: Request):
    authorize(request)
    check = one('select ch.*, lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    if not check:
        raise HTTPException(404, 'Check not found')
    check['items'] = json.loads(check.pop('items_json'))
    check['students'] = rows('select roll_no, first_name from students where class_id=? order by roll_no', (check['class_id'],))
    return check

@app.post('/api/checks/{check_id}/responses')
def save_results(check_id: str, payload: ResultsRequest, request: Request):
    authorize(request)
    check = one('select ch.*, lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    if not check:
        raise HTTPException(404, 'Check not found')
    students = {item['roll_no'] for item in rows('select roll_no from students where class_id=?', (check['class_id'],))}
    items = json.loads(check['items_json'])
    if payload.check_mode == 'class_count':
        if not payload.class_counts:
            raise HTTPException(422, 'Class counts are required.')
        class_size = len(students)
        for values in payload.class_counts.values():
            if sum(int(value) for value in values.values()) > class_size:
                raise HTTPException(422, 'A class count cannot exceed the class size.')
    else:
        for response in payload.responses:
            if int(response.get('roll_no', -1)) not in students:
                raise HTTPException(422, 'That roll number is not in this class.')
            index = int(response.get('item_index', -1))
            if index < 0 or index >= len(items):
                raise HTTPException(422, 'That question or task does not exist.')
            option = response.get('chosen_option')
            if check['check_type'] == 'mcq' and option not in {'A', 'B', 'C', 'D', 'absent'}:
                raise HTTPException(422, 'MCQ answers must be A, B, C, D, or absent.')
            if check['check_type'] == 'observation' and response.get('rating') not in {'got_it', 'partly', 'not_yet', 'absent'}:
                raise HTTPException(422, 'Observation ratings are got_it, partly, not_yet, or absent.')
    db = conn()
    db.execute('delete from responses where check_id=?', (check_id,))
    if payload.check_mode == 'class_count':
        db.execute('insert into responses(check_id, item_index, check_mode, class_counts_json) values(?,?,?,?)', (check_id, 0, payload.check_mode, json.dumps(payload.class_counts)))
    else:
        for response in payload.responses:
            db.execute('insert into responses(check_id,roll_no,item_index,chosen_option,rating,error_id,check_mode) values(?,?,?,?,?,?,?)', (check_id, response.get('roll_no'), response.get('item_index'), response.get('chosen_option'), response.get('rating'), response.get('error_id'), payload.check_mode))
    db.commit(); db.close()
    return analyze_results(check_id).model_dump()

@app.get('/api/checks/{check_id}/insight')
def insight(check_id: str, request: Request):
    authorize(request)
    return analyze_results(check_id).model_dump()

@app.post('/api/checks/{check_id}/next-steps')
def next_steps(check_id: str, request: Request):
    authorize(request)
    return generate_next_steps(check_id)

@app.post('/api/checks/{check_id}/use-warmup')
def use_warmup(check_id: str, request: Request):
    authorize(request)
    check = one('select ch.*, lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    insight_row = one('select insight_json from insights where check_id=?', (check_id,))
    if not check or not insight_row:
        raise HTTPException(422, 'Save results and calculate the insight first.')
    data = json.loads(insight_row['insight_json'])
    weak = next((item for item in data['concepts'] if item['status'] == 'Needs re-teaching'), None)
    warmup = f"Review {weak['concept_id']} for 6 minutes using a quick example and pair practice." if weak else 'Use a 5-minute warm-up on the previous lesson.'
    database = conn()
    database.execute("INSERT OR REPLACE INTO pending_warmups VALUES(?,?,?,datetime('now'))", (check['class_id'], warmup, check_id))
    database.commit(); database.close()
    return {'warmup': warmup}

@app.get('/api/progress/{class_id}')
def progress(class_id: str, request: Request):
    authorize(request)
    history = rows('''select i.insight_json, i.created_at, ch.id as check_id, lp.chapter_or_topic
                      from insights i join checks ch on ch.id=i.check_id join lesson_plans lp on lp.id=ch.lesson_plan_id
                      where lp.class_id=? order by i.created_at''', (class_id,))
    checks = []
    concepts = {}
    for entry in history:
        data = json.loads(entry['insight_json'])
        checks.append({'check_id': entry['check_id'], 'topic': entry['chapter_or_topic'], 'created_at': entry['created_at']})
        for concept in data['concepts']:
            concepts.setdefault(concept['concept_id'], []).append({'check_id': entry['check_id'], 'percent': concept['percent_correct'], 'status': concept['status']})
    return {'checks': checks, 'concepts': concepts}
@app.get('/api/usage')
def usage(request: Request):
    authorize(request)
    calls = rows('select * from llm_calls order by created_at desc')
    runs = rows('''select r.*, c.name as class_name,
        coalesce(sum(l.input_tokens), 0) as input_tokens,
        coalesce(sum(l.cached_input_tokens), 0) as cached_input_tokens,
        coalesce(sum(l.output_tokens), 0) as output_tokens
        from runs r left join classes c on c.id=r.class_id
        left join llm_calls l on l.run_id=r.id
        group by r.id order by r.created_at desc''')
    return {
        'totals': {
            'runs': len(runs),
            'input_tokens': sum(x['input_tokens'] for x in calls),
            'cached_input_tokens': sum(x['cached_input_tokens'] for x in calls),
            'output_tokens': sum(x['output_tokens'] for x in calls),
            'cost_usd': sum(x['cost_usd'] for x in calls),
            'provider_cost_usd': sum(x['provider_cost_usd'] for x in calls),
        },
        'per_agent': rows('select agent_name, sum(input_tokens) as input_tokens, sum(cached_input_tokens) as cached_input_tokens, sum(output_tokens) as output_tokens, sum(cost_usd) as cost_usd, sum(provider_cost_usd) as provider_cost_usd from llm_calls group by agent_name'),
        'recent_runs': runs,
    }
app.mount('/', StaticFiles(directory=str(ROOT / "static"), html=True), name='static')
