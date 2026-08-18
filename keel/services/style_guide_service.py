"""Service layer for the authoring style guide (backed by the file store).

The style guide lives as `catalog/style_guide/<entity>.yaml`. The set of *fields*
an entity has is derived from its Pydantic schema, so a field with no methodology
yet surfaces as a coverage gap, and a field whose schema entry was removed reads as
an orphan — both computed on the fly, no skeleton table to keep in sync.
"""
from __future__ import annotations

from typing import Any

import yaml as yaml_mod

from keel.schemas.mitigation import Implementation, MitigationCreate
from keel.schemas.style_guide import (
    CoverageReport,
    EntityCoverage,
    FieldCoverage,
    StyleGuideEntity,
    StyleGuideFieldRead,
    StyleGuideFull,
)
from keel.schemas.threat import MitigationLink, ThreatCreate, Weakness
from keel.store import get_store

# Slots that count toward the "richness" percentage.
TRACKED_SLOTS = ("purpose", "content_requirements", "instructions", "avoid", "examples")
# The minimum bar a field must have to count as authored (drives list_incomplete / the CI gate).
REQUIRED_SLOTS = ("purpose", "content_requirements")
# All authorable slots (persisted per field).
SLOTS = (
    "purpose", "content_requirements", "instructions",
    "avoid", "examples", "subfields", "allowed_values",
)
# Entities the style guide tracks, in display order.
ENTITY_ORDER = ("threat", "weakness", "mitigation_link", "mitigation", "implementation")

# Fields covered by a sub-entity's own bar, so they are not repeated on the parent.
_SUBENTITY_FIELDS = {"weaknesses", "mitigations"}


def _canonical_fields(entity_type: str) -> list[str]:
    """The fields an entity has, per its schema — so the style guide can never drift
    from the model: a new field surfaces as a gap, a removed one reads as an orphan."""
    if entity_type == "threat":
        return [f for f in ThreatCreate.model_fields if f not in ("id", *_SUBENTITY_FIELDS)]
    if entity_type == "weakness":
        return list(Weakness.model_fields)
    if entity_type == "mitigation_link":
        return [f for f in MitigationLink.model_fields if f != "id"]
    if entity_type == "mitigation":
        # implementations has its own bar, so it is not repeated on the parent.
        return [f for f in MitigationCreate.model_fields if f not in ("id", "implementations")]
    if entity_type == "implementation":
        return list(Implementation.model_fields)
    return []


def _read_field(
    entity_type: str, field_name: str, slots: dict[str, Any], canonical: list[str],
    updated_by: str | None = None,
) -> StyleGuideFieldRead:
    return StyleGuideFieldRead(
        entity_type=entity_type,
        field_name=field_name,
        is_orphan=field_name not in canonical,
        updated_by=updated_by,
        **{slot: slots.get(slot) for slot in SLOTS},
    )


def _entity(entity_type: str) -> StyleGuideEntity:
    canonical = _canonical_fields(entity_type)
    stored = get_store().style_guide.get(entity_type, {})
    names = list(dict.fromkeys([*canonical, *stored.keys()]))  # canonical first, then extras
    fields = {n: _read_field(entity_type, n, stored.get(n) or {}, canonical) for n in names}
    return StyleGuideEntity(entity_type=entity_type, fields=fields)


def _entity_types() -> list[str]:
    types = list(ENTITY_ORDER)
    for et in get_store().style_guide:
        if et not in types:
            types.append(et)
    return types


async def get_full_guide() -> StyleGuideFull:
    return StyleGuideFull(entities={et: _entity(et) for et in _entity_types()})


async def get_entity(entity_type: str) -> StyleGuideEntity:
    return _entity(entity_type)


async def get_field(entity_type: str, field_name: str) -> StyleGuideFieldRead:
    canonical = _canonical_fields(entity_type)
    stored = get_store().style_guide.get(entity_type, {})
    if field_name not in canonical and field_name not in stored:
        raise KeyError(f"{entity_type}.{field_name} not found")
    return _read_field(entity_type, field_name, stored.get(field_name) or {}, canonical)


async def update_field(
    entity_type: str,
    field_name: str,
    patch: dict[str, Any],
    *,
    updated_by: str,
) -> StyleGuideFieldRead:
    store = get_store()
    canonical = _canonical_fields(entity_type)
    entity = store.style_guide.setdefault(entity_type, {})
    if field_name not in canonical and field_name not in entity:
        raise KeyError(f"{entity_type}.{field_name} not found")
    with store.lock:
        slot = entity.setdefault(field_name, {})
        for key in SLOTS:
            if key in patch:
                slot[key] = patch[key]
        store.write_style(entity_type)
    return _read_field(entity_type, field_name, entity[field_name], canonical, updated_by)


def _completeness(field: StyleGuideFieldRead) -> int:
    filled = sum(1 for slot in TRACKED_SLOTS if getattr(field, slot))
    return int(round(100 * filled / len(TRACKED_SLOTS)))


async def get_coverage() -> CoverageReport:
    entities: list[EntityCoverage] = []
    overall_sum = 0
    overall_count = 0
    for et in _entity_types():
        fields = [
            FieldCoverage(field_name=f.field_name, completeness=_completeness(f), is_orphan=False)
            for f in _entity(et).fields.values() if not f.is_orphan
        ]
        ent_overall = int(round(sum(f.completeness for f in fields) / max(len(fields), 1)))
        entities.append(EntityCoverage(entity_type=et, fields=fields, overall=ent_overall))
        overall_sum += sum(f.completeness for f in fields)
        overall_count += len(fields)
    overall = int(round(overall_sum / overall_count)) if overall_count else 0
    return CoverageReport(entities=entities, overall=overall)


async def list_incomplete() -> list[dict[str, Any]]:
    """Return non-orphan fields missing a required slot (purpose / content_requirements) —
    i.e. fields whose authoring bar is not yet written. Optional slots do not count."""
    out: list[dict[str, Any]] = []
    for et in _entity_types():
        for field in _entity(et).fields.values():
            if field.is_orphan:
                continue
            missing = [slot for slot in REQUIRED_SLOTS if not getattr(field, slot)]
            if missing:
                out.append({
                    "entity_type": et,
                    "field_name": field.field_name,
                    "missing_slots": missing,
                })
    return out


async def import_yaml(
    yaml_text: str,
    *,
    mode: str = "merge",
    updated_by: str,
) -> dict[str, int]:
    """Import style guide from YAML text and write the affected entity files.

    mode='merge' UPSERTs by (entity, field), preserving slots absent from the YAML.
    mode='replace' clears all slots for entities present in the YAML first.
    """
    if mode not in ("merge", "replace"):
        raise ValueError("mode must be 'merge' or 'replace'")

    store = get_store()
    data = yaml_mod.safe_load(yaml_text) or {}
    entities = data.get("entities", {}) or {}

    inserted = 0
    updated_count = 0
    skipped = 0
    with store.lock:
        for entity_type, ent in entities.items():
            fields = (ent or {}).get("fields", {}) or {}
            target = store.style_guide.setdefault(entity_type, {})
            if mode == "replace":
                target.clear()
            for field_name, field_data in fields.items():
                if not isinstance(field_data, dict):
                    skipped += 1
                    continue
                payload = {k: field_data.get(k) for k in SLOTS if k in field_data}
                if field_name in target:
                    target[field_name].update(payload)
                    updated_count += 1
                else:
                    target[field_name] = payload
                    inserted += 1
            store.write_style(entity_type)
    return {"inserted": inserted, "updated": updated_count, "skipped": skipped}


async def export_yaml() -> str:
    """Dump the current style guide (non-orphan fields with content) to YAML text."""
    out: dict[str, Any] = {"version": "1.0", "entities": {}}
    for et in _entity_types():
        fields_out: dict[str, dict[str, Any]] = {}
        for field in _entity(et).fields.values():
            if field.is_orphan:
                continue
            slot: dict[str, Any] = {}
            for key in SLOTS:
                value = getattr(field, key)
                if value is None or (isinstance(value, (list, dict)) and len(value) == 0):
                    continue
                slot[key] = value
            if slot:
                fields_out[field.field_name] = slot
        out["entities"][et] = {"fields": fields_out}
    return yaml_mod.dump(out, allow_unicode=True, default_flow_style=False, sort_keys=False)
