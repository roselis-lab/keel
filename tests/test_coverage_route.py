from fastapi.testclient import TestClient

from keel.main import app


def test_coverage_route_shape():
    r = TestClient(app).get("/api/style-guide/coverage")
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["overall"] <= 100
    assert any(e["entity_type"] == "threat" for e in body["entities"])
