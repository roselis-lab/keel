"""Compliance: an entry's standing comes from what the report says about its threats.

The rule worth pinning is the worst-of: an entry answered by two threats is only as
good as the weaker answer, and a gap in the library is never reported as the system's
failure."""
from keel.schemas.report import Report
from keel.services.compliance_service import standing


def _finding(fid, status, note=None):
    req = {"mitigation_id": "CTRL-X", "coverage_status": status}
    if note:
        req["coverage_note"] = note
    return dict(
        id=fid, from_catalog=True, scenario="s", asset="a", attack_surface="tool-output",
        source={"who": "external-attacker", "motive": "m", "access": "x"},
        vulnerability=f"weak spot of {fid}", exploitation_complexity="low", harm="data-exposed",
        risk={"likelihood": "high", "severity": "high", "reasoning": "r"},
        delta="new", requirements=[req],
    )


REPORT = Report(
    system_id="sys", system_name="Sys", system_description="d", date="2026-01-01",
    assessor="A <a@example.com>",
    findings=[_finding("T-OPEN", "needs_implementation"),
              _finding("T-DONE", "already_covered", note="the gateway already does it")],
    discarded=[{"id": "T-NA", "reason": "no tool takes a URL from the model"}],
    open_questions=[{"id": "Q1", "question": "q?", "asks_for": "fact", "looked_in": "repo",
                     "needed_for": "n", "how_to_check": "h"}],
    paused=[{"id": "T-WAIT", "from_catalog": True, "waiting_on": ["Q1"], "note": "waits on Q1"}],
    surfaces=[{"id": "S1", "kind": "entry", "name": "api", "where": "/api", "note": "n"}],
)


def _entry(ref, threats, state="covered"):
    return {"ref": ref, "title": ref, "state": state, "threats": threats, "mitigations": []}


def _run(*entries):
    src = {"source": {"id": "fw"}, "entries": list(entries)}
    return {e["ref"]: e for e in standing(REPORT, [src])[0]["entries"]}


def test_each_threat_state_maps_to_a_standing_with_the_reports_reason():
    got = _run(_entry("A", ["T-OPEN"]), _entry("B", ["T-DONE"]), _entry("C", ["T-NA"]),
               _entry("D", ["T-WAIT"]), _entry("E", ["T-NEVER"]))
    assert {k: v["standing"] for k, v in got.items()} == {
        "A": "not_met", "B": "met", "C": "does_not_apply", "D": "waiting", "E": "not_assessed"}
    assert got["C"]["threats"][0]["why"] == "no tool takes a URL from the model"
    assert got["A"]["threats"][0]["open_fixes"] == 1


def test_an_entry_is_only_as_good_as_its_weakest_threat():
    got = _run(_entry("A", ["T-DONE", "T-OPEN"]), _entry("B", ["T-NA", "T-NEVER"]))
    assert got["A"]["standing"] == "not_met"
    assert got["B"]["standing"] == "not_assessed"


def test_library_gaps_and_out_of_scope_are_not_blamed_on_the_system():
    got = _run(_entry("G", [], state="gap"), _entry("O", [], state="out_of_scope"),
               _entry("C", []))
    assert got["G"]["standing"] == "library_gap"
    assert got["O"]["standing"] == "out_of_scope"
    assert got["C"]["standing"] == "not_assessed"


def test_counts_add_up_to_the_entries():
    src = {"source": {"id": "fw"}, "entries": [_entry("A", ["T-OPEN"]), _entry("B", ["T-NA"])]}
    counts = standing(REPORT, [src])[0]["counts"]
    assert counts["not_met"] == 1 and counts["does_not_apply"] == 1
    assert sum(counts.values()) == 2
