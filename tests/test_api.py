from fastapi.testclient import TestClient

from app.main import app


def test_public_api_and_class_creation():
    with TestClient(app) as client:
        health = client.get('/api/health')
        assert health.status_code == 200
        boards = client.get('/api/boards').json()
        assert len(boards['boards']) == 2
        assert client.get('/api/classes').status_code == 200
        created = client.post('/api/classes', json={
            'board': 'NCERT', 'grade': 2, 'section': 'T',
            'class_size': 3, 'period_minutes': 35, 'resources': ['chalkboard'],
        })
        assert created.status_code == 200


def test_usage_is_a_summary():
    with TestClient(app) as client:
        usage = client.get('/api/usage').json()
        assert 'totals' in usage
        assert 'per_agent' in usage
        assert 'recent_runs' in usage
