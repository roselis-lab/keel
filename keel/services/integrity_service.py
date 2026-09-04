"""What the rules say about one record, right after it was written.

Everything here is advice. The record is already on disk - pydantic and the service
guards refused anything that could not be written at all - so the question left is not
"may this exist" but "what is still wrong with it". Blocking now would be theatre.

The rules themselves live in `keel.rules`, shared with `keel validate`. This module is
the thin adapter: fetch the catalog, run the rules for one entity, hand back plain dicts.
"""
from __future__ import annotations

from typing import Any

from keel.rules import Catalog, check_entity
from keel.store import get_store


def after_write(entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    """Findings about `entity_id`. Empty is the normal answer."""
    from keel.services.coverage_service import load_sources

    store = get_store()
    cat = Catalog.from_store(store, coverage=load_sources())
    return [f.as_dict() for f in check_entity(entity_type, entity_id, cat)]
