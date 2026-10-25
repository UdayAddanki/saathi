from __future__ import annotations

import json
import sqlite3
import uuid
from .config import DB_PATH, ROOT, DEMO_MODE, DEMO_PASSWORD
SCHEMA = """
CREATE TABLE IF NOT EXISTS classes(id TEXT PRIMARY KEY,name TEXT,board TEXT,grade INTEGER,section TEXT,class_size INTEGER,period_minutes INTEGER,resources_json TEXT);
CREATE TABLE IF NOT EXISTS class_contexts(class_id TEXT PRIMARY KEY,learning_level_choice TEXT,learning_level_text TEXT,unit_goal TEXT,updated_at TEXT,current_situation TEXT DEFAULT '',classroom_vision TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS students(class_id TEXT,roll_no INTEGER,first_name TEXT);
CREATE TABLE IF NOT EXISTS papers(id TEXT PRIMARY KEY,class_id TEXT,source TEXT,questions_json TEXT,confirmed INTEGER DEFAULT 0,created_at TEXT);
CREATE TABLE IF NOT EXISTS paper_files(id TEXT PRIMARY KEY,paper_id TEXT,page_number INTEGER,mime_type TEXT,path TEXT,size INTEGER,created_at TEXT);
CREATE TABLE IF NOT EXISTS sheet_files(id TEXT PRIMARY KEY,paper_id TEXT,roll_no INTEGER,page_number INTEGER,mime_type TEXT,path TEXT,size INTEGER,created_at TEXT);
CREATE TABLE IF NOT EXISTS sheet_readings(paper_id TEXT,roll_no INTEGER,question_number INTEGER,transcribed_answer TEXT,confidence TEXT,unreadable INTEGER,ai_suggestion TEXT);
CREATE TABLE IF NOT EXISTS results(paper_id TEXT,roll_no INTEGER,question_number INTEGER,mark REAL,max_marks REAL,confirmed_by_teacher INTEGER,edited INTEGER);
CREATE TABLE IF NOT EXISTS check_selections(paper_id TEXT,roll_no INTEGER);
CREATE TABLE IF NOT EXISTS lesson_plans(id TEXT PRIMARY KEY,class_id TEXT,board TEXT,grade INTEGER,subject TEXT,chapter_or_topic TEXT,mode TEXT,plan_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS checks(id TEXT PRIMARY KEY,lesson_plan_id TEXT,check_type TEXT,items_json TEXT);
CREATE TABLE IF NOT EXISTS responses(check_id TEXT,roll_no INTEGER,item_index INTEGER,chosen_option TEXT,rating TEXT,error_id TEXT);
CREATE TABLE IF NOT EXISTS insights(check_id TEXT,insight_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS review_results(id TEXT PRIMARY KEY,run_id TEXT,passed INTEGER,issues_json TEXT,revision INTEGER,created_at TEXT);
CREATE TABLE IF NOT EXISTS llm_calls(id TEXT PRIMARY KEY,run_id TEXT,agent_name TEXT,input_tokens INTEGER,cached_input_tokens INTEGER,output_tokens INTEGER,cost_usd REAL,provider_cost_usd REAL,duration_ms INTEGER,created_at TEXT,teacher_id TEXT);
CREATE TABLE IF NOT EXISTS tool_calls(id TEXT PRIMARY KEY,run_id TEXT,agent_name TEXT,tool_name TEXT,arguments_json TEXT,duration_ms INTEGER,created_at TEXT);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,kind TEXT,class_id TEXT,status TEXT,total_cost_usd REAL,created_at TEXT,teacher_id TEXT);
CREATE TABLE IF NOT EXISTS pending_warmups(class_id TEXT PRIMARY KEY,warmup TEXT,source_check_id TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS teachers(id TEXT PRIMARY KEY,username TEXT UNIQUE COLLATE NOCASE,email TEXT UNIQUE COLLATE NOCASE,password_hash TEXT,password_salt TEXT,created_at TEXT,last_active TEXT,force_password_change INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,teacher_id TEXT,token_hash TEXT UNIQUE,expires_at TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS password_resets(id TEXT PRIMARY KEY,teacher_id TEXT,token_hash TEXT UNIQUE,expires_at TEXT,used INTEGER DEFAULT 0,created_at TEXT);
CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY,teacher_id TEXT,plan_id TEXT,check_id TEXT,grade INTEGER,board TEXT,rating INTEGER,teach_decision TEXT,usual_time TEXT,saathi_minutes REAL,comment TEXT,teacher_name TEXT,opened_plan_tab_at TEXT,prepare_clicked_at TEXT,plan_ready_at TEXT,first_print_or_feedback_at TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS check_corrections(paper_id TEXT PRIMARY KEY,count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,check_id TEXT,kind TEXT,readiness_level TEXT,roll_no INTEGER,content_json TEXT,review_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS paper_checks(paper_id TEXT PRIMARY KEY,check_id TEXT);
"""
def conn() -> sqlite3.Connection:
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init_db() -> None:
    c = conn()
    c.executescript(SCHEMA)
    class_columns = {row[1] for row in c.execute("PRAGMA table_info(classes)")}
    if "teacher_id" not in class_columns:
        c.execute("ALTER TABLE classes ADD COLUMN teacher_id TEXT")
    teacher_columns = {row[1] for row in c.execute("PRAGMA table_info(teachers)")}
    for name, definition in {"display_name": "TEXT DEFAULT ''", "school": "TEXT DEFAULT ''", "failed_logins": "INTEGER DEFAULT 0", "locked_until": "INTEGER DEFAULT 0", "setup_complete": "INTEGER DEFAULT 0"}.items():
        if name not in teacher_columns:
            c.execute(f"ALTER TABLE teachers ADD COLUMN {name} {definition}")
    for table in ("runs", "llm_calls", "feedback", "uploads"):
        columns = {row[1] for row in c.execute(f"PRAGMA table_info({table})")}
        if columns and "teacher_id" not in columns:
            c.execute(f"ALTER TABLE {table} ADD COLUMN teacher_id TEXT")
    sheet_columns = {row[1] for row in c.execute("PRAGMA table_info(sheet_files)")}
    if "teacher_id" not in sheet_columns:
        c.execute("ALTER TABLE sheet_files ADD COLUMN teacher_id TEXT")
    response_columns = {row[1] for row in c.execute("PRAGMA table_info(responses)")}
    if "check_mode" not in response_columns:
        c.execute("ALTER TABLE responses ADD COLUMN check_mode TEXT DEFAULT 'each_child'")
    if "class_counts_json" not in response_columns:
        c.execute("ALTER TABLE responses ADD COLUMN class_counts_json TEXT")
    student_columns = {row[1] for row in c.execute("PRAGMA table_info(students)")}
    if "readiness_level" not in student_columns:
        c.execute("ALTER TABLE students ADD COLUMN readiness_level TEXT DEFAULT 'mid'")
    if "updated_at" not in student_columns:
        c.execute("ALTER TABLE students ADD COLUMN updated_at TEXT")
    plan_columns = {row[1] for row in c.execute("PRAGMA table_info(lesson_plans)")}
    for name, definition in {"lesson_type": "TEXT DEFAULT '5-step'", "chapter": "TEXT DEFAULT ''", "topic": "TEXT DEFAULT ''", "day_number": "INTEGER DEFAULT 1", "total_days": "INTEGER DEFAULT 1", "context_snapshot_json": "TEXT DEFAULT '{}'", "differentiated": "INTEGER DEFAULT 0", "differentiation_types_json": "TEXT DEFAULT '[]'"}.items():
        if name not in plan_columns:
            c.execute(f"ALTER TABLE lesson_plans ADD COLUMN {name} {definition}")
    context_columns = {row[1] for row in c.execute("PRAGMA table_info(class_contexts)")}
    for name, definition in {"current_situation": "TEXT DEFAULT ''", "classroom_vision": "TEXT DEFAULT ''"}.items():
        if name not in context_columns:
            c.execute(f"ALTER TABLE class_contexts ADD COLUMN {name} {definition}")
    demos = json.load(open(ROOT / "data/demo_classes.json"))
    for x in demos:
        if not c.execute('select 1 from classes where id=?',(x['id'],)).fetchone():
            c.execute('insert into classes(id,name,board,grade,section,class_size,period_minutes,resources_json,teacher_id) values(?,?,?,?,?,?,?,?,?)',(x['id'],x['name'],x['board'],x['grade'],x['section'],x['class_size'],x['period_minutes'],json.dumps(x['resources']),None))
            for i,n in enumerate(x['students'],1):
                c.execute('insert into students(class_id,roll_no,first_name,readiness_level,updated_at) values(?,?,?,?,?)',(x['id'],i,n,'mid',None))
    if DEMO_MODE and DB_PATH.name != 'test.db' and not c.execute('select id from teachers where username=?', ('demo',)).fetchone():
        from .auth import password_hash
        import datetime
        hashed, salt = password_hash(DEMO_PASSWORD)
        teacher_id = str(uuid.uuid4())
        c.execute('insert into teachers(id,username,email,password_hash,password_salt,created_at,last_active,force_password_change) values(?,?,?,?,?,?,?,?)', (teacher_id, 'demo', 'demo@saathi.local', hashed, salt, datetime.datetime.now(datetime.timezone.utc).isoformat(), None, 0))
        c.execute('update classes set teacher_id=? where teacher_id is null', (teacher_id,))
    c.commit(); c.close()
def rows(sql: str, args: tuple = ()) -> list[dict]:
    c=conn(); out=[dict(r) for r in c.execute(sql,args)]; c.close(); return out
def one(sql: str, args: tuple = ()) -> dict | None:
    a=rows(sql,args); return a[0] if a else None
def add_run(class_id: str, kind: str = "plan", teacher_id: str | None = None) -> str:
    import datetime
    run_id = str(uuid.uuid4())
    c = conn()
    c.execute("INSERT INTO runs(id,kind,class_id,status,total_cost_usd,created_at,teacher_id) VALUES(?,?,?,?,?,?,?)", (run_id, kind, class_id, "running", 0, datetime.datetime.now(datetime.timezone.utc).isoformat(), teacher_id))
    c.commit()
    c.close()
    return run_id
