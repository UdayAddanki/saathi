import json
import uuid

from app.db import conn, init_db
from app.diagnosis import analyze_results


def make_check(check_type='mcq'):
    init_db()
    lesson_id = str(uuid.uuid4())
    check_id = str(uuid.uuid4())
    items = [{
        'concept_id': 'place-value',
        'stem': 'Value?',
        'options': {'A': '40', 'B': '4', 'C': '400', 'D': '44'},
        'correct_option': 'A',
        'option_errors': {'B': {'misconception_id': 'M-PV-02', 'description': 'digit value', 'ai_suggested': False}, 'C': {'misconception_id': 'M-PV-01', 'description': 'place', 'ai_suggested': False}, 'D': {'misconception_id': 'M-PV-01', 'description': 'whole', 'ai_suggested': False}},
    }]
    db = conn()
    db.execute('insert into lesson_plans(id,class_id,board,grade,subject,chapter_or_topic,mode,plan_json,created_at) values(?,?,?,?,?,?,?,?,?)', (lesson_id, '3A-TS', 'TS_SCERT', 3, 'Mathematics', 'place value', 'curated', '{}', 'now'))
    db.execute('insert into checks values(?,?,?,?)', (check_id, lesson_id, check_type, json.dumps(items * 5)))
    db.commit()
    return db, check_id


def test_diagnosis_groups_absent_and_top_error():
    db, check_id = make_check()
    patterns = {1: ['A'] * 5, 2: ['A'] * 5, 3: ['A'] * 5, 4: ['A'] * 5, 5: ['A', 'A', 'B', 'B', 'C'], 6: ['A', 'A', 'B', 'B', 'C'], 7: ['B'] * 5, 8: ['absent'] * 5}
    for roll, answers in patterns.items():
        for item_index, answer in enumerate(answers):
            db.execute('insert into responses(check_id,roll_no,item_index,chosen_option,check_mode) values(?,?,?,?,?)', (check_id, roll, item_index, answer, 'each_child'))
    db.commit(); db.close()
    insight = analyze_results(check_id)
    assert len(insight.groups['ready']) == 4
    assert len(insight.groups['practice']) == 2
    assert len(insight.groups['reteach']) == 1
    assert insight.missed_lesson == [{'roll_no': 8}]
    assert insight.top_errors[0]['count'] == 3


def test_class_count_and_prerequisite_flag():
    db, check_id = make_check()
    db.execute('insert into responses(check_id,item_index,check_mode,class_counts_json) values(?,?,?,?)', (check_id, 0, 'class_count', json.dumps({str(i): {'A': 2, 'B': 8, 'C': 0, 'D': 0} for i in range(5)})))
    db.commit(); db.close()
    insight = analyze_results(check_id)
    assert insight.check_mode == 'class_count'
    assert insight.concepts[0]['percent_correct'] == 20
    assert 'whole_class_reteach' in insight.recommended_actions
    assert insight.groups == {'ready': [], 'practice': [], 'reteach': []}

def test_confirmed_paper_diagnosis_is_persisted():
    db, check_id = make_check()
    paper_id = str(uuid.uuid4())
    db.execute('insert into papers(id,class_id,source,questions_json,confirmed,created_at) values(?,?,?,?,?,?)', (paper_id, '3A-TS', 'saathi_check', json.dumps(json.loads(db.execute('select items_json from checks where id=?', (check_id,)).fetchone()[0])), 1, 'now'))
    db.execute('insert into paper_checks values(?,?)', (paper_id, check_id))
    for roll in (1, 2):
        for question in range(1, 6):
            db.execute('insert into results values(?,?,?,?,?,?,?)', (paper_id, roll, question, 1 if roll == 1 else 0, 1, 1, 0))
            db.execute('insert into responses(check_id,roll_no,item_index,chosen_option,check_mode) values(?,?,?,?,?)', (check_id, roll, question - 1, 'A' if roll == 1 else 'B', 'each_child'))
    for roll in (1, 2):
        db.execute('insert or replace into students(class_id,roll_no,first_name,readiness_level,updated_at) values(?,?,?,?,?)', ('3A-TS', roll, f'Child{roll}', 'mid', None))
    db.commit(); db.close()
    insight = analyze_results(check_id)
    saved = conn().execute('select insight_json from insights where check_id=?', (check_id,)).fetchone()
    assert saved is not None
    assert json.loads(saved[0])['check_id'] == check_id
    assert insight.groups['ready']
