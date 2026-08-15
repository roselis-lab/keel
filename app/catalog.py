"""Diffable catalog: the source of truth for library content.

The catalog lives as reviewable YAML under `catalog/` (one file per threat, one per
mitigation, and one per entity under `style_guide/`). `threat_library.db` is a *generated*
artifact: `alembic upgrade head` builds the schema, then `keel seed` loads the catalog into
it. This keeps content changes readable in pull requests instead of a binary blob.

`keel export` does the inverse (DB -> catalog/), used after editing content via the MCP
tools or the browse UI. `keel validate` checks the YAML against the schemas before it ever
touches the database.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mitigation, Threat, ThreatMitigation
from app.schemas.mitigation import MitigationCreate
from app.schemas.threat import MitigationRef, ThreatCreate
from app.services.style_guide_service import export_yaml as _export_style_yaml
from app.services.style_guide_service import import_yaml as _import_style_yaml

# Anchored at the project root so it works regardless of the current directory.
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"

_THREAT_KEYS = {"id", "title", "description", "impact_class", "vulnerability", "reachability", "tags", "mitigations"}
_MITIGATION_KEYS = {
    "id", "name", "status", "mitigation_class", "purpose", "formal_implementation_risk",
    "review", "maintainer", "owner", "locus", "scope", "control_mechanism",
    "failure_behavior", "telemetry", "anti_patterns", "validation", "faq",
}


def _dump(data: Any) -> str:
    # width kept effectively unlimited so prose values stay one-per-line instead of
    # being hard-wrapped at ~80 cols (noisy diffs, and just annoying to read).
    return yaml.dump(
        data, allow_unicode=True, default_flow_style=False, sort_keys=False, width=1_000_000
    )


async def export_catalog(
    session: AsyncSession, catalog_dir: Path = DEFAULT_CATALOG_DIR
) -> dict[str, int]:
    """Dump DB content to `catalog/`: one YAML per threat and per mitigation, plus one
    file per entity under `style_guide/`. Overwrites the files for current rows."""
    threats_dir = catalog_dir / "threats"
    mit_dir = catalog_dir / "mitigations"
    threats_dir.mkdir(parents=True, exist_ok=True)
    mit_dir.mkdir(parents=True, exist_ok=True)

    threats = (await session.execute(select(Threat).order_by(Threat.id))).scalars().all()
    mitigations = (await session.execute(select(Mitigation).order_by(Mitigation.id))).scalars().all()
    links = (await session.execute(select(ThreatMitigation).order_by(ThreatMitigation.id))).scalars().all()

    links_by_threat: dict[str, list[dict[str, str]]] = {}
    for link in links:
        links_by_threat.setdefault(link.threat_id, []).append(
            {"mitigation_id": link.mitigation_id, "rationale": link.rationale}
        )

    for t in threats:
        record = {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "impact_class": t.impact_class,
            "vulnerability": t.vulnerability or [],
            "reachability": t.reachability,
            "tags": t.tags or [],
            "mitigations": sorted(
                links_by_threat.get(t.id, []), key=lambda m: m["mitigation_id"]
            ),
        }
        (threats_dir / f"{t.id}.yaml").write_text(_dump(record), encoding="utf-8")

    for m in mitigations:
        record = {
            "id": m.id,
            "name": m.name,
            "status": m.status,
            "mitigation_class": m.mitigation_class,
            "purpose": m.purpose,
            "formal_implementation_risk": m.formal_implementation_risk,
            "review": m.review,
            "maintainer": m.maintainer,
            "owner": m.owner,
            "locus": m.locus,
            "scope": m.scope,
            "control_mechanism": m.control_mechanism,
            "failure_behavior": m.failure_behavior,
            "telemetry": m.telemetry,
            "anti_patterns": m.anti_patterns or [],
            "validation": m.validation or [],
            "faq": m.faq or [],
        }
        (mit_dir / f"{m.id}.yaml").write_text(_dump(record), encoding="utf-8")

    # Style guide: one file per entity, so a field's authoring bar diffs on its own.
    sg = yaml.safe_load(await _export_style_yaml(session)) or {}
    sg_dir = catalog_dir / "style_guide"
    sg_dir.mkdir(parents=True, exist_ok=True)
    for entity_type, ent in (sg.get("entities") or {}).items():
        (sg_dir / f"{entity_type}.yaml").write_text(_dump(ent), encoding="utf-8")
    legacy = catalog_dir / "style_guide.yaml"
    if legacy.exists():
        legacy.unlink()

    return {"threats": len(threats), "mitigations": len(mitigations), "links": len(links)}


async def _load_style_guide(session: AsyncSession, catalog_dir: Path) -> None:
    """Load style_guide/ (one file per entity), or a legacy single style_guide.yaml."""
    entities: dict[str, Any] = {}
    sg_dir = catalog_dir / "style_guide"
    if sg_dir.is_dir():
        for path in sorted(sg_dir.glob("*.yaml")):
            entities[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    legacy = catalog_dir / "style_guide.yaml"
    if not entities and legacy.exists():
        entities = (yaml.safe_load(legacy.read_text(encoding="utf-8")) or {}).get("entities", {}) or {}
    if entities:
        combined = yaml.safe_dump({"entities": entities}, allow_unicode=True, sort_keys=False)
        await _import_style_yaml(session, combined, mode="merge", updated_by="seed")


async def load_catalog(
    session: AsyncSession, catalog_dir: Path = DEFAULT_CATALOG_DIR
) -> dict[str, int]:
    """Upsert `catalog/` YAML into the DB (idempotent). The schema must already exist
    (run `alembic upgrade head` first). Mitigations load before threats so the links
    resolve."""
    if not catalog_dir.exists():
        raise FileNotFoundError(f"catalog directory not found: {catalog_dir}")

    n_mit = 0
    for path in sorted((catalog_dir / "mitigations").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        fields = {
            "name": rec.get("name"),
            "status": rec.get("status"),
            "mitigation_class": rec.get("mitigation_class"),
            "purpose": rec.get("purpose"),
            "formal_implementation_risk": rec.get("formal_implementation_risk"),
            "review": rec.get("review"),
            "maintainer": rec.get("maintainer"),
            "owner": rec.get("owner"),
            "locus": rec.get("locus"),
            "scope": rec.get("scope"),
            "control_mechanism": rec.get("control_mechanism"),
            "failure_behavior": rec.get("failure_behavior"),
            "telemetry": rec.get("telemetry"),
            "anti_patterns": rec.get("anti_patterns") or None,
            "validation": rec.get("validation") or None,
            "faq": rec.get("faq") or None,
        }
        row = await session.get(Mitigation, rec["id"])
        if row is None:
            session.add(Mitigation(id=rec["id"], **fields))
        else:
            for k, v in fields.items():
                setattr(row, k, v)
        n_mit += 1
    await session.flush()

    n_threat = 0
    n_link = 0
    for path in sorted((catalog_dir / "threats").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tid = rec["id"]
        fields = {
            "title": rec.get("title"),
            "description": rec.get("description"),
            "impact_class": rec.get("impact_class"),
            "vulnerability": rec.get("vulnerability") or None,
            "reachability": rec.get("reachability"),
            "tags": rec.get("tags") or None,
        }
        row = await session.get(Threat, tid)
        if row is None:
            session.add(Threat(id=tid, **fields))
        else:
            for k, v in fields.items():
                setattr(row, k, v)
        n_threat += 1

        for link in rec.get("mitigations") or []:
            mid = link["mitigation_id"]
            link_id = f"{tid}::{mid}"
            lrow = await session.get(ThreatMitigation, link_id)
            if lrow is None:
                session.add(
                    ThreatMitigation(
                        id=link_id,
                        threat_id=tid,
                        mitigation_id=mid,
                        rationale=link.get("rationale") or "",
                    )
                )
            else:
                lrow.rationale = link.get("rationale") or ""
            n_link += 1

    await _load_style_guide(session, catalog_dir)
    await session.commit()
    return {"threats": n_threat, "mitigations": n_mit, "links": n_link}


def _fmt_err(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"]) or "(root)"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def validate_catalog(catalog_dir: Path = DEFAULT_CATALOG_DIR) -> list[str]:
    """Validate catalog YAML before it touches the database. Checks each record against
    the Pydantic schema (types and the strict enums), that a file's `id` matches its
    filename, that ids are unique, that no unknown fields slipped in, and that every
    threat->mitigation link resolves. Returns human-readable errors (empty list = valid)."""
    errors: list[str] = []
    if not catalog_dir.exists():
        return [f"catalog directory not found: {catalog_dir}"]

    mit_ids: set[str] = set()
    for path in sorted((catalog_dir / "mitigations").glob("*.yaml")):
        rel = path.relative_to(catalog_dir).as_posix()
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict):
            errors.append(f"{rel}: not a YAML mapping")
            continue
        unknown = set(rec) - _MITIGATION_KEYS
        if unknown:
            errors.append(f"{rel}: unknown field(s): {', '.join(sorted(unknown))}")
        try:
            MitigationCreate(**{k: rec[k] for k in rec if k in _MITIGATION_KEYS})
        except ValidationError as e:
            errors.append(f"{rel}: {_fmt_err(e)}")
        rid = rec.get("id")
        if rid != path.stem:
            errors.append(f"{rel}: id {rid!r} does not match filename {path.stem!r}")
        elif rid in mit_ids:
            errors.append(f"{rel}: duplicate mitigation id {rid!r}")
        else:
            mit_ids.add(rid)

    threat_ids: set[str] = set()
    for path in sorted((catalog_dir / "threats").glob("*.yaml")):
        rel = path.relative_to(catalog_dir).as_posix()
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict):
            errors.append(f"{rel}: not a YAML mapping")
            continue
        unknown = set(rec) - _THREAT_KEYS
        if unknown:
            errors.append(f"{rel}: unknown field(s): {', '.join(sorted(unknown))}")
        try:
            ThreatCreate(**{k: rec[k] for k in rec if k in _THREAT_KEYS and k != "mitigations"})
        except ValidationError as e:
            errors.append(f"{rel}: {_fmt_err(e)}")
        rid = rec.get("id")
        if rid != path.stem:
            errors.append(f"{rel}: id {rid!r} does not match filename {path.stem!r}")
        elif rid in threat_ids:
            errors.append(f"{rel}: duplicate threat id {rid!r}")
        else:
            threat_ids.add(rid)

        links = rec.get("mitigations") or []
        if not isinstance(links, list):
            errors.append(f"{rel}: 'mitigations' must be a list")
            continue
        for i, link in enumerate(links):
            if not isinstance(link, dict):
                errors.append(f"{rel}: mitigations[{i}] is not a mapping")
                continue
            try:
                ref = MitigationRef(**link)
            except ValidationError as e:
                errors.append(f"{rel}: mitigations[{i}]: {_fmt_err(e)}")
                continue
            if ref.mitigation_id not in mit_ids:
                errors.append(
                    f"{rel}: mitigations[{i}] references unknown mitigation {ref.mitigation_id!r}"
                )

    sg_dir = catalog_dir / "style_guide"
    if sg_dir.is_dir():
        for path in sorted(sg_dir.glob("*.yaml")):
            rel = path.relative_to(catalog_dir).as_posix()
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("fields"), dict):
                errors.append(f"{rel}: expected a mapping with a 'fields' mapping")

    return errors
