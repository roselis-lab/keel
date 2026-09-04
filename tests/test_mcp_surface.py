"""The MCP surface: contract and behaviour.

MCP is the primary authoring interface, and until now it was the only layer with no
tests at all. That is how `batch_update_threats` wrote unvalidated values to disk for as
long as it did, and how `check_library_health` kept describing fields deleted in the v2
migration — a docstring is the description a connecting model reads to decide whether to
call a tool, so a stale one is a defect, not a typo.
"""
import json
import shutil
from pathlib import Path

import pytest

from keel.lib.style_guide import SERVER_INSTRUCTIONS, TOOL_ENTITY_TYPES
from keel.mcp import tools as _tools  # noqa: F401 — importing registers every tool
from keel.mcp.registry import TOOL_REGISTRY, dispatch_tool, get_tool_list
from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import Threat
from keel.store import Store, set_store

# Names deleted from the catalog schemas. A tool description that still uses one is
# telling a connecting model about a schema that has not existed for months. Report
# fields are excluded: `vulnerability`, `attack_surface` and `asset` are live there, and
# a report still has a `status`.
DEAD_FIELDS = ("impact_class", "mitigation_status", "assessor_dialogue")


@pytest.fixture
def store(catalog_dir):
    s = Store(catalog_dir(
        mitigations=[{"id": "CTRL-A", "mitigation_class": "gating_control"},
                     {"id": "CTRL-LOG", "mitigation_class": "detector"}],
        threats=[{"id": "T-A", "harm": "data-exposed"}],
    ))
    set_store(s)
    yield s
    set_store(None)


# --------------------------------------------------------------------------- #
# Contract: does the surface describe the schema that actually exists?
# --------------------------------------------------------------------------- #
def test_no_tool_description_names_a_field_that_no_longer_exists():
    live = set(Threat.model_fields) | set(MitigationCreate.model_fields)
    offenders = []
    for tool in get_tool_list():
        text = tool["description"].lower()
        for dead in DEAD_FIELDS:
            if dead in live:
                continue
            if dead in text:
                offenders.append((tool["name"], dead))
    assert offenders == [], offenders


def test_every_catalog_field_is_reachable_through_a_write_tool():
    """MCP is the primary authoring interface. A field it cannot write is a field the
    catalog cannot be finished in — nine of the mitigation card's sixteen were once
    unreachable, which made a complete card impossible to author here."""
    from keel.mcp.tools.mitigations import MITIGATION_FIELDS
    from keel.mcp.tools.threats import THREAT_FIELDS

    threat_named = {f.strip() for f in THREAT_FIELDS.split(",")}
    mitigation_named = {f.strip() for f in MITIGATION_FIELDS.split(",")}

    # `mitigations` is deliberately absent: links are managed by their own tools.
    assert set(Threat.model_fields) - {"id", "mitigations"} <= threat_named
    assert set(MitigationCreate.model_fields) - {"id"} <= mitigation_named


def test_write_tools_stay_under_the_parameter_limit():
    """Models start mis-filling arguments past roughly eight parameters, which is why
    the field-heavy writes take a `fields` map instead of one argument per field."""
    for tool in get_tool_list():
        count = len(tool["inputSchema"].get("properties", {}))
        assert count <= 8, (tool["name"], count)


def test_no_tool_parameter_names_a_field_that_no_longer_exists():
    live = set(Threat.model_fields) | set(MitigationCreate.model_fields) | {"threat_id", "mitigation_id"}
    offenders = []
    for tool in get_tool_list():
        for param in tool["inputSchema"].get("properties", {}):
            if param in DEAD_FIELDS and param not in live:
                offenders.append((tool["name"], param))
    assert offenders == [], offenders


def test_every_tool_has_a_description_and_a_schema():
    for tool in get_tool_list():
        assert tool["description"].strip(), tool["name"]
        assert tool["inputSchema"]["type"] == "object", tool["name"]


def test_write_tools_name_their_style_guide_entity_and_nothing_more():
    """The rule itself lives in the server instructions. Repeating it per tool cost 11%
    of the whole tool list for five copies of one paragraph."""
    for tool in get_tool_list():
        pointer_lines = [ln for ln in tool["description"].splitlines() if "Style guide" in ln]
        if tool["name"] in TOOL_ENTITY_TYPES:
            assert len(pointer_lines) == 1, tool["name"]
            assert len(pointer_lines[0]) < 60, pointer_lines
        else:
            assert not pointer_lines, tool["name"]
    assert "get_style_guide" in SERVER_INSTRUCTIONS


def test_the_tool_list_stays_small():
    """Every name and description is paid for in every conversation with the server.

    The budget is on what we write. `inputSchema` is generated from the signatures by
    pydantic and its size moves with the Python and pydantic version, so holding it to a
    byte count fails on a runner with a different interpreter and tells the author
    nothing they can act on. The descriptions are the thing that bloats and the thing an
    edit can fix, so they are what is measured; the total keeps a loose cap with room for
    the generated half to differ across environments."""
    tools = get_tool_list()
    assert len(TOOL_REGISTRY) <= 26, sorted(TOOL_REGISTRY)
    written = sum(len(t["name"]) + len(t["description"]) for t in tools)
    assert written < 15_000, written
    assert len(json.dumps(tools)) < 28_000, len(json.dumps(tools))


def test_removed_tools_are_gone():
    """`get_stats` was wholly contained in `check_library_health`; bulk style-guide YAML
    is a migration and moved to `keel style-guide`."""
    for name in ("get_stats", "export_style_guide_yaml", "import_style_guide_yaml",
                 "list_incomplete_style_fields", "get_citations"):
        assert name not in TOOL_REGISTRY


# --------------------------------------------------------------------------- #
# Behaviour
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_unknown_tool_is_reported_not_raised():
    result = await dispatch_tool("nope", {})
    assert result["success"] is False and result["code"] == "not_found"
    assert "get_threat" in result["hint"]        # says what does exist


@pytest.mark.asyncio
async def test_a_missing_argument_is_answered_with_the_signature():
    """Echoing Python's TypeError tells the caller nothing it can act on."""
    result = await dispatch_tool("get_threat", {})
    assert result["code"] == "invalid"
    assert "threat_id" in result["hint"]


@pytest.mark.asyncio
async def test_batch_update_validates_each_item(store):
    """This is the hole the missing tests hid: values went straight onto the record, so
    the batch tool bypassed every check the single-threat tool enforced."""
    result = await dispatch_tool("batch_update_threats", {
        "updates": [{"threat_id": "T-A", "harm": "not-a-harm"}],
        "confirm": True,
    })
    assert result["updated"] == []
    assert result["success"] is False
    assert "harm" in result["errors"][0]["error"]
    assert store.threats["T-A"]["harm"] == "data-exposed"


@pytest.mark.asyncio
async def test_batch_update_applies_the_valid_items_and_reports_the_rest(store):
    result = await dispatch_tool("batch_update_threats", {
        "updates": [
            {"threat_id": "T-A", "harm": "code-execution"},
            {"threat_id": "T-GONE", "harm": "downtime"},
        ],
        "confirm": True,
    })
    assert result["updated"] == ["T-A"]
    assert store.threats["T-A"]["harm"] == "code-execution"
    assert result["errors"][0]["threat_id"] == "T-GONE"


@pytest.mark.asyncio
async def test_batch_update_preview_does_not_write(store):
    result = await dispatch_tool("batch_update_threats", {
        "updates": [{"threat_id": "T-A", "harm": "code-execution"}],
    })
    assert result["confirm_required"] is True
    assert store.threats["T-A"]["harm"] == "data-exposed"


@pytest.mark.asyncio
async def test_health_reports_the_three_tiers_separately(store):
    result = await dispatch_tool("check_library_health", {})
    assert set(result) >= {"errors", "warnings", "load_problems", "stats"}
    assert result["error_count"] == 0
    # T-A has no references and no linked mitigation: advisory and gap, not an error.
    assert any(w["code"] == "missing_references" for w in result["warnings"])
    assert {f["code"] for f in result["warnings"]} >= {"missing_references"}


@pytest.mark.asyncio
async def test_health_surfaces_a_record_the_loader_refused(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-BAD", "harm": "not-a-harm"}])
    set_store(Store(d))
    try:
        result = await dispatch_tool("check_library_health", {})
        err = result["load_problems"][0]
        # Enough for a model to go and fix it without a second call.
        assert err["file"] == "threats/T-BAD.yaml"
        assert err["field"] == "harm"
        assert err["dropped"] is True
        assert err["message"]
    finally:
        set_store(None)


@pytest.mark.asyncio
async def test_create_and_read_a_threat_round_trips(store):
    created = await dispatch_tool("create_threat", {
        "threat_id": "T-NEW",
        "fields": {
            "title": "A new threat",
            "harm": "code-execution",
            "weaknesses": [{"component": "tool", "text": "runs whatever it is handed"}],
            "reachability": "no interpreter is reachable",
        },
    })
    assert created["success"] is True
    got = await dispatch_tool("get_threat", {"threat_id": "T-NEW"})
    assert got["harm"] == "code-execution"
    assert got["weaknesses"][0]["component"] == "tool"


@pytest.mark.asyncio
async def test_linking_a_mitigation_that_does_not_exist_is_refused(store):
    result = await dispatch_tool("add_threat_mitigation", {
        "threat_id": "T-A", "mitigation_id": "CTRL-GONE",
        "strength": "gating", "rationale": "would block it",
    })
    assert result["success"] is False
    assert store.threats["T-A"].get("mitigations") in (None, [])


# --------------------------------------------------------------------------- #
# The record-level bar
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_the_record_bar_comes_with_the_entity_and_not_with_a_field():
    """It exists because some rules are about whether a record should exist at all, and
    those have no field to live in. A field-scoped call must not carry it, or the reason
    for having a separate place evaporates."""
    whole = await dispatch_tool("get_style_guide", {"entity_type": "threat"})
    one = await dispatch_tool("get_style_guide",
                              {"entity_type": "threat", "field_name": "title"})
    # Shape only: the key is there on the entity and absent on the field. Whether the
    # block has content is the catalog's business, not this test's.
    assert "entity" in whole
    assert "entity" not in one


@pytest.mark.asyncio
async def test_one_write_tool_scopes_the_same_way_the_read_does(tmp_path, monkeypatch):
    """Two tools would cost a slot in a list that is paid for in every conversation, and
    the read already says `field_name` means the field and its absence means the record."""
    src = Path("catalog")
    dst = tmp_path / "catalog"
    shutil.copytree(src, dst)
    set_store(Store(dst))
    try:
        r = await dispatch_tool("update_style_guide",
                                {"entity_type": "threat", "patch": {"purpose": "A chain."}})
        assert r["success"] and r["scope"] == "record", r
        r = await dispatch_tool("update_style_guide",
                                {"entity_type": "threat", "field_name": "title",
                                 "patch": {"purpose": "Name what goes wrong."}})
        assert r["success"] and r["scope"] == "field", r
        # And it survives a reload, which is the only proof the file was written right.
        set_store(Store(dst))
        again = await dispatch_tool("get_style_guide", {"entity_type": "threat"})
        assert again["entity"]["purpose"] == "A chain."
    finally:
        set_store(None)


@pytest.mark.asyncio
async def test_a_record_slot_that_does_not_exist_is_refused_with_the_list():
    """`content_requirements` and `examples` belong to fields. Accepting them here would
    persist a slot nothing ever reads."""
    r = await dispatch_tool("update_style_guide",
                            {"entity_type": "threat", "patch": {"examples": ["x"]}})
    assert r["success"] is False
    assert "examples" in r["error"] and r["allowed_slots"]
