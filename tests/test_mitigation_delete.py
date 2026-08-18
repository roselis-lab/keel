"""Deleting a mitigation that is linked to a threat.

Points the global store at a temp catalog holding one threat linked to one
mitigation, then exercises `delete_mitigation` — which is documented to unlink the
mitigation from any referencing threats before removing it.
"""
import pytest

from keel.services.mitigation_service import delete_mitigation
from keel.store import Store, set_store


@pytest.fixture
def store(tmp_path):
    (tmp_path / "threats").mkdir()
    (tmp_path / "mitigations").mkdir()
    s = Store(tmp_path)
    s.mitigations["CTRL-DLP"] = {
        "id": "CTRL-DLP", "name": "Data-loss prevention", "mitigation_class": "gating_control",
    }
    s.threats["T-DEMO"] = {
        "id": "T-DEMO",
        "title": "Sensitive data disclosure",
        "harm": "data-exposed",
        "weaknesses": [{"component": "tool", "text": "returns raw records", "nature": "targeted"}],
        "reachability": "NOT applicable if the model sees no secrets",
        "mitigations": [{"id": "CTRL-DLP", "strength": "gating", "rationale": "blocks the path"}],
    }
    set_store(s)
    yield s
    set_store(None)


@pytest.mark.asyncio
async def test_preview_counts_linked_threats(store):
    """The unconfirmed preview counts the threats that reference the mitigation."""
    result = await delete_mitigation("CTRL-DLP", confirm=False)
    assert result["confirm_required"] is True
    assert result["preview"]["linked_threats"] == 1


@pytest.mark.asyncio
async def test_confirmed_delete_unlinks_and_removes(store):
    """Confirmed delete drops the mitigation and unlinks it from the threat."""
    result = await delete_mitigation("CTRL-DLP", confirm=True)
    assert result["success"] is True
    assert result["removed_links"] == 1
    assert "CTRL-DLP" not in store.mitigations
    assert store.threats["T-DEMO"]["mitigations"] == []
