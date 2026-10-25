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
