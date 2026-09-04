"""Report schema — a persisted assess-genai-with-library run.

The skill writes the first pass; the specialist corrects it while it is a draft, and
finalizing freezes it. The conditional validators on `Requirement` follow the same
`model_validator(mode="after")` pattern as `Implementation.coverage`/`covers`.
"""
import pytest
from pydantic import ValidationError

from keel.schemas.report import Discarded, Finding, IgnoredMitigation, Report, Requirement


def _requirement(**over):
    base = dict(mitigation_id="CTRL-URL-ALLOWLIST", coverage_status="needs_implementation")
    base.update(over)
    return Requirement(**base)


def test_requirement_with_mitigation_id_needs_no_description():
    assert _requirement().description is None


def test_requirement_without_mitigation_id_requires_description():
    with pytest.raises(ValidationError):
        _requirement(mitigation_id=None)


def test_requirement_without_mitigation_id_and_description_is_valid():
    r = _requirement(mitigation_id=None, description="Restrict outbound requests to an allowlist.")
    assert r.description == "Restrict outbound requests to an allowlist."


def test_requirement_rejects_description_when_mitigation_id_set():
    with pytest.raises(ValidationError):
        _requirement(description="redundant — the catalog card already names it")


def test_requirement_already_covered_requires_coverage_note():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="already_covered")


def test_requirement_partial_requires_coverage_note():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="partial")


def test_requirement_already_covered_with_note_is_valid():
    r = _requirement(coverage_status="already_covered", coverage_note="Closed by a shared Vault instance.")
    assert r.coverage_note == "Closed by a shared Vault instance."


def test_requirement_needs_implementation_rejects_stray_coverage_note():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="needs_implementation", coverage_note="shouldn't be here")


def test_discarded_has_no_chain_fields():
    """A discard is an id + why. Deliberately NOT the full Finding chain."""
    d = Discarded(id="T-XSS", reason="output is plain JSON, no render path")
    assert d.model_dump() == {"id": "T-XSS", "reason": "output is plain JSON, no render path"}
    with pytest.raises(ValidationError):
        Discarded(id="T-XSS", reason="...", asset="should not be accepted")


def _finding(**over):
    base = dict(
        id="T-SSRF", from_catalog=True, scenario="an attacker reaches an internal service via SSRF",
        source={"who": "external-attacker", "motive": "recon", "access": "the public API"},
        asset="internal metadata endpoint", attack_surface="tool-output",
        vulnerability="a tool builds a URL from unvalidated model output",
        exploitation_complexity="medium", harm="data-exposed",
        risk={"likelihood": "medium", "severity": "high", "reasoning": "reachable, no compensating control"},
        delta="new attack surface introduced by the outbound-fetch tool",
    )
    base.update(over)
    return Finding(**base)


def test_finding_parses_with_catalog_enums():
    f = _finding()
    assert f.harm == "data-exposed"
    assert f.attack_surface == "tool-output"
    assert f.source.who == "external-attacker"


def test_finding_carries_requirements_and_ignored_mitigations():
    f = _finding(
        requirements=[{"mitigation_id": "CTRL-URL-ALLOWLIST", "coverage_status": "needs_implementation"}],
        ignored_mitigations=[{"mitigation_id": "CTRL-SOME-OTHER", "reason": "no outbound egress on this system"}],
    )
    assert isinstance(f.requirements[0], Requirement)
    assert isinstance(f.ignored_mitigations[0], IgnoredMitigation)


def test_report_parses_minimal():
    r = Report(
        system_id="checkout-agent", system_name="Checkout Agent",
        system_description="Handles checkout for the storefront.",
        date="2026-08-26", assessor="Jane Doe <jane@example.com>",
        findings=[_finding().model_dump()],
        discarded=[{"id": "T-XSS", "reason": "no render path"}],
        meta={"questions": [{"question": "q", "answer": "a", "impact": "i"}]},
    )
    assert r.system_id == "checkout-agent"
    assert len(r.findings) == 1


def test_report_defaults_lists_to_empty():
    r = Report(
        system_id="x", system_name="X", system_description="d",
        date="2026-08-26", assessor="a",
    )
    assert r.findings == [] and r.discarded == []
    assert r.delta_summary is None


def test_report_without_meta_gets_an_empty_one():
    """Reports written before the block existed still parse, and read as "we kept no
    record of how this ran" rather than blowing up."""
    r = Report(
        system_id="x", system_name="X", system_description="d",
        date="2026-08-26", assessor="a",
    )
    assert r.meta.questions == [] and r.meta.volunteered == [] and r.meta.critique == []
    assert r.meta.started_at is None


def test_meta_keeps_the_three_things_that_improve_the_skill():
    r = Report(
        system_id="x", system_name="X", system_description="d",
        date="2026-08-26", assessor="a",
        meta={
            "started_at": "2026-08-26T14:05:00", "finished_at": "2026-08-26T14:58:00",
            "questions": [{"question": "capped?", "answer": "200 EUR", "impact": "kept it high"}],
            "volunteered": ["the tool runs under a service account — never asked"],
            "critique": ["graded on the cap alone; nothing bounded a sequence of calls"],
        },
    )
    assert r.meta.questions[0].impact == "kept it high"
    # the sharpest signal: a hole in the skill, named
    assert "never asked" in r.meta.volunteered[0]
    assert r.meta.critique


def test_report_starts_as_a_draft():
    """Reports written before the field existed must not read as frozen records."""
    r = Report(
        system_id="x", system_name="X", system_description="d",
        date="2026-08-26", assessor="a",
    )
    assert r.status == "draft"


def test_requirement_included_defaults_to_shipping_it():
    assert _requirement().included is True


def test_requirement_already_covered_defaults_to_not_shipping_it():
    """Nothing to ask the product team for — the control is already in this deployment."""
    r = _requirement(coverage_status="already_covered", coverage_note="the gateway does it")
    assert r.included is False


def test_requirement_included_survives_an_explicit_choice():
    """The specialist can decide either way; the decision is recorded, not re-derived."""
    covered = _requirement(
        coverage_status="already_covered", coverage_note="the gateway does it", included=True
    )
    open_one = _requirement(included=False)
    assert covered.included is True
    assert open_one.included is False
