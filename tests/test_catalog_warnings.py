"""Advisory warnings tier: quality checks that surface problems without failing CI.
`keel validate` prints them to stderr and stays exit 0; `--strict` exits 1 on them.

Every test here builds the exact catalog it asserts on. These checks used to be
asserted against the repo's own catalog, which meant they passed only while that
catalog stayed broken.
"""
import os
import subprocess
import sys

from keel.catalog import catalog_warnings, catalog_warnings_structured, validate_catalog


def _categories(items):
    return [w["category"] for w in items]


def test_clean_catalog_produces_no_warnings(catalog_dir):
    d = catalog_dir(
        mitigations=[{"id": "CTRL-SCOPE", "mitigation_class": "gating_control"}],
        threats=[
            {
                "id": "T-LEAK",
                "weaknesses": [
                    {"component": "tool", "text": "no scoping on lookups", "nature": "targeted"},
                    {"component": "model", "text": "echoes tool output verbatim", "nature": "secondary"},
                ],
                "mitigations": [
                    {"id": "CTRL-SCOPE", "strength": "gating", "rationale": "scopes the token"}
                ],
                "references": [{"title": "A leak writeup", "url": "https://example.com/leak", "note": "shows the path end to end"}],
            }
        ],
    )
    assert validate_catalog(d) == []
    assert catalog_warnings(d) == []


def test_empty_catalog_produces_no_warnings(catalog_dir):
    """A catalog with nothing in it has nothing to advise on. In particular the
    unused-`nature` check must not fire on zero weaknesses."""
    assert catalog_warnings(catalog_dir()) == []


def test_gating_link_to_non_gating_control_is_flagged(catalog_dir):
    d = catalog_dir(
        mitigations=[{"id": "CTRL-LOG", "mitigation_class": "detector"}],
        threats=[
            {
                "id": "T-LEAK",
                "mitigations": [
                    {"id": "CTRL-LOG", "strength": "gating", "rationale": "records the access"}
                ],
                "references": [{"title": "A leak writeup", "url": "https://example.com/leak", "note": "shows the path end to end"}],
                "weaknesses": [
                    {"component": "tool", "text": "no scoping", "nature": "secondary"},
                ],
            }
        ],
    )
    items = catalog_warnings_structured(d)
    assert _categories(items) == ["over_graded_strength"]
    hit = items[0]
    assert hit["entity_type"] == "threat"
    assert hit["entity_id"] == "T-LEAK"
    assert "should not back a gating link" in hit["message"]
    assert "is a detector" in hit["message"]


def test_soft_link_to_non_gating_control_is_not_flagged(catalog_dir):
    d = catalog_dir(
        mitigations=[{"id": "CTRL-LOG", "mitigation_class": "detector"}],
        threats=[
            {
                "id": "T-LEAK",
                "mitigations": [
                    {"id": "CTRL-LOG", "strength": "soft", "rationale": "shortens dwell time"}
                ],
                "references": [{"title": "A leak writeup", "url": "https://example.com/leak", "note": "shows the path end to end"}],
                "weaknesses": [{"component": "tool", "text": "no scoping", "nature": "secondary"}],
            }
        ],
    )
    # Asserts the one thing this test is about. It used to assert that there were no
    # warnings at all, which passed only because the "all soft, nothing closes it"
    # advice was being filed as an error instead.
    from keel.catalog import catalog_warnings_structured

    assert not [w for w in catalog_warnings_structured(d)
                if w["category"] == "over_graded_strength"]


def test_threat_without_references_is_flagged(catalog_dir):
    d = catalog_dir(
        threats=[
            {"id": "T-ONE", "weaknesses": [{"component": "tool", "text": "a", "nature": "secondary"}]},
            {
                "id": "T-TWO",
                "references": [{"title": "An advisory", "url": "https://example.com/advisory", "note": "vendor confirmed it"}],
                "weaknesses": [{"component": "tool", "text": "b", "nature": "secondary"}],
            },
        ]
    )
    items = catalog_warnings_structured(d)
    assert _categories(items) == ["missing_references"]
    assert items[0]["entity_id"] == "T-ONE"


def test_nature_flagged_as_unused_when_every_weakness_is_targeted(catalog_dir):
    d = catalog_dir(
        threats=[
            {
                "id": "T-ONE",
                "references": [{"title": "A leak writeup", "url": "https://example.com/leak", "note": "shows the path end to end"}],
                "weaknesses": [{"component": "tool", "text": "a", "nature": "targeted"}],
            }
        ]
    )
    items = catalog_warnings_structured(d)
    assert _categories(items) == ["unused_nature"]
    assert items[0]["entity_type"] is None
    assert items[0]["entity_id"] is None


def test_catalog_warnings_strings_match_structured_messages(catalog_dir):
    """catalog_warnings() must stay a pure projection of the structured data —
    same messages, same order, nothing lost in the format-string round trip."""
    d = catalog_dir(
        mitigations=[{"id": "CTRL-LOG", "mitigation_class": "detector"}],
        threats=[
            {
                "id": "T-LEAK",
                "mitigations": [{"id": "CTRL-LOG", "strength": "gating", "rationale": "logs"}],
            }
        ],
    )
    assert catalog_warnings(d) == [w["message"] for w in catalog_warnings_structured(d)]


def _run_validate(catalog_path, *flags):
    env = {**os.environ, "CATALOG_DIR": str(catalog_path)}
    return subprocess.run(
        [sys.executable, "-m", "keel", "validate", *flags],
        capture_output=True,
        text=True,
        env=env,
    )


def test_validate_non_strict_exits_zero_and_prints_warnings(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-ONE"}])
    r = _run_validate(d)
    assert r.returncode == 0, r.stderr
    assert "no references" in r.stderr, r.stderr


def test_validate_strict_exits_one_on_warnings(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-ONE"}])
    r = _run_validate(d, "--strict")
    assert r.returncode == 1, r.stderr
    assert "treated as errors" in r.stderr, r.stderr


def test_validate_exits_one_on_hard_error(catalog_dir):
    """A dangling link is an error, not advice — it fails without --strict."""
    d = catalog_dir(
        threats=[
            {"id": "T-ONE", "mitigations": [{"id": "CTRL-GONE", "strength": "soft", "rationale": "x"}]}
        ]
    )
    r = _run_validate(d)
    assert r.returncode == 1, r.stderr
    assert "CTRL-GONE" in r.stderr and "not in the catalog" in r.stderr, r.stderr


# --------------------------------------------------------------------------- #
# The two channels must not mix
# --------------------------------------------------------------------------- #
def test_authoring_advice_is_a_warning_not_an_error(catalog_dir):
    """`lint_threat`'s output used to be appended to validate_catalog's ERROR list, so a
    structurally perfect threat whose controls happen to all be soft failed CI. That is
    an ordinary in-progress state, and the function's own docstring called the advice
    non-blocking while the code blocked on it."""
    d = catalog_dir(
        mitigations=[{"id": "CTRL-LOG", "mitigation_class": "detector"}],
        threats=[{"id": "T-SOFT", "mitigations": [
            {"id": "CTRL-LOG", "strength": "soft", "rationale": "Lowers likelihood."}]}],
    )
    assert validate_catalog(d) == []
    assert any("nothing closes this threat" in w for w in catalog_warnings(d))


def test_a_real_defect_is_still_an_error(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-D", "mitigations": [
        {"id": "CTRL-GHOST", "strength": "soft", "rationale": "x"}]}])
    assert any("CTRL-GHOST" in e and "not in the catalog" in e for e in validate_catalog(d))


def test_advice_carries_the_entity_it_belongs_to(catalog_dir):
    """So the dashboard can pin it to a row rather than printing a loose sentence."""
    from keel.catalog import catalog_warnings_structured

    d = catalog_dir(
        mitigations=[{"id": "CTRL-LOG", "mitigation_class": "detector"}],
        threats=[{"id": "T-SOFT", "mitigations": [
            {"id": "CTRL-LOG", "strength": "soft", "rationale": "Lowers likelihood."}]}],
    )
    hit = next(w for w in catalog_warnings_structured(d)
               if w["category"] == "no_gating_control")
    assert hit["entity_type"] == "threat" and hit["entity_id"] == "T-SOFT"
