"""CRUD REST endpoints for the browse UI.

Write tests point the global store at a TEMP catalog (via `set_store`) so they never
touch the real `catalog/*.yaml`; each resets the store in a `finally`. The read-only
health test runs against whatever the real store loads and writes nothing.
"""
from fastapi.testclient import TestClient

from keel.main import app
from keel.store import Store, set_store

THREAT = {
    "id": "T-CRUD-TEST",
    "title": "CRUD test threat",
    "harm": "code-execution",
    "weaknesses": [
        {"component": "tool", "text": "a recognizable architectural weakness", "nature": "targeted"}
    ],
    "reachability": "NOT applicable if the tool has no valuable access",
}
MITIGATION = {
    "id": "CTRL-CRUD-TEST",
    "name": "CRUD test control",
    "mitigation_class": "gating_control",
}


def _temp_store(tmp_path) -> Store:
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    return Store(tmp_path)


def test_create_threat_then_get(tmp_path):
    set_store(_temp_store(tmp_path))
    try:
        client = TestClient(app)
        r = client.post("/threats", json=THREAT)
        assert r.status_code in (200, 201), r.text
        assert r.json()["success"] is True

        got = client.get(f"/threats/{THREAT['id']}")
        assert got.status_code == 200
        assert got.json()["id"] == THREAT["id"]

        dup = client.post("/threats", json=THREAT)
        assert dup.status_code == 409
    finally:
        set_store(None)


def test_delete_threat(tmp_path):
    set_store(_temp_store(tmp_path))
    try:
        client = TestClient(app)
        assert client.post("/threats", json=THREAT).status_code in (200, 201)

        d = client.delete(f"/threats/{THREAT['id']}")
        assert d.status_code == 200, d.text
        assert d.json()["success"] is True

        assert client.get(f"/threats/{THREAT['id']}").status_code == 404
        assert client.delete("/threats/T-DOES-NOT-EXIST").status_code == 404
    finally:
        set_store(None)


def test_create_and_delete_mitigation(tmp_path):
    set_store(_temp_store(tmp_path))
    try:
        client = TestClient(app)
        r = client.post("/mitigations", json=MITIGATION)
        assert r.status_code in (200, 201), r.text
        assert r.json()["success"] is True

        got = client.get(f"/mitigations/{MITIGATION['id']}")
        assert got.status_code == 200
        assert got.json()["id"] == MITIGATION["id"]

        dup = client.post("/mitigations", json=MITIGATION)
        assert dup.status_code == 409

        d = client.delete(f"/mitigations/{MITIGATION['id']}")
        assert d.status_code == 200, d.text
        assert d.json()["success"] is True
        assert client.get(f"/mitigations/{MITIGATION['id']}").status_code == 404
        assert client.delete(f"/mitigations/{MITIGATION['id']}").status_code == 404
    finally:
        set_store(None)


def test_health_library_read_only():
    # Uses the real store, read-only; writes nothing to the catalog.
    set_store(None)
    client = TestClient(app)
    r = client.get("/health/library")
    assert r.status_code == 200
    body = r.json()
    assert "stats" in body
    assert "issues" in body
