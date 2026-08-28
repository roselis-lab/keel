"""REST for browsing and editing the library.

Reads are the primary surface. A small set of write endpoints back the browse
UI's inline editing — they delegate to the same service layer the MCP write
tools use, and every write lands directly in `catalog/*.yaml`.
"""
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import ValidationError

from keel import githistory
from keel.catalog import lint_threat
from keel.config import settings
from keel.schema_export import build_schemas
from keel.schemas.mitigation import MitigationCreate, MitigationUpdate
from keel.schemas.threat import Threat, ThreatCreate, ThreatUpdate
from keel.services import (
    health_service,
    mitigation_service,
    report_service,
    style_guide_service,
    threat_service,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
# Threats
# --------------------------------------------------------------------------- #
@router.get("/threats")
async def list_threats(brief: bool = True, include: list[str] | None = Query(default=None)):
    return await threat_service.list_threats(brief=brief, include=include)


@router.post("/threats/validate")
async def validate_threat(payload: dict = Body(...)):
    """One validator, two channels: Pydantic gives blocking structure errors; lint_threat
    gives non-blocking advice. The browser renders these into its red and amber channels."""
    try:
        threat = Threat(**payload)
    except ValidationError as exc:
        errors = [
            {"field": ".".join(str(x) for x in e["loc"]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        return {"ok": False, "errors": errors, "advice": []}
    advice = [{"field": item["field"], "msg": item["msg"]} for item in lint_threat(threat)]
    return {"ok": True, "errors": [], "advice": advice}


@router.post("/threats", status_code=201)
async def create_threat(data: ThreatCreate):
    """Create a threat. Duplicate id → 409; body validation is handled by ThreatCreate (422)."""
    result = await threat_service.create_threat(data)
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("error"))
    return result


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


@router.delete("/threats/{threat_id}")
async def delete_threat(threat_id: str):
    """Delete a threat (and its mitigation links). 404 if missing."""
    result = await threat_service.delete_threat(threat_id, confirm=True)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.put("/threats/{threat_id}/mitigations/{mitigation_id}")
async def link_mitigation(
    threat_id: str,
    mitigation_id: str,
    strength: str = Body("gating", embed=True),
    rationale: str = Body("", embed=True),
    exception: str | None = Body(None, embed=True),
):
    result = await threat_service.add_mitigation(threat_id, mitigation_id, strength, rationale, exception)
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


@router.post("/mitigations", status_code=201)
async def create_mitigation(data: MitigationCreate):
    """Create a mitigation. Duplicate id → 409; body validation via MitigationCreate (422)."""
    result = await mitigation_service.create_mitigation(data)
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("error"))
    return result


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


@router.delete("/mitigations/{mitigation_id}")
async def delete_mitigation(mitigation_id: str):
    """Delete a mitigation. The service also unlinks it from any threats. 404 if missing."""
    result = await mitigation_service.delete_mitigation(mitigation_id, confirm=True)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# --------------------------------------------------------------------------- #
# Health / overview
# --------------------------------------------------------------------------- #
@router.get("/health/library")
async def health_library():
    """Overview stats + issues + style-guide coverage for the overview page."""
    return await health_service.check_library_health()


@router.get("/health/warnings")
async def health_warnings():
    """Structured advisory warnings (over-graded links, missing references, unused
    vocabulary) — the same checks `keel validate` runs, in dashboard-friendly form."""
    return await health_service.get_catalog_warnings()


# --------------------------------------------------------------------------- #
# Style guide
# --------------------------------------------------------------------------- #
@router.get("/style-guide")
async def get_style_guide():
    return (await style_guide_service.get_full_guide()).model_dump()


@router.get("/style-guide/coverage")
async def style_guide_coverage():
    return (await style_guide_service.get_coverage()).model_dump()


@router.patch("/style-guide/{entity_type}/{field_name}")
async def update_style_field(entity_type: str, field_name: str, patch: dict = Body(...)):
    try:
        row = await style_guide_service.update_field(
            entity_type, field_name, patch, updated_by="ui"
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return row.model_dump()


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
@router.get("/schema/{entity}")
async def get_schema(entity: str):
    schemas = build_schemas()
    if entity not in schemas:
        raise HTTPException(status_code=404, detail=f"unknown entity {entity!r}")
    return schemas[entity]


# --------------------------------------------------------------------------- #
# Git history (read-only)
# --------------------------------------------------------------------------- #
@router.get("/history/recent")
async def recent_history(limit: int = Query(default=20, ge=1, le=100)):
    """Recent commits across the whole catalog. Always 200; `available: False` when
    git is unavailable or the catalog isn't inside a git repo."""
    return githistory.recent_activity(limit=limit)


@router.get("/history/{entity}/{id}")
async def entry_history(entity: str, id: str):
    """Commit list for one entry's YAML file. 200 with `{available, ...}`.

    A bad entity or an id that fails the allowlist/pattern → 404 (rejected before
    any git call); a valid entry with no tracked history → 200 with
    `{available: False, commits: []}`.
    """
    if not githistory.is_valid_ref(entity, id):
        raise HTTPException(status_code=404, detail="unknown entity or id")
    return githistory.history(entity, id)


@router.get("/history/{entity}/{id}/{sha}")
async def entry_diff(entity: str, id: str, sha: str):
    """Unified diff for one commit, scoped to the entry's file. 404 if not found."""
    if not githistory.is_valid_ref(entity, id):
        raise HTTPException(status_code=404, detail="unknown entity or id")
    result = githistory.diff(entity, id, sha)
    if result is None:
        raise HTTPException(status_code=404, detail="commit or entry not found")
    return result


# --------------------------------------------------------------------------- #
# Reports. The skill writes the first pass to disk; the specialist corrects it here
# while it is a draft. A final report is frozen — revising it means reopening it as a
# new dated draft, so a correction lands beside the record instead of erasing it.
# --------------------------------------------------------------------------- #
@router.get("/reports")
async def list_reports():
    """One entry per assessed system that has at least one parseable report."""
    return {"reports": report_service.list_reports()}


@router.get("/reports/insights")
async def report_insights():
    """The archive read across systems: what several systems ask for and nobody has
    built, what the assessments found that the catalog does not carry, which cards keep
    getting ruled out, and which assessments were never finalized.

    Declared BEFORE /reports/{system_id} — routes match in declaration order, and
    "insights" is a legal system id, so the parameterised route would swallow it.
    """
    return report_service.insights()


@router.get("/reports/{system_id}")
async def report_series(system_id: str):
    """A system's report dates, newest first. An unknown or empty system returns an
    empty series rather than 404 — having no reports yet is not an error."""
    return {"series": report_service.get_report_series(system_id)}


@router.get("/reports/{system_id}/{date}")
async def get_report(system_id: str, date: str):
    """One report. 404 when it is missing or cannot be parsed."""
    result = report_service.get_report(system_id, date)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result["report"]


@router.put("/reports/{system_id}/{date}")
async def save_report(system_id: str, date: str, body: dict):
    """Replace a draft with its corrected version. 409 when the report is already final,
    422 when the body does not validate."""
    result = report_service.save_report(system_id, date, body)
    if result["success"]:
        return result["report"]
    if "errors" in result:
        raise HTTPException(status_code=422, detail=result)
    if "final" in result["error"]:
        raise HTTPException(status_code=409, detail=result["error"])
    raise HTTPException(status_code=404, detail=result["error"])


@router.post("/reports/{system_id}/{date}/finalize")
async def finalize_report(system_id: str, date: str):
    """Freeze a draft into a dated record. Finalizing twice is a no-op, not an error."""
    result = report_service.finalize_report(system_id, date)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result["report"]


@router.post("/reports/{system_id}/{date}/reopen")
async def reopen_report(system_id: str, date: str):
    """Copy a report into a fresh draft dated today. 409 when today already has one."""
    result = report_service.reopen_report(system_id, date)
    if result["success"]:
        return result["report"]
    if "already exists" in result["error"]:
        raise HTTPException(status_code=409, detail=result["error"])
    raise HTTPException(status_code=404, detail=result["error"])


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
@router.get("/config")
async def get_config():
    """UI config. `repo_url` powers the optional 'Edit on GitHub' link on save."""
    return {"repo_url": settings.repo_url}
