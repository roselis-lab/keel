"""Generate JSON Schema from the Pydantic models — the single structural source the
browser forms and IDE autocomplete read. Generated, never hand-written, so it cannot
drift from the models."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import MitigationLink, ThreatCreate, Weakness

DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def build_schemas() -> dict[str, dict[str, Any]]:
    """Return {entity: json_schema} for every authorable entity."""
    return {
        "threat": ThreatCreate.model_json_schema(),
        "mitigation": MitigationCreate.model_json_schema(),
        "weakness": Weakness.model_json_schema(),
        "mitigation_link": MitigationLink.model_json_schema(),
    }


def _serialize(schemas: dict[str, Any]) -> dict[str, str]:
    """entity -> file text. Sorted keys + trailing newline for stable diffs."""
    return {
        entity: json.dumps(schema, indent=2, sort_keys=True) + "\n"
        for entity, schema in schemas.items()
    }


def write_schemas(out_dir: Path = DEFAULT_SCHEMA_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for entity, text in _serialize(build_schemas()).items():
        (out_dir / f"{entity}.schema.json").write_text(text, encoding="utf-8")


def schemas_are_fresh(out_dir: Path = DEFAULT_SCHEMA_DIR) -> bool:
    """True when the on-disk files match what the models would generate right now."""
    for entity, text in _serialize(build_schemas()).items():
        path = out_dir / f"{entity}.schema.json"
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            return False
    return True
