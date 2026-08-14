"""Diffable catalog: the source of truth for library content.

The catalog lives as reviewable YAML under `catalog/` (one file per threat, one per
mitigation, plus `style_guide.yaml`). `threat_library.db` is a *generated* artifact:
`alembic upgrade head` builds the schema, then `keel seed` loads the catalog into it.
This keeps content changes readable in pull requests instead of hidden in a binary blob.

`keel export` does the inverse (DB -> catalog/), used after editing content via the MCP
tools or the browse UI to write the changes back to the reviewable YAML.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mitigation, Threat, ThreatMitigation
from app.services.style_guide_service import export_yaml as _export_style_yaml
from app.services.style_guide_service import import_yaml as _import_style_yaml

# Anchored at the project root so it works regardless of the current directory.
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


def _dump(data: Any) -> str:
    return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)


async def export_catalog(
    session: AsyncSession, catalog_dir: Path = DEFAULT_CATALOG_DIR
) -> dict[str, int]:
    """Dump DB content to `catalog/`: one YAML per threat and per mitigation, plus
    style_guide.yaml. Overwrites the files that exist for current rows."""
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
            "title": m.title,
            "description": m.description,
            "type": m.type,
            "requirement_level": m.requirement_level,
            "implementations": m.implementations or [],
        }
        (mit_dir / f"{m.id}.yaml").write_text(_dump(record), encoding="utf-8")

    (catalog_dir / "style_guide.yaml").write_text(
        await _export_style_yaml(session), encoding="utf-8"
    )
    return {"threats": len(threats), "mitigations": len(mitigations), "links": len(links)}


async def load_catalog(
    session: AsyncSession, catalog_dir: Path = DEFAULT_CATALOG_DIR
) -> dict[str, int]:
    """Upsert `catalog/` YAML into the DB (idempotent). The schema must already
    exist (run `alembic upgrade head` first). Mitigations load before threats so
    the links resolve."""
    if not catalog_dir.exists():
        raise FileNotFoundError(f"catalog directory not found: {catalog_dir}")

    n_mit = 0
    for path in sorted((catalog_dir / "mitigations").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        fields = {
            "title": rec.get("title"),
            "description": rec.get("description"),
            "type": rec.get("type"),
            "requirement_level": rec.get("requirement_level"),
            "implementations": rec.get("implementations") or None,
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

    style_path = catalog_dir / "style_guide.yaml"
    if style_path.exists():
        await _import_style_yaml(
            session, style_path.read_text(encoding="utf-8"), mode="merge", updated_by="seed"
        )

    await session.commit()
    return {"threats": n_threat, "mitigations": n_mit, "links": n_link}
