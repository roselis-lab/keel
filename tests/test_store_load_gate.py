"""Loading is a gate: a record that fails its schema never enters the working set.

Every write path validates, so a bad record can only arrive by hand-editing YAML or
pulling someone else's. Before this gate those records loaded silently and the app
served them; `keel validate` only found out when a person happened to run it.
"""
import pytest
import yaml

from keel.services.health_service import check_library_health
from keel.store import Store, set_store


def _problems_for(store, entity_id):
    return [p for p in store.problems if p["entity_id"] == entity_id]


def test_valid_records_load_with_no_problems(catalog_dir):
    store = Store(catalog_dir(
        mitigations=[{"id": "CTRL-A"}],
        threats=[{"id": "T-A", "mitigations": [
            {"id": "CTRL-A", "strength": "gating", "rationale": "blocks it"}
        ]}],
    ))
    assert list(store.threats) == ["T-A"]
    assert list(store.mitigations) == ["CTRL-A"]
    assert store.problems == []


def test_bad_enum_value_is_dropped_and_reported(catalog_dir):
    store = Store(catalog_dir(threats=[
        {"id": "T-GOOD"},
        {"id": "T-BAD", "harm": "not-a-harm"},
    ]))
    assert list(store.threats) == ["T-GOOD"]
    p = _problems_for(store, "T-BAD")[0]
    assert p == {
        "file": "threats/T-BAD.yaml",
        "entity_type": "threat",
        "entity_id": "T-BAD",
        "field": "harm",
        "message": p["message"],
        "dropped": True,
    }
    assert "data-exposed" in p["message"]  # the message lists what was allowed


def test_unknown_field_is_dropped(catalog_dir):
    """`extra="forbid"` is what makes a renamed field visible instead of silently ignored."""
    store = Store(catalog_dir(threats=[{"id": "T-OLD", "impact_class": "data-exposed"}]))
    assert store.threats == {}
    assert _problems_for(store, "T-OLD")[0]["field"] == "impact_class"


def test_id_filename_mismatch_is_dropped(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-A"}])
    (d / "threats" / "T-A.yaml").rename(d / "threats" / "T-RENAMED.yaml")
    store = Store(d)
    assert store.threats == {}
    p = store.problems[0]
    assert p["field"] == "id"
    assert "does not match filename" in p["message"]


def test_unparseable_yaml_is_dropped(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-A"}])
    (d / "threats" / "T-BROKEN.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    store = Store(d)
    assert list(store.threats) == ["T-A"]
    broken = [p for p in store.problems if p["file"] == "threats/T-BROKEN.yaml"][0]
    assert "not readable as YAML" in broken["message"]


def test_a_dangling_link_does_not_stop_the_threat_loading(catalog_dir):
    """The rest of the threat is still true, so evicting it would hide more than it shows.

    The store says nothing about the link: whether it resolves is a question about the
    catalog rather than about this record, and it is answered once, by the rules. It used
    to be answered here as well, which handed the dashboard the same defect twice at two
    different severities."""
    from keel.rules import Catalog, check_entity

    store = Store(catalog_dir(threats=[
        {"id": "T-A", "mitigations": [{"id": "CTRL-GONE", "strength": "soft", "rationale": "r"}]}
    ]))
    assert list(store.threats) == ["T-A"]
    assert store.problems == []

    finding = next(f for f in check_entity("threat", "T-A", Catalog.from_store(store))
                   if f.code == "dangling_link")
    assert finding.field == "mitigations.0.id"
    assert "CTRL-GONE" in finding.message


def test_malformed_style_guide_is_reported(catalog_dir):
    d = catalog_dir(style_guide={"threat": {"title": {"purpose": "The name."}}})
    (d / "style_guide" / "broken.yaml").write_text(
        yaml.safe_dump({"no_fields_key": True}), encoding="utf-8"
    )
    store = Store(d)
    assert "threat" in store.style_guide
    assert "broken" not in store.style_guide
    assert [p["file"] for p in store.problems] == ["style_guide/broken.yaml"]


def test_reload_clears_stale_problems(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-BAD", "harm": "not-a-harm"}])
    store = Store(d)
    assert store.problems

    (d / "threats" / "T-BAD.yaml").write_text(
        yaml.safe_dump({
            "id": "T-BAD", "title": "Fixed", "harm": "data-exposed",
            "weaknesses": [{"component": "tool", "text": "x"}], "reachability": "r",
        }),
        encoding="utf-8",
    )
    store.reload()
    assert store.problems == []
    assert list(store.threats) == ["T-BAD"]


@pytest.mark.asyncio
async def test_health_surfaces_load_errors(catalog_dir):
    """The dashboard reads this. A hard error that never reaches a screen is not enforced."""
    store = Store(catalog_dir(threats=[{"id": "T-BAD", "harm": "not-a-harm"}]))
    set_store(store)
    try:
        result = await check_library_health()
        assert result["error_count"] == 1
        # A record that failed its schema is a load problem, not a rule finding: it is
        # not in the catalog for a rule to have an opinion about.
        assert result["load_problems"][0]["entity_id"] == "T-BAD"
        assert result["load_problems"][0]["field"] == "harm"
    finally:
        set_store(None)
