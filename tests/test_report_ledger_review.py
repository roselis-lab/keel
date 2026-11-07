"""Surface ledger, refutation, requirements a team can build, and two grades.

A report shows two kinds of completeness: every catalog threat class was considered, and
every surface of the system was walked. A `high` rests on someone who did not raise it
trying to break it. A requirement that ships says what must hold, where, and how anyone
will know it is done. A refuted finding stays refuted until a new fact brings it back.
"""

import pytest
import yaml

import keel.config
from keel.errors import Invalid
from keel.services import report_service
from keel.store import Store, set_store
from tests.test_report_evidence import _finding, _messages, _report


@pytest.fixture
def archive(catalog_dir, tmp_path, monkeypatch):
    d = catalog_dir(
        threats=[{"id": "T-A", "harm": "data-exposed", "source": ["external-attacker", "internal"]}],
        mitigations=[{"id": "CTRL-X", "validation": []}],
    )
    set_store(Store(d))
    reports = tmp_path / "reports"
    (reports / "demo").mkdir(parents=True)
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(reports))
    yield reports
    set_store(None)


REVIEW = {"by": "fresh reviewer", "verdict": "stands", "note": "re-read [1]; nothing stops the refund"}
LEDGER = [{"id": "S1", "kind": "entry", "name": "chat", "where": "/chat", "outcome": ["T-A"]}]
SHIPS = {
    "mitigation_id": None, "coverage_status": "needs_implementation",
    "description": "Cap refunds the bot can issue without a person.",
}
BUILDABLE = {
    **SHIPS,
    "invariant": "No refund above 50 EUR leaves without a person's approval.",
    "enforce_at": "the refund service, before the gateway call",
    "done_check": "a test that asks the bot for a 60 EUR refund and expects a pending approval",
}


def _put(reports, date, payload):
    (reports / "demo" / f"{date}.yaml").write_text(
        yaml.safe_dump(_report(date=date, findings=[]), sort_keys=False), encoding="utf-8")
    return report_service.save_report("demo", date, payload)


def _finalize_errors(reports, payload):
    _put(reports, "2026-11-06", payload)
    with pytest.raises(Invalid) as exc:
        report_service.finalize_report("demo", "2026-11-06")
    return _messages(exc)


def _ok(**over):
    r = _report(findings=[_finding(review=REVIEW)], surfaces=LEDGER)
    r.update(over)
    return r


def test_the_complete_report_finalizes(archive):
    _put(archive, "2026-11-06", _ok(findings=[_finding(review=REVIEW, requirements=[BUILDABLE])]))
    assert report_service.finalize_report("demo", "2026-11-06")["report"]["status"] == "final"


# --- surface ledger ------------------------------------------------------------- #

def test_no_ledger_blocks_finalize(archive):
    assert "no surface ledger" in _finalize_errors(archive, _ok(surfaces=[]))


def test_a_surface_nobody_walked_blocks_finalize(archive):
    ledger = LEDGER + [{"id": "S2", "kind": "tool", "name": "refund", "where": "tools/refund.py"}]
    assert "S2" in _finalize_errors(archive, _ok(surfaces=ledger))


def test_a_surface_with_a_reason_nothing_reaches_harm_is_walked(archive):
    ledger = LEDGER + [{"id": "S2", "kind": "data", "name": "logs", "where": "stdout",
                        "note": "write-only, nothing reads it back into the model"}]
    _put(archive, "2026-11-06", _ok(surfaces=ledger))
    assert report_service.finalize_report("demo", "2026-11-06")["report"]["status"] == "final"


def test_a_ledger_outcome_must_be_a_branch_of_this_report(archive):
    ledger = [{**LEDGER[0], "outcome": ["T-NOPE"]}]
    with pytest.raises(Invalid) as exc:
        _put(archive, "2026-11-06", _ok(surfaces=ledger))
    assert "T-NOPE" in _messages(exc)


def test_ledger_ids_are_unique(archive):
    with pytest.raises(Invalid) as exc:
        _put(archive, "2026-11-06", _ok(surfaces=LEDGER + LEDGER))
    assert "S1" in _messages(exc)


# --- refutation ----------------------------------------------------------------- #

def test_a_high_nobody_tried_to_refute_blocks_finalize(archive):
    assert "refute" in _finalize_errors(archive, _ok(findings=[_finding()]))


def test_a_medium_needs_no_review(archive):
    medium = _finding(risk={"likelihood": "high", "severity": "medium", "reasoning": "Bounded."})
    _put(archive, "2026-11-06", _ok(findings=[medium]))
    assert report_service.finalize_report("demo", "2026-11-06")["report"]["status"] == "final"


def test_refuted_is_not_a_review_verdict_it_is_a_discard(archive):
    with pytest.raises(Invalid):
        _put(archive, "2026-11-06", _ok(findings=[_finding(review={**REVIEW, "verdict": "refuted"})]))


def test_a_finding_refuted_in_review_is_not_also_graded(archive):
    refuted = [{"id": "T-A", "by": "review",
                "reason": "the gateway rejects amounts the order does not hold [1]", "evidence": [1]}]
    with pytest.raises(Invalid) as exc:
        _put(archive, "2026-11-06", _ok(discarded=refuted))
    assert "refuted in review" in _messages(exc)


def test_a_finding_refuted_earlier_comes_back_with_advice(archive):
    earlier = _ok(date="2026-10-01", findings=[], discarded=[
        {"id": "T-A", "by": "review", "root_cause": "model-sets-refund-amount",
         "reason": "the gateway caps the amount at the order total.", "evidence": [1]}])
    _put(archive, "2026-10-01", earlier)
    again = _ok(findings=[_finding(review=REVIEW, root_cause="model-sets-refund-amount")])
    advice = " | ".join(_put(archive, "2026-11-06", again)["advice"])
    assert "refuted in review on 2026-10-01" in advice


def test_a_threat_discarded_earlier_by_reachability_comes_back_with_advice(archive):
    earlier = _ok(date="2026-10-01", findings=[], discarded=[
        {"id": "T-A", "reason": "the bot had no refund tool then.", "evidence": [1]}])
    _put(archive, "2026-10-01", earlier)
    advice = " | ".join(_put(archive, "2026-11-06", _ok())["advice"])
    assert "ruled out by reachability on 2026-10-01" in advice


# --- one defect, one finding ---------------------------------------------------- #

def test_the_same_fingerprint_twice_is_refused(archive):
    f = _finding(review=REVIEW, root_cause="model-sets-refund-amount")
    with pytest.raises(Invalid) as exc:
        _put(archive, "2026-11-06", _ok(findings=[f, dict(f)]))
    assert "more than once" in _messages(exc)


def test_one_threat_with_two_root_causes_is_two_findings(archive):
    a = _finding(review=REVIEW, root_cause="model-sets-refund-amount")
    b = _finding(review=REVIEW, root_cause="refund-tool-has-no-cap")
    assert _put(archive, "2026-11-06", _ok(findings=[a, b]))["success"]


# --- requirements a team can build ---------------------------------------------- #

def test_an_ask_with_no_card_and_no_invariant_place_and_check_blocks_finalize(archive):
    msg = _finalize_errors(archive, _ok(findings=[_finding(review=REVIEW, requirements=[SHIPS])]))
    assert "invariant" in msg and "enforce_at" in msg and "done_check" in msg


def test_a_catalog_requirement_leans_on_its_card(archive):
    card = {"mitigation_id": "CTRL-X", "coverage_status": "needs_implementation"}
    _put(archive, "2026-11-06", _ok(findings=[_finding(review=REVIEW, requirements=[card])]))
    assert report_service.finalize_report("demo", "2026-11-06")["report"]["status"] == "final"


def test_a_card_with_no_validation_gets_advice(archive):
    card = {"mitigation_id": "CTRL-X", "coverage_status": "needs_implementation"}
    advice = " | ".join(_put(archive, "2026-11-06", _ok(findings=[_finding(review=REVIEW, requirements=[card])]))["advice"])
    assert "CTRL-X has no validation" in advice


def test_a_legacy_threat_is_kept_and_graded(archive):
    f = _finding(review=REVIEW, origin="legacy", delta="existed before the bot, unchanged")
    assert _put(archive, "2026-11-06", _ok(findings=[f]))["report"]["findings"][0]["origin"] == "legacy"


def test_a_requirement_left_out_of_the_hand_off_needs_none_of_it(archive):
    dropped = {**SHIPS, "included": False}
    _put(archive, "2026-11-06", _ok(findings=[_finding(review=REVIEW, requirements=[dropped])]))
    assert report_service.finalize_report("demo", "2026-11-06")["report"]["status"] == "final"


# --- today and at launch -------------------------------------------------------- #

def test_a_feature_not_live_may_carry_todays_grade(archive):
    f = _finding(review=REVIEW, deployment="not_deployed",
                 risk_today={"likelihood": "low", "severity": "high", "reasoning": "Not published yet."})
    assert _put(archive, "2026-11-06", _ok(findings=[f]))["success"]


def test_a_live_feature_has_one_grade(archive):
    f = _finding(review=REVIEW, deployment="live",
                 risk_today={"likelihood": "low", "severity": "high", "reasoning": "Same."})
    with pytest.raises(Invalid) as exc:
        _put(archive, "2026-11-06", _ok(findings=[f]))
    assert "risk_today" in _messages(exc)


# --- open questions say how to settle them -------------------------------------- #

def test_an_open_question_keeps_its_check(archive):
    q = {"id": "Q1", "question": "Who can edit the knowledge base?", "looked_in": "the repo has no ACLs",
         "needed_for": "T-A at reachability", "how_to_check": "export the space's edit permissions"}
    saved = _put(archive, "2026-11-06", _ok(open_questions=[q]))
    assert saved["report"]["open_questions"][0]["how_to_check"].startswith("export")
