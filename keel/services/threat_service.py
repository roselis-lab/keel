"""Service layer for threat operations."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from keel.models import Threat, ThreatMitigation, Mitigation
from keel.schemas.threat import ThreatCreate, ThreatUpdate


def _mitigations_of(threat: Threat) -> list[dict[str, str]]:
    return [
        {"mitigation_id": link.mitigation_id, "rationale": link.rationale}
        for link in threat.mitigation_links
    ]


def _threat_item(threat: Threat, include: list[str]) -> dict[str, Any]:
    item: dict[str, Any] = {"id": threat.id, "title": threat.title}
    if "description" in include:
        item["description"] = threat.description
    if "impact_class" in include:
        item["impact_class"] = threat.impact_class
    if "vulnerability" in include:
        item["vulnerability"] = threat.vulnerability
    if "reachability" in include:
        item["reachability"] = threat.reachability
    if "tags" in include:
        item["tags"] = threat.tags
    if "mitigations" in include:
        item["mitigations"] = _mitigations_of(threat)
    return item


async def list_threats(
    session: AsyncSession,
    brief: bool = True,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """List all threats. `brief` returns [id, title] pairs."""
    result = await session.execute(
        select(Threat).options(selectinload(Threat.mitigation_links)).order_by(Threat.id)
    )
    threats = result.scalars().all()

    if brief:
        return {"threats": [[t.id, t.title] for t in threats], "count": len(threats)}

    include = include or []
    return {
        "threats": [_threat_item(t, include) for t in threats],
        "count": len(threats),
    }


async def get_threat(
    session: AsyncSession,
    threat_id: str,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """Get a threat. Mitigations are always included."""
    result = await session.execute(
        select(Threat)
        .options(selectinload(Threat.mitigation_links))
        .where(Threat.id == threat_id)
    )
    threat = result.scalar_one_or_none()
    if not threat:
        return {"error": f"Threat '{threat_id}' not found", "success": False}

    include = set(include or []) | {
        "description", "impact_class", "vulnerability", "reachability", "tags", "mitigations",
    }
    response = _threat_item(threat, list(include))
    response["success"] = True
    return response


async def create_threat(session: AsyncSession, data: ThreatCreate) -> dict[str, Any]:
    """Create a new threat."""
    if await session.get(Threat, data.id):
        return {"error": f"Threat '{data.id}' already exists", "success": False}

    threat = Threat(
        id=data.id,
        title=data.title,
        description=data.description,
        impact_class=data.impact_class,
        vulnerability=data.vulnerability,
        reachability=data.reachability,
        tags=data.tags,
    )
    session.add(threat)
    await session.commit()
    return {"id": threat.id, "title": threat.title, "success": True}


async def update_threat(
    session: AsyncSession,
    threat_id: str,
    data: ThreatUpdate,
) -> dict[str, Any]:
    """Update threat content."""
    threat = await session.get(Threat, threat_id)
    if not threat:
        return {"error": f"Threat '{threat_id}' not found", "success": False}

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(threat, field, value)
    await session.commit()
    return {"id": threat.id, "updated": list(update_data.keys()), "success": True}


async def delete_threat(
    session: AsyncSession,
    threat_id: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete a threat and its mitigation links."""
    result = await session.execute(
        select(Threat).options(selectinload(Threat.mitigation_links)).where(Threat.id == threat_id)
    )
    threat = result.scalar_one_or_none()
    if not threat:
        return {"error": f"Threat '{threat_id}' not found", "success": False}

    if not confirm:
        return {
            "preview": {
                "id": threat.id,
                "title": threat.title,
                "mitigation_link_count": len(threat.mitigation_links),
            },
            "confirm_required": True,
        }

    await session.delete(threat)
    await session.commit()
    return {"success": True, "deleted": threat_id}


async def batch_update_threats(
    session: AsyncSession,
    updates: list[dict[str, Any]],
    confirm: bool = False,
) -> dict[str, Any]:
    """Batch update threats by threat_id."""
    if not confirm:
        preview = []
        for u in updates:
            threat = await session.get(Threat, u.get("threat_id"))
            if threat:
                preview.append({
                    "threat_id": threat.id,
                    "current_title": threat.title,
                    "proposed": {k: v for k, v in u.items() if k != "threat_id"},
                })
        return {"preview": preview, "count": len(preview), "confirm_required": True}

    updated = []
    for u in updates:
        tid = u.get("threat_id")
        threat = await session.get(Threat, tid) if tid else None
        if not threat:
            continue
        for field in ("title", "description", "impact_class", "vulnerability", "reachability", "tags"):
            if field in u:
                setattr(threat, field, u[field])
        updated.append(tid)

    await session.commit()
    return {"success": True, "updated": updated, "count": len(updated)}


# ============================================================================
# Threat <-> Mitigation links
# ============================================================================


async def add_mitigation(
    session: AsyncSession,
    threat_id: str,
    mitigation_id: str,
    rationale: str,
) -> dict[str, Any]:
    """Link a mitigation to a threat with a rationale (UPSERTs the rationale)."""
    if not await session.get(Threat, threat_id):
        return {"error": f"Threat '{threat_id}' not found", "success": False}
    if not await session.get(Mitigation, mitigation_id):
        return {"error": f"Mitigation '{mitigation_id}' not found", "success": False}

    link_id = f"{threat_id}::{mitigation_id}"
    link = await session.get(ThreatMitigation, link_id)
    if link:
        link.rationale = rationale
    else:
        session.add(ThreatMitigation(
            id=link_id,
            threat_id=threat_id,
            mitigation_id=mitigation_id,
            rationale=rationale,
        ))
    await session.commit()
    return {"success": True, "threat_id": threat_id, "mitigation_id": mitigation_id}


async def remove_mitigation(
    session: AsyncSession,
    threat_id: str,
    mitigation_id: str,
) -> dict[str, Any]:
    """Unlink a mitigation from a threat."""
    link = await session.get(ThreatMitigation, f"{threat_id}::{mitigation_id}")
    if not link:
        return {"error": "Link not found", "success": False}
    await session.delete(link)
    await session.commit()
    return {"success": True, "removed": f"{threat_id}::{mitigation_id}"}
