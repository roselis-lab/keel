"""Failures are typed, and each edge translates them once.

Services used to return `{"success": False, "error": "..."}` and every caller worked out
the kind by reading the sentence - the REST layer branched on `if "already has" in
result["error"]`, so rewording a message silently changed an HTTP status. These tests
pin the contract that replaced it: the kind carries the status, and the payload carries
enough for a caller to fix the call without another round trip.
"""
import pytest
from fastapi.testclient import TestClient

from keel.errors import Conflict, Invalid, NotFound, invalid_from_pydantic
from keel.main import app
from keel.mcp import tools as _tools  # noqa: F401
from keel.mcp.registry import dispatch_tool
from keel.schemas.threat import Threat
from keel.store import Store, set_store


@pytest.fixture
def store(catalog_dir):
    s = Store(catalog_dir(
        threats=[{"id": "T-DATA-LEAK"}],
        mitigations=[{"id": "CTRL-ACCESS", "mitigation_class": "gating_control"}],
    ))
    set_store(s)
    yield s
    set_store(None)


# --------------------------------------------------------------------------- #
# The kinds carry their own status
# --------------------------------------------------------------------------- #
def test_each_kind_maps_to_one_status():
    assert NotFound("x").status == 404
    assert Conflict("x").status == 409
    assert Invalid("x").status == 422


def test_the_payload_drops_what_it_does_not_have():
    """A simple failure stays a short answer."""
    assert NotFound("gone").as_dict() == {
        "success": False, "code": "not_found", "error": "gone"}


def test_pydantic_errors_arrive_whole():
    """Flattening three bad fields into one sentence costs three round trips to fix."""
    try:
        Threat(id="T-X")
    except Exception as exc:  # noqa: BLE001 - the point is the conversion
        err = invalid_from_pydantic(exc)
    assert len(err.details) > 1
    assert all("field" in d and "message" in d for d in err.details)
    assert "fields are invalid" in err.message


# --------------------------------------------------------------------------- #
# HTTP: one handler, no branches in the routes
# --------------------------------------------------------------------------- #
def test_http_translates_the_kind_to_the_status(store):
    client = TestClient(app)
    assert client.get("/api/threats/T-GHOST").status_code == 404
    assert client.get("/api/mitigations/CTRL-GHOST").status_code == 404


def test_http_returns_the_structured_body_not_just_a_sentence(store):
    body = TestClient(app).get("/api/threats/T-GHOST").json()
    assert body["code"] == "not_found"
    assert body["entity_type"] == "threat"
    assert body["entity_id"] == "T-GHOST"
    assert body["hint"]


# --------------------------------------------------------------------------- #
# MCP: the same failure, shaped for a model
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_a_near_miss_id_is_answered_with_the_real_one(store):
    """An error that only rejects makes the caller guess again; one that names the id
    they almost typed ends it in a turn."""
    result = await dispatch_tool("get_threat", {"threat_id": "T-DATA-LEEK"})
    assert result["code"] == "not_found"
    assert "T-DATA-LEAK" in result["hint"]


@pytest.mark.asyncio
async def test_an_id_with_no_near_miss_points_at_search(store):
    result = await dispatch_tool("get_mitigation", {"mitigation_id": "ZZZZ-NOPE"})
    assert "search" in result["hint"]


@pytest.mark.asyncio
async def test_linking_a_missing_control_is_an_integrity_error_not_a_not_found(store):
    """The threat is fine and the call is well formed; what is wrong is the pair."""
    result = await dispatch_tool("add_threat_mitigation", {
        "threat_id": "T-DATA-LEAK", "mitigation_id": "CTRL-GHOST",
        "strength": "gating", "rationale": "would block it"})
    assert result["code"] == "integrity"
    assert result["field"] == "mitigation_id"


@pytest.mark.asyncio
async def test_a_bad_grade_says_what_the_grades_are(store):
    result = await dispatch_tool("add_threat_mitigation", {
        "threat_id": "T-DATA-LEAK", "mitigation_id": "CTRL-ACCESS",
        "strength": "strong", "rationale": "x"})
    assert result["code"] == "invalid"
    assert "gating" in result["hint"] and "soft" in result["hint"]


@pytest.mark.asyncio
async def test_a_duplicate_id_says_which_call_to_make_instead(store):
    result = await dispatch_tool("create_threat", {"threat_id": "T-DATA-LEAK", "fields": {
        "title": "Again", "harm": "downtime",
        "weaknesses": [{"component": "tool", "text": "x"}], "reachability": "y"}})
    assert result["code"] == "conflict"
    assert "update_threat" in result["hint"]


@pytest.mark.asyncio
async def test_unlinking_something_that_is_not_linked_lists_what_is(store):
    await dispatch_tool("add_threat_mitigation", {
        "threat_id": "T-DATA-LEAK", "mitigation_id": "CTRL-ACCESS",
        "strength": "gating", "rationale": "blocks it"})
    result = await dispatch_tool("remove_threat_mitigation", {
        "threat_id": "T-DATA-LEAK", "mitigation_id": "CTRL-GHOST"})
    assert result["code"] == "not_found"
    assert "CTRL-ACCESS" in result["hint"]


@pytest.mark.asyncio
async def test_a_service_failure_never_escapes_as_a_traceback(store):
    """A tool that raises kills the turn. Every KeelError has to come back as a payload."""
    for name, args in (
        ("get_threat", {"threat_id": "nope"}),
        ("update_threat", {"threat_id": "nope", "fields": {"harm": "downtime"}}),
        ("delete_mitigation", {"mitigation_id": "nope", "confirm": True}),
        ("get_report", {"system_id": "nope", "date": "2026-01-01"}),
    ):
        result = await dispatch_tool(name, args)
        assert result["success"] is False, name
        assert result["code"], name
