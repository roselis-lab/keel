"""The Implementation entity attached to a mitigation.

An Implementation records how an org realizes a control: a short title, the
concrete details, and an optional reference link. The reference catalog ships
these empty; orgs fill them after forking, so the field defaults to [].
"""
import pytest
from pydantic import ValidationError

from keel.schemas.mitigation import Implementation, MitigationCreate


def test_valid_implementation_parses():
    impl = Implementation(
        title="Platform-enforced tool sandbox",
        description="Tool calls run in a locked-down container with no network egress.",
        reference="https://example.com/runbook",
    )
    assert impl.title == "Platform-enforced tool sandbox"
    assert str(impl.reference) == "https://example.com/runbook"


def test_implementation_missing_title_raises():
    with pytest.raises(ValidationError):
        Implementation(description="details but no title")


def test_reference_rejects_non_url():
    with pytest.raises(ValidationError):
        Implementation(title="t", description="d", reference="not a url")


def test_reference_is_optional():
    impl = Implementation(title="t", description="d")
    assert impl.reference is None


def test_mitigation_default_implementations_is_empty():
    m = MitigationCreate(id="CTRL-X", name="X", mitigation_class="gating_control")
    assert m.implementations == []


def test_mitigation_carries_implementations():
    m = MitigationCreate(
        id="CTRL-X",
        name="X",
        mitigation_class="gating_control",
        implementations=[{"title": "t", "description": "d"}],
    )
    assert m.implementations[0].title == "t"
