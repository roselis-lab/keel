"""Every entity is fully writable over MCP, and every write is checked.

MCP is the primary authoring interface, so a field it cannot reach is a field the
catalog cannot be finished in. Nine of the mitigation card's sixteen fields were once
unreachable and reports were not exposed at all — the assessment skill wrote YAML with a
plain file write, straight past the service that refuses a made-up control id.
"""
import pytest
import yaml

import keel.config
from keel.mcp import tools as _tools  # noqa: F401 — importing registers every tool
from keel.mcp.registry import dispatch_tool
from keel.schemas.mitigation import MitigationBase
from keel.schemas.threat import Threat
from keel.store import Store, set_store


@pytest.fixture
def store(catalog_dir):
    s = Store(catalog_dir(
        threats=[{"id": "T-A"}],
        mitigations=[{"id": "CTRL-A", "mitigation_class": "gating_control"}],
    ))
    set_store(s)
    yield s
    set_store(None)


# --------------------------------------------------------------------------- #
# Threats
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_threat_crud_round_trips(store):
    created = await dispatch_tool("create_threat", {"threat_id": "T-N", "fields": {
        "title": "A threat", "harm": "downtime",
        "weaknesses": [{"component": "tool", "text": "no ceiling on retries"}],
        "reachability": "the tool cannot be called in a loop",
    }})
    assert created["success"] is True and created["id"] == "T-N"
    # A fresh threat has no references and no linked control yet: said, not blocked.
    assert {a["code"] for a in created["advice"]} == {"missing_references"}

    got = await dispatch_tool("get_threat", {"threat_id": "T-N"})
    assert got["harm"] == "downtime"

    updated = await dispatch_tool("update_threat", {"threat_id": "T-N", "fields": {
        "harm": "code-execution", "tags": ["agentic"],
    }})
    assert updated["success"] is True
    assert updated["changed"] == ["harm", "tags"]
    assert store.threats["T-N"]["harm"] == "code-execution"

    deleted = await dispatch_tool("delete_threat", {"threat_id": "T-N", "confirm": True})
    assert deleted["success"] is True
    assert "T-N" not in store.threats


@pytest.mark.asyncio
async def test_every_threat_field_is_writable(store):
    """The whole point of the `fields` map: nothing on the record is out of reach."""
    writable = set(Threat.model_fields) - {"id", "mitigations"}
    result = await dispatch_tool("update_threat", {"threat_id": "T-A", "fields": {
        "title": "Retitled",
        "harm": "reputation-legal",
        "source": ["internal"],
        "weaknesses": [{"component": "memory", "surface": ["memory"],
                        "text": "notes survive the session"}],
        "reachability": "memory is wiped between turns",
        "references": [{"title": "A writeup", "url": "https://example.com/x",
                        "note": "the incident this is drawn from"}],
        "positioning": "ASI06 is broader than this; the retrieval half lands separately.",
        "tags": ["multi-agent"],
    }})
    assert result["success"] is True
    assert set(result["changed"]) == writable


@pytest.mark.asyncio
async def test_an_unknown_field_is_refused_and_the_error_lists_the_real_ones(store):
    """An error that only rejects makes the model guess again."""
    result = await dispatch_tool("update_threat", {"threat_id": "T-A",
                                                   "fields": {"harmm": "downtime"}})
    assert result["code"] == "invalid"
    assert result["field"] == "harmm"
    assert "harm" in result["hint"] and "reachability" in result["hint"]


@pytest.mark.asyncio
async def test_a_bad_enum_value_is_refused_before_it_reaches_disk(store):
    result = await dispatch_tool("update_threat", {"threat_id": "T-A",
                                                   "fields": {"harm": "not-a-harm"}})
    assert result["success"] is False
    assert store.threats["T-A"]["harm"] == "data-exposed"


@pytest.mark.asyncio
async def test_delete_without_confirm_previews_and_writes_nothing(store):
    result = await dispatch_tool("delete_threat", {"threat_id": "T-A"})
    assert result.get("confirm_required") is True
    assert "T-A" in store.threats


# --------------------------------------------------------------------------- #
# Mitigations
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_every_mitigation_field_is_writable(store):
    """Nine of these were unreachable over MCP, which made a complete card impossible
    to author through the interface meant for authoring."""
    writable = set(MitigationBase.model_fields)
    result = await dispatch_tool("update_mitigation", {"mitigation_id": "CTRL-A", "fields": {
        "name": "Renamed",
        "mitigation_class": "detector",
        "purpose": "Catches the call after it happens.",
        "formal_implementation_risk": "A dashboard nobody opens.",
        "review": "Re-read when a new tool is added.",
        "maintainer": "platform-security",
        "locus": {"value": "infrastructure", "note": "It sits in the shared runtime."},
        "scope": "Every agent that can call an external tool.",
        "out_of_scope": "Calls that change nothing.",
        "control_mechanism": "Every tool call is logged with its arguments.",
        "failure_behavior": {"value": "fail_open",
                             "note": "A blind detector stops nothing on its own."},
        "telemetry": {"events": [{"name": "tool.called",
                                  "records": "A tool ran with these arguments.",
                                  "attributes": ["call id", "arguments"]}],
                      "evidence": "Held outside the agent's own store."},
        "anti_patterns": ["Logging the decision but not the arguments."],
        "validation": [{"criterion": "A call appears in the log within a minute."}],
        "faq": [{"question": "Does this stop the call?", "answer": "No."}],
        "positioning": "SAIF names the risk; this is the control side of it.",
        "requires": [],
        "implementations": [{"title": "Gateway log", "description": "Recorded at the gateway."}],
    }})
    assert result["success"] is True
    assert set(result["changed"]) == writable


@pytest.mark.asyncio
async def test_mitigation_create_and_delete(store):
    created = await dispatch_tool("create_mitigation", {"mitigation_id": "CTRL-N", "fields": {
        "name": "A control", "mitigation_class": "process",
    }})
    assert created["success"] is True and created["id"] == "CTRL-N"
    assert "card_incomplete" in {a["code"] for a in created["advice"]}
    assert (await dispatch_tool("get_mitigation", {"mitigation_id": "CTRL-N"}))["name"] == "A control"

    deleted = await dispatch_tool("delete_mitigation", {"mitigation_id": "CTRL-N", "confirm": True})
    assert deleted["success"] is True


@pytest.mark.asyncio
async def test_get_returns_who_else_names_this_entry(store):
    """Folded into get rather than a tool of its own: "who else says this exists" is
    something you want while reading the entry, not something you think to ask for."""
    assert (await dispatch_tool("get_threat", {"threat_id": "T-A"}))["cited_by"] == []
    assert (await dispatch_tool("get_mitigation", {"mitigation_id": "CTRL-A"}))["cited_by"] == []


# --------------------------------------------------------------------------- #
# Coverage
# --------------------------------------------------------------------------- #
@pytest.fixture
def covered(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-A"}], mitigations=[{"id": "CTRL-A"}])
    (d / "coverage").mkdir(exist_ok=True)
    (d / "coverage" / "demo.yaml").write_text(yaml.safe_dump({
        "source": {"id": "demo", "title": "Demo", "version": "1", "checked": "2026-08-30",
                   "url": "https://example.com/l", "entry_count": 2},
        "entries": [{"ref": "D1", "title": "One", "state": "gap"},
                    {"ref": "D2", "title": "Two", "state": "gap"}],
    }), encoding="utf-8")
    set_store(Store(d))
    yield d
    set_store(None)


@pytest.mark.asyncio
async def test_covering_an_entry_records_the_ids(covered):
    result = await dispatch_tool("set_coverage_entry", {
        "source_id": "demo", "ref": "D1", "state": "covered", "threats": ["T-A"],
    })
    assert result["success"] is True
    matrix = await dispatch_tool("get_coverage", {"source_id": "demo", "state": "covered"})
    assert matrix["sources"][0]["entries"][0]["threats"] == ["T-A"]
    # And the reverse view follows without anything being stored twice.
    assert (await dispatch_tool("get_threat", {"threat_id": "T-A"}))["cited_by"][0]["ref"] == "D1"


@pytest.mark.asyncio
async def test_a_coverage_claim_may_not_name_something_that_does_not_exist(covered):
    """This file is Keel's public claim; a dangling id here is a false statement."""
    result = await dispatch_tool("set_coverage_entry", {
        "source_id": "demo", "ref": "D1", "state": "covered", "threats": ["T-GHOST"],
    })
    assert result["success"] is False
    assert "T-GHOST" in result["error"]


@pytest.mark.asyncio
async def test_out_of_scope_needs_its_reasoning(covered):
    result = await dispatch_tool("set_coverage_entry", {
        "source_id": "demo", "ref": "D1", "state": "out_of_scope",
    })
    assert result["success"] is False
    assert "note" in result["error"]


@pytest.mark.asyncio
async def test_coverage_returns_counts_only_until_rows_are_asked_for(covered):
    """130+ rows is not something to hand over because someone asked a yes/no question."""
    counts = await dispatch_tool("get_coverage", {})
    assert "entries" not in counts["sources"][0]
    assert counts["sources"][0]["counts"] == {"covered": 0, "out_of_scope": 0, "gap": 2}
    assert "entries_omitted" in counts

    rows = await dispatch_tool("get_coverage", {"source_id": "demo"})
    assert len(rows["sources"][0]["entries"]) == 2


@pytest.mark.asyncio
async def test_an_unknown_source_or_ref_says_what_is_known(covered):
    bad_source = await dispatch_tool("set_coverage_entry", {
        "source_id": "nope", "ref": "D1", "state": "gap"})
    assert bad_source["code"] == "not_found"
    assert "demo" in bad_source["hint"]

    bad_ref = await dispatch_tool("set_coverage_entry", {
        "source_id": "demo", "ref": "D9", "state": "gap"})
    assert "get_coverage" in bad_ref["hint"]


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
@pytest.fixture
def reports(store, tmp_path, monkeypatch):
    d = tmp_path / "reports"
    d.mkdir()
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(d))
    return d


@pytest.mark.asyncio
async def test_report_create_read_and_save(reports):
    created = await dispatch_tool("create_report", {
        "system_id": "support-bot", "system_name": "Support Bot",
        "system_description": "Answers help-centre questions.",
        "assessor": "Tester <t@example.com>", "date": "2026-08-30",
    })
    assert created == {"success": True, "system_id": "support-bot", "date": "2026-08-30"}

    listed = await dispatch_tool("list_reports", {})
    assert listed["reports"][0]["system_id"] == "support-bot"

    report = await dispatch_tool("get_report", {"system_id": "support-bot", "date": "2026-08-30"})
    report["system_description"] = "Now also issues refunds."
    saved = await dispatch_tool("save_report", {
        "system_id": "support-bot", "date": "2026-08-30", "report": report,
    })
    assert saved["success"] is True
    assert saved["reverted_to_draft"] is False

    reread = await dispatch_tool("get_report", {"system_id": "support-bot", "date": "2026-08-30"})
    assert reread["system_description"] == "Now also issues refunds."


@pytest.mark.asyncio
async def test_creating_a_report_twice_does_not_discard_the_first(reports):
    args = {"system_id": "support-bot", "system_name": "Support Bot",
            "system_description": "Answers questions.", "assessor": "T <t@example.com>",
            "date": "2026-08-30"}
    assert (await dispatch_tool("create_report", args))["success"] is True
    again = await dispatch_tool("create_report", args)
    assert again["code"] == "conflict"
    assert "get_report" in again["hint"]        # names the way forward


@pytest.mark.asyncio
async def test_a_report_may_not_invent_a_control_id(reports):
    """The gate that the skill's plain file write used to walk straight past."""
    await dispatch_tool("create_report", {
        "system_id": "support-bot", "system_name": "Support Bot",
        "system_description": "Answers questions.", "assessor": "T <t@example.com>",
        "date": "2026-08-30",
    })
    report = await dispatch_tool("get_report", {"system_id": "support-bot", "date": "2026-08-30"})
    report["findings"] = [{
        "id": "T-A", "from_catalog": True,
        "scenario": "Someone talks it into doing the wrong thing.",
        "source": {"who": "external-attacker", "motive": "money", "access": "the chat"},
        "asset": "customer records", "attack_surface": "user-input",
        "vulnerability": "no scoping on lookups", "exploitation_complexity": "low",
        "harm": "data-exposed",
        "risk": {"likelihood": "high", "severity": "high", "reasoning": "Anyone can reach it."},
        "delta": "new this quarter",
        "requirements": [{"mitigation_id": "CTRL-INVENTED",
                          "coverage_status": "needs_implementation"}],
    }]
    result = await dispatch_tool("save_report", {
        "system_id": "support-bot", "date": "2026-08-30", "report": report,
    })
    assert result["code"] == "invalid"
    assert "CTRL-INVENTED" in " ".join(d["message"] for d in result["details"])
    assert "leave mitigation_id empty" in result["hint"]


@pytest.mark.asyncio
async def test_there_is_no_way_to_delete_a_report(reports):
    from keel.mcp.registry import TOOL_REGISTRY

    assert not [n for n in TOOL_REGISTRY if "report" in n and "delete" in n]
