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
from keel.schemas.threat import Threat
from keel.store import DEFAULT_CATALOG_DIR

# Technique words that must never be a threat/weakness identity (they are mechanisms →
# they belong in `source` / `references`). Kept LLM-specific so established threat names
# like "command injection" are not flagged.
_TECHNIQUE_WORDS = ("prompt injection", "jailbreak")

_MITIGATION_KEYS = {
    "id", "name", "status", "mitigation_class", "purpose", "formal_implementation_risk",
    "review", "maintainer", "owner", "locus", "scope", "control_mechanism",
    "failure_behavior", "telemetry", "anti_patterns", "validation", "faq",
    "implementations",
}


def _fmt_err(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"]) or "(root)"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def lint_threat(threat: Threat) -> list[dict[str, str]]:
    """Non-blocking advice for one threat (no gating control; a technique used as identity).
    These are the 'amber' nudges the authoring UI shows; they never block a save. Each item
    carries a `field` (dotted path, or "") so the UI can pin the note to the right input."""
    out: list[dict[str, str]] = []
    if threat.mitigations and not any(m.strength == "gating" for m in threat.mitigations):
        out.append({
            "field": "mitigations",
            "msg": "no `gating` mitigation (all soft) — no architectural closure",
        })
    for tw in _TECHNIQUE_WORDS:
        if tw in threat.title.lower():
            out.append({
                "field": "title",
                "msg": f"technique {tw!r} used as the threat title — belongs in source/references",
            })
            continue
        for i, w in enumerate(threat.weaknesses):
            if tw in w.text.lower() and len(w.text) < 40:
                out.append({
                    "field": f"weaknesses.{i}.text",
                    "msg": f"technique {tw!r} used as a weakness identity — belongs in source/references",
                })
                break
    return out


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

        # Whole-record schema validation (extra="forbid" catches unknown fields; Literals
        # enforce the frozen vocabularies; HttpUrl enforces reference links).
        threat = None
        try:
            threat = Threat(**rec)
        except ValidationError as e:
            errors.append(f"{rel}: {_fmt_err(e)}")

        rid = rec.get("id")
        if rid != path.stem:
            errors.append(f"{rel}: id {rid!r} does not match filename {path.stem!r}")
        elif rid in threat_ids:
            errors.append(f"{rel}: duplicate threat id {rid!r}")
        elif rid:
            threat_ids.add(rid)

        if threat is None:
            continue

        # Link integrity: every mitigation id resolves to a real card.
        for i, link in enumerate(threat.mitigations):
            if link.id not in mit_ids:
                errors.append(f"{rel}: mitigations[{i}] references unknown mitigation {link.id!r}")

        # Non-blocking authoring advice (no gating control; a technique used as identity).
        for item in lint_threat(threat):
            errors.append(f"{rel}: {item['msg']}")

    sg_dir = catalog_dir / "style_guide"
    if sg_dir.is_dir():
        for path in sorted(sg_dir.glob("*.yaml")):
            rel = path.relative_to(catalog_dir).as_posix()
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("fields"), dict):
                errors.append(f"{rel}: expected a mapping with a 'fields' mapping")

    return errors


def catalog_warnings(catalog_dir: Path = DEFAULT_CATALOG_DIR) -> list[str]:
    """Advisory quality checks over the catalog (NOT errors). These surface soft problems —
    over-graded links, missing provenance, an unused vocabulary — without failing CI. Runs
    read-only over the raw YAML (same load path as `validate_catalog`). Returns human-readable
    warnings; an empty list means nothing to nudge on.

    Checks:
      1. Over-graded link strength: a `gating` link whose target control is not a
         `gating_control` (a detector/process/advisory control does not architecturally block).
      2. Missing references: a threat with no `references` (provenance) to map to prior art.
      3. Unused `nature`: no weakness anywhere is marked `secondary` (the field may be dead).
    """
    warnings: list[str] = []
    if not catalog_dir.exists():
        return warnings

    # Mitigation id -> mitigation_class, read straight from the YAML.
    mit_class: dict[str, str] = {}
    for path in sorted((catalog_dir / "mitigations").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(rec, dict) and rec.get("id"):
            mit_class[rec["id"]] = rec.get("mitigation_class")

    any_secondary = False
    for path in sorted((catalog_dir / "threats").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict):
            continue
        tid = rec.get("id") or path.stem

        # 1. Over-graded link strength (strength vs mitigation_class).
        for link in rec.get("mitigations") or []:
            if not isinstance(link, dict) or link.get("strength") != "gating":
                continue
            mid = link.get("id")
            cls = mit_class.get(mid)
            if cls is not None and cls != "gating_control":
                warnings.append(
                    f"{tid} -> {mid}: strength 'gating' but mitigation_class is '{cls}' "
                    "— a non-gating control should not back a gating link"
                )

        # 2. Threat missing references (provenance).
        if not (rec.get("references") or []):
            warnings.append(
                f"{tid}: no references (provenance) — map to CWE/CAPEC/OWASP-LLM/ATLAS"
            )

        # 3. Track whether the `nature` field is ever used as 'secondary'.
        for w in rec.get("weaknesses") or []:
            if isinstance(w, dict) and w.get("nature") == "secondary":
                any_secondary = True

    if not any_secondary:
        warnings.append(
            "no weakness is marked 'secondary' — the nature field may be unused "
            "(every weakness is 'targeted')"
        )

    return warnings
