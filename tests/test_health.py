"""Health and stats checks over the file store.

Builds an isolated store on a temp catalog directory and exercises the same service
functions the MCP `get_stats` / `check_library_health` tools call.
"""
import pytest

from keel.services.health_service import check_library_health, get_stats
from keel.store import Store, set_store


@pytest.fixture
def store(tmp_path):
    """A fresh, empty store pointed at a temp catalog; installed as the global store."""
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    s = Store(tmp_path)
    set_store(s)
    yield s
    set_store(None)


@pytest.mark.asyncio
async def test_get_stats_counts_records(store):
    """Counts track the records actually present."""
    store.mitigations["M-DEMO"] = {
        "id": "M-DEMO", "name": "Demo control", "mitigation_class": "gating_control",
    }
    store.threats["T-DEMO"] = {
        "id": "T-DEMO",
        "title": "Demo threat",
        "harm": "code-execution",
        "surface": ["tool-output"],
        "source": ["external-attacker"],
        "weaknesses": [{"component": "tool", "text": "a recognizable architectural weakness", "nature": "targeted"}],
        "reachability": "NOT applicable if the tool has no valuable access",
        "mitigations": [{"id": "M-DEMO", "strength": "gating", "rationale": "blocks the path"}],
    }
    assert await get_stats() == {
        "threats": 1,
        "mitigations": 1,
        "threat_mitigation_links": 1,
    }


@pytest.mark.asyncio
async def test_check_library_health_flags_gaps(store):
    """A threat missing the pieces that make it a threat is reported field by field, by
    the same rules a write would have reported."""
    store.threats["T-BAD"] = {"id": "T-BAD", "title": "Incomplete threat", "mitigations": []}
    result = await check_library_health()
    fields = {f["field"] for f in result["errors"]
              if f["entity_id"] == "T-BAD" and f["code"] == "threat_incomplete"}
    assert fields == {"harm", "reachability", "weaknesses"}


@pytest.mark.asyncio
async def test_health_reports_implementation_coverage_counts(store):
    store.mitigations["CTRL-A"] = {
        "id": "CTRL-A", "name": "A", "mitigation_class": "gating_control",
        "implementations": [],
    }
    store.mitigations["CTRL-B"] = {
        "id": "CTRL-B", "name": "B", "mitigation_class": "gating_control",
        "implementations": [{"title": "t", "description": "d", "coverage": "local"}],
    }
    store.mitigations["CTRL-C"] = {
        "id": "CTRL-C", "name": "C", "mitigation_class": "gating_control",
        "implementations": [
            {"title": "t1", "description": "d1", "coverage": "local"},
            {"title": "t2", "description": "d2", "coverage": "shared", "covers": "everything"},
        ],
    }
    result = await check_library_health()
    assert result["implementation_coverage_counts"] == {"shared": 1, "local_only": 1, "none": 1}


def test_route_health_warnings_ok():
    from fastapi.testclient import TestClient

    from keel.main import app

    client = TestClient(app)
    r = client.get("/api/health/warnings")
    assert r.status_code == 200
    assert isinstance(r.json()["warnings"], list)


@pytest.mark.asyncio
async def test_dangling_link_is_a_hard_error_not_a_gap(store):
    """A link to a missing mitigation is an error, carrying the file and field that hold
    it — not a content gap. It is reported once, at one severity."""
    store.threats["T-DANGLE"] = {
        "id": "T-DANGLE",
        "title": "Links to nothing",
        "harm": "code-execution",
        "weaknesses": [{"component": "tool", "text": "weak", "nature": "targeted"}],
        "mitigations": [{"id": "CTRL-GHOST", "strength": "gating", "rationale": "n/a"}],
    }
    result = await check_library_health()
    hit = next(e for e in result["errors"]
               if e["entity_id"] == "T-DANGLE" and e["code"] == "dangling_link")
    assert hit["field"] == "mitigations.0.id"
    assert "CTRL-GHOST" in hit["message"]
    # The record itself loaded; what is wrong is the pair, so it is not a load problem.
    # Reported once: the record loaded, so nothing about it is a load problem.
    assert not [p for p in result["load_problems"] if p["entity_id"] == "T-DANGLE"]
