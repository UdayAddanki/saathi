from pathlib import Path

from app.config import find_portkey_key


def test_repo_env_wins(tmp_path: Path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / '.env').write_text('PORTKEY_API_KEY=local-secret\n')
    (tmp_path / '.env').write_text('PORTKEY_API_KEY=parent-secret\n')
    try:
        assert find_portkey_key(repo) == 'local-secret'
    finally:
        (tmp_path / '.env').unlink(missing_ok=True)


def test_parent_env_is_fallback(tmp_path: Path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    (tmp_path / '.env').write_text('PORTKEY_API_KEY=parent-secret\n')
    try:
        assert find_portkey_key(repo) == 'parent-secret'
    finally:
        (tmp_path / '.env').unlink(missing_ok=True)


def test_app_can_start_without_a_key():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        assert client.get('/api/health').status_code == 200
