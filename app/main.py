from __future__ import annotations

import json
import datetime
import logging
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from .config import ACCESS_CODE, DAILY_BUDGET_USD, KEY_FOUND
from .db import init_db, rows, one, conn
from .models import PlanRequest, ClassRequest
from .pipeline import generate_plan
from .config import ROOT

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
    return {'ok': True, 'key_found': KEY_FOUND, 'access_required': bool(ACCESS_CODE), 'message': None if KEY_FOUND else 'PORTKEY_API_KEY not found'}

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
