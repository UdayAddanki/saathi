from __future__ import annotations

import json
import datetime
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from typing import List
from fastapi.staticfiles import StaticFiles
from .config import ACCESS_CODE, DAILY_BUDGET_USD, DEMO_MODE, KEY_FOUND
from .db import init_db, rows, one, conn, add_run
from .models import PlanRequest, ClassRequest
from .pipeline import generate_plan, generate_next_steps
from .config import ROOT
from .diagnosis import analyze_results
from .models import ResultsRequest
from .roll import parse_roll_file, normalize_level
from .roll_pdf import parse_roll_pdf
from .marking import mark_answer
from .agents.readers import answer_sheet_reader
from pydantic_ai import BinaryContent
from .usage import record
from .agents.resources import resource_builder

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

@app.get('/api/classes/{class_id}/context')
def get_context(class_id: str, request: Request):
    authorize(request)
    return one('select * from class_contexts where class_id=?', (class_id,)) or {'class_id': class_id, 'learning_level_choice': 'Mixed levels', 'learning_level_text': '', 'current_situation': '', 'classroom_vision': '', 'unit_goal': ''}

@app.get('/api/classes/{class_id}/roll')
def get_roll(class_id: str, request: Request):
    authorize(request)
    return rows('select roll_no,first_name,readiness_level from students where class_id=? order by roll_no', (class_id,))

@app.post('/api/classes/{class_id}/roll/upload')
async def upload_roll(class_id: str, request: Request, file: UploadFile = File(...)):
    authorize(request)
    parsed = parse_roll_file(await file.read(2 * 1024 * 1024 + 1), file.filename or '')
    return {'rows': parsed, 'valid': all(item['valid'] for item in parsed)}

@app.post('/api/classes/{class_id}/roll/upload-pdf')
async def upload_roll_pdf(class_id: str, request: Request, file: UploadFile = File(...)):
    authorize(request)
    try:
        parsed = parse_roll_pdf(await file.read(10 * 1024 * 1024 + 1))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {'rows': parsed, 'valid': True}

@app.post('/api/classes/{class_id}/roll/save')
def save_roll(class_id: str, payload: list[dict], request: Request):
    authorize(request)
    import datetime
    if not payload:
        raise HTTPException(422, 'Choose a file and press Preview, or type names into the three boxes.')
    seen = set()
    for item in payload:
        roll_no = item.get('roll_no')
        if not isinstance(roll_no, int) or isinstance(roll_no, bool) or roll_no <= 0:
            raise HTTPException(422, f'Roll number must be a positive integer (problem at roll {roll_no or "blank"}).')
        if roll_no in seen:
            raise HTTPException(422, f'Duplicate roll number {roll_no}. Each child must have a unique roll number.')
        seen.add(roll_no)
        if not item.get('first_name') or not str(item.get('first_name')).strip():
            raise HTTPException(422, f'Missing name on roll {roll_no}.')
        if normalize_level(item.get('readiness_level')) is None:
            raise HTTPException(422, f'Unknown readiness level on roll {roll_no}. Use Low, Mid, or High.')
    db = conn(); db.execute('delete from students where class_id=?', (class_id,))
    for index, item in enumerate(payload, 1):
        db.execute('insert into students(class_id,roll_no,first_name,readiness_level,updated_at) values(?,?,?,?,?)', (class_id, index, item.get('first_name'), normalize_level(item.get('readiness_level')), datetime.datetime.now(datetime.timezone.utc).isoformat()))
    db.commit(); db.close(); return get_roll(class_id, request)

@app.get('/api/classes/{class_id}/roll-template.csv')
def roll_template(class_id: str, request: Request):
    authorize(request)
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse('roll number,name,readiness level\n1,Example Low,Low\n2,Example Mid,Mid\n3,Example High,High\n', media_type='text/csv', headers={'Content-Disposition':'attachment; filename=saathi-roll-template.csv'})

@app.put('/api/classes/{class_id}/context')
def save_context(class_id: str, payload: dict, request: Request):
    authorize(request)
    text = ' '.join(str(payload.get(key, '')) for key in ('learning_level_text', 'current_situation', 'classroom_vision', 'unit_goal'))
    if INJECTION_PATTERNS.search(text):
        raise HTTPException(400, 'That classroom context contains text Saathi cannot treat as classroom context.')
    if len(payload.get('learning_level_text', '')) > 300 or len(payload.get('current_situation', '')) > 500 or len(payload.get('classroom_vision', '')) > 300 or len(payload.get('unit_goal', '')) > 300:
        raise HTTPException(422, 'Classroom context fields are too long.')
    import datetime
    database = conn(); database.execute('insert or replace into class_contexts(class_id,learning_level_choice,learning_level_text,unit_goal,updated_at,current_situation,classroom_vision) values(?,?,?,?,?,?,?)', (class_id, payload.get('learning_level_choice', 'Mixed levels'), payload.get('learning_level_text', ''), payload.get('unit_goal', ''), datetime.datetime.now(datetime.timezone.utc).isoformat(), payload.get('current_situation', ''), payload.get('classroom_vision', ''))); database.commit(); database.close()
    return get_context(class_id, request)

@app.post('/api/classes/{class_id}/chapter-document')
async def upload_chapter_document(class_id: str, request: Request, file: UploadFile = File(...)):
    """Store an optional PDF locally for the current class; never expose its contents in HTML."""
    authorize(request)
    if not one('select id from classes where id=?', (class_id,)):
        raise HTTPException(404, 'Class not found')
    filename = file.filename or 'chapter.pdf'
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(400, 'Only PDF chapter documents are supported.')
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024 or not content.startswith(b'%PDF'):
        raise HTTPException(400, 'Please choose a valid PDF smaller than 10 MB.')
    import uuid
    upload_dir = ROOT / 'uploads'
    upload_dir.mkdir(exist_ok=True)
    stored = upload_dir / f'{class_id}-{uuid.uuid4().hex}.pdf'
    stored.write_bytes(content)
    return {'filename': filename, 'stored': stored.name}
@app.post('/api/classes')
def create_class(req: ClassRequest, request: Request):
 authorize(request)
 import uuid,json
 cid=str(uuid.uuid4()); c=conn(); c.execute('insert into classes values(?,?,?,?,?,?,?,?)',(cid,f'{req.grade}{req.section}',req.board,req.grade,req.section,req.class_size,req.period_minutes,json.dumps(req.resources))); c.executemany('insert into students(class_id,roll_no,first_name,readiness_level,updated_at) values(?,?,?,?,?)',[(cid,i,None,'mid',None) for i in range(1,req.class_size+1)]); c.commit(); c.close(); return {'id':cid}
@app.post('/api/plans')
def plan(req: PlanRequest, request: Request):
 authorize(request)
 if not KEY_FOUND: raise HTTPException(503,'PORTKEY_API_KEY not found')
 if not budget_remaining(): raise HTTPException(429, 'Today’s lesson budget has been reached. Please try again tomorrow.')
 run_id = 'preflight-' + str(time.time_ns())
 check_injection(run_id, req.chapter_or_topic, req.teacher_note)
 enforce_rate_limit(request)
 context = get_context(req.class_id, request)
 if req.learning_level_text or req.current_situation or req.classroom_vision or req.unit_goal or req.learning_level_choice != 'Mixed levels':
     context = save_context(req.class_id, {'learning_level_choice': req.learning_level_choice, 'learning_level_text': req.learning_level_text, 'current_situation': req.current_situation, 'classroom_vision': req.classroom_vision, 'unit_goal': req.unit_goal}, request)
 total_days = 1 if req.lesson_type == 'experiential' else req.total_days
 day_number = 1 if req.lesson_type == 'experiential' else req.day_number
 return generate_plan(req.class_id, req.subject, req.chapter_or_topic, req.teacher_note, chapter=req.chapter, topic=req.topic, lesson_type=req.lesson_type, classroom_context=context, differentiated=req.differentiated, differentiation_types=req.differentiation_types, use_last_groups=req.use_last_groups, day_number=day_number, total_days=total_days, project_idea=req.project_idea, project_scope=req.project_scope)
@app.get('/api/plans/{plan_id}')
def saved(plan_id: str, request: Request):
 authorize(request)
 x=one('select * from lesson_plans where id=?',(plan_id,))
 if not x: raise HTTPException(404,'Plan not found')
 return x

@app.get('/api/lessons/recent')
def recent_lessons(request: Request, class_id: str | None = None):
    authorize(request)
    sql = '''select lp.id, lp.chapter_or_topic, lp.topic, lp.lesson_type, lp.created_at, c.name as class_name, c.grade, ch.id as check_id, ch.check_type
                   from lesson_plans lp join classes c on c.id=lp.class_id join checks ch on ch.lesson_plan_id=lp.id
                   where (? is null or lp.class_id=?) order by lp.created_at desc limit 10'''
    return rows(sql, (class_id, class_id))

@app.get('/api/checks/{check_id}')
def get_check(check_id: str, request: Request):
    authorize(request)
    check = one('select ch.*, lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    if not check:
        raise HTTPException(404, 'Check not found')
    check['items'] = json.loads(check.pop('items_json'))
    check['students'] = rows('select roll_no, first_name, readiness_level from students where class_id=? order by roll_no', (check['class_id'],))
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

@app.post('/api/papers/from-check/{check_id}')
def paper_from_check(check_id: str, request: Request):
    authorize(request)
    check = one('select ch.*,lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    if not check:
        raise HTTPException(404, 'Check not found')
    items = json.loads(check['items_json']); items = items if isinstance(items, list) else items.get('questions', items.get('tasks', []))
    paper_id = __import__('uuid').uuid4().hex
    db = conn(); db.execute('insert into papers(id,class_id,source,questions_json,confirmed,created_at) values(?,?,?,?,?,?)', (paper_id, check['class_id'], 'saathi_check', json.dumps(items), 1, __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())); db.commit(); db.close()
    return {'id': paper_id, 'questions': items, 'confirmed': True}

@app.post('/api/checks/{check_id}/submissions')
async def upload_submissions(check_id: str, request: Request, files: List[UploadFile] = File(...)):
    authorize(request)
    check = one('select ch.*, lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    if not check: raise HTTPException(404, 'Check not found')
    paper = one('select id from papers where class_id=? and source=? order by created_at desc limit 1', (check['class_id'], 'saathi_check'))
    if not paper:
        items = json.loads(check['items_json']); items = items if isinstance(items, list) else items.get('questions', items.get('tasks', []))
        paper_id = uuid.uuid4().hex; db = conn(); db.execute('insert into papers(id,class_id,source,questions_json,confirmed,created_at) values(?,?,?,?,?,datetime("now"))', (paper_id, check['class_id'], 'saathi_check', json.dumps(items), 1)); db.commit(); db.close()
    else: paper_id = paper['id']
    db = conn(); db.execute('insert or replace into paper_checks values(?,?)', (paper_id, check_id)); db.commit(); db.close()
    students = {int(row['roll_no']): row for row in rows('select roll_no,first_name,readiness_level from students where class_id=?', (check['class_id'],))}
    directory = ROOT / 'uploads' / check['class_id']; directory.mkdir(parents=True, exist_ok=True); output = []
    for file in files:
        suffix = (file.filename or '').lower().rsplit('.', 1)[-1]
        if suffix in {'doc', 'docx', 'ppt', 'pptx'}: raise HTTPException(415, 'Please save Word or PowerPoint files as PDF and upload again.')
        if suffix not in {'pdf', 'jpg', 'jpeg', 'png', 'heic'}: raise HTTPException(415, 'Upload a PDF, JPG, PNG, or HEIC answer sheet.')
        data = await file.read(10 * 1024 * 1024 + 1)
        if len(data) > 10 * 1024 * 1024: raise HTTPException(413, 'Each answer sheet must be 10 MB or smaller.')
        match = re.search(r'(?:roll[_ -]?)?(\d+)', file.filename or '', re.I); roll_no = int(match.group(1)) if match else None
        stored = directory / f'{uuid.uuid4().hex}.{suffix}'; stored.write_bytes(data)
        db = conn(); file_id = uuid.uuid4().hex; db.execute('insert into sheet_files(id,paper_id,roll_no,page_number,mime_type,path,size) values(?,?,?,?,?,?,?)', (file_id, paper_id, roll_no if roll_no in students else None, 1, suffix, str(stored), len(data))); db.commit(); db.close()
        output.append({'file_id': file_id, 'filename': file.filename, 'roll_no': roll_no if roll_no in students else None, 'child': students.get(roll_no), 'status': 'Uploaded' if roll_no in students else 'Needs teacher assignment'})
    return {'paper_id': paper_id, 'files': output}

@app.get('/api/papers/{paper_id}/submission-review')
def submission_review(paper_id: str, request: Request):
    authorize(request); paper = one('select id from papers where id=?', (paper_id,))
    if not paper: raise HTTPException(404, 'Paper not found')
    return {'paper_id': paper_id, 'files': rows('select id,roll_no,page_number,mime_type,path,size from sheet_files where paper_id=?', (paper_id,)), 'confirmed': False}

@app.post('/api/papers/{paper_id}/assign-submission')
def assign_submission(paper_id: str, payload: dict, request: Request):
    authorize(request); roll_no = int(payload.get('roll_no', 0)); file_id = payload.get('file_id')
    if roll_no <= 0 or not one('select id from sheet_files where id=? and paper_id=?', (file_id, paper_id)): raise HTTPException(422, 'Choose a valid child for this file.')
    db = conn(); db.execute('update sheet_files set roll_no=? where id=? and paper_id=?', (roll_no, file_id, paper_id)); db.commit(); db.close(); return {'assigned': True}

@app.post('/api/papers/{paper_id}/read-submissions')
async def read_submissions(paper_id: str, request: Request):
    authorize(request); paper = one('select * from papers where id=?', (paper_id,))
    if not paper: raise HTTPException(404, 'Paper not found')
    questions = json.loads(paper['questions_json']); run_id = add_run(paper['class_id'], 'answer_sheet_reading'); readings = []
    for sheet in rows('select * from sheet_files where paper_id=? and roll_no is not null', (paper_id,)):
        started = time.perf_counter()
        result = await answer_sheet_reader.run([BinaryContent(data=__import__('pathlib').Path(sheet['path']).read_bytes(), media_type='image/' + sheet['mime_type'] if sheet['mime_type'] != 'pdf' else 'application/pdf'), 'Transcribe every question option.'])
        usage = record(run_id, 'answer_sheet_reader', result.usage, started)
        db = conn(); db.execute('delete from sheet_readings where paper_id=? and roll_no=?', (paper_id, sheet['roll_no']))
        for number, answer in result.output.answers.items():
            clean_number = int(str(number).lstrip('Qq'))
            confidence = result.output.confidence.get(number, result.output.confidence.get(str(clean_number), 'low'))
            unreadable_numbers = {int(str(value).lstrip('Qq')) for value in result.output.unreadable}
            db.execute('insert into sheet_readings values(?,?,?,?,?,?,?)', (paper_id, sheet['roll_no'], clean_number, answer, confidence, int(clean_number in unreadable_numbers), None))
        db.commit(); db.close(); readings.append({'roll_no': sheet['roll_no'], 'usage': usage})
    db = conn(); db.execute('update runs set status=? where id=?', ('complete', run_id)); db.commit(); db.close()
    return {'paper_id': paper_id, 'readings': readings}

@app.get('/api/papers/{paper_id}/review-grid')
def review_grid(paper_id: str, request: Request):
    authorize(request); paper = one('select * from papers where id=?', (paper_id,))
    if not paper: raise HTTPException(404, 'Paper not found')
    questions = json.loads(paper['questions_json']); output = []
    for reading in rows('select * from sheet_readings where paper_id=? order by roll_no,question_number', (paper_id,)):
        question_number = int(reading['question_number'])
        if question_number > len(questions):
            continue
        question = questions[question_number - 1]; answer = reading['transcribed_answer']; answer_option = str(answer or '').strip().upper()[:1]; correct = question.get('correct_option')
        if not correct: correct = question.get('correct_answer')
        output.append({'roll_no': reading['roll_no'], 'question_number': question_number, 'answer': answer_option, 'raw_answer': answer, 'confidence': reading['confidence'], 'unreadable': bool(reading['unreadable']), 'mark': None if reading['unreadable'] or not answer else (1 if answer_option == str(correct).upper() else 0)})
    return {'paper_id': paper_id, 'questions': questions, 'cells': output}

@app.post('/api/papers/{paper_id}/confirm')
def confirm_paper(paper_id: str, payload: dict, request: Request):
    authorize(request)
    db = conn(); db.execute('update papers set questions_json=?,confirmed=1 where id=?', (json.dumps(payload.get('questions', [])), paper_id)); db.commit(); db.close(); return {'paper_id': paper_id, 'confirmed': True}

@app.post('/api/papers/{paper_id}/results/confirm')
def confirm_results(paper_id: str, payload: list[dict], request: Request):
    authorize(request)
    db = conn(); db.execute('delete from results where paper_id=?', (paper_id,))
    for item in payload:
        db.execute('insert into results values(?,?,?,?,?,?,?)', (paper_id, item['roll_no'], item['question_number'], item.get('mark'), item.get('max_marks', 1), 1, int(item.get('edited', False))))
    corrections = sum(1 for item in payload if item.get('edited'))
    db.execute('insert or replace into check_corrections(paper_id,count) values(?,?)', (paper_id, corrections))
    mapping = db.execute('select check_id from paper_checks where paper_id=?', (paper_id,)).fetchone()
    if mapping:
        db.execute('delete from responses where check_id=?', (mapping[0],))
        for item in payload:
            db.execute('insert into responses(check_id,roll_no,item_index,chosen_option,check_mode) values(?,?,?,?,?)', (mapping[0], item['roll_no'], int(item['question_number']) - 1, item.get('answer'), 'each_child'))
    db.commit(); db.close(); return {'confirmed': True, 'count': len(payload), 'corrections': corrections}

@app.get('/api/papers/{paper_id}/progress')
def paper_progress(paper_id: str, request: Request):
    authorize(request)
    paper = one('select * from papers where id=?', (paper_id,))
    if not paper:
        raise HTTPException(404, 'Paper not found')
    questions = json.loads(paper['questions_json']); results = rows('select * from results where paper_id=? and confirmed_by_teacher=1', (paper_id,))
    students = rows('select roll_no,first_name,readiness_level from students where class_id=?', (paper['class_id'],))
    by_child = {}
    for result in results:
        entry = by_child.setdefault(result['roll_no'], {'marks': 0, 'max': 0})
        entry['marks'] += result['mark'] or 0; entry['max'] += result['max_marks'] or 0
    child_data = []
    for student in students:
        entry = by_child.get(student['roll_no'])
        if entry:
            child_data.append({**student, 'mastery': round(100 * entry['marks'] / entry['max']) if entry['max'] else None})
    levels = {}
    for level in ('low', 'mid', 'high'):
        values = [item['mastery'] for item in child_data if item['readiness_level'] == level and item['mastery'] is not None]
        levels[level] = {'count': len(values), 'mastery': round(sum(values) / len(values)) if values else None}
    average = [item['mastery'] for item in child_data if item['mastery'] is not None]
    question_by_readiness = {}
    for question_number in range(1, len(questions) + 1):
        question_by_readiness[str(question_number)] = {}
        for level in ('low', 'mid', 'high'):
            selected = [r for r in results if r['question_number'] == question_number and next((s['readiness_level'] for s in students if s['roll_no'] == r['roll_no']), 'mid') == level]
            question_by_readiness[str(question_number)][level] = round(100 * sum(float(r['mark'] or 0) for r in selected) / sum(float(r['max_marks'] or 1) for r in selected)) if selected else None
    return {'paper_id': paper_id, 'class_size': len(students), 'checked': len(child_data), 'class_average': round(sum(average) / len(average)) if average else None, 'by_readiness': levels, 'children': child_data, 'questions': questions, 'question_by_readiness': question_by_readiness}

@app.get('/api/checks/{check_id}/insight')
def insight(check_id: str, request: Request):
    authorize(request)
    return analyze_results(check_id).model_dump()

@app.post('/api/checks/{check_id}/next-steps')
def next_steps(check_id: str, request: Request):
    authorize(request)
    return generate_next_steps(check_id)

@app.post('/api/checks/{check_id}/resources/{kind}')
async def generate_resources(check_id: str, kind: str, request: Request):
    authorize(request)
    if kind not in {'worksheets', 'meeting_plans'}: raise HTTPException(422, 'Unknown resource type.')
    check = one('select ch.*,lp.class_id from checks ch join lesson_plans lp on lp.id=ch.lesson_plan_id where ch.id=?', (check_id,))
    if not check: raise HTTPException(404, 'Check not found')
    insight = analyze_results(check_id); rolls = []
    if kind == 'meeting_plans':
        students = rows('select roll_no from students where class_id=?', (check['class_id'],))
        rolls = [item['roll_no'] for item in students[:5]]
    run_id = add_run(check['class_id'], kind); prompt = f'kind={kind}; check_id={check_id}; insight={insight.model_dump_json()}; roll_numbers={rolls}. Return resources only.'
    started = time.perf_counter(); result = await resource_builder.run(prompt); usage = record(run_id, 'resource_builder', result.usage, started)
    content = result.output.model_dump(); db = conn(); db.execute('delete from resources where check_id=? and kind=?', (check_id, kind)); db.execute('insert into resources values(?,?,?,?,?,?,?,datetime("now"))', (uuid.uuid4().hex, check_id, kind, None, None, json.dumps(content), '{}',)); db.execute('update runs set status=?,total_cost_usd=? where id=?', ('complete', usage['cost_usd'], run_id)); db.commit(); db.close()
    return {'check_id': check_id, 'kind': kind, 'resources': content, 'usage': usage, 'roll_numbers': rolls}

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
