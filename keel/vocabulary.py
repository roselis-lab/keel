"""The four frozen vocabularies, read from `catalog/*.yaml`.

`harm`, `surface`, `source` and `components` are enforced as `Literal`s in the schemas,
which is what makes an unknown value impossible. The YAML files carry what the Literal
cannot: a human name and a one-line gloss for each value — "downstream" means "a system
that executes or consumes the agent's output (CI/CD, DB, renderer)", and without that a
reader is left guessing from a bare token.

Those files existed and nothing read them. A file that describes the system but is never
loaded is worse than no file: it drifts, and its drift is invisible. So they are loaded
now, and `validate_catalog` requires their keys to match the Literals exactly in both
directions — a value added to one and not the other is an error, not a surprise.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, get_args

import yaml

from keel.schemas.threat import Component, Harm, Source, Surface
from keel.store import resolve_catalog_dir

# file stem -> (top-level key in that file, the Literal it must match)
VOCABULARIES: dict[str, tuple[str, tuple[str, ...]]] = {
    "harm": ("harm", get_args(Harm)),
    "surface": ("surface", get_args(Surface)),
    "source": ("source", get_args(Source)),
    "components": ("components", get_args(Component)),
}


def load_vocabularies(catalog_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return `{name: {value: {name, desc, ...}}}`, skipping any file that is missing or
    malformed. `validate_catalog` is what complains about those; this stays quiet so a
    half-set-up fork still starts."""
    catalog_dir = catalog_dir or resolve_catalog_dir()
    out: dict[str, dict[str, Any]] = {}
    for stem, (key, _) in VOCABULARIES.items():
        path = catalog_dir / f"{stem}.yaml"
        if not path.is_file():
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        entries = data.get(key) if isinstance(data, dict) else None
        if isinstance(entries, dict):
            out[stem] = entries
    return out


def vocabulary_errors(catalog_dir: Path | None = None) -> list[str]:
    """Every way a vocabulary file can disagree with the schema that enforces it."""
    catalog_dir = catalog_dir or resolve_catalog_dir()
    errors: list[str] = []

    for stem, (key, allowed) in VOCABULARIES.items():
        rel = f"{stem}.yaml"
        path = catalog_dir / rel
        if not path.is_file():
            errors.append(f"{rel}: missing — this file is the gloss for the {key!r} vocabulary")
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            errors.append(f"{rel}: not readable as YAML: {e}")
            continue
        if not isinstance(data, dict) or not isinstance(data.get(key), dict):
            errors.append(f"{rel}: expected a mapping under {key!r}")
            continue

        entries = data[key]
        extra = sorted(set(entries) - set(allowed))
        missing = sorted(set(allowed) - set(entries))
        if extra:
            errors.append(
                f"{rel}: {', '.join(repr(x) for x in extra)} "
                f"— not in the schema; add to the Literal in keel/schemas/threat.py or remove"
            )
        if missing:
            errors.append(
                f"{rel}: {', '.join(repr(x) for x in missing)} "
                f"— in the schema but not glossed here; every value needs a name and a description"
            )
        for value, entry in entries.items():
            if value in extra:
                continue
            if not isinstance(entry, dict) or not (entry.get("name") and entry.get("desc")):
                errors.append(f"{rel}: {value!r} needs both a `name` and a `desc`")

    return errors
