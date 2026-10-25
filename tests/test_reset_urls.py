from unittest.mock import patch

from app import main
from app.db import one


def reset_link(client, headers=None):
    email = one('select email from teachers order by created_at desc')['email']
    with patch('app.mailer.send_reset_email') as send:
        response = client.post('/api/auth/forgot-password', json={'identity': email}, headers=headers or {})
    assert response.status_code == 200
    return send.call_args.args[1]


def test_reset_url_uses_configured_app_url(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'APP_URL', 'https://saathi.example')
    assert reset_link(client_as_teacher).startswith('https://saathi.example/reset?token=')


def test_reset_url_uses_request_host_when_unconfigured(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'APP_URL', '')
    assert reset_link(client_as_teacher).startswith('http://testserver/reset?token=')


def test_reset_url_uses_forwarded_https(client_as_teacher, monkeypatch):
    monkeypatch.setattr(main, 'APP_URL', '')
    link = reset_link(client_as_teacher, {'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': 'school.example'})
    assert link.startswith('https://school.example/reset?token=')
