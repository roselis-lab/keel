"""Generate JSON Schema from the Pydantic models — the single structural source the
browser forms and IDE autocomplete read. Generated, never hand-written, so it cannot
drift from the models."""
from __future__ import annotations

from typing import Any

from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import MitigationLink, ThreatCreate, Weakness


def build_schemas() -> dict[str, dict[str, Any]]:
    """Return {entity: json_schema} for every authorable entity."""
    return {
        "threat": ThreatCreate.model_json_schema(),
        "mitigation": MitigationCreate.model_json_schema(),
        "weakness": Weakness.model_json_schema(),
        "mitigation_link": MitigationLink.model_json_schema(),
    }
