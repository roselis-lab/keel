"""Service layer for the style guide stored in `style_guide_field`.

Skeleton rows are synced from the model columns of the tracked entities, so a
new content field automatically surfaces as an uncovered methodology gap.
"""
from __future__ import annotations

from typing import Any

import yaml as yaml_mod
from sqlalchemy import inspect as sa_inspect, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from keel.models import StyleGuideField, Threat, Mitigation, ThreatMitigation
from keel.schemas.style_guide import (
    CoverageReport,
    EntityCoverage,
    FieldCoverage,
    StyleGuideEntity,
    StyleGuideFieldRead,
    StyleGuideFull,
)


# Slots that count toward "completeness".
TRACKED_SLOTS = ("purpose", "content_requirements", "instructions", "avoid", "examples")


ENTITY_MODEL_MAPPING: dict[str, type] = {
    "threat": Threat,
    "mitigation": Mitigation,
    "threat_mitigation": ThreatMitigation,
}

# Identifiers and foreign keys carry no authoring methodology.
TECHNICAL_FIELDS: dict[str, set[str]] = {
    "threat": {"id"},
    "mitigation": {"id"},
    "threat_mitigation": {"id", "threat_id", "mitigation_id"},
}


def _model_content_fields(entity_type: str, model_class: type) -> list[str]:
    mapper = sa_inspect(model_class)
    fields = {col.key for col in mapper.columns}
    excluded = TECHNICAL_FIELDS.get(entity_type, set())
    return sorted(fields - excluded)


async def sync_skeletons(session: AsyncSession) -> dict[str, int]:
    """Insert skeleton rows for new model fields; mark removed fields as orphan.

    Returns counts {inserted, orphaned, unorphaned}. Idempotent.
    """
    inserted = 0
    orphaned = 0
    unorphaned = 0

    for entity_type, model_class in ENTITY_MODEL_MAPPING.items():
        model_fields = set(_model_content_fields(entity_type, model_class))

        existing_rows = (await session.execute(
            select(StyleGuideField).where(StyleGuideField.entity_type == entity_type)
        )).scalars().all()
        existing_by_name = {r.field_name: r for r in existing_rows}

        for field_name in sorted(model_fields - existing_by_name.keys()):
            session.add(StyleGuideField(
                entity_type=entity_type,
                field_name=field_name,
                updated_by="auto-sync",
                is_orphan=False,
            ))
            inserted += 1

        for field_name in model_fields & existing_by_name.keys():
            row = existing_by_name[field_name]
            if row.is_orphan:
                row.is_orphan = False
                unorphaned += 1

        for field_name in existing_by_name.keys() - model_fields:
            row = existing_by_name[field_name]
            if not row.is_orphan:
                row.is_orphan = True
                orphaned += 1

    await session.commit()
    return {"inserted": inserted, "orphaned": orphaned, "unorphaned": unorphaned}


async def get_full_guide(session: AsyncSession) -> StyleGuideFull:
    rows = (await session.execute(
        select(StyleGuideField)
        .order_by(StyleGuideField.entity_type, StyleGuideField.sort_order, StyleGuideField.field_name)
    )).scalars().all()
    by_entity: dict[str, dict[str, StyleGuideFieldRead]] = {}
    for r in rows:
        by_entity.setdefault(r.entity_type, {})[r.field_name] = StyleGuideFieldRead.model_validate(r)
    entities = {
        et: StyleGuideEntity(entity_type=et, fields=fields)
        for et, fields in by_entity.items()
    }
    return StyleGuideFull(entities=entities)


async def get_entity(session: AsyncSession, entity_type: str) -> StyleGuideEntity:
    rows = (await session.execute(
        select(StyleGuideField)
        .where(StyleGuideField.entity_type == entity_type)
        .order_by(StyleGuideField.sort_order, StyleGuideField.field_name)
    )).scalars().all()
    return StyleGuideEntity(
        entity_type=entity_type,
        fields={r.field_name: StyleGuideFieldRead.model_validate(r) for r in rows},
    )


async def get_field(
    session: AsyncSession, entity_type: str, field_name: str,
) -> StyleGuideFieldRead:
    row = (await session.execute(
        select(StyleGuideField).where(
            StyleGuideField.entity_type == entity_type,
            StyleGuideField.field_name == field_name,
        )
    )).scalar_one_or_none()
    if row is None:
        raise KeyError(f"{entity_type}.{field_name} not found")
    return StyleGuideFieldRead.model_validate(row)


async def update_field(
    session: AsyncSession,
    entity_type: str,
    field_name: str,
    patch: dict[str, Any],
    *,
    updated_by: str,
) -> StyleGuideFieldRead:
    row = (await session.execute(
        select(StyleGuideField).where(
            StyleGuideField.entity_type == entity_type,
            StyleGuideField.field_name == field_name,
        )
    )).scalar_one_or_none()
    if row is None:
        raise KeyError(f"{entity_type}.{field_name} not found")
    for key, value in patch.items():
        if hasattr(row, key):
            setattr(row, key, value)
    row.updated_by = updated_by
    await session.commit()
    await session.refresh(row)
    return StyleGuideFieldRead.model_validate(row)


def _completeness(row: StyleGuideField) -> int:
    filled = sum(1 for slot in TRACKED_SLOTS if getattr(row, slot))
    return int(round(100 * filled / len(TRACKED_SLOTS)))


async def get_coverage(session: AsyncSession) -> CoverageReport:
    rows = (await session.execute(
        select(StyleGuideField).order_by(StyleGuideField.entity_type, StyleGuideField.field_name)
    )).scalars().all()
    by_entity: dict[str, list[FieldCoverage]] = {}
    for r in rows:
        if r.is_orphan:
            continue
        by_entity.setdefault(r.entity_type, []).append(FieldCoverage(
            field_name=r.field_name,
            completeness=_completeness(r),
            is_orphan=r.is_orphan,
        ))
    entities: list[EntityCoverage] = []
    overall_sum = 0
    overall_count = 0
    for et, fields in by_entity.items():
        ent_overall = int(round(sum(f.completeness for f in fields) / max(len(fields), 1)))
        entities.append(EntityCoverage(entity_type=et, fields=fields, overall=ent_overall))
        overall_sum += sum(f.completeness for f in fields)
        overall_count += len(fields)
    overall = int(round(overall_sum / overall_count)) if overall_count else 0
    return CoverageReport(entities=entities, overall=overall)


_IMPORT_SLOTS = (
    "purpose", "content_requirements", "instructions",
    "avoid", "examples", "subfields", "allowed_values",
)


async def import_yaml(
    session: AsyncSession,
    yaml_text: str,
    *,
    mode: str = "merge",
    updated_by: str,
) -> dict[str, int]:
    """Import style guide from YAML text.

    mode='merge' UPSERTs by (entity_type, field_name), preserving slots absent
    from the YAML. mode='replace' clears all slots for entities present in the
    YAML before importing.
    """
    if mode not in ("merge", "replace"):
        raise ValueError("mode must be 'merge' or 'replace'")

    data = yaml_mod.safe_load(yaml_text) or {}
    entities = data.get("entities", {}) or {}

    if mode == "replace":
        for entity_type in entities.keys():
            await session.execute(
                update(StyleGuideField)
                .where(StyleGuideField.entity_type == entity_type)
                .values(
                    purpose=None,
                    content_requirements=None,
                    instructions=None,
                    avoid=None,
                    examples=None,
                    subfields=None,
                    allowed_values=None,
                )
            )

    inserted = 0
    updated_count = 0
    skipped = 0
    for entity_type, ent in entities.items():
        fields = (ent or {}).get("fields", {}) or {}
        for field_name, field_data in fields.items():
            if not isinstance(field_data, dict):
                skipped += 1
                continue
            payload = {k: field_data.get(k) for k in _IMPORT_SLOTS if k in field_data}

            row = (await session.execute(
                select(StyleGuideField).where(
                    StyleGuideField.entity_type == entity_type,
                    StyleGuideField.field_name == field_name,
                )
            )).scalar_one_or_none()

            if row is None:
                session.add(StyleGuideField(
                    entity_type=entity_type,
                    field_name=field_name,
                    updated_by=updated_by,
                    **payload,
                ))
                inserted += 1
            else:
                for k, v in payload.items():
                    setattr(row, k, v)
                row.updated_by = updated_by
                updated_count += 1

    await session.commit()
    return {"inserted": inserted, "updated": updated_count, "skipped": skipped}


async def export_yaml(session: AsyncSession) -> str:
    """Dump the current style guide to YAML text."""
    full = await get_full_guide(session)
    out: dict[str, Any] = {"version": full.version, "entities": {}}
    for entity_type, ent in full.entities.items():
        fields_out: dict[str, dict[str, Any]] = {}
        for field_name, field in ent.fields.items():
            # Skip orphans: fields whose model column no longer exists. Their methodology
            # is retained in the DB (recoverable if the field returns) but must not leak
            # back into the catalog, which mirrors the live model.
            if field.is_orphan:
                continue
            slot: dict[str, Any] = {}
            for k in _IMPORT_SLOTS:
                v = getattr(field, k)
                if v is None:
                    continue
                if isinstance(v, (list, dict)) and len(v) == 0:
                    continue
                slot[k] = v
            if slot:
                fields_out[field_name] = slot
        out["entities"][entity_type] = {"fields": fields_out}
    return yaml_mod.dump(out, allow_unicode=True, default_flow_style=False, sort_keys=False)


async def list_incomplete(session: AsyncSession) -> list[dict[str, Any]]:
    """Return non-orphan fields with one or more empty tracked slots."""
    rows = (await session.execute(
        select(StyleGuideField).where(StyleGuideField.is_orphan == False)  # noqa: E712
    )).scalars().all()
    out: list[dict[str, Any]] = []
    for r in rows:
        missing = [slot for slot in TRACKED_SLOTS if not getattr(r, slot)]
        if missing:
            out.append({
                "entity_type": r.entity_type,
                "field_name": r.field_name,
                "missing_slots": missing,
            })
    return out
