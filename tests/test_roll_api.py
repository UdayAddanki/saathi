from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


FIXTURES = Path(__file__).parent / 'fixtures' / 'class_roll'


@pytest.mark.parametrize('filename', ['class_roll_3A_valid.xlsx', 'class_roll_3A_valid.csv'])
def test_roll_upload_save_and_reload(filename):
    with TestClient(app) as client:
        created = client.post('/api/classes', json={
            'board': 'TS_SCERT', 'grade': 3, 'section': filename[-5],
            'class_size': 38, 'period_minutes': 40, 'resources': [],
        })
        assert created.status_code == 200
        class_id = created.json()['id']
        path = FIXTURES / filename
        with path.open('rb') as uploaded:
            preview_response = client.post(
                f'/api/classes/{class_id}/roll/upload',
                files={'file': (filename, uploaded, 'application/octet-stream')},
            )
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert preview['valid'] is True
        assert len(preview['rows']) == 38
        saved = client.post(f'/api/classes/{class_id}/roll/save', json=preview['rows'])
        assert saved.status_code == 200
        loaded = client.get(f'/api/classes/{class_id}/roll').json()
        assert {level: sum(row['readiness_level'] == level for row in loaded)
                for level in ('low', 'mid', 'high')} == {'low': 10, 'mid': 16, 'high': 12}
        assert loaded[1]['roll_no'] == 2 and loaded[1]['first_name'] == 'Bhavya' and loaded[1]['readiness_level'] == 'mid'
        changed = [dict(row) for row in preview['rows']]
        changed[1]['readiness_level'] = 'high'
        assert client.post(f'/api/classes/{class_id}/roll/save', json=changed).status_code == 200
        moved = client.get(f'/api/classes/{class_id}/roll').json()[1]
        assert moved['roll_no'] == 2 and moved['readiness_level'] == 'high'


def test_roll_save_reports_empty_and_duplicate_roll_numbers():
    with TestClient(app) as client:
        created = client.post('/api/classes', json={'board': 'NCERT', 'grade': 3, 'section': 'Z', 'class_size': 2, 'period_minutes': 40, 'resources': []})
        class_id = created.json()['id']
        empty = client.post(f'/api/classes/{class_id}/roll/save', json=[])
        assert empty.status_code == 422
        assert 'Choose a file and press Preview' in empty.json()['detail']
        duplicate = client.post(f'/api/classes/{class_id}/roll/save', json=[
            {'roll_no': 12, 'first_name': 'A', 'readiness_level': 'low'},
            {'roll_no': 12, 'first_name': 'B', 'readiness_level': 'mid'},
        ])
        assert duplicate.status_code == 422
        assert 'Duplicate roll number 12' in duplicate.json()['detail']
