from fastapi.testclient import TestClient

from keel.main import app

client = TestClient(app)

GOOD = {
    "id": "T-TMP", "title": "Sensitive data disclosure", "harm": "data-exposed",
    "weaknesses": [{"component": "tool", "text": "returns raw records with no scoping"}],
    "reachability": "NOT applicable if the model sees no secrets",
    "mitigations": [{"id": "CTRL-DLP", "strength": "soft", "rationale": "lowers likelihood"}],
}


def test_validate_returns_advice_not_error_for_all_soft():
    r = client.post("/api/threats/validate", json=GOOD)
    body = r.json()
    assert body["ok"] is True                 # structurally valid
    assert any("nothing closes this threat" in a["msg"] for a in body["advice"])


def test_validate_returns_structure_error_for_bad_harm():
    bad = {**GOOD, "harm": "oops"}
    body = client.post("/api/threats/validate", json=bad).json()
    assert body["ok"] is False
    assert any(e["field"] == "harm" for e in body["errors"])
