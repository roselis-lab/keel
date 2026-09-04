"""A control that presupposes another one.

Two layers, kept apart. A prerequisite that cannot mean anything - it does not exist,
points at itself, or closes a loop - is refused on the way in and never reaches disk.
A prerequisite that is simply not being asked for alongside its dependant is advice,
because the assessor may have a reason and a half-written draft trips it constantly.
"""
import pytest
import yaml

import keel.config
from keel.mcp import tools as _tools  # noqa: F401
from keel.mcp.registry import dispatch_tool
from keel.services import report_service
from keel.store import Store, set_store


@pytest.fixture
def store(catalog_dir):
    s = Store(catalog_dir(mitigations=[
        {"id": "CTRL-TRACE", "mitigation_class": "evidential_mitigation"},
        {"id": "CTRL-MEM", "mitigation_class": "evidential_mitigation"},
        {"id": "CTRL-OTHER", "mitigation_class": "detector"},
    ]))
    set_store(s)
    yield s
    set_store(None)


# --------------------------------------------------------------------------- #
# Layer one: refused on write
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_a_real_prerequisite_is_recorded(store):
    result = await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-MEM", "fields": {"requires": ["CTRL-TRACE"]}})
    assert result["success"] is True
    assert store.mitigations["CTRL-MEM"]["requires"] == ["CTRL-TRACE"]
    assert (await dispatch_tool("get_mitigation",
                                {"mitigation_id": "CTRL-MEM"}))["requires"] == ["CTRL-TRACE"]


@pytest.mark.asyncio
async def test_a_prerequisite_that_does_not_exist_is_refused(store):
    result = await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-MEM", "fields": {"requires": ["CTRL-GHOST"]}})
    assert result["success"] is False
    assert "CTRL-GHOST" in result["error"]
    assert not store.mitigations["CTRL-MEM"].get("requires")


@pytest.mark.asyncio
async def test_a_card_cannot_require_itself(store):
    result = await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-MEM", "fields": {"requires": ["CTRL-MEM"]}})
    assert result["success"] is False
    assert "itself" in result["error"]


@pytest.mark.asyncio
async def test_a_cycle_is_refused(store):
    """Neither control can be verified first, so the pair means nothing."""
    await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-TRACE", "fields": {"requires": ["CTRL-OTHER"]}})
    result = await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-OTHER", "fields": {"requires": ["CTRL-TRACE"]}})
    assert result["code"] == "integrity"
    assert "leads back to CTRL-OTHER" in result["error"]
    assert "cycle" in result["hint"]


@pytest.mark.asyncio
async def test_a_longer_cycle_is_refused_too(store):
    await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-TRACE", "fields": {"requires": ["CTRL-OTHER"]}})
    await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-MEM", "fields": {"requires": ["CTRL-TRACE"]}})
    result = await dispatch_tool("update_mitigation", {
        "mitigation_id": "CTRL-OTHER", "fields": {"requires": ["CTRL-MEM"]}})
    assert result["code"] == "integrity"
    assert "cycle" in result["hint"]


@pytest.mark.asyncio
async def test_create_is_guarded_the_same_way(store):
    result = await dispatch_tool("create_mitigation", {
        "mitigation_id": "CTRL-NEW",
        "fields": {"name": "New", "mitigation_class": "process", "requires": ["CTRL-GHOST"]}})
    assert result["success"] is False
    assert "CTRL-NEW" not in store.mitigations


# --------------------------------------------------------------------------- #
# Layer two: advice on an assessment
# --------------------------------------------------------------------------- #
def _report(requirements):
    return {
        "system_id": "demo", "system_name": "Demo", "system_description": "A system.",
        "date": "2026-08-30", "assessor": "T <t@example.com>", "status": "draft",
        "findings": [{
            "id": "T-X", "from_catalog": False,
            "scenario": "Something goes wrong in a way a reader can picture.",
            "source": {"who": "external-attacker", "motive": "money", "access": "the chat"},
            "asset": "records", "attack_surface": "user-input",
            "vulnerability": "no scoping", "exploitation_complexity": "low",
            "harm": "data-exposed",
            "risk": {"likelihood": "high", "severity": "high", "reasoning": "Reachable."},
            "delta": "new", "requirements": requirements,
        }],
    }


@pytest.fixture
def reports(store, tmp_path, monkeypatch):
    store.mitigations["CTRL-MEM"]["requires"] = ["CTRL-TRACE"]
    d = tmp_path / "reports"
    (d / "demo").mkdir(parents=True)
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(d))
    return d


def _seed(d, payload):
    (d / "demo" / "2026-08-30.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_asking_for_a_control_without_its_prerequisite_is_advised(reports):
    payload = _report([{"mitigation_id": "CTRL-MEM",
                        "coverage_status": "needs_implementation"}])
    _seed(reports, payload)
    result = report_service.save_report("demo", "2026-08-30", payload)

    assert result["success"] is True          # advice never blocks
    assert "CTRL-TRACE" in result["advice"][0]


def test_asking_for_both_is_quiet(reports):
    payload = _report([
        {"mitigation_id": "CTRL-MEM", "coverage_status": "needs_implementation"},
        {"mitigation_id": "CTRL-TRACE", "coverage_status": "needs_implementation"},
    ])
    _seed(reports, payload)
    assert report_service.save_report("demo", "2026-08-30", payload)["advice"] == []


def test_a_requirement_dropped_from_the_hand_off_does_not_count_as_asked(reports):
    """`included: false` means the product team never sees it, so it cannot satisfy
    another control's prerequisite."""
    payload = _report([
        {"mitigation_id": "CTRL-MEM", "coverage_status": "needs_implementation"},
        {"mitigation_id": "CTRL-TRACE", "coverage_status": "needs_implementation",
         "included": False},
    ])
    _seed(reports, payload)
    result = report_service.save_report("demo", "2026-08-30", payload)
    assert "CTRL-TRACE" in result["advice"][0]
