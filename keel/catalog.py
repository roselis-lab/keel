"""Catalog validation.

`catalog/*.yaml` is the source of truth (loaded into memory by `keel.store`). This
module answers one question: may this catalog be trusted as it stands. It parses each
file, checks what only a file can know (its id matches its name, ids are unique, no
unknown fields, the vocabulary files agree with the Literals), and then hands the parsed
records to the rule registry, which owns everything decided by looking across records.

Errors only. Anything a half-authored entry may legitimately trip is advice and belongs
in `catalog_warnings`, which never fails CI on its own.
Run via `keel validate`; also used in CI.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import Threat
from keel.store import resolve_catalog_dir

# Derived, not retyped. The list lived here, in `store.MITIGATION_ORDER` and in the model
# itself, so adding a field meant remembering three places and finding out on the third.
_MITIGATION_KEYS = set(MitigationCreate.model_fields)


def _fmt_err(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"]) or "(root)"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def validate_catalog(catalog_dir: Path | None = None) -> list[str]:
    """Validate catalog YAML. Checks each record against the Pydantic schema (types and
    strict enums), that a file's `id` matches its filename, that ids are unique, that no
    unknown fields slipped in, and that every threat->mitigation link resolves. Returns
    human-readable errors (empty list = valid)."""
    catalog_dir = catalog_dir or resolve_catalog_dir()
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



    # The four vocabulary files are the human gloss for the Literals that enforce them.
    # They must agree in both directions, or the gloss silently describes a schema that
    # no longer exists.
    from keel.vocabulary import vocabulary_errors

    errors.extend(vocabulary_errors(catalog_dir))

    from keel.services.coverage_service import coverage_errors

    errors.extend(coverage_errors(catalog_dir))

    # Everything decided by looking across records - a link to nothing, a card that does
    # not say what it does, a coverage row naming something deleted - comes from the one
    # rule registry, so `keel validate` and a write cannot disagree about what is wrong.
    errors.extend(
        f"{f['entity_type']}/{f['entity_id']}: {f['message']}"
        for f in catalog_findings(catalog_dir) if f["severity"] == "error"
    )

    sg_dir = catalog_dir / "style_guide"
    if sg_dir.is_dir():
        for path in sorted(sg_dir.glob("*.yaml")):
            rel = path.relative_to(catalog_dir).as_posix()
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("fields"), dict):
                errors.append(f"{rel}: expected a mapping with a 'fields' mapping")

    return errors


def _catalog_for(catalog_dir: Path | None = None):
    """Load the records the rules run over. Rules are pure and never read the disk, so
    the loading is done once here."""
    from keel.rules import Catalog
    from keel.services.coverage_service import load_sources
    from keel.store import Store

    catalog_dir = catalog_dir or resolve_catalog_dir()
    store = Store(catalog_dir)
    return Catalog.from_store(store, coverage=load_sources(catalog_dir))


def catalog_findings(catalog_dir: Path | None = None) -> list[dict[str, str | None]]:
    """Every rule, over every record. The sweep entry point; `keel validate` and the
    dashboard both read this."""
    from keel.rules import check_all

    catalog_dir = catalog_dir or resolve_catalog_dir()
    if not catalog_dir.exists():
        return []
    return [f.as_dict() for f in check_all(_catalog_for(catalog_dir))]


def catalog_warnings_structured(catalog_dir: Path | None = None) -> list[dict[str, str | None]]:
    """The advisory half of the sweep, in the shape the dashboard already renders.

    `category` is the rule's code. Kept as a separate function because errors and advice
    go to different places in the UI and fail CI differently."""
    return [
        {"category": f["code"], "entity_type": f.get("entity_type"),
         "entity_id": f.get("entity_id"), "message": _sentence(f)}
        for f in catalog_findings(catalog_dir) if f["severity"] == "advice"
    ]


def _sentence(finding: dict[str, str | None]) -> str:
    """A finding as one line that stands on its own, for a terminal or a log."""
    subject = finding.get("entity_id")
    return f"{subject}: {finding['message']}" if subject else finding["message"]


def catalog_warnings(catalog_dir: Path | None = None) -> list[str]:
    """Advisory findings as sentences. Never fails CI on its own; `--strict` does."""
    return [w["message"] for w in catalog_warnings_structured(catalog_dir)]
