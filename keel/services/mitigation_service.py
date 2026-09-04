"""Service layer for mitigation operations (backed by the file store)."""
from typing import Any

from keel.errors import Conflict, IntegrityError, NotFound
from keel.schemas.mitigation import MitigationCreate, MitigationUpdate
from keel.store import MITIGATION_ORDER, get_store

# Fields returnable via `include` (id/name/class are always shown).
_INCLUDABLE = [f for f in MITIGATION_ORDER if f not in ("id", "name", "mitigation_class")]
_LIST_FIELDS = ("anti_patterns", "validation", "faq")


def _mitigation_item(rec: dict[str, Any], include: list[str]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": rec["id"],
        "name": rec.get("name"),
        "mitigation_class": rec.get("mitigation_class"),
    }
    for field in include:
        if field in _INCLUDABLE:
            item[field] = rec.get(field)
    return item


async def list_mitigations(brief: bool = True, include: list[str] | None = None) -> dict[str, Any]:
    """List all mitigations. `brief` returns [id, name, mitigation_class] triples."""
    store = get_store()
    mitigations = [store.mitigations[k] for k in sorted(store.mitigations)]
    if brief:
        return {
            "mitigations": [[m["id"], m.get("name"), m.get("mitigation_class")] for m in mitigations],
            "count": len(mitigations),
        }
    include = include or []
    return {
        "mitigations": [_mitigation_item(m, include) for m in mitigations],
        "count": len(mitigations),
    }


def _cited_by(entity_id: str) -> list[dict[str, str]]:
    """Which tracked sources name this card — see the note in `threat_service`."""
    from keel.services.coverage_service import by_entity

    return by_entity().get(entity_id, [])


async def get_mitigation(mitigation_id: str) -> dict[str, Any]:
    """Get a mitigation card with all fields, plus `cited_by`."""
    rec = _require(mitigation_id)
    response = _mitigation_item(rec, _INCLUDABLE)
    response["cited_by"] = _cited_by(mitigation_id)
    response["success"] = True
    return response


def _require(mitigation_id: str) -> dict[str, Any]:
    """The card, or a NotFound that suggests the id the caller almost typed."""
    store = get_store()
    rec = store.mitigations.get(mitigation_id)
    if rec:
        return rec
    close = [m for m in sorted(store.mitigations)
             if m.lower().startswith(mitigation_id[:6].lower())]
    raise NotFound(
        f"no mitigation {mitigation_id!r}",
        entity_type="mitigation", entity_id=mitigation_id,
        hint=f"did you mean {', '.join(close[:3])}?" if close else
             "call search or list_mitigations to see what is there",
    )


def _check_requires(mitigation_id: str, requires: list[str] | None) -> None:
    """Refuse the write. A prerequisite that does not resolve, points at itself, or
    closes a loop is not advice about an entry - it is an entry that cannot mean
    anything, so it never reaches disk."""
    if not requires:
        return
    store = get_store()

    if mitigation_id in requires:
        raise IntegrityError(
            f"{mitigation_id} cannot require itself",
            entity_type="mitigation", entity_id=mitigation_id, field="requires",
        )
    missing = [m for m in requires if m != mitigation_id and m not in store.mitigations]
    if missing:
        raise IntegrityError(
            f"requires {', '.join(missing)}, which "
            f"{'is' if len(missing) == 1 else 'are'} not in the catalog",
            entity_type="mitigation", entity_id=mitigation_id, field="requires",
            hint="a prerequisite has to be a card that exists; create it first",
        )

    # Walk the graph from each prerequisite; reaching the card again is a cycle, and a
    # cycle means neither card can ever be verified first.
    seen, stack = set(), list(requires)
    while stack:
        current = stack.pop()
        if current == mitigation_id:
            raise IntegrityError(
                f"requires {', '.join(requires)}, which leads back to {mitigation_id}",
                entity_type="mitigation", entity_id=mitigation_id, field="requires",
                hint="a cycle leaves neither control verifiable first",
            )
        if current in seen:
            continue
        seen.add(current)
        stack.extend((store.mitigations.get(current) or {}).get("requires") or [])


async def create_mitigation(data: MitigationCreate) -> dict[str, Any]:
    """Create a new mitigation."""
    store = get_store()
    if data.id in store.mitigations:
        raise Conflict(
            f"mitigation {data.id!r} already exists",
            entity_type="mitigation", entity_id=data.id,
            hint="use update_mitigation to change it, or pick another id",
        )
    _check_requires(data.id, data.requires)
    rec = data.model_dump()
    for field in _LIST_FIELDS:
        if rec.get(field) is None:
            rec[field] = []
    with store.lock:
        store.mitigations[data.id] = rec
        store.write_mitigation(data.id)
    return {"id": data.id, "name": data.name, "success": True}


async def update_mitigation(mitigation_id: str, data: MitigationUpdate) -> dict[str, Any]:
    """Update mitigation content."""
    store = get_store()
    rec = _require(mitigation_id)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if "requires" in update_data:
        _check_requires(mitigation_id, update_data["requires"])
    with store.lock:
        rec.update(update_data)
        store.write_mitigation(mitigation_id)
    return {"id": mitigation_id, "updated": list(update_data.keys()), "success": True}


async def delete_mitigation(mitigation_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a mitigation. Also unlinks it from any threats that reference it."""
    store = get_store()
    rec = _require(mitigation_id)

    linked = [
        t["id"] for t in store.threats.values()
        if any(link["id"] == mitigation_id for link in (t.get("mitigations") or []))
    ]
    if not confirm:
        return {
            "preview": {"id": rec["id"], "name": rec.get("name"), "linked_threats": len(linked)},
            "confirm_required": True,
        }
    with store.lock:
        for tid in linked:
            threat = store.threats[tid]
            threat["mitigations"] = [
                link for link in threat["mitigations"] if link["id"] != mitigation_id
            ]
            store.write_threat(tid)
        del store.mitigations[mitigation_id]
        store.delete_mitigation_file(mitigation_id)
    return {"success": True, "deleted": mitigation_id, "removed_links": len(linked)}
