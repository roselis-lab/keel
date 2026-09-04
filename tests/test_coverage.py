"""The coverage matrix: Keel's public claim about the sources it tracks.

The three states carry the whole point. `covered` is the easy one. `gap` is the honest
admission. `out_of_scope` is the one that buys trust — Keel's own boundary with the
reasoning attached. The schema refuses an out-of-scope row with no reason, and the rules
refuse a `covered` that names an entry which is not there.

What is tested here is the code: the validators and the derived views, on fixtures. What
the shipped catalog says is the rules' business, reached through `keel validate` and the
one bridge test in test_catalog.py, so that a content change never fails in Python.

`out_of_scope` describes Keel, never the source. An entry Keel answers in a shape of its
own - prompt injection, modelled as a mechanism across many threats rather than as one
row - is `covered`, and the shape is explained on the entry, in its `positioning`. A row
records the mapping and nothing else: it is about the whole set of ids answering a source,
so a sentence written about one of them stops being true when a second joins it.
"""
import pytest
import yaml
from pydantic import ValidationError

from keel.catalog import catalog_findings, catalog_warnings, validate_catalog
from keel.schemas.coverage import CoverageEntry
from keel.services import coverage_service
from keel.store import Store, set_store

SOURCE = {
    "id": "demo-source",
    "title": "Demo Source",
    "version": "2026",
    "url": "https://example.com/list",
    "checked": "2026-08-29",
    "entry_count": 3,
}


@pytest.fixture
def coverage(catalog_dir):
    """A catalog with one threat, one mitigation and one tracked source."""
    def build(entries, source=None):
        d = catalog_dir(threats=[{"id": "T-A"}], mitigations=[{"id": "CTRL-A"}])
        (d / "coverage").mkdir(exist_ok=True)
        (d / "coverage" / "demo-source.yaml").write_text(
            yaml.safe_dump({"source": {**SOURCE, **(source or {})}, "entries": entries}),
            encoding="utf-8",
        )
        set_store(Store(d))
        return d
    yield build
    set_store(None)


# --------------------------------------------------------------------------- #
# The states mean what they say
# --------------------------------------------------------------------------- #
def test_out_of_scope_without_a_reason_is_refused():
    """A refusal with no reasoning is indistinguishable from an omission, which is the
    one thing the matrix exists to prevent."""
    with pytest.raises(ValidationError, match="out_of_scope needs a note"):
        CoverageEntry(ref="X1", title="Something", state="out_of_scope")


def test_out_of_scope_cannot_also_claim_coverage():
    with pytest.raises(ValidationError, match="out_of_scope must name nothing"):
        CoverageEntry(ref="X1", title="S", state="out_of_scope", note="because", threats=["T-A"])


def test_covered_must_name_something():
    with pytest.raises(ValidationError, match="covered must name at least one"):
        CoverageEntry(ref="X1", title="S", state="covered")


def test_gap_must_name_nothing():
    with pytest.raises(ValidationError, match="gap must name nothing"):
        CoverageEntry(ref="X1", title="S", state="gap", threats=["T-A"])


def test_duplicate_refs_in_one_source_are_refused(coverage):
    d = coverage([
        {"ref": "X1", "title": "One", "state": "gap"},
        {"ref": "X1", "title": "One again", "state": "gap"},
    ])
    assert any("duplicate ref" in e for e in validate_catalog(d))


# --------------------------------------------------------------------------- #
# A claim has to be true
# --------------------------------------------------------------------------- #
def test_claiming_a_threat_that_is_not_in_the_catalog_is_an_error(coverage):
    d = coverage([{"ref": "X1", "title": "One", "state": "covered", "threats": ["T-GONE"]}])
    errs = validate_catalog(d)
    assert any("T-GONE" in e and "not in the catalog" in e for e in errs), errs


def test_claiming_a_mitigation_that_is_not_in_the_catalog_is_an_error(coverage):
    d = coverage([{"ref": "X1", "title": "One", "state": "covered", "mitigations": ["CTRL-GONE"]}])
    assert any("CTRL-GONE" in e for e in validate_catalog(d))


def test_a_true_claim_validates(coverage):
    d = coverage([
        {"ref": "X1", "title": "One", "state": "covered", "threats": ["T-A"]},
        {"ref": "X2", "title": "Two", "state": "out_of_scope", "note": "A mechanism, not a threat."},
        {"ref": "X3", "title": "Three", "state": "gap"},
    ])
    assert validate_catalog(d) == []


def test_the_filename_must_match_the_source_id(coverage):
    d = coverage([{"ref": "X1", "title": "One", "state": "gap"}], source={"id": "other-name"})
    assert any("does not match filename" in e for e in validate_catalog(d))


# --------------------------------------------------------------------------- #
# Unfinished work is counted out loud
# --------------------------------------------------------------------------- #
def test_a_partial_import_is_reported_with_both_numbers(coverage):
    """A matrix showing twelve rows of a hundred-and-one-entry release looks complete.
    Saying "12 of 101" is the difference between a claim and a boast."""
    d = coverage([{"ref": "X1", "title": "One", "state": "gap"}], source={"entry_count": 101})
    hit = [f for f in catalog_findings(d) if f["code"] == "partial_import"]
    assert hit, catalog_findings(d)
    assert "1 of 101" in hit[0]["message"]


def test_a_source_nothing_answers_is_reported(coverage):
    d = coverage([{"ref": f"X{i}", "title": str(i), "state": "gap"} for i in range(3)])
    cats = {f["code"] for f in catalog_findings(d)}
    assert "nothing_answered" in cats


def test_one_out_of_scope_row_counts_as_answering(coverage):
    """A boundary is a decision, not a hole — a source with one is not untouched."""
    d = coverage([
        {"ref": "X1", "title": "One", "state": "out_of_scope", "note": "Out of scope, because."},
        {"ref": "X2", "title": "Two", "state": "gap"},
        {"ref": "X3", "title": "Three", "state": "gap"},
    ])
    cats = {f["code"] for f in catalog_findings(d)}
    assert "nothing_answered" not in cats


def test_coverage_warnings_reach_the_catalog_advisory_tier(coverage):
    d = coverage([{"ref": "X1", "title": "One", "state": "gap"}], source={"entry_count": 9})
    assert any("1 of 9" in w for w in catalog_warnings(d))


# --------------------------------------------------------------------------- #
# Derived views
# --------------------------------------------------------------------------- #
def test_citations_are_derived_not_stored(coverage):
    """The file is written source-first, because a gap needs a row to be empty in. The
    card's "who names me" view is turned around here rather than duplicated on disk."""
    coverage([
        {"ref": "X1", "title": "One", "state": "covered", "threats": ["T-A"], },
        {"ref": "X2", "title": "Two", "state": "covered", "mitigations": ["CTRL-A"]},
    ])
    index = coverage_service.by_entity()
    assert [c["ref"] for c in index["T-A"]] == ["X1"]
    assert index["T-A"][0]["source_title"] == "Demo Source"
    assert [c["ref"] for c in index["CTRL-A"]] == ["X2"]


def test_an_entry_no_source_names_is_absent_from_the_index_not_broken(coverage):
    """Naming nothing is Keel's own contribution, and the app says so rather than
    treating it as a missing citation."""
    coverage([{"ref": "X1", "title": "One", "state": "gap"}])
    assert coverage_service.by_entity() == {}


def test_out_of_scope_rows_are_not_citations(coverage):
    """Out of scope says "we do not model this", so it must never read as corroboration."""
    coverage([{"ref": "X1", "title": "One", "state": "out_of_scope", "note": "Not a threat."}])
    assert coverage_service.by_entity() == {}


def test_gaps_lists_only_what_nothing_answers(coverage):
    coverage([
        {"ref": "X1", "title": "One", "state": "covered", "threats": ["T-A"]},
        {"ref": "X2", "title": "Two", "state": "out_of_scope", "note": "No."},
        {"ref": "X3", "title": "Three", "state": "gap"},
    ])
    assert [g["ref"] for g in coverage_service.gaps()] == ["X3"]


def test_matrix_counts_every_state(coverage):
    coverage([
        {"ref": "X1", "title": "One", "state": "covered", "threats": ["T-A"]},
        {"ref": "X2", "title": "Two", "state": "out_of_scope", "note": "No."},
        {"ref": "X3", "title": "Three", "state": "gap"},
    ])
    s = coverage_service.matrix()["sources"][0]
    assert s["counts"] == {"covered": 1, "out_of_scope": 1, "gap": 1}
    assert s["imported"] == 3


# --------------------------------------------------------------------------- #
# The shipped files
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Where the explanation of a mapping lives
# --------------------------------------------------------------------------- #
def test_a_covered_row_carries_no_note(coverage):
    """A row is about the whole set of ids answering a source, so a sentence written
    about one of them stops being true the moment a second joins it. The explanation is
    a property of the entry and lives in its `positioning`."""
    d = coverage([{"ref": "X1", "title": "One", "state": "covered", "threats": ["T-A"],
                   "note": "answered for half of it"}])
    errs = validate_catalog(d)
    assert any("positioning" in e for e in errs), errs


def test_an_out_of_scope_row_still_needs_its_note(coverage):
    """There is no entry to hang it on: the whole point is that Keel has none."""
    d = coverage([{"ref": "X1", "title": "One", "state": "out_of_scope"}])
    assert any("needs a note" in e for e in validate_catalog(d))


def test_a_gap_may_say_what_it_is_waiting_on(coverage):
    d = coverage([{"ref": "X1", "title": "One", "state": "gap",
                   "note": "Waiting on the retrieval half being modelled."}])
    assert validate_catalog(d) == []
