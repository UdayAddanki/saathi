import os
import tempfile
from pathlib import Path
import pytest

# Test processes never open the developer's real database. This is set while
# conftest is imported, before app.db reads SAATHI_DB_PATH.
TEST_DB_DIR = Path(tempfile.mkdtemp(prefix='saathi-tests-'))
os.environ['SAATHI_DB_PATH'] = str(TEST_DB_DIR / 'test.db')

@pytest.fixture
def client_as_teacher():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        username = f'test-{next(_names)}'
        response = client.post('/api/auth/signup', json={'username': username, 'password': 'strong-pass-123', 'email': f'{username}@example.com', 'consent': True})
        assert response.status_code == 200, response.text
        from app.db import conn
        db = conn()
        teacher_id = db.execute('select id from teachers where username=?', (username,)).fetchone()[0]
        db.execute('delete from classes where id=?', ('3A-TS',))
        db.execute('insert into classes(id,name,board,grade,section,class_size,period_minutes,resources_json,teacher_id) values(?,?,?,?,?,?,?,?,?)', ('3A-TS', '3A', 'TS_SCERT', 3, 'A', 3, 40, '[]', teacher_id))
        db.commit()
        db.close()
        yield client

_names = iter(range(100000))
