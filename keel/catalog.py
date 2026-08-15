"""Catalog validation.

`catalog/*.yaml` is the source of truth (loaded into memory by `keel.store`). This
module validates those files against the schemas before they are trusted: strict
enums, id/filename agreement, unique ids, no unknown fields, and link integrity.
Run via `keel validate`; also used in CI.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import MitigationRef, ThreatCreate
from keel.store import DEFAULT_CATALOG_DIR

_THREAT_KEYS = {
    "id", "title", "description", "impact_class", "vulnerability", "reachability",
    "tags", "mitigations",
}
_MITIGATION_KEYS = {
    "id", "name", "status", "mitigation_class", "purpose", "formal_implementation_risk",
    "review", "maintainer", "owner", "locus", "scope", "control_mechanism",
    "failure_behavior", "telemetry", "anti_patterns", "validation", "faq",
}


def _fmt_err(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"]) or "(root)"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def validate_catalog(catalog_dir: Path = DEFAULT_CATALOG_DIR) -> list[str]:
    """Validate catalog YAML. Checks each record against the Pydantic schema (types and
    strict enums), that a file's `id` matches its filename, that ids are unique, that no
    unknown fields slipped in, and that every threat->mitigation link resolves. Returns
    human-readable errors (empty list = valid)."""
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
