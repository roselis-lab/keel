"""Reading the coverage matrix, and turning it around.

The files are written source-first — every entry of a tracked release, present whether
or not Keel answers it. That direction is forced: the matrix's job is completeness of
somebody else's list, and a gap is only visible if the row exists to be empty.

A card needs the opposite view — "who names me" — so that is derived here rather than
stored twice. One direction on disk, both directions in the app.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.errors import Forbidden, IntegrityError, Invalid, NotFound, invalid_from_pydantic
from keel.schemas.coverage import CoverageFile
from keel.store import get_store

COVERAGE_DIRNAME = "coverage"


def _dir(catalog_dir: Path | None = None) -> Path:
    """Default to the catalog the store actually loaded, not to a freshly resolved path.
    The matrix names ids that must exist in the store, so reading the two from different
    directories would make every claim look false."""
    return Path(catalog_dir or get_store().dir) / COVERAGE_DIRNAME


def load_sources(catalog_dir: Path | None = None) -> list[CoverageFile]:
    """Every valid coverage file, ordered by title. Invalid ones are skipped here and
    reported by `coverage_errors`, the same split the catalog itself uses."""
    out: list[CoverageFile] = []
    directory = _dir(catalog_dir)
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            out.append(CoverageFile(**data))
        except (yaml.YAMLError, ValidationError, TypeError):
            continue
    return sorted(out, key=lambda f: f.source.title)


def coverage_errors(catalog_dir: Path | None = None) -> list[str]:
    """Hard problems: a file that will not parse, a filename that disagrees with its id,
    or an entry pointing at an entry that is not in the catalog.

    A dangling id here is worse than one inside the catalog, because this file is the
    public claim. "We cover ASI02" pointing at a threat that was deleted is not a broken
    link, it is a false statement about what Keel does.
    """
    errors: list[str] = []
    directory = _dir(catalog_dir)
    if not directory.is_dir():
        return errors

    store = get_store()
    seen_ids: set[str] = set()

    for path in sorted(directory.glob("*.yaml")):
        rel = f"{COVERAGE_DIRNAME}/{path.name}"
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            errors.append(f"{rel}: not readable as YAML: {e}")
            continue
        try:
            doc = CoverageFile(**data)
        except (ValidationError, TypeError) as e:
            first = e.errors()[0] if isinstance(e, ValidationError) else None
            loc = ".".join(str(x) for x in first["loc"]) if first else ""
            msg = first["msg"] if first else str(e)
            errors.append(f"{rel}: {loc}: {msg}" if loc else f"{rel}: {msg}")
            continue

        if doc.source.id != path.stem:
            errors.append(f"{rel}: source id {doc.source.id!r} does not match filename {path.stem!r}")
        elif doc.source.id in seen_ids:
            errors.append(f"{rel}: duplicate source id {doc.source.id!r}")
        else:
            seen_ids.add(doc.source.id)

        for e in doc.entries:
            for tid in e.threats:
                if tid not in store.threats:
                    errors.append(
                        f"{rel}: {e.ref} claims threat {tid!r}, which is not in the catalog"
                    )
            for mid in e.mitigations:
                if mid not in store.mitigations:
                    errors.append(
                        f"{rel}: {e.ref} claims mitigation {mid!r}, which is not in the catalog"
                    )

    return errors


def _matrix_warnings(catalog_dir: Path | None = None) -> list[dict[str, Any]]:
    """The matrix's own advice, from the shared registry rather than a second copy."""
    from keel.catalog import catalog_findings

    return [f for f in catalog_findings(catalog_dir) if f.get("entity_type") == "coverage"
            and f["severity"] == "advice"]


def matrix(catalog_dir: Path | None = None) -> dict[str, Any]:
    """The whole matrix, plus per-source tallies. What the coverage screen renders."""
    sources = []
    for doc in load_sources(catalog_dir):
        counts = {"covered": 0, "out_of_scope": 0, "gap": 0}
        for e in doc.entries:
            counts[e.state] += 1
        sources.append({
            "source": doc.source.model_dump(mode="json"),
            "counts": counts,
            "imported": len(doc.entries),
            "entries": [e.model_dump(mode="json") for e in doc.entries],
        })
    return {"sources": sources, "warnings": _matrix_warnings(catalog_dir)}


def by_entity(catalog_dir: Path | None = None) -> dict[str, list[dict[str, str]]]:
    """The reverse index: Keel id -> the source entries that name it.

    This is what puts "corroborated by OWASP LLM06, ATLAS AML.T0053" on a card without
    the card storing it. A card that appears nowhere in here is not a defect — it is
    Keel's own contribution, and saying so is worth as much as the corroboration.
    """
    out: dict[str, list[dict[str, str]]] = {}
    for doc in load_sources(catalog_dir):
        for e in doc.entries:
            if e.state != "covered":
                continue
            cite = {
                "source_id": doc.source.id,
                "source_title": doc.source.title,
                "version": doc.source.version,
                "ref": e.ref,
                "title": e.title,
                "url": str(doc.source.url),
            }
            for key in (*e.threats, *e.mitigations):
                out.setdefault(key, []).append(cite)
    return out


def gaps(catalog_dir: Path | None = None) -> list[dict[str, str]]:
    """Every entry nothing answers yet, flattened — the authoring queue, ordered by how
    many tracked sources name the same thing."""
    rows: list[dict[str, str]] = []
    for doc in load_sources(catalog_dir):
        for e in doc.entries:
            if e.state == "gap":
                rows.append({
                    "source_id": doc.source.id,
                    "source_title": doc.source.title,
                    "ref": e.ref,
                    "title": e.title,
                    "group": e.group,
                })
    rows.sort(key=lambda r: (r["source_id"], r["ref"]))
    return rows


def set_entry(
    source_id: str,
    ref: str,
    state: str,
    threats: list[str] | None = None,
    mitigations: list[str] | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Move one row of the matrix, validating the claim before it is written.

    This is the write that happens constantly while the catalog is refilled: a threat
    lands, and the entries it answers stop being gaps. Everything else about a source —
    its pin, its release, the size of its list — is a statement about the outside world
    that has to be checked against the outside world, so it is not editable here.
    """
    from keel.schemas.coverage import CoverageEntry, CoverageFile

    directory = _dir()
    # Through the store's guard, not by joining strings. Built by hand this accepted
    # `../../elsewhere` and was stopped only by the file out there failing to parse as a
    # coverage document - which is luck, not a check.
    try:
        path = get_store().coverage_path(source_id)
    except ValueError as e:
        raise Forbidden(f"{source_id!r} is not a source name", hint=str(e)) from e
    if not path.is_file():
        known = sorted(p.stem for p in directory.glob("*.yaml")) if directory.is_dir() else []
        raise NotFound(
            f"no tracked source {source_id!r}",
            entity_type="coverage", entity_id=source_id,
            hint=f"tracked: {', '.join(known)}" if known else "no sources are tracked yet",
        )

    try:
        doc = CoverageFile(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
    except (yaml.YAMLError, ValidationError, TypeError) as e:
        raise Invalid(f"coverage/{source_id}.yaml does not parse: {e}") from e

    index = next((i for i, e in enumerate(doc.entries) if e.ref == ref), None)
    if index is None:
        raise NotFound(
            f"{source_id} has no entry {ref!r}",
            entity_type="coverage", entity_id=source_id, field="ref",
            hint="entries come from the published release and are not created here; "
                 "call get_coverage to see them",
        )

    existing = doc.entries[index]
    try:
        updated = CoverageEntry(
            ref=existing.ref,
            title=existing.title,     # the source's own wording is not ours to edit
            group=existing.group,
            state=state,
            threats=threats or [],
            mitigations=mitigations or [],
            note=note if note is not None else (existing.note if state == existing.state else None),
        )
    except ValidationError as e:
        raise invalid_from_pydantic(e, hint="see get_coverage for what each state means") from e

    store = get_store()
    missing = [t for t in updated.threats if t not in store.threats]
    missing += [m for m in updated.mitigations if m not in store.mitigations]
    if missing:
        raise IntegrityError(
            f"not in the catalog: {', '.join(missing)}",
            entity_type="coverage", entity_id=source_id,
            hint="a coverage claim is a public statement, so it may only name entries "
                 "that exist - author them first, or leave the row as a gap",
        )

    doc.entries[index] = updated
    payload = doc.model_dump(mode="json", exclude_none=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=1_000_000),
        encoding="utf-8",
    )
    return {"success": True, "source_id": source_id, "ref": ref,
            "entry": updated.model_dump(mode="json")}
