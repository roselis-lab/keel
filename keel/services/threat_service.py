"""Service layer for threat operations (backed by the file store)."""
from typing import Any

from keel.schemas.threat import ThreatCreate, ThreatUpdate
from keel.store import get_store

_THREAT_FIELDS = ("harm", "surface", "source", "weaknesses", "reachability", "references", "tags")


def _mitigations_of(rec: dict[str, Any]) -> list[dict[str, Any]]:
    return list(rec.get("mitigations") or [])


def _threat_item(rec: dict[str, Any], include: list[str]) -> dict[str, Any]:
    item: dict[str, Any] = {"id": rec["id"], "title": rec.get("title")}
    for field in _THREAT_FIELDS:
        if field in include:
            item[field] = rec.get(field)
    if "mitigations" in include:
        item["mitigations"] = _mitigations_of(rec)
    return item


async def list_threats(brief: bool = True, include: list[str] | None = None) -> dict[str, Any]:
    """List all threats. `brief` returns [id, title] pairs."""
    store = get_store()
    threats = [store.threats[k] for k in sorted(store.threats)]
    if brief:
        return {"threats": [[t["id"], t.get("title")] for t in threats], "count": len(threats)}
    include = include or []
    return {"threats": [_threat_item(t, include) for t in threats], "count": len(threats)}


async def get_threat(threat_id: str, include: list[str] | None = None) -> dict[str, Any]:
    """Get a threat. Weaknesses and mitigations are always included."""
    rec = get_store().threats.get(threat_id)
    if not rec:
        return {"error": f"Threat '{threat_id}' not found", "success": False}
    include = list(set(include or []) | set(_THREAT_FIELDS) | {"mitigations"})
    response = _threat_item(rec, include)
    response["success"] = True
    return response


async def create_threat(data: ThreatCreate) -> dict[str, Any]:
    """Create a new threat."""
    store = get_store()
    if data.id in store.threats:
        return {"error": f"Threat '{data.id}' already exists", "success": False}
    rec = data.model_dump(mode="json")
    with store.lock:
        store.threats[data.id] = rec
        store.write_threat(data.id)
    return {"id": data.id, "title": data.title, "success": True}


async def update_threat(threat_id: str, data: ThreatUpdate) -> dict[str, Any]:
    """Update threat content."""
    store = get_store()
    rec = store.threats.get(threat_id)
    if not rec:
        return {"error": f"Threat '{threat_id}' not found", "success": False}
    update_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    with store.lock:
        rec.update(update_data)
        store.write_threat(threat_id)
    return {"id": threat_id, "updated": list(update_data.keys()), "success": True}


async def delete_threat(threat_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a threat."""
    store = get_store()
    rec = store.threats.get(threat_id)
    if not rec:
        return {"error": f"Threat '{threat_id}' not found", "success": False}
    if not confirm:
        return {
            "preview": {
                "id": rec["id"],
                "title": rec.get("title"),
                "mitigation_link_count": len(_mitigations_of(rec)),
            },
            "confirm_required": True,
        }
    with store.lock:
        del store.threats[threat_id]
        store.delete_threat_file(threat_id)
    return {"success": True, "deleted": threat_id}


async def batch_update_threats(
    updates: list[dict[str, Any]],
    confirm: bool = False,
) -> dict[str, Any]:
    """Batch update threats by threat_id."""
    store = get_store()
    if not confirm:
        preview = []
        for u in updates:
            rec = store.threats.get(u.get("threat_id"))
            if rec:
                preview.append({
                    "threat_id": rec["id"],
                    "current_title": rec.get("title"),
                    "proposed": {k: v for k, v in u.items() if k != "threat_id"},
                })
        return {"preview": preview, "count": len(preview), "confirm_required": True}

    updated = []
    with store.lock:
        for u in updates:
            tid = u.get("threat_id")
            rec = store.threats.get(tid) if tid else None
            if not rec:
                continue
            for field in ("title", *_THREAT_FIELDS):
                if field in u:
                    rec[field] = u[field]
            store.write_threat(tid)
            updated.append(tid)
    return {"success": True, "updated": updated, "count": len(updated)}


# ============================================================================
# Threat <-> Mitigation links (stored inline in the threat's YAML)
# ============================================================================


async def add_mitigation(
    threat_id: str,
    mitigation_id: str,
    strength: str,
    rationale: str,
) -> dict[str, Any]:
    """Link a mitigation to a threat (UPSERTs strength + rationale)."""
    store = get_store()
    if threat_id not in store.threats:
        return {"error": f"Threat '{threat_id}' not found", "success": False}
    if mitigation_id not in store.mitigations:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}
    if strength not in ("gating", "soft"):
        return {"error": "strength must be 'gating' or 'soft'", "success": False}
    with store.lock:
        rec = store.threats[threat_id]
        links = rec.setdefault("mitigations", [])
        for link in links:
            if link["id"] == mitigation_id:
                link["strength"] = strength
                link["rationale"] = rationale
                break
        else:
            links.append({"id": mitigation_id, "strength": strength, "rationale": rationale})
        links.sort(key=lambda x: x["id"])
        store.write_threat(threat_id)
    return {"success": True, "threat_id": threat_id, "mitigation_id": mitigation_id}


async def remove_mitigation(threat_id: str, mitigation_id: str) -> dict[str, Any]:
    """Unlink a mitigation from a threat."""
    store = get_store()
    rec = store.threats.get(threat_id)
    links = list(rec.get("mitigations") or []) if rec else []
    kept = [link for link in links if link["id"] != mitigation_id]
    if rec is None or len(kept) == len(links):
        return {"error": "Link not found", "success": False}
    with store.lock:
        rec["mitigations"] = kept
        store.write_threat(threat_id)
    return {"success": True, "removed": f"{threat_id}::{mitigation_id}"}
