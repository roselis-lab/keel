"""Catalog validation: the shipped catalog is valid, and bad records are caught."""
from app.catalog import validate_catalog


def test_shipped_catalog_is_valid():
    """The catalog that ships in the repo passes validation."""
    assert validate_catalog() == []


def test_validate_catches_bad_records(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    (tmp_path / "threats" / "T-BAD.yaml").write_text(
        "id: T-BAD\n"
        "impact_class: nonsense\n"       # not in the enum
        "oops: 1\n"                       # unknown field
        "mitigations:\n"
        "- mitigation_id: CTRL-GHOST\n"   # dangling link
        "  rationale: x\n",
        encoding="utf-8",
    )
    joined = " ".join(validate_catalog(tmp_path))
    assert "unknown field" in joined
    assert "impact_class" in joined
    assert "unknown mitigation" in joined


def test_validate_flags_id_filename_mismatch(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    (tmp_path / "mitigations" / "CTRL-X.yaml").write_text(
        "id: CTRL-Y\nname: t\nmitigation_class: gating_control\n", encoding="utf-8"
    )
    assert any("does not match filename" in e for e in validate_catalog(tmp_path))
