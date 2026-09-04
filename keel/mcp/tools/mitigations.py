"""MCP tools for mitigation cards. See `threats.py` for why writes take a `fields` map."""
from typing import Any

from pydantic import ValidationError

from keel.errors import Invalid, invalid_from_pydantic
from keel.mcp.registry import register_tool
from keel.schemas.mitigation import MitigationCreate, MitigationUpdate
from keel.services.integrity_service import after_write
from keel.services.mitigation_service import (
    create_mitigation as _create_mitigation,
    delete_mitigation as _delete_mitigation,
    get_mitigation as _get_mitigation,
    list_mitigations as _list_mitigations,
    update_mitigation as _update_mitigation,
)

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}

MITIGATION_FIELDS = (
    "name, mitigation_class, purpose, formal_implementation_risk, review, maintainer, "
    "locus, scope, out_of_scope, control_mechanism, failure_behavior, telemetry, "
    "anti_patterns, validation, faq, positioning, requires, implementations"
)


def _reject(exc: Exception) -> Invalid:
    """Say what is wrong AND what would be right: an error that only rejects makes the
    caller guess again, one that names the allowed fields ends the loop in a turn."""
    return invalid_from_pydantic(exc, hint=f"fields: {MITIGATION_FIELDS}")


def _with_advice(result: dict[str, Any], mitigation_id: str) -> dict[str, Any]:
    """See the note in `threats.py`: attached only when there is something to say."""
    advice = after_write("mitigation", mitigation_id)
    return {**result, "advice": advice} if advice else result


@register_tool(annotations=_RO)
async def list_mitigations(brief: bool = True, include: list[str] | None = None) -> dict:
    """Lists mitigation cards. Returns {mitigations: [...], count}.

    brief=True (the default) returns id, name and mitigation_class only. Ask for more
    with include, naming any of: purpose, scope, control_mechanism, failure_behavior,
    telemetry, anti_patterns, validation, faq, review, maintainer, locus,
    formal_implementation_risk, implementations. A card is long; pulling every field for
    every card to find one id is the expensive mistake this guards against."""
    return await _list_mitigations(brief=brief, include=include)


@register_tool(annotations=_RO)
async def get_mitigation(mitigation_id: str) -> dict:
    """Gets one mitigation card with every field, plus `cited_by` — the entries in the
    tracked sources (OWASP, ATLAS, SAIF) that name this control. An empty `cited_by`
    means no tracked source has it, which makes the card Keel's own rather than a
    restatement."""
    return await _get_mitigation(mitigation_id)


@register_tool(annotations=_WRITE, entity_type="mitigation")
async def create_mitigation(mitigation_id: str, fields: dict[str, Any]) -> dict:
    """Creates a mitigation card. Returns {success, id}.

    `fields` must carry name and mitigation_class; everything else is optional and can
    be filled in later. mitigation_class is one of gating_control, detector, process,
    evidential_mitigation, corrective — it is a switch that changes how control_mechanism
    and failure_behavior are read, so pick it before writing either.

    Call get_style_guide(entity_type="mitigation") first. A card written without it
    usually fails review on the same three things: a purpose that restates the name,
    prose about what an organisation should decide (that belongs in `implementations`),
    and a control_mechanism that does not match the class."""
    try:
        payload = MitigationCreate(id=mitigation_id, **fields)
    except ValidationError as exc:
        raise _reject(exc) from exc
    await _create_mitigation(payload)
    return _with_advice({"success": True, "id": mitigation_id}, mitigation_id)


@register_tool(annotations=_WRITE, entity_type="mitigation")
async def update_mitigation(mitigation_id: str, fields: dict[str, Any]) -> dict:
    """Updates a mitigation card. Only the fields named change.

    Returns {success, id, changed: [...]}. List-valued fields (anti_patterns, validation,
    faq, implementations) are REPLACED wholesale, not merged — read the current value
    first if you mean to append. Every field of the card is writable here; call
    get_style_guide(entity_type="mitigation") for the list and what each one is for.

    `requires` names controls this one presupposes - use it only where this card's
    acceptance criteria cannot be checked without the other in place. An id that does
    not exist, points at itself, or closes a loop is refused, not warned about."""
    try:
        payload = MitigationUpdate(**fields)
    except ValidationError as exc:
        raise _reject(exc) from exc
    result = await _update_mitigation(mitigation_id, payload)
    # What the service applied, not what the caller sent.
    return _with_advice({"success": True, "id": mitigation_id,
                           "changed": sorted(result["updated"])},
                          mitigation_id)


@register_tool(annotations=_DESTRUCTIVE)
async def delete_mitigation(mitigation_id: str, confirm: bool = False) -> dict:
    """Deletes a mitigation card and unlinks it from every threat that referenced it.
    Called without confirm=True it only previews, including how many threats would lose
    the link."""
    result = await _delete_mitigation(mitigation_id, confirm=confirm)
    return _with_advice(result, mitigation_id) if confirm else result
