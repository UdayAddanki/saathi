from app import main
from app.db import one

def test_setup_complete_is_persisted(client_as_teacher):
    assert client_as_teacher.get('/api/auth/me').json()['setup_complete'] == 0
    assert client_as_teacher.post('/api/auth/setup-complete').status_code == 200
    assert client_as_teacher.get('/api/auth/me').json()['setup_complete'] == 1

def test_admin_list_and_csv_require_code(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'ADMIN_CODE', 'admin-test')
    assert client_as_teacher.get('/admin/pilot').status_code == 401
    response = client_as_teacher.get('/admin/pilot', headers={'X-Admin-Code':'admin-test'})
    assert response.status_code == 200 and 'teachers' in response.json()
    csv = client_as_teacher.get('/admin/pilot.csv', headers={'X-Admin-Code':'admin-test'})
    assert csv.status_code == 200 and 'username' in csv.text

def test_admin_reset_sets_force_change(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'ADMIN_CODE', 'admin-test')
    teacher_id = one('select id from teachers order by created_at desc')['id']
    response = client_as_teacher.post(f'/admin/pilot/{teacher_id}/reset-password', headers={'X-Admin-Code':'admin-test'})
    assert response.status_code == 200 and response.json()['temporary_password']
    assert one('select force_password_change from teachers where id=?', (teacher_id,))['force_password_change'] == 1
