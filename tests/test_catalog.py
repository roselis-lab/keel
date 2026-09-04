"""Catalog validation: the shipped catalog is valid, and bad records are caught."""
from keel.catalog import validate_catalog


def test_shipped_catalog_is_valid():
    """The catalog that ships in the repo passes validation."""
    assert validate_catalog() == []


def test_validate_accepts_mitigation_with_implementations(catalog_dir):
    tmp_path = catalog_dir()
    (tmp_path / "mitigations" / "CTRL-Z.yaml").write_text(
        "id: CTRL-Z\nname: Z\nmitigation_class: gating_control\n"
        "purpose: Stops the action leaving on model judgement.\n"
        "scope: Every tool call that moves money.\n"
        "out_of_scope: Reads that change nothing.\n"
        "control_mechanism: A middleware before the call.\n"
        "locus: {value: infrastructure, note: A property of the runtime.}\n"
        "failure_behavior: {value: fail_closed, note: Without an approval nothing runs.}\n"
        "implementations:\n"
        "- title: Platform sandbox\n"
        "  description: Tool calls run in a locked-down container.\n"
        "  reference: https://example.com/runbook\n",
        encoding="utf-8",
    )
    assert validate_catalog(tmp_path) == []


def test_validate_catches_bad_records(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    (tmp_path / "threats" / "T-BAD.yaml").write_text(
        "id: T-BAD\n"
        "title: bad\n"
        "harm: nonsense\n"                       # not in the enum
        "weaknesses:\n- {component: tool, text: w}\n"
        "reachability: x\n"
        "oops: 1\n",                             # unknown field
        encoding="utf-8",
    )
    joined = " ".join(validate_catalog(tmp_path))
    assert "harm" in joined      # invalid enum caught
    assert "oops" in joined      # unknown field caught (extra=forbid)


def test_validate_flags_dangling_mitigation(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    (tmp_path / "threats" / "T-D.yaml").write_text(
        "id: T-D\ntitle: t\nharm: code-execution\n"
        "weaknesses:\n- {component: tool, text: w, nature: targeted}\n"
        "reachability: x\n"
        "mitigations:\n- {id: CTRL-GHOST, strength: gating, rationale: x}\n",
        encoding="utf-8",
    )
    assert any("CTRL-GHOST" in e and "not in the catalog" in e
               for e in validate_catalog(tmp_path))


def test_validate_flags_id_filename_mismatch(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    (tmp_path / "mitigations" / "CTRL-X.yaml").write_text(
        "id: CTRL-Y\nname: t\nmitigation_class: gating_control\n", encoding="utf-8"
    )
    assert any("does not match filename" in e for e in validate_catalog(tmp_path))
