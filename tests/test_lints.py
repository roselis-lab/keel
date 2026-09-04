"""The rules themselves: pure functions over records, no store and no disk.

Written this way on purpose. A rule that needs a catalog on disk to be tested is a rule
that cannot run from both entry points, and testing them through the store would hide
which layer a failure came from.
"""
import pytest

from keel.rules import REGISTRY, Catalog, check_all, check_entity


def _threat(**over):
    base = {
        "id": "T-X", "title": "Sensitive data disclosure", "harm": "data-exposed",
        "weaknesses": [{"component": "tool", "text": "returns raw records with no scoping"}],
        "reachability": "the model sees nothing worth taking",
        "mitigations": [{"id": "CTRL-DLP", "strength": "soft", "rationale": "lowers likelihood"}],
        "references": [{"title": "A writeup", "url": "https://example.com/x"}],
    }
    base.update(over)
    return base


_DEFAULT = object()


def _catalog(threats=None, mitigations=_DEFAULT):
    # A sentinel, not `or`: an empty dict of mitigations is a case worth testing, and
    # `mitigations or {...}` would silently swap it for the default.
    if mitigations is _DEFAULT:
        mitigations = {"CTRL-DLP": {"id": "CTRL-DLP", "mitigation_class": "detector"}}
    return Catalog(threats={t["id"]: t for t in (threats or [_threat()])},
                   mitigations=mitigations)


def codes(findings):
    return {f.code for f in findings}


# --------------------------------------------------------------------------- #
# Threat rules
# --------------------------------------------------------------------------- #
def test_all_soft_links_are_flagged_as_nothing_closing_the_threat():
    found = check_entity("threat", "T-X", _catalog())
    assert "no_gating_control" in codes(found)


def test_a_gating_link_to_a_detector_is_over_graded():
    cat = _catalog([_threat(mitigations=[
        {"id": "CTRL-DLP", "strength": "gating", "rationale": "blocks"}])])
    hit = next(f for f in check_entity("threat", "T-X", cat)
               if f.code == "over_graded_strength")
    assert "detector" in hit.message
    assert hit.field == "mitigations.0.strength"


def test_a_gating_link_to_a_gating_control_is_quiet():
    cat = _catalog(
        [_threat(mitigations=[{"id": "CTRL-G", "strength": "gating", "rationale": "blocks"}])],
        {"CTRL-G": {"id": "CTRL-G", "mitigation_class": "gating_control"}},
    )
    assert "over_graded_strength" not in codes(check_entity("threat", "T-X", cat))
    assert "no_gating_control" not in codes(check_entity("threat", "T-X", cat))


def test_a_link_to_a_card_that_is_not_there_is_an_error():
    cat = _catalog(mitigations={})
    hit = next(f for f in check_entity("threat", "T-X", cat) if f.code == "dangling_link")
    assert hit.severity == "error"


def test_missing_pieces_of_a_threat_are_errors():
    cat = _catalog([_threat(weaknesses=[], harm="")])
    found = [f for f in check_entity("threat", "T-X", cat) if f.code == "threat_incomplete"]
    assert {f.field for f in found} == {"harm", "weaknesses"}
    assert all(f.severity == "error" for f in found)


# --------------------------------------------------------------------------- #
# Mitigation rules
# --------------------------------------------------------------------------- #
def test_a_card_that_does_not_say_what_it_does_is_incomplete():
    cat = Catalog(mitigations={"CTRL-A": {"id": "CTRL-A", "name": "A",
                                          "mitigation_class": "gating_control"}})
    found = [f for f in check_entity("mitigation", "CTRL-A", cat)
             if f.code == "card_incomplete"]
    assert {f.field for f in found} == {"purpose", "scope", "out_of_scope",
                                        "control_mechanism", "locus", "failure_behavior"}


def test_a_card_with_no_acceptance_criteria_is_advised():
    cat = Catalog(mitigations={"CTRL-A": {"id": "CTRL-A"}})
    assert "no_acceptance_criteria" in codes(check_entity("mitigation", "CTRL-A", cat))


def test_a_prerequisite_that_is_not_there_is_an_error():
    cat = Catalog(mitigations={"CTRL-A": {"id": "CTRL-A", "requires": ["CTRL-GONE"]}})
    hit = next(f for f in check_entity("mitigation", "CTRL-A", cat)
               if f.code == "dangling_prerequisite")
    assert hit.severity == "error"


def test_a_card_no_threat_links_is_advised():
    cat = _catalog(mitigations={"CTRL-DLP": {"id": "CTRL-DLP"},
                                "CTRL-LONELY": {"id": "CTRL-LONELY"}})
    assert "orphan_control" in codes(check_entity("mitigation", "CTRL-LONELY", cat))
    assert "orphan_control" not in codes(check_entity("mitigation", "CTRL-DLP", cat))


# --------------------------------------------------------------------------- #
# The registry itself
# --------------------------------------------------------------------------- #
def test_both_entry_points_run_the_same_rules():
    """The reason the registry exists: a rule cannot reach one caller and miss the other.
    The dashboard used to know 'this threat has no weaknesses' while the write that
    caused it said nothing."""
    cat = _catalog([_threat(weaknesses=[], references=[])])
    swept = {f.code for f in check_all(cat) if f.entity_id == "T-X"}
    single = codes(check_entity("threat", "T-X", cat))
    assert swept == single


def test_a_rule_cannot_be_registered_twice():
    from keel.rules import rule

    with pytest.raises(ValueError, match="duplicate rule code"):
        rule("no_gating_control", entity="threat", severity="advice",
             label="Duplicate")(lambda *a: [])


def test_every_rule_declares_what_it_is():
    for code, r in REGISTRY.items():
        assert r.entity in ("threat", "mitigation", "catalog"), code
        assert r.severity in ("error", "advice"), code
        assert r.label and r.label != code, code


def test_the_served_catalogue_covers_every_rule():
    """The UI groups findings by rule and takes its labels from here rather than keeping
    a copy. Two such copies used to live in the dashboard and fell behind every rename."""
    from keel.rules import catalogue

    served = {r["code"] for r in catalogue()}
    assert served == set(REGISTRY)
    assert all(r["label"] for r in catalogue())


def test_errors_sort_before_advice():
    """A sweep is read top-down; what breaks the catalog goes first."""
    cat = _catalog([_threat(weaknesses=[], references=[])])
    severities = [f.severity for f in check_all(cat)]
    assert severities == sorted(severities, key=lambda s: s != "error")


def test_anti_patterns_with_nothing_to_catch_them_are_advised():
    """They stay separate fields - one is read while designing, the other while accepting
    - but a list of ways to get it wrong that no criterion would catch is a warning
    nobody can act on."""
    cat = Catalog(mitigations={"CTRL-A": {
        "id": "CTRL-A", "anti_patterns": ["Approving by default."], "validation": []}})
    assert "unchecked_anti_patterns" in codes(check_entity("mitigation", "CTRL-A", cat))


def test_anti_patterns_backed_by_a_criterion_are_quiet():
    cat = Catalog(mitigations={"CTRL-A": {
        "id": "CTRL-A", "anti_patterns": ["Approving by default."],
        "validation": [{"criterion": "Approve is not the default action."}]}})
    assert "unchecked_anti_patterns" not in codes(check_entity("mitigation", "CTRL-A", cat))


def test_a_decision_field_missing_entirely_is_an_error():
    """`locus` and `failure_behavior` are values a reader filters on. The schema refuses
    one written without its reasoning; this catches a card that never got the field."""
    cat = Catalog(mitigations={"CTRL-A": {"id": "CTRL-A"}})
    fields = {f.field for f in check_entity("mitigation", "CTRL-A", cat)
              if f.code == "card_incomplete"}
    assert {"locus", "failure_behavior"} <= fields


# --------------------------------------------------------------------------- #
# The splitting test, as far as a rule can run it
# --------------------------------------------------------------------------- #
def _gated(tid, harm="data-exposed", ctrl="CTRL-G", reach="not reachable"):
    return _threat(id=tid, harm=harm, reachability=reach,
                   mitigations=[{"id": ctrl, "strength": "gating", "rationale": "blocks"}])


_GATES = {"CTRL-G": {"id": "CTRL-G", "mitigation_class": "gating_control"},
          "CTRL-H": {"id": "CTRL-H", "mitigation_class": "gating_control"}}


def test_two_threats_closed_by_the_same_gate_are_merge_candidates():
    """Two chains are two threats only if ruling one out does not rule out the other, or
    closing one does not close the other. The second half is checkable, so the catalog
    says so rather than leaving a split nobody can justify sitting there."""
    cat = _catalog([_gated("T-1"), _gated("T-2")], _GATES)
    hits = [f for f in check_all(cat) if f.code == "merge_candidate"]
    assert {f.entity_id for f in hits} == {"T-1", "T-2"}
    assert "T-2" in hits[0].message and hits[0].field == "reachability"
    assert all(f.severity == "advice" for f in hits)


def test_different_gating_controls_are_not_merge_candidates():
    cat = _catalog([_gated("T-1"), _gated("T-2", ctrl="CTRL-H")], _GATES)
    assert not [f for f in check_all(cat) if f.code == "merge_candidate"]


def test_different_harms_are_not_merge_candidates():
    """One threat rests on one harm, so the same control serving two of them is two
    threats however alike the mechanism looks."""
    cat = _catalog([_gated("T-1"), _gated("T-2", harm="code-execution")], _GATES)
    assert not [f for f in check_all(cat) if f.code == "merge_candidate"]


def test_threats_with_no_gating_control_are_left_to_the_other_rule():
    """`no_gating_control` already speaks for them; pairing them on an empty set would
    flag every unfinished threat against every other."""
    cat = _catalog([_threat(id="T-1", mitigations=[]), _threat(id="T-2", mitigations=[])], {})
    assert not [f for f in check_all(cat) if f.code == "merge_candidate"]
