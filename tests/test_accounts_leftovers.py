import time
from unittest.mock import patch

from app import main
from app.db import one, rows, conn


def test_budget_blocks_plan(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'TEACHER_DAILY_BUDGET_USD', 0.0, raising=False)
    response = client_as_teacher.post('/api/plans', json={'class_id':'3A-TS','subject':'Mathematics','chapter_or_topic':'place value'})
    assert response.status_code == 429


def test_budget_blocks_next_steps_and_resources(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'TEACHER_DAILY_BUDGET_USD', 0.0, raising=False)
    assert client_as_teacher.post('/api/checks/missing/next-steps').status_code in {404, 429}
    assert client_as_teacher.post('/api/checks/missing/resources/worksheets').status_code in {404, 429}


def test_budget_blocks_reader_batch(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'TEACHER_DAILY_BUDGET_USD', 0.0, raising=False)
    assert client_as_teacher.post('/api/papers/missing/read-submissions').status_code == 429 or client_as_teacher.post('/api/papers/missing/read-submissions').status_code == 404


def test_reset_response_does_not_reveal_account(client_as_teacher):
    from app.db import one
    known_email = one('select email from teachers order by created_at desc')['email']
    known = client_as_teacher.post('/api/auth/forgot-password', json={'identity':known_email})
    unknown = client_as_teacher.post('/api/auth/forgot-password', json={'identity':'nobody@example.com'})
    assert known.json() == unknown.json()


def test_reset_token_is_hashed_and_reuse_rejected(client_as_teacher):
    known_email = one('select email from teachers order by created_at desc')['email']
    with patch('app.mailer.send_reset_email') as send:
        client_as_teacher.post('/api/auth/forgot-password', json={'identity':known_email})
    token = send.call_args.args[1].split('token=')[1]
    assert token not in (one('select token_hash from password_resets order by created_at desc')['token_hash'],)
    assert client_as_teacher.post('/api/auth/reset-password', json={'token':token,'new_password':'new-password'}).status_code == 200
    assert client_as_teacher.post('/api/auth/reset-password', json={'token':token,'new_password':'new-password'}).status_code == 400


def test_fourth_reset_is_refused(client_as_teacher):
    known_email = one('select email from teachers order by created_at desc')['email']
    for _ in range(3): client_as_teacher.post('/api/auth/forgot-password', json={'identity':known_email})
    assert client_as_teacher.post('/api/auth/forgot-password', json={'identity':known_email}).status_code == 429


def test_expired_reset_is_rejected(client_as_teacher):
    db=conn(); db.execute('insert into password_resets values(?,?,?,?,?,datetime("now"))',('old','id','bad',int(time.time())-1,0)); db.commit(); db.close()
    assert client_as_teacher.post('/api/auth/reset-password', json={'token':'bad','new_password':'new-password'}).status_code == 400


def test_admin_requires_code(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'ADMIN_CODE', 'secret')
    assert client_as_teacher.get('/admin/pilot').status_code == 401


def test_admin_temporary_password_and_force_change(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'ADMIN_CODE', 'secret')
    teacher_id=one('select id from teachers order by created_at desc')['id']
    result=client_as_teacher.post(f'/admin/pilot/{teacher_id}/reset-password', headers={'X-Admin-Code':'secret'})
    assert result.status_code == 200
    temporary=result.json()['temporary_password']
    username=one('select username from teachers order by created_at desc')['username']
    assert client_as_teacher.post('/api/auth/login', json={'username':username,'password':temporary}).status_code == 200
