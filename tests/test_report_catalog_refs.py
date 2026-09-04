"""A report may ask for a control the library does not have — but not by inventing an id.

`mitigation_id: null` + `description` is the supported way to record an ask with no
cataloged control behind it, and `insights()` reads exactly those as the library's own
to-do list. A made-up id looks like a cataloged control, resolves to nothing, and
nothing downstream can tell the two apart — so it is refused on save.
"""
import pytest
import yaml

from keel.errors import Invalid
import keel.config
from keel.services import report_service
from keel.store import Store, set_store


def _report(requirements):
    return {
        "system_id": "demo",
        "system_name": "Demo",
        "system_description": "A system.",
        "date": "2026-08-29",
        "assessor": "Tester <t@example.com>",
        "status": "draft",
        "findings": [{
            "id": "T-A",
            "from_catalog": True,
            "scenario": "Something goes wrong in a way a reader can picture.",
            "source": {"who": "external-attacker", "motive": "money", "access": "the chat"},
            "asset": "customer records",
            "attack_surface": "user-input",
            "vulnerability": "no scoping on lookups",
            "exploitation_complexity": "low",
            "harm": "data-exposed",
            "risk": {"likelihood": "high", "severity": "high", "reasoning": "Reachable by anyone."},
            "delta": "new: the lookup tool was added this quarter",
            "requirements": requirements,
        }],
    }


@pytest.fixture
def catalog(catalog_dir, tmp_path, monkeypatch):
    d = catalog_dir(
        mitigations=[{"id": "CTRL-REAL"}],
        threats=[{"id": "T-A"}],
    )
    set_store(Store(d))
    reports = tmp_path / "reports"
    (reports / "demo").mkdir(parents=True)
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(reports))
    yield reports
    set_store(None)


def _seed(reports, payload):
    (reports / "demo" / "2026-08-29.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )


def test_a_requirement_with_no_catalog_control_is_allowed(catalog):
    """The wanted case: the assessment names something the library is missing."""
    payload = _report([{
        "mitigation_id": None,
        "coverage_status": "needs_implementation",
        "description": "Refuse a refund unless the warehouse recorded the return.",
    }])
    _seed(catalog, payload)
    result = report_service.save_report("demo", "2026-08-29", payload)
    assert result["success"] is True


def test_a_requirement_naming_a_real_control_is_allowed(catalog):
    payload = _report([{
        "mitigation_id": "CTRL-REAL",
        "coverage_status": "needs_implementation",
    }])
    _seed(catalog, payload)
    assert report_service.save_report("demo", "2026-08-29", payload)["success"] is True


def test_an_invented_mitigation_id_is_refused(catalog):
    payload = _report([{
        "mitigation_id": "CTRL-SOUNDS-PLAUSIBLE",
        "coverage_status": "needs_implementation",
    }])
    _seed(catalog, payload)
    with pytest.raises(Invalid) as exc:
        report_service.save_report("demo", "2026-08-29", payload)
    assert "CTRL-SOUNDS-PLAUSIBLE" in " ".join(d["message"] for d in exc.value.details)
    # The error has to name the supported alternative, or it just blocks the agent.
    assert "leave mitigation_id empty" in exc.value.hint


def test_an_invented_id_in_ignored_mitigations_is_refused(catalog):
    payload = _report([])
    payload["findings"][0]["ignored_mitigations"] = [
        {"mitigation_id": "CTRL-GHOST", "reason": "would not stop the first loss"}
    ]
    _seed(catalog, payload)
    with pytest.raises(Invalid) as exc:
        report_service.save_report("demo", "2026-08-29", payload)
    assert "CTRL-GHOST" in " ".join(d["message"] for d in exc.value.details)


def test_from_catalog_on_a_threat_that_is_not_in_the_catalog_is_refused(catalog):
    payload = _report([])
    payload["findings"][0]["id"] = "T-INVENTED"
    _seed(catalog, payload)
    with pytest.raises(Invalid) as exc:
        report_service.save_report("demo", "2026-08-29", payload)
    assert "from_catalog" in " ".join(d["message"] for d in exc.value.details)


def test_a_system_specific_threat_is_allowed_when_not_marked_from_catalog(catalog):
    payload = _report([])
    payload["findings"][0]["id"] = "T-INVENTED"
    payload["findings"][0]["from_catalog"] = False
    _seed(catalog, payload)
    assert report_service.save_report("demo", "2026-08-29", payload)["success"] is True


def test_a_discarded_threat_must_be_a_real_one(catalog):
    payload = _report([])
    payload["discarded"] = [{"id": "T-NOPE", "reason": "no interpreter here"}]
    _seed(catalog, payload)
    with pytest.raises(Invalid) as exc:
        report_service.save_report("demo", "2026-08-29", payload)
    assert "T-NOPE" in " ".join(d["message"] for d in exc.value.details)
