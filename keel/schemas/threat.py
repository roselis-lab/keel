"""Threat schema: component → surface/source → weakness(nature) → threat → harm →
reachability → mitigation(strength). Frozen vocabularies as Literals; prose fields
free; references are real URLs.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# --- frozen vocabularies (mirrored in catalog/{components,harm,surface,source}.yaml) ---
Component = Literal["model", "tool", "downstream", "memory", "knowledge-base", "identity-store"]
Harm = Literal["wrong-decision", "data-exposed", "code-execution", "downtime", "reputation-legal"]
Surface = Literal["user-agent", "agent-agent", "agent-environment"]
Source = Literal[
    "external-attacker", "internal", "hallucination", "error", "accident", "training-data"
]
Nature = Literal["targeted", "secondary"]
Strength = Literal["gating", "soft"]


class Weakness(BaseModel):
    """An architectural predisposing condition on a component."""

    model_config = ConfigDict(extra="forbid")
    component: Component
    text: str = Field(..., description="Architectural condition: cause + where + defect")
    nature: Nature = "targeted"


class MitigationLink(BaseModel):
    """Link to a mitigation card, with its role for this threat."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="A real CTRL-* mitigation id")
    strength: Strength = Field(..., description="gating (blocks) | soft (only lowers likelihood)")
    rationale: str
    exception: str | None = Field(
        None,
        description="Rare, narrow carve-out where this control doesn't apply to this threat "
        "(the threat itself stays live) — NOT a restatement of reachability",
    )


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    url: HttpUrl


class Threat(BaseModel):
    """A threat: what can go wrong, resting on weaknesses at components."""

    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    harm: Harm
    surface: list[Surface] = Field(default_factory=list)
    source: list[Source] = Field(default_factory=list)
    weaknesses: list[Weakness] = Field(..., min_length=1)
    reachability: str = Field(..., description="Rule-out gate on the un-mitigated arch: 'NOT applicable if…'")
    mitigations: list[MitigationLink] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ThreatCreate(Threat):
    """Create payload — same shape, id required."""


class ThreatUpdate(BaseModel):
    """Partial update; only provided fields change."""

    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    harm: Harm | None = None
    surface: list[Surface] | None = None
    source: list[Source] | None = None
    weaknesses: list[Weakness] | None = None
    reachability: str | None = None
    mitigations: list[MitigationLink] | None = None
    references: list[Reference] | None = None
    tags: list[str] | None = None
