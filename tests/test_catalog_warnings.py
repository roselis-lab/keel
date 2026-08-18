"""Advisory warnings tier: deterministic quality checks that surface problems on the
real catalog without failing CI. `catalog_warnings()` returns advice; `keel validate`
prints it to stderr but stays exit 0, while `keel validate --strict` exits 1 on warnings.
"""
import subprocess
import sys

from keel.catalog import catalog_warnings, validate_catalog


def test_hard_validation_still_clean():
    """The advisory tier must not disturb the hard-error tier."""
    assert validate_catalog() == []


def test_over_graded_link_strength_warning():
    """A `gating` link to a non-gating control is flagged. Real case: T-CRED-THEFT links
    CTRL-AUDIT-LOGGING as `gating`, but CTRL-AUDIT-LOGGING is a `detector`."""
    warnings = catalog_warnings()
    hit = "T-CRED-THEFT -> CTRL-AUDIT-LOGGING"
    matches = [w for w in warnings if w.startswith(hit)]
    assert matches, warnings
    assert "strength 'gating'" in matches[0]
    assert "mitigation_class is 'detector'" in matches[0]


def test_missing_references_warnings_for_all_thirteen_threats():
    warnings = catalog_warnings()
    ref_warnings = [w for w in warnings if "no references (provenance)" in w]
    assert len(ref_warnings) == 13, ref_warnings
    assert any(w.startswith("T-CRED-THEFT:") for w in ref_warnings)


def test_single_nature_unused_warning():
    warnings = catalog_warnings()
    nature_warnings = [w for w in warnings if "the nature field may be unused" in w]
    assert len(nature_warnings) == 1, nature_warnings
    assert "no weakness is marked 'secondary'" in nature_warnings[0]


def test_validate_non_strict_exits_zero_and_prints_warnings():
    r = subprocess.run(
        [sys.executable, "-m", "keel", "validate"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "Warning" in r.stderr, r.stderr


def test_validate_strict_exits_one_on_warnings():
    r = subprocess.run(
        [sys.executable, "-m", "keel", "validate", "--strict"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1, r.stderr
    assert "Warning" in r.stderr, r.stderr
