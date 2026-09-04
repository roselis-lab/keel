"""Service layer for threat operations (backed by the file store).

Failures raise (see `keel.errors`) rather than returning an error dict. The adapters
translate once, so nothing above this layer has to read a message to work out what went
wrong.
"""
from typing import Any

from pydantic import ValidationError

from keel.errors import Conflict, IntegrityError, Invalid, NotFound
from keel.schemas.threat import ThreatCreate, ThreatUpdate
from keel.store import get_store

_THREAT_FIELDS = ("harm", "source", "weaknesses", "reachability", "references",
                  "positioning", "tags")


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


def _cited_by(entity_id: str) -> list[dict[str, str]]:
    """Which tracked sources name this entry. Answered here rather than by a tool of its
    own: "who else says this exists" is something you want while reading the entry, not
    something you think to ask for separately."""
    from keel.services.coverage_service import by_entity

    return by_entity().get(entity_id, [])


def _require(threat_id: str) -> dict[str, Any]:
    """The record, or a NotFound naming a near miss. Suggesting the id the caller almost
    typed turns a dead end into a correction."""
    store = get_store()
    rec = store.threats.get(threat_id)
    if rec:
        return rec
    close = [t for t in sorted(store.threats) if t.lower().startswith(threat_id[:4].lower())]
    raise NotFound(
        f"no threat {threat_id!r}",
        entity_type="threat", entity_id=threat_id,
        hint=f"did you mean {', '.join(close[:3])}?" if close else
             "call search or list_threats to see what is there",
    )


async def get_threat(threat_id: str, include: list[str] | None = None) -> dict[str, Any]:
    """Get a threat. Weaknesses, mitigations and `cited_by` are always included."""
    rec = _require(threat_id)
    include = list(set(include or []) | set(_THREAT_FIELDS) | {"mitigations"})
    response = _threat_item(rec, include)
    response["cited_by"] = _cited_by(threat_id)
    response["success"] = True
    return response


async def create_threat(data: ThreatCreate) -> dict[str, Any]:
    """Create a new threat."""
    store = get_store()
    if data.id in store.threats:
        raise Conflict(
            f"threat {data.id!r} already exists",
            entity_type="threat", entity_id=data.id,
            hint="use update_threat to change it, or pick another id",
        )
    rec = data.model_dump(mode="json")
    with store.lock:
        store.threats[data.id] = rec
        store.write_threat(data.id)
    return {"id": data.id, "title": data.title, "success": True}


async def update_threat(threat_id: str, data: ThreatUpdate) -> dict[str, Any]:
    """Update threat content."""
    store = get_store()
    rec = _require(threat_id)
    update_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    with store.lock:
        rec.update(update_data)
        store.write_threat(threat_id)
    return {"id": threat_id, "updated": list(update_data.keys()), "success": True}


async def delete_threat(threat_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a threat."""
    store = get_store()
    rec = _require(threat_id)
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
    """Batch update threats by threat_id.

    Each item is validated as a `ThreatUpdate`, exactly as the single-threat path is.
    This used to assign raw values straight onto the record, so the batch tool was a
    hole around every check the single tool enforced: `harm: not-a-harm` went to disk.
    An item that fails validation is reported and skipped; the rest still apply.
    """
    store = get_store()

    parsed: list[tuple[str, dict[str, Any]]] = []
    errors: list[dict[str, Any]] = []
    for i, u in enumerate(updates):
        tid = u.get("threat_id")
        if not tid or tid not in store.threats:
            errors.append({"index": i, "threat_id": tid, "error": f"Threat {tid!r} not found"})
            continue
        try:
            data = ThreatUpdate(**{k: v for k, v in u.items() if k != "threat_id"})
        except ValidationError as e:
            errors.append({
                "index": i,
                "threat_id": tid,
                "error": "; ".join(
                    f"{'.'.join(str(x) for x in err['loc']) or '(root)'}: {err['msg']}"
                    for err in e.errors()
                ),
            })
            continue
        parsed.append((tid, data.model_dump(mode="json", exclude_unset=True, exclude_none=True)))

    if not confirm:
        preview = [
            {
                "threat_id": tid,
                "current_title": store.threats[tid].get("title"),
                "proposed": fields,
            }
            for tid, fields in parsed
        ]
        return {
            "preview": preview,
            "count": len(preview),
            "errors": errors,
            "confirm_required": True,
            "success": True,
        }

    updated = []
    with store.lock:
        for tid, fields in parsed:
            store.threats[tid].update(fields)
            store.write_threat(tid)
            updated.append(tid)
    return {
        "success": not errors,
        "updated": updated,
        "count": len(updated),
        "errors": errors,
    }


# ============================================================================
# Threat <-> Mitigation links (stored inline in the threat's YAML)
# ============================================================================


async def add_mitigation(
    threat_id: str,
    mitigation_id: str,
    strength: str,
    rationale: str,
    exception: str | None = None,
) -> dict[str, Any]:
    """Link a mitigation to a threat (UPSERTs strength + rationale + exception)."""
    store = get_store()
    _require(threat_id)
    if mitigation_id not in store.mitigations:
        raise IntegrityError(
            f"no mitigation {mitigation_id!r} to link",
            entity_type="mitigation", entity_id=mitigation_id, field="mitigation_id",
            hint="create the card first, or search for the id you meant",
        )
    if strength not in ("gating", "soft"):
        raise Invalid(
            f"strength {strength!r} is not a grade",
            field="strength",
            hint="gating (an architectural control that blocks the threat) or "
                 "soft (only lowers likelihood)",
        )
    with store.lock:
        rec = store.threats[threat_id]
        links = rec.setdefault("mitigations", [])
        for link in links:
            if link["id"] == mitigation_id:
                link["strength"] = strength
                link["rationale"] = rationale
                if exception:
                    link["exception"] = exception
                else:
                    link.pop("exception", None)
                break
        else:
            new_link = {"id": mitigation_id, "strength": strength, "rationale": rationale}
            if exception:
                new_link["exception"] = exception
            links.append(new_link)
        links.sort(key=lambda x: x["id"])
        store.write_threat(threat_id)
    return {"success": True, "threat_id": threat_id, "mitigation_id": mitigation_id}


async def remove_mitigation(threat_id: str, mitigation_id: str) -> dict[str, Any]:
    """Unlink a mitigation from a threat."""
    store = get_store()
    rec = _require(threat_id)
    links = list(rec.get("mitigations") or [])
    kept = [link for link in links if link["id"] != mitigation_id]
    if len(kept) == len(links):
        raise NotFound(
            f"{threat_id} does not link {mitigation_id}",
            entity_type="threat", entity_id=threat_id,
            hint=f"it links {', '.join(link['id'] for link in links) or 'nothing'}",
        )
    with store.lock:
        rec["mitigations"] = kept
        store.write_threat(threat_id)
    return {"success": True, "removed": f"{threat_id}::{mitigation_id}"}
