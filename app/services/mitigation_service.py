"""Service layer for mitigation operations."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mitigation, ThreatMitigation
from app.schemas.mitigation import MitigationCreate, MitigationUpdate


def _mitigation_item(m: Mitigation, include: list[str]) -> dict[str, Any]:
    item: dict[str, Any] = {"id": m.id, "title": m.title, "type": m.type}
    if "description" in include:
        item["description"] = m.description
    if "requirement_level" in include:
        item["requirement_level"] = m.requirement_level
    if "implementations" in include:
        item["implementations"] = m.implementations
    return item


async def list_mitigations(
    session: AsyncSession,
    brief: bool = True,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """List all mitigations. `brief` returns [id, title, type] triples."""
    result = await session.execute(select(Mitigation).order_by(Mitigation.id))
    mitigations = result.scalars().all()

    if brief:
        return {
            "mitigations": [[m.id, m.title, m.type] for m in mitigations],
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
    response = _mitigation_item(m, ["description", "requirement_level", "implementations"])
    response["success"] = True
    return response


async def create_mitigation(session: AsyncSession, data: MitigationCreate) -> dict[str, Any]:
    """Create a new mitigation."""
    if await session.get(Mitigation, data.id):
        return {"error": f"Mitigation '{data.id}' already exists", "success": False}

    m = Mitigation(
        id=data.id,
        title=data.title,
        description=data.description,
        type=data.type,
        requirement_level=data.requirement_level,
        implementations=data.implementations,
    )
    session.add(m)
    await session.commit()
    return {"id": m.id, "title": m.title, "success": True}


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
            "preview": {"id": m.id, "title": m.title, "linked_threats": len(links)},
            "confirm_required": True,
        }

    # Delete links explicitly — SQLite does not enforce FK CASCADE by default.
    for link in links:
        await session.delete(link)
    await session.delete(m)
    await session.commit()
    return {"success": True, "deleted": mitigation_id, "removed_links": len(links)}
