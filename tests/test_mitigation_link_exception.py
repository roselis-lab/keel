"""MitigationLink.exception — a rare, optional carve-out where one specific control
doesn't apply to one specific threat (the threat itself stays live). Distinct from a
threat's own `reachability`, which rules out the whole threat.
"""
from fastapi.testclient import TestClient

from keel.main import app
from keel.schemas.threat import MitigationLink, Threat
from keel.store import Store, set_store

THREAT = {
    "id": "T-EXC-TEST",
    "title": "Exception test threat",
    "harm": "code-execution",
    "weaknesses": [
        {"component": "tool", "text": "a recognizable architectural weakness", "nature": "targeted"}
    ],
    "reachability": "NOT applicable if the tool has no valuable access",
}
MITIGATION = {
    "id": "CTRL-EXC-TEST",
    "name": "Exception test control",
    "mitigation_class": "gating_control",
}


def test_mitigation_link_exception_defaults_to_none():
    link = MitigationLink(id="CTRL-X", strength="gating", rationale="blocks it")
    assert link.exception is None


def test_mitigation_link_accepts_exception():
    link = MitigationLink(id="CTRL-X", strength="gating", rationale="blocks it", exception="not relevant if X")
    assert link.exception == "not relevant if X"


def test_threat_carries_mitigation_exception():
    t = Threat(
        id="T-X", title="Sensitive data disclosure", harm="data-exposed",
        weaknesses=[{"component": "tool", "text": "returns raw records with no scoping"}],
        reachability="NOT applicable if the model sees no secrets",
        mitigations=[{"id": "CTRL-DLP", "strength": "soft", "rationale": "lowers likelihood", "exception": "narrow case"}],
    )
    assert t.mitigations[0].exception == "narrow case"


def _temp_store(tmp_path) -> Store:
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    return Store(tmp_path)


def test_route_link_mitigation_with_exception_round_trips(tmp_path):
    set_store(_temp_store(tmp_path))
    try:
        client = TestClient(app)
        assert client.post("/threats", json=THREAT).status_code in (200, 201)
        assert client.post("/mitigations", json=MITIGATION).status_code in (200, 201)

        r = client.put(
            f"/threats/{THREAT['id']}/mitigations/{MITIGATION['id']}",
            json={"strength": "gating", "rationale": "blocks it", "exception": "narrow architectural case"},
        )
        assert r.status_code == 200, r.text

        got = client.get(f"/threats/{THREAT['id']}").json()
        link = got["mitigations"][0]
        assert link["exception"] == "narrow architectural case"

        # Updating without exception clears it (upsert semantics match strength/rationale).
        r2 = client.put(
            f"/threats/{THREAT['id']}/mitigations/{MITIGATION['id']}",
            json={"strength": "gating", "rationale": "blocks it"},
        )
        assert r2.status_code == 200, r2.text
        got2 = client.get(f"/threats/{THREAT['id']}").json()
        assert got2["mitigations"][0].get("exception") is None
    finally:
        set_store(None)
