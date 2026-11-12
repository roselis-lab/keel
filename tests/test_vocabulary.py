"""The vocabulary files and the Literals that enforce them must agree.

`catalog/{harm,surface,source,components}.yaml` existed and nothing read them. A file
that describes the system but is never loaded is worse than no file: it drifts, and the
drift is invisible. They are the source of the human gloss now, and disagreement with
the schema is an error.
"""
import yaml

from keel.catalog import validate_catalog
from keel.store import Store
from keel.vocabulary import VOCABULARIES, load_vocabularies, vocabulary_errors


def test_the_shipped_vocabularies_match_the_schema():
    assert vocabulary_errors() == []


def test_every_value_in_every_literal_is_glossed():
    vocab = load_vocabularies()
    for stem, (key, allowed) in VOCABULARIES.items():
        assert set(vocab[stem]) == set(allowed), stem
        for value, entry in vocab[stem].items():
            assert entry["name"] and entry["desc"], (stem, value)


def test_a_value_in_the_file_but_not_the_schema_is_an_error(catalog_dir):
    d = catalog_dir()
    data = yaml.safe_load((d / "harm.yaml").read_text(encoding="utf-8"))
    data["harm"]["invented-harm"] = {"name": "Invented", "desc": "Not in the Literal."}
    (d / "harm.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    errs = vocabulary_errors(d)
    assert any("invented-harm" in e and "not in the schema" in e for e in errs), errs
    assert any("invented-harm" in e for e in validate_catalog(d))


def test_a_value_in_the_schema_but_not_the_file_is_an_error(catalog_dir):
    d = catalog_dir()
    data = yaml.safe_load((d / "surface.yaml").read_text(encoding="utf-8"))
    del data["surface"]["agent-message"]
    (d / "surface.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    errs = vocabulary_errors(d)
    assert any("agent-message" in e and "not glossed here" in e for e in errs), errs


def test_a_value_missing_its_gloss_is_an_error(catalog_dir):
    d = catalog_dir()
    data = yaml.safe_load((d / "source.yaml").read_text(encoding="utf-8"))
    data["source"]["model-mistake"] = {"name": "Model: honest mistake"}   # no desc
    (d / "source.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    assert any("model-mistake" in e and "desc" in e for e in vocabulary_errors(d))


def test_every_surface_lists_its_variants():
    """The assessor reads these while building the surface ledger; a surface with none
    leaves its ledger rows to memory."""
    for value, entry in load_vocabularies()["surface"].items():
        assert entry["variants"], value
        assert all(isinstance(x, str) and x.strip() for x in entry["variants"]), value


def test_a_surface_without_variants_is_an_error(catalog_dir):
    d = catalog_dir()
    data = yaml.safe_load((d / "surface.yaml").read_text(encoding="utf-8"))
    del data["surface"]["memory"]["variants"]
    data["surface"]["tool-output"]["variants"] = ["fine", ""]
    (d / "surface.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    errs = vocabulary_errors(d)
    assert any("'memory'" in e and "variants" in e for e in errs), errs
    assert any("'tool-output'" in e and "not a non-empty string" in e for e in errs), errs


def test_variants_are_served_with_the_vocabulary(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-A"}])
    assert Store(d).vocabulary["surface"]["model-output"]["variants"]


def test_a_missing_file_is_an_error(catalog_dir):
    d = catalog_dir()
    (d / "components.yaml").unlink()
    assert any("components.yaml: missing" in e for e in vocabulary_errors(d))


def test_the_store_carries_the_vocabulary_and_reports_its_defects(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-A"}])
    store = Store(d)
    assert store.vocabulary["components"]["downstream"]["name"] == "Downstream consumer"
    assert store.problems == []

    (d / "harm.yaml").unlink()
    store.reload()
    problem = next(p for p in store.problems if p["file"] == "harm.yaml")
    # Not dropped: the catalog still loads, the gloss is just gone.
    assert problem["dropped"] is False
    assert "missing" in problem["message"]
