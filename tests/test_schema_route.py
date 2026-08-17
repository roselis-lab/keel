from fastapi.testclient import TestClient

from keel.main import app


def test_schema_endpoint_returns_threat_schema():
    client = TestClient(app)
    r = client.get("/schema/threat")
    assert r.status_code == 200
    assert r.json()["properties"]["harm"]["enum"][0] == "wrong-decision"


def test_schema_endpoint_unknown_entity_404():
    client = TestClient(app)
    assert client.get("/schema/nope").status_code == 404
