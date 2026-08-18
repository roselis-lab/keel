from fastapi.testclient import TestClient

from keel.main import app


def test_config_route_returns_repo_url():
    r = TestClient(app).get("/config")
    assert r.status_code == 200
    body = r.json()
    assert "repo_url" in body
    assert isinstance(body["repo_url"], str)
