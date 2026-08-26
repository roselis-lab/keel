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
        "surface": ["agent-environment"],
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
    """A threat with no weaknesses, no harm and no mitigation surfaces in every bucket."""
    store.threats["T-BAD"] = {"id": "T-BAD", "title": "Incomplete threat", "mitigations": []}
    result = await check_library_health()
    issues = result["issues"]
    assert "T-BAD" in issues["threats_missing_weaknesses"]
    assert "T-BAD" in issues["threats_missing_harm"]
    assert "T-BAD" in issues["threats_without_mitigation"]


@pytest.mark.asyncio
async def test_health_reports_mitigation_status_and_coverage_counts(store):
    store.mitigations["CTRL-A"] = {
        "id": "CTRL-A", "name": "A", "mitigation_class": "gating_control", "status": "draft",
        "implementations": [],
    }
    store.mitigations["CTRL-B"] = {
        "id": "CTRL-B", "name": "B", "mitigation_class": "gating_control", "status": "verified",
        "implementations": [{"title": "t", "description": "d", "coverage": "local"}],
    }
    store.mitigations["CTRL-C"] = {
        "id": "CTRL-C", "name": "C", "mitigation_class": "gating_control", "status": "draft",
        "implementations": [
            {"title": "t1", "description": "d1", "coverage": "local"},
            {"title": "t2", "description": "d2", "coverage": "shared", "covers": "everything"},
        ],
    }
    result = await check_library_health()
    assert result["mitigation_status_counts"] == {"draft": 2, "verified": 1, "unset": 0}
    assert result["implementation_coverage_counts"] == {"shared": 1, "local_only": 1, "none": 1}


def test_route_health_warnings_ok():
    from fastapi.testclient import TestClient

    from keel.main import app

    client = TestClient(app)
    r = client.get("/health/warnings")
    assert r.status_code == 200
    assert isinstance(r.json()["warnings"], list)


@pytest.mark.asyncio
async def test_dangling_link_is_flagged(store):
    """A link to a missing mitigation is reported."""
    store.threats["T-DANGLE"] = {
        "id": "T-DANGLE",
        "title": "Links to nothing",
        "harm": "code-execution",
        "weaknesses": [{"component": "tool", "text": "weak", "nature": "targeted"}],
        "mitigations": [{"id": "CTRL-GHOST", "strength": "gating", "rationale": "n/a"}],
    }
    result = await check_library_health()
    assert "T-DANGLE::CTRL-GHOST" in result["issues"]["dangling_mitigation_links"]
