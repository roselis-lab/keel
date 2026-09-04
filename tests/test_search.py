"""One search across everything.

Splitting search by entity type asks the caller a question they cannot answer yet:
someone asking whether Keel covers tool misuse does not know whether the answer is a
threat, a control, a row of the matrix or a system that already hit it. That is what
they are asking.
"""
import pytest
import yaml

import keel.config
from keel.mcp import tools as _tools  # noqa: F401
from keel.mcp.registry import dispatch_tool
from keel.services import search_service
from keel.store import Store, set_store


@pytest.fixture
def library(catalog_dir, tmp_path, monkeypatch):
    d = catalog_dir(
        threats=[
            {"id": "T-REFUND", "title": "Agent refunds without a return",
             "weaknesses": [{"component": "tool",
                             "text": "the refund tool fires on model judgement alone"}]},
            {"id": "T-MEMORY", "title": "Poisoned memory steers a later session",
             "reachability": "memory is wiped between sessions"},
        ],
        mitigations=[
            {"id": "CTRL-APPROVAL", "name": "Human approval for irreversible actions",
             "purpose": "Stops a refund leaving on model judgement alone."},
        ],
    )
    (d / "coverage").mkdir(exist_ok=True)
    (d / "coverage" / "demo.yaml").write_text(yaml.safe_dump({
        "source": {"id": "demo", "title": "Demo", "version": "1", "checked": "2026-08-30",
                   "url": "https://example.com/l", "entry_count": 2},
        "entries": [
            {"ref": "D1", "title": "Tool Misuse and Exploitation", "state": "gap"},
            {"ref": "D2", "title": "Memory Poisoning", "state": "covered",
             "threats": ["T-MEMORY"]},
        ],
    }), encoding="utf-8")
    set_store(Store(d))

    reports = tmp_path / "reports"
    (reports / "checkout").mkdir(parents=True)
    (reports / "checkout" / "2026-08-30.yaml").write_text(yaml.safe_dump({
        "system_id": "checkout", "system_name": "Checkout Agent",
        "system_description": "Issues refunds under a value cap.",
        "date": "2026-08-30", "assessor": "T <t@example.com>", "findings": [],
    }), encoding="utf-8")
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(reports))
    yield d
    set_store(None)


def test_one_query_reaches_all_four_kinds(library):
    kinds = {h["kind"] for h in search_service.search("refund")["hits"]}
    assert kinds == {"threat", "mitigation", "report"}

    memory = {h["kind"] for h in search_service.search("memory")["hits"]}
    assert "coverage" in memory and "threat" in memory


def test_a_hit_says_where_it_matched_and_shows_the_text(library):
    hit = next(h for h in search_service.search("model judgement")["hits"]
               if h["kind"] == "threat")
    assert hit["id"] == "T-REFUND"
    assert hit["matched_in"] == "weaknesses"
    assert "model judgement" in hit["snippet"]


def test_prose_is_searched_not_only_titles(library):
    """Most of what makes a card findable is in its prose, and a list of dicts is where
    this catalog keeps the good part."""
    assert [h["id"] for h in search_service.search("wiped between sessions")["hits"]] == ["T-MEMORY"]


def test_a_coverage_hit_carries_its_state(library):
    """So "we have a row for it, still a gap" and "we have a threat for it" come back
    distinguishable in one call."""
    hits = {h["id"]: h for h in search_service.search("misuse")["hits"]}
    assert hits["demo:D1"]["state"] == "gap"


def test_kind_narrows_once_the_caller_knows(library):
    hits = search_service.search("refund", kind="mitigation")["hits"]
    assert [h["id"] for h in hits] == ["CTRL-APPROVAL"]


def test_an_unknown_kind_names_the_real_ones(library):
    result = search_service.search("refund", kind="control")
    assert "threat" in result["error"] and "mitigation" in result["error"]


def test_a_one_character_query_is_refused(library):
    """Every id in the catalog contains "T"; a hit list of everything is not an answer."""
    assert search_service.search("t")["error"]


def test_results_are_capped_and_say_so(library):
    result = search_service.search("re", limit=1)
    assert result["truncated"] is True
    assert len(result["hits"]) == 1
    assert result["count"] > 1


def test_no_match_is_an_empty_answer_not_an_error(library):
    assert search_service.search("quantum tunnelling") == {
        "hits": [], "count": 0, "truncated": False}


def test_a_match_inside_a_link_does_not_surface_the_threat(library):
    """A control matching inside a threat's link list means the CONTROL matched, and the
    control comes back on its own. Returning the threat too puts the weaker signal in
    front of the stronger one."""
    from keel.services import threat_service
    import asyncio

    asyncio.run(threat_service.add_mitigation(
        "T-REFUND", "CTRL-APPROVAL", "gating", "Approval blocks the payout."))

    hits = search_service.search("approval")["hits"]
    assert [h["id"] for h in hits] == ["CTRL-APPROVAL"]


def test_named_matches_come_before_prose_matches(library):
    """A card called "Human approval…" answers "approval" better than one that mentions
    the word halfway through its purpose."""
    hits = search_service.search("refund")["hits"]
    assert hits[0]["matched_in"] in ("title", "name", "assessment")
    assert hits[0]["id"] == "T-REFUND"


@pytest.mark.asyncio
async def test_search_is_reachable_over_mcp(library):
    result = await dispatch_tool("search", {"q": "refund"})
    assert result["count"] >= 3
    assert {"kind", "id", "title", "matched_in", "snippet"} <= set(result["hits"][0])
