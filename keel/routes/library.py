"""REST for browsing and editing the library.

Reads are the primary surface. A small set of write endpoints back the browse
UI's inline editing — they delegate to the same service layer the MCP write
tools use, and every write lands directly in `catalog/*.yaml`.
"""
from fastapi import APIRouter, Body, HTTPException, Query

from keel.schemas.mitigation import MitigationUpdate
from keel.schemas.threat import ThreatUpdate
from keel.services import mitigation_service, style_guide_service, threat_service

router = APIRouter()


# --------------------------------------------------------------------------- #
# Threats
# --------------------------------------------------------------------------- #
@router.get("/threats")
async def list_threats(brief: bool = True, include: list[str] | None = Query(default=None)):
    return await threat_service.list_threats(brief=brief, include=include)


@router.get("/threats/{threat_id}")
async def get_threat(threat_id: str):
    result = await threat_service.get_threat(threat_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.patch("/threats/{threat_id}")
async def update_threat(threat_id: str, data: ThreatUpdate):
    result = await threat_service.update_threat(threat_id, data)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.put("/threats/{threat_id}/mitigations/{mitigation_id}")
async def link_mitigation(
    threat_id: str,
    mitigation_id: str,
    rationale: str = Body("", embed=True),
):
    result = await threat_service.add_mitigation(threat_id, mitigation_id, rationale)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.delete("/threats/{threat_id}/mitigations/{mitigation_id}")
async def unlink_mitigation(threat_id: str, mitigation_id: str):
    result = await threat_service.remove_mitigation(threat_id, mitigation_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# --------------------------------------------------------------------------- #
# Mitigations
# --------------------------------------------------------------------------- #
@router.get("/mitigations")
async def list_mitigations(brief: bool = True, include: list[str] | None = Query(default=None)):
    return await mitigation_service.list_mitigations(brief=brief, include=include)


@router.get("/mitigations/{mitigation_id}")
async def get_mitigation(mitigation_id: str):
    result = await mitigation_service.get_mitigation(mitigation_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.patch("/mitigations/{mitigation_id}")
async def update_mitigation(mitigation_id: str, data: MitigationUpdate):
    result = await mitigation_service.update_mitigation(mitigation_id, data)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# --------------------------------------------------------------------------- #
# Style guide
# --------------------------------------------------------------------------- #
@router.get("/style-guide")
async def get_style_guide():
    return (await style_guide_service.get_full_guide()).model_dump()


@router.patch("/style-guide/{entity_type}/{field_name}")
async def update_style_field(entity_type: str, field_name: str, patch: dict = Body(...)):
    try:
        row = await style_guide_service.update_field(
            entity_type, field_name, patch, updated_by="ui"
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return row.model_dump()
