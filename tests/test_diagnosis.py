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
    db.execute('insert into lesson_plans values(?,?,?,?,?,?,?,?,?)', (lesson_id, '3A-TS', 'TS_SCERT', 3, 'Mathematics', 'place value', 'curated', '{}', 'now'))
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
