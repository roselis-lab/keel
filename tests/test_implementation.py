"""The Implementation entity attached to a mitigation.

An Implementation records how an org realizes a control: a short title, the
concrete details, and an optional reference link. The reference catalog ships
these empty; orgs fill them after forking, so the field defaults to [].
"""
import pytest
from pydantic import ValidationError

from keel.schemas.mitigation import Implementation, MitigationCreate
from keel.services.mitigation_service import create_mitigation, get_mitigation
from keel.store import Store, set_store


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


def test_implementation_defaults_to_local_coverage():
    impl = Implementation(title="t", description="d")
    assert impl.coverage == "local"
    assert impl.covers is None


def test_shared_coverage_requires_covers():
    with pytest.raises(ValidationError):
        Implementation(title="t", description="d", coverage="shared")


def test_shared_coverage_with_covers_parses():
    impl = Implementation(title="t", description="d", coverage="shared", covers="all agents on the Agent Platform")
    assert impl.covers == "all agents on the Agent Platform"


def test_local_coverage_rejects_covers():
    with pytest.raises(ValidationError):
        Implementation(title="t", description="d", coverage="local", covers="all agents on the Agent Platform")


def test_implementation_owner_defaults_to_none():
    impl = Implementation(title="t", description="d")
    assert impl.owner is None


def test_implementation_accepts_owner():
    impl = Implementation(title="t", description="d", owner="platform security engineering")
    assert impl.owner == "platform security engineering"


def test_mitigation_has_no_owner_field():
    """owner lives on Implementation now (accountable per real deployment), not on the
    abstract mitigation card — see keel/schemas/mitigation.py MitigationBase."""
    m = MitigationCreate(id="CTRL-X", name="X", mitigation_class="gating_control")
    assert not hasattr(m, "owner")


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


@pytest.fixture
def temp_store(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    set_store(Store(tmp_path))
    yield
    set_store(None)


@pytest.mark.asyncio
async def test_get_mitigation_round_trips_implementations(temp_store):
    await create_mitigation(
        MitigationCreate(
            id="CTRL-RT",
            name="Round trip",
            mitigation_class="gating_control",
            implementations=[
                {"title": "Platform sandbox", "description": "locked-down container"}
            ],
        )
    )
    got = await get_mitigation("CTRL-RT")
    assert got["success"] is True
    assert got["implementations"] == [
        {
            "title": "Platform sandbox", "description": "locked-down container", "reference": None,
            "coverage": "local", "covers": None, "owner": None,
        }
    ]
