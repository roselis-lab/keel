"""Service layer for mitigation operations (backed by the file store)."""
from typing import Any

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


async def get_mitigation(mitigation_id: str) -> dict[str, Any]:
    """Get a mitigation card with all fields."""
    rec = get_store().mitigations.get(mitigation_id)
    if not rec:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}
    response = _mitigation_item(rec, _INCLUDABLE)
    response["success"] = True
    return response


async def create_mitigation(data: MitigationCreate) -> dict[str, Any]:
    """Create a new mitigation."""
    store = get_store()
    if data.id in store.mitigations:
        return {"error": f"Mitigation '{data.id}' already exists", "success": False}
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
    rec = store.mitigations.get(mitigation_id)
    if not rec:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    with store.lock:
        rec.update(update_data)
        store.write_mitigation(mitigation_id)
    return {"id": mitigation_id, "updated": list(update_data.keys()), "success": True}


async def delete_mitigation(mitigation_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a mitigation. Also unlinks it from any threats that reference it."""
    store = get_store()
    rec = store.mitigations.get(mitigation_id)
    if not rec:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}

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
