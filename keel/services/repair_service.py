"""Raw-file repair for records the store refused to load.

A record that fails its schema never enters the working set, so there is nothing for
the structured editor to open — it cannot build a form for a record it could not parse.
That would leave the one thing the dashboard shouts about as the one thing you cannot
act on from the app, which is the wrong way round: something reported as broken should
be fixable where it is reported.

So this serves the file's text and takes it back, validating on the way in. It is a
deliberately narrow door: only YAML files directly inside the catalog's own three
directories, and a save that does not validate is refused with the field and the reason
rather than written and reported later.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.errors import Forbidden, Invalid, NotFound
from keel.store import get_store

# Allowlists, checked before any path is built — an untrusted segment never reaches the
# filesystem. Mirrors the shape `keel.githistory` uses for the same reason.
_DIRS = {"threats", "mitigations", "style_guide"}
_STEM_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _resolve(rel_path: str) -> Path:
    """The file, or a Forbidden. Every rejection names the shape that would be accepted,
    because a caller told only "no" tries a variation of the same wrong thing."""
    hint = f"expected '<directory>/<file>.yaml' with directory in {sorted(_DIRS)}"
    parts = rel_path.split("/")
    if len(parts) != 2:
        raise Forbidden(f"{rel_path!r} is not a catalog path", hint=hint)
    directory, name = parts
    if directory not in _DIRS:
        raise Forbidden(f"unknown catalog directory {directory!r}", hint=hint)
    if not name.endswith(".yaml") or not _STEM_RE.match(name):
        raise Forbidden(f"not a catalog file name: {name!r}", hint=hint)

    base = Path(get_store().dir).resolve()
    path = (base / directory / name).resolve()
    if path.parent != base / directory:  # belt and braces after the pattern check
        raise Forbidden("path escapes the catalog directory", hint=hint)
    return path


def _require_file(rel_path: str) -> Path:
    path = _resolve(rel_path)
    if not path.is_file():
        raise NotFound(f"no catalog file at {rel_path}", entity_id=rel_path)
    return path


def _validate(rel_path: str, text: str) -> list[dict[str, str | None]]:
    """Return the same `{field, message}` shape the store's load problems carry, so the
    UI renders a rejected save and a rejected load identically."""
    directory = rel_path.split("/")[0]
    try:
        rec = yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        return [{"field": None, "message": f"not readable as YAML: {e}"}]
    if not isinstance(rec, dict):
        return [{"field": None, "message": "not a YAML mapping"}]

    if directory == "style_guide":
        if not isinstance(rec.get("fields"), dict):
            return [{"field": "fields", "message": "expected a mapping with a 'fields' mapping"}]
        return []

    stem = rel_path.split("/")[1][: -len(".yaml")]
    if rec.get("id") != stem:
        return [{
            "field": "id",
            "message": f"id {rec.get('id')!r} does not match filename {stem!r}",
        }]

    from keel.store import _model_for

    try:
        _model_for(directory)(**rec)
    except ValidationError as e:
        return [
            {"field": ".".join(str(x) for x in err["loc"]) or None, "message": err["msg"]}
            for err in e.errors()
        ]
    return []


async def read_file(rel_path: str) -> dict[str, Any]:
    path = _require_file(rel_path)
    text = path.read_text(encoding="utf-8")
    return {"path": rel_path, "text": text, "errors": _validate(rel_path, text)}


async def write_file(rel_path: str, text: str) -> dict[str, Any]:
    """Validate, then write. A save that would not load is refused, so the file on disk
    and the catalog in memory cannot drift apart through this door."""
    path = _require_file(rel_path)

    errors = _validate(rel_path, text)
    if errors:
        raise Invalid(
            f"{rel_path} would still not load",
            details=errors,
            hint="this door cannot write a file the loader would refuse - fix the "
                 "reported fields and save again",
        )

    store = get_store()
    with store.lock:
        path.write_text(text, encoding="utf-8")
        store.reload()
    return {"success": True, "path": rel_path, "errors": [], "problems": store.problems}
