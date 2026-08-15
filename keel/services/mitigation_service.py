"""Service layer for mitigation operations."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from keel.models import Mitigation, ThreatMitigation
from keel.schemas.mitigation import MitigationCreate, MitigationUpdate


# Fields returnable via `include` (everything past the id/name/class always shown).
_INCLUDABLE = [
    "status", "purpose", "formal_implementation_risk", "review", "maintainer", "owner",
    "locus", "scope", "control_mechanism", "failure_behavior", "telemetry", "anti_patterns",
    "validation", "faq",
]


def _mitigation_item(m: Mitigation, include: list[str]) -> dict[str, Any]:
    item: dict[str, Any] = {"id": m.id, "name": m.name, "mitigation_class": m.mitigation_class}
    for field in include:
        if field in _INCLUDABLE:
            item[field] = getattr(m, field)
    return item


async def list_mitigations(
    session: AsyncSession,
    brief: bool = True,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """List all mitigations. `brief` returns [id, name, mitigation_class] triples."""
    result = await session.execute(select(Mitigation).order_by(Mitigation.id))
    mitigations = result.scalars().all()

    if brief:
        return {
            "mitigations": [[m.id, m.name, m.mitigation_class] for m in mitigations],
            "count": len(mitigations),
        }

    include = include or []
    return {
        "mitigations": [_mitigation_item(m, include) for m in mitigations],
        "count": len(mitigations),
    }


async def get_mitigation(session: AsyncSession, mitigation_id: str) -> dict[str, Any]:
    """Get a mitigation with all fields."""
    m = await session.get(Mitigation, mitigation_id)
    if not m:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}
    response = _mitigation_item(m, _INCLUDABLE)
    response["success"] = True
    return response


async def create_mitigation(session: AsyncSession, data: MitigationCreate) -> dict[str, Any]:
    """Create a new mitigation."""
    if await session.get(Mitigation, data.id):
        return {"error": f"Mitigation '{data.id}' already exists", "success": False}

    m = Mitigation(**data.model_dump())
    session.add(m)
    await session.commit()
    return {"id": m.id, "name": m.name, "success": True}


async def update_mitigation(
    session: AsyncSession,
    mitigation_id: str,
    data: MitigationUpdate,
) -> dict[str, Any]:
    """Update mitigation content."""
    m = await session.get(Mitigation, mitigation_id)
    if not m:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(m, field, value)
    await session.commit()
    return {"id": m.id, "updated": list(update_data.keys()), "success": True}


async def delete_mitigation(
    session: AsyncSession,
    mitigation_id: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete a mitigation. Blocked while threats still link to it unless confirmed."""
    m = await session.get(Mitigation, mitigation_id)
    if not m:
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}

    links = (await session.execute(
        select(ThreatMitigation).where(ThreatMitigation.mitigation_id == mitigation_id)
    )).scalars().all()

    if not confirm:
        return {
            "preview": {"id": m.id, "name": m.name, "linked_threats": len(links)},
            "confirm_required": True,
        }

    # Delete links explicitly — SQLite does not enforce FK CASCADE by default.
    for link in links:
        await session.delete(link)
    await session.delete(m)
    await session.commit()
    return {"success": True, "deleted": mitigation_id, "removed_links": len(links)}
