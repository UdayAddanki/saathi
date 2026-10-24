from __future__ import annotations
import json
import datetime
import time
import uuid
from .config import ROOT
from .db import one
CONCEPTS=json.load(open(ROOT/'data/concepts.json'))
MISCONCEPTIONS=json.load(open(ROOT/'data/misconceptions.json'))
CURRENT_RUN_ID: str | None = None
CURRENT_AGENT: str = "unknown"

def _log_tool(name: str, arguments: dict, started: float) -> None:
    """Record tool execution when called during a pipeline run."""
    if CURRENT_RUN_ID is None:
        return
    from .db import conn
    db = conn()
    db.execute("INSERT INTO tool_calls VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), CURRENT_RUN_ID, CURRENT_AGENT, name, json.dumps(arguments), int((time.perf_counter() - started) * 1000), datetime.datetime.now(datetime.timezone.utc).isoformat()))
    db.commit()
    db.close()
def subjects_for_grade(grade: int) -> list[str]:
    """Return subjects available for a grade."""
    return ['English', 'Mathematics'] + (['Environmental Studies (EVS)'] if grade >= 3 else [])
def get_curriculum_context(board: str, grade: int, subject: str, chapter_or_topic: str) -> dict:
    """Return curriculum context and curated/open mode."""
    started = time.perf_counter()
    q=chapter_or_topic.casefold(); matches=[c for c in CONCEPTS if c['subject']==subject and any(k.casefold() in q for k in c['keywords']) and grade in c['grades']]
    result = {'board':board,'grade':grade,'subject':subject,'chapter':None,'concepts':matches,'mode':'curated' if matches else 'open'}
    _log_tool('get_curriculum_context', {'board':board,'grade':grade,'subject':subject,'chapter_or_topic':chapter_or_topic}, started)
    return result
def get_class_profile(class_id: str) -> dict:
    """Return class context without student names."""
    started = time.perf_counter(); x=one('select * from classes where id=?',(class_id,));
    if not x: return None
    x['resources']=json.loads(x.pop('resources_json')); _log_tool('get_class_profile', {'class_id':class_id}, started); return x
def get_latest_insights(class_id: str) -> str:
    """Return Phase 2 insight placeholder."""
    started = time.perf_counter(); result = 'no data yet'; _log_tool('get_latest_insights', {'class_id':class_id}, started); return result
def get_misconceptions(concept_id: str) -> list[dict]:
    """Return curated misconceptions for a concept."""
    started = time.perf_counter(); result = [m for m in MISCONCEPTIONS if m['concept_id']==concept_id]; _log_tool('get_misconceptions', {'concept_id':concept_id}, started); return result
