from app import main

def payload():
    return {'rating':5,'teach_decision':'yes','usual_time':'15_30','saathi_minutes':12,'comment':'Useful','teacher_name':'A'}

def test_feedback_valid_and_owned(client_as_teacher):
    response=client_as_teacher.post('/api/feedback',json=payload()); assert response.status_code==200

def test_feedback_validation(client_as_teacher):
    assert client_as_teacher.post('/api/feedback',json={**payload(),'rating':6}).status_code==422
    assert client_as_teacher.post('/api/feedback',json={**payload(),'comment':'x'*501}).status_code==422

def test_feedback_requires_session():
    from fastapi.testclient import TestClient
    with TestClient(main.app) as client: assert client.post('/api/feedback',json=payload()).status_code==401
