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
        "impact_class": "decision-integrity",
        "vulnerability": ["a recognizable exploitation pattern"],
        "reachability": "not applicable if the attacker cannot influence the input",
        "mitigations": [{"mitigation_id": "M-DEMO", "rationale": "blocks the path"}],
    }
    assert await get_stats() == {
        "threats": 1,
        "mitigations": 1,
        "threat_mitigation_links": 1,
    }


@pytest.mark.asyncio
async def test_check_library_health_flags_gaps(store):
    """A threat with no facets and no mitigation surfaces in every relevant bucket."""
    store.threats["T-BAD"] = {"id": "T-BAD", "title": "Incomplete threat", "mitigations": []}
    result = await check_library_health()
    issues = result["issues"]
    assert "T-BAD" in issues["threats_missing_vulnerability"]
    assert "T-BAD" in issues["threats_missing_impact_class"]
    assert "T-BAD" in issues["threats_without_mitigation"]


@pytest.mark.asyncio
async def test_dangling_link_is_flagged(store):
    """A link to a missing mitigation is reported."""
    store.threats["T-DANGLE"] = {
        "id": "T-DANGLE",
        "title": "Links to nothing",
        "impact_class": "decision-integrity",
        "vulnerability": ["pattern"],
        "mitigations": [{"mitigation_id": "CTRL-GHOST", "rationale": "n/a"}],
    }
    result = await check_library_health()
    assert "T-DANGLE::CTRL-GHOST" in result["issues"]["dangling_mitigation_links"]
