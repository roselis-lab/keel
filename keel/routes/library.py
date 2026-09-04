"""REST for browsing and editing the library.

Reads are the primary surface. A small set of write endpoints back the browse
UI's inline editing — they delegate to the same service layer the MCP write
tools use, and every write lands directly in `catalog/*.yaml`.
"""
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import ValidationError

from keel import githistory
from keel.config import settings
from keel.schema_export import build_schemas
from keel.schemas.mitigation import MitigationCreate, MitigationUpdate
from keel.schemas.threat import Threat, ThreatCreate, ThreatUpdate
from keel.store import get_store
from keel.services import (
    coverage_service,
    health_service,
    mitigation_service,
    repair_service,
    report_service,
    search_service,
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
    """One validator, two channels: pydantic gives blocking structure errors, the rule
    registry gives non-blocking advice. The browser renders these into its red and amber
    channels, and the advice is the same set a write or `keel validate` would report."""
    from keel.rules import Catalog, check_entity

    try:
        threat = Threat(**payload)
    except ValidationError as exc:
        errors = [
            {"field": ".".join(str(x) for x in e["loc"]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        return {"ok": False, "errors": errors, "advice": []}

    # Against the catalog as it stands, but with THIS record in place of the stored one,
    # so the editor judges what is about to be saved rather than what is already there.
    store = get_store()
    cat = Catalog(threats={**store.threats, threat.id: threat.model_dump(mode="json")},
                  mitigations=store.mitigations)
    advice = [
        {"field": f.field, "msg": f.message}
        for f in check_entity("threat", threat.id, cat) if f.severity == "advice"
    ]
    return {"ok": True, "errors": [], "advice": advice}


@router.post("/threats", status_code=201)
async def create_threat(data: ThreatCreate):
    """Create a threat. Duplicate id → 409; body validation is handled by ThreatCreate (422)."""
    return await threat_service.create_threat(data)


@router.get("/threats/{threat_id}")
async def get_threat(threat_id: str):
    return await threat_service.get_threat(threat_id)


@router.patch("/threats/{threat_id}")
async def update_threat(threat_id: str, data: ThreatUpdate):
    return await threat_service.update_threat(threat_id, data)


@router.delete("/threats/{threat_id}")
async def delete_threat(threat_id: str):
    """Delete a threat (and its mitigation links). 404 if missing."""
    return await threat_service.delete_threat(threat_id, confirm=True)


@router.put("/threats/{threat_id}/mitigations/{mitigation_id}")
async def link_mitigation(
    threat_id: str,
    mitigation_id: str,
    strength: str = Body("gating", embed=True),
    rationale: str = Body("", embed=True),
    exception: str | None = Body(None, embed=True),
):
    return await threat_service.add_mitigation(threat_id, mitigation_id, strength, rationale, exception)


@router.delete("/threats/{threat_id}/mitigations/{mitigation_id}")
async def unlink_mitigation(threat_id: str, mitigation_id: str):
    return await threat_service.remove_mitigation(threat_id, mitigation_id)


# --------------------------------------------------------------------------- #
# Mitigations
# --------------------------------------------------------------------------- #
@router.get("/mitigations")
async def list_mitigations(brief: bool = True, include: list[str] | None = Query(default=None)):
    return await mitigation_service.list_mitigations(brief=brief, include=include)


@router.post("/mitigations", status_code=201)
async def create_mitigation(data: MitigationCreate):
    """Create a mitigation. Duplicate id → 409; body validation via MitigationCreate (422)."""
    return await mitigation_service.create_mitigation(data)


@router.get("/mitigations/{mitigation_id}")
async def get_mitigation(mitigation_id: str):
    return await mitigation_service.get_mitigation(mitigation_id)


@router.patch("/mitigations/{mitigation_id}")
async def update_mitigation(mitigation_id: str, data: MitigationUpdate):
    return await mitigation_service.update_mitigation(mitigation_id, data)


@router.delete("/mitigations/{mitigation_id}")
async def delete_mitigation(mitigation_id: str):
    """Delete a mitigation. The service also unlinks it from any threats. 404 if missing."""
    return await mitigation_service.delete_mitigation(mitigation_id, confirm=True)


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


@router.get("/rules")
async def get_rules():
    """Every rule the catalog is checked against: code, what it applies to, how serious
    it is, and the label a screen groups it under.

    Served rather than mirrored, because a screen with its own copy of the rule list
    falls behind it silently - the dashboard used to carry two such copies."""
    from keel.rules import catalogue

    return {"rules": catalogue()}


@router.get("/vocabulary")
async def get_vocabulary():
    """The four frozen vocabularies with their human names and one-line glosses.

    The schemas enforce these as `Literal`s, which is what makes an unknown value
    impossible; this is what the Literal cannot carry — what `downstream` actually
    means. Shape: `{harm: {value: {name, desc}}, surface: ..., source: ..., components: ...}`."""
    return get_store().vocabulary


@router.get("/search")
async def search(q: str = Query(..., min_length=2), kind: str | None = None, limit: int = 20):
    """One query across threats, mitigations, coverage rows and assessments."""
    return search_service.search(q, kind=kind, limit=limit)


# --------------------------------------------------------------------------- #
# Coverage — what the tracked sources say, and what Keel says back
# --------------------------------------------------------------------------- #
@router.get("/coverage")
async def coverage_matrix():
    """The whole matrix: every entry of every tracked release, with its state.

    Note this is not `/style-guide/coverage`, which measures how much of the style guide
    has been authored. This one measures Keel against other people's lists."""
    return coverage_service.matrix()


@router.get("/coverage/citations")
async def coverage_citations():
    """Reverse index: Keel id -> the source entries that name it. Derived, never stored —
    the files are written source-first so that a gap has a row to be empty in."""
    return coverage_service.by_entity()


@router.get("/coverage/gaps")
async def coverage_gaps():
    """Every tracked entry nothing answers yet — the authoring queue."""
    rows = coverage_service.gaps()
    return {"gaps": rows, "count": len(rows)}


# --------------------------------------------------------------------------- #
# Repair — raw text for a file the store refused to load
# --------------------------------------------------------------------------- #
@router.get("/catalog/file")
async def read_catalog_file(path: str = Query(..., description="e.g. threats/T-X.yaml")):
    """Raw YAML for one catalog file, with whatever is wrong with it.

    A record that fails its schema is not in the store, so the structured editor has
    nothing to open. Reporting a defect the reader cannot then act on is the wrong way
    round, so the app hands back the text itself."""
    return await repair_service.read_file(path)


@router.put("/catalog/file")
async def write_catalog_file(payload: dict = Body(...)):
    """Validate then write. A save that would not load is refused with the field and the
    reason, so this door cannot put the catalog into the state it exists to repair."""
    path, text = payload.get("path"), payload.get("text")
    if not isinstance(path, str) or not isinstance(text, str):
        raise HTTPException(status_code=422, detail="expected {path, text}")
    return await repair_service.write_file(path, text)


# --------------------------------------------------------------------------- #
# Style guide
# --------------------------------------------------------------------------- #
@router.get("/style-guide")
async def get_style_guide():
    return (await style_guide_service.get_full_guide()).model_dump()


@router.get("/style-guide/coverage")
async def style_guide_coverage():
    return (await style_guide_service.get_coverage()).model_dump()


# Declared before the two-segment route so `/style-guide/coverage` keeps winning and a
# one-segment PATCH is not read as a field name.
@router.patch("/style-guide/{entity_type}")
async def update_style_entity(entity_type: str, patch: dict = Body(...)):
    """The bar for the record as a whole, the part no single field's bar can carry."""
    try:
        row = await style_guide_service.update_entity(entity_type, patch, updated_by="ui")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return row.model_dump() if row else {}


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
# Reports. The skill writes the first pass; the specialist edits it here and finalises
# when satisfied. Editing a final report drops it back to draft — a document that
# changed after sign-off is not signed off any more.
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
    """One report. 404 when it is missing, 422 when it cannot be parsed."""
    return report_service.get_report(system_id, date)["report"]


@router.put("/reports/{system_id}/{date}")
async def save_report(system_id: str, date: str, body: dict):
    """Write a report. A final report goes back to draft; 422 when the body does not
    validate or names catalog entries that do not exist."""
    return report_service.save_report(system_id, date, body)["report"]


@router.post("/reports/{system_id}/{date}/finalize")
async def finalize_report(system_id: str, date: str):
    """Freeze a draft into a dated record. Finalizing twice is a no-op, not an error."""
    return report_service.finalize_report(system_id, date)["report"]


@router.post("/reports")
async def create_report(body: dict):
    """An empty draft for a system with no prior assessment. 409 if that file exists."""
    return report_service.create_report(
        system_id=(body.get("system_id") or "").strip(),
        system_name=(body.get("system_name") or "").strip(),
        system_description=(body.get("system_description") or "").strip(),
        # The assessor is whoever this checkout belongs to; the UI does not ask.
        assessor=(body.get("assessor") or "").strip() or githistory.identity(),
        date=(body.get("date") or "").strip() or None,
    )["report"]


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
@router.get("/config")
async def get_config():
    """UI config. `repo_url` powers the optional 'Edit on GitHub' link on save."""
    return {"repo_url": settings.repo_url}
