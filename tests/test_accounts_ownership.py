import pytest
from fastapi.testclient import TestClient

from app.main import app


def signup(client, username):
    response = client.post('/api/auth/signup', json={'username': username, 'password': 'strong-pass-123', 'email': f'{username}@example.com', 'consent': True})
    assert response.status_code == 200


def test_teacher_ownership_for_class_and_unknown_id():
    with TestClient(app) as teacher_a, TestClient(app) as teacher_b:
        signup(teacher_a, 'teacher-a'); created = teacher_a.post('/api/classes', json={'board':'NCERT','grade':3,'section':'A','class_size':3,'period_minutes':40,'resources':[]}); class_id = created.json()['id']
        signup(teacher_b, 'teacher-b')
        assert teacher_a.get(f'/api/classes/{class_id}').status_code == 200
        assert teacher_b.get(f'/api/classes/{class_id}').status_code == 404
        assert teacher_b.get('/api/classes/not-a-real-class').status_code == 404


def concrete(path):
    return path.replace('{class_id}', 'unknown-class').replace('{plan_id}', 'unknown-plan').replace('{check_id}', 'unknown-check').replace('{paper_id}', 'unknown-paper')

@pytest.mark.parametrize('route', [route for route in app.routes if getattr(route, 'path', '').startswith('/api/') and route.path not in {'/api/health', '/api/auth/signup', '/api/auth/login'}], ids=lambda r: f'{sorted(r.methods)[0]} {r.path}')
def test_every_protected_api_route_requires_a_session(route):
    with TestClient(app) as client:
        method = sorted(route.methods)[0]
        response = client.request(method, concrete(route.path), json={})
        assert response.status_code == 401, route.path
