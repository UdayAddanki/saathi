from fastapi.testclient import TestClient
from app.main import app

def test_reset_page_serves_reset_form():
    with TestClient(app) as client:
        response = client.get('/reset?token=example')
    assert response.status_code == 200
    assert 'id="reset-screen"' in response.text
    assert 'id="reset-password"' in response.text
