"""MCP tools for threats and their mitigation links.

Writes take a `fields` mapping rather than one parameter per field. A threat has ten
fields and a mitigation card sixteen; spelling each out doubles the tool schema every
client pays for on every conversation, and pushes past the eight-parameter mark where
models start mis-filling arguments. The field list is not lost — `get_style_guide` is
already the mandatory call before authoring, and it names every field with the bar it
has to meet. One place to look, not two that drift.
"""
from typing import Any

from pydantic import ValidationError

from keel.errors import Invalid, invalid_from_pydantic
from keel.mcp.registry import register_tool
from keel.schemas.threat import Strength, ThreatCreate, ThreatUpdate
from keel.services.integrity_service import after_write
from keel.services.threat_service import (
    add_mitigation as _add_mitigation,
    batch_update_threats as _batch_update_threats,
    create_threat as _create_threat,
    delete_threat as _delete_threat,
    get_threat as _get_threat,
    list_threats as _list_threats,
    remove_mitigation as _remove_mitigation,
    update_threat as _update_threat,
)

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}

THREAT_FIELDS = (
    "title, harm, source, weaknesses, reachability, references, "
    "positioning, tags"
)


def _reject(exc: Exception) -> Invalid:
    """Say what is wrong AND what would be right. An error that only rejects makes the
    caller guess again; one that names the allowed fields ends the loop in a turn."""
    return invalid_from_pydantic(exc, hint=f"fields: {THREAT_FIELDS}")


def _with_advice(result: dict[str, Any], entity_type: str, entity_id: str) -> dict[str, Any]:
    """Attach what the rules say about the record that was just written. Omitted when
    they say nothing, so the normal answer stays a few dozen bytes and a non-empty
    `advice` always means something worth reading."""
    advice = after_write(entity_type, entity_id)
    return {**result, "advice": advice} if advice else result


@register_tool(annotations=_RO)
async def list_threats(brief: bool = True, include: list[str] | None = None) -> dict:
    """Lists threats. Returns {threats: [...], count}.

    brief=True (the default) returns id and title only — enough to pick one. Ask for more
    with include, naming any of: harm, source, weaknesses, reachability,
    mitigations, references, tags. Fetching a whole catalog of full records to read two
    titles is the expensive mistake this guards against."""
    return await _list_threats(brief=brief, include=include)


@register_tool(annotations=_RO)
async def get_threat(threat_id: str) -> dict:
    """Gets one threat in full: harm, source, weaknesses, reachability, linked
    mitigations, references, tags, plus `cited_by` — the entries in the tracked sources
    (OWASP, ATLAS, SAIF) that name this threat. An empty `cited_by` is not a defect; it
    means no source Keel tracks has this, so the entry is Keel's own."""
    return await _get_threat(threat_id)


@register_tool(annotations=_WRITE, entity_type="threat")
async def create_threat(threat_id: str, fields: dict[str, Any]) -> dict:
    """Creates a threat. Returns {success, id} — call get_threat to read it back.

    `fields` must carry title, harm, weaknesses and reachability; source,
    references and tags are optional. `weaknesses` is a list of {component, text,
    nature?}, each an architectural condition (cause + where + defect) — not a technique
    and not a consequence. `harm` is the consequence class and `reachability` is the
    condition under which this threat is not a live path at all.

    Call get_style_guide(entity_type="threat") first: it lists every field with the bar
    it has to meet, and get_vocabulary explains the allowed harm/surface/source values.
    `surface` is named per weakness, not on the threat.
    Link mitigations afterwards with add_threat_mitigation, and record which entries of
    the tracked sources this answers with set_coverage_entry."""
    try:
        payload = ThreatCreate(id=threat_id, **fields)
    except ValidationError as exc:
        raise _reject(exc) from exc
    await _create_threat(payload)
    return _with_advice({"success": True, "id": threat_id}, "threat", threat_id)


@register_tool(annotations=_WRITE, entity_type="threat")
async def update_threat(threat_id: str, fields: dict[str, Any]) -> dict:
    """Updates a threat. Only the fields named change; the rest are left alone.

    Returns {success, id, changed: [...]}. List-valued fields (weaknesses, references,
    tags) are REPLACED wholesale, not merged — read the current value first if you mean
    to append. Allowed fields: title, harm, source, weaknesses, reachability,
    references, tags. Mitigation links are not edited here; use add_threat_mitigation."""
    try:
        payload = ThreatUpdate(**fields)
    except ValidationError as exc:
        raise _reject(exc) from exc
    result = await _update_threat(threat_id, payload)
    # What the service applied, not what the caller sent. The two could differ, and
    # reporting the input claimed a save that had not happened.
    return _with_advice(
        {"success": True, "id": threat_id, "changed": sorted(result["updated"])},
        "threat", threat_id)


@register_tool(annotations=_DESTRUCTIVE)
async def delete_threat(threat_id: str, confirm: bool = False) -> dict:
    """Deletes a threat and its mitigation links. Called without confirm=True it only
    previews what would go, so an accidental call cannot destroy anything."""
    result = await _delete_threat(threat_id, confirm=confirm)
    return _with_advice(result, "threat", threat_id) if confirm else result


@register_tool(annotations=_WRITE, entity_type="threat")
async def batch_update_threats(updates: list[dict], confirm: bool = False) -> dict:
    """Updates many threats in one call — for sweeps across the catalog, where one call
    per threat would be a dozen round trips.

    Each item is {threat_id, ...fields} with the same fields update_threat takes. Called
    without confirm=True it previews. Every item is validated separately: valid ones
    apply, invalid ones come back in `errors` with the reason, and a bad item never
    blocks a good one."""
    return await _batch_update_threats(updates, confirm=confirm)


@register_tool(annotations=_WRITE)
async def add_threat_mitigation(
    threat_id: str, mitigation_id: str, strength: Strength, rationale: str,
    exception: str | None = None,
) -> dict:
    """Links a mitigation to a threat, or updates an existing link.

    strength: `gating` (an architectural control outside the model that blocks the
    threat) or `soft` (only lowers likelihood). Grading a detector or a process as gating
    is the most common error here, and `keel validate` flags it. rationale says why this
    control fits THIS threat. exception is rare — a narrow case where the control does
    not apply though the threat stays live; never a restatement of reachability."""
    result = await _add_mitigation(threat_id, mitigation_id, strength, rationale, exception)
    return _with_advice(result, "threat", threat_id) if result.get("success") else result


@register_tool(annotations=_WRITE)
async def remove_threat_mitigation(threat_id: str, mitigation_id: str) -> dict:
    """Unlinks a mitigation from a threat. Neither entry is deleted."""
    return await _remove_mitigation(threat_id, mitigation_id)
