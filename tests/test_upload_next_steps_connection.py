import json
import uuid

from pydantic_ai.models.function import FunctionModel

from app.db import conn


def test_upload_confirm_persists_insight_and_next_steps_uses_it(client_as_teacher, monkeypatch):
    plan_id, check_id, paper_id = (uuid.uuid4().hex for _ in range(3))
    items = [{'concept_id': 'place-value', 'stem': 'Which is 4?', 'options': {'A': '4', 'B': '40', 'C': '400', 'D': '44'}, 'correct_option': 'A', 'option_errors': {}} for _ in range(5)]
    db = conn()
    db.execute('insert into lesson_plans(id,class_id,board,grade,subject,chapter_or_topic,mode,plan_json,created_at) values(?,?,?,?,?,?,?,?,?)', (plan_id, '3A-TS', 'TS_SCERT', 3, 'Mathematics', 'place value', 'curated', '{}', 'now'))
    db.execute('insert into checks values(?,?,?,?)', (check_id, plan_id, 'mcq', json.dumps({'questions': items})))
    db.execute('insert into papers(id,class_id,source,questions_json,confirmed,created_at) values(?,?,?,?,?,?)', (paper_id, '3A-TS', 'saathi_check', json.dumps(items), 1, 'now'))
    db.execute('insert into paper_checks values(?,?)', (paper_id, check_id))
    db.commit(); db.close()

    payload = [{'roll_no': 1, 'question_number': number, 'answer': 'A', 'mark': 1, 'max_marks': 1, 'edited': False} for number in range(1, 6)]
    confirmed = client_as_teacher.post(f'/api/papers/{paper_id}/results/confirm', json=payload)
    assert confirmed.status_code == 200, confirmed.text
    assert conn().execute('select 1 from insights where check_id=?', (check_id,)).fetchone()

    # The real Coach is intentionally replaced with a deterministic no-network result.
    assert FunctionModel(lambda messages, info: info.model_response(parts=[])) is not None
    monkeypatch.setattr('app.main.generate_next_steps', lambda check_id, teacher_id: {'check_id': check_id, 'next_steps': {'summary': 'Coach plan ready'}})
    response = client_as_teacher.post(f'/api/checks/{check_id}/next-steps')
    assert response.status_code == 200
    assert response.json()['next_steps']['summary'] == 'Coach plan ready'
