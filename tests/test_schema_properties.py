"""Properties every schema must hold, checked across every schema.

Written after a hole that had seven green tests sitting next to it. `extra="forbid"` was
asserted per model - on Report, on RunMeta, on Threat - and Mitigation simply never got
one, so a misspelled field was silently dropped and the write still answered "changed".
Seven tests of the same property, none of them covering the model that lacked it.

A property stated once over every model covers the models nobody thought about, and the
ones that do not exist yet. These tests are cheap and they replace a dozen per-field
assertions that only re-tested pydantic.
"""
import pytest
from pydantic import BaseModel, ValidationError

from keel.schemas import coverage, mitigation, report, style_guide, threat

MODULES = (threat, mitigation, report, coverage, style_guide)

# Models that describe a payload arriving from outside. Response shapes are excluded:
# they are built by us from records already validated, and forbidding extras there would
# only stop us adding a derived field like `cited_by` to an answer.
RESPONSE_MODELS = {"Mitigation", "Threat"}


def _models():
    seen = {}
    for module in MODULES:
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
                if obj.__module__.startswith("keel."):
                    seen[f"{obj.__module__}.{obj.__name__}"] = obj
    return sorted(seen.items())


def test_there_are_models_to_check():
    """A silent empty parametrisation would make every test below vacuously pass."""
    assert len(_models()) > 10


@pytest.mark.parametrize("name,model", _models(), ids=lambda x: x if isinstance(x, str) else "")
def test_every_input_model_refuses_unknown_fields(name, model):
    """A dropped field is worse than a rejected one: the caller is told it was saved."""
    if model.__name__ in RESPONSE_MODELS and "Create" not in name and "Update" not in name:
        pytest.skip("response shape, not an input")
    with pytest.raises(ValidationError):
        model.model_validate({"definitely_not_a_field_xyz": 1})


@pytest.mark.parametrize("name,model", _models(), ids=lambda x: x if isinstance(x, str) else "")
def test_every_id_field_is_constrained_to_a_file_name(name, model):
    """An id is also a file name. The store refuses to leave its directory regardless,
    but a model that lets `../../x` through pushes a readable error down to a layer that
    can only say "not a usable file name"."""
    field = model.model_fields.get("id")
    if field is None or field.annotation is not str:
        pytest.skip("no plain string id")
    with pytest.raises(ValidationError):
        model.model_validate({"id": "../../escape"})


def test_every_frozen_vocabulary_is_glossed():
    """A Literal the catalog cannot explain is a token the reader has to guess at."""
    from keel.vocabulary import VOCABULARIES, load_vocabularies

    vocab = load_vocabularies()
    for stem, (_key, allowed) in VOCABULARIES.items():
        assert set(vocab[stem]) == set(allowed), stem


# --------------------------------------------------------------------------- #
# Where the surface lives
# --------------------------------------------------------------------------- #
def test_the_surface_is_a_property_of_the_weakness_not_the_threat():
    """A threat is a chain and crosses more than one boundary, so a list on the threat
    could never say which weakness sits on which. It moved down to the weakness, where
    component + surface together name the place a control has to sit."""
    assert "surface" not in threat.Threat.model_fields
    assert "surface" not in threat.ThreatUpdate.model_fields
    assert "surface" in threat.Weakness.model_fields


def test_a_weakness_about_authority_needs_no_surface():
    """Not every weakness is content flowing in. A token scoped wider than the request
    that uses it has nothing crossing a channel, and forcing a channel onto it would put
    a wrong answer in a field readers filter on."""
    w = threat.Weakness(component="identity-store", text="a standing token, full scope")
    assert w.surface == []
