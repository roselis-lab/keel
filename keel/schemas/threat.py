from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Strict, minimal, closed anchor. Enforced here (Pydantic), not in the DB — the
# column is a plain string so growing it is a deliberate decision, not a schema
# accident. Keep this list tight; it is a near-complete partition of "what asset".
ImpactClass = Literal[
    "decision-integrity",
    "data-confidentiality",
    "infrastructure-execution",
    "resource-availability",
    "reputation-compliance",
    "recon-exposure",
]


class MitigationRef(BaseModel):
    """A mitigation linked to a threat, with rationale."""

    mitigation_id: str
    rationale: str


class ThreatBase(BaseModel):
    title: str | None = Field(None, description="Threat title")
    description: str | None = Field(None, description="What the threat is (impact narrative)")
    impact_class: ImpactClass | None = Field(None, description="Asset/damage anchor (strict enum)")
    vulnerability: list[str] | None = Field(
        None,
        description="Prose list: HOW the system is exploitable — each item one recognizable pattern (cause+where+weakness). Sole recognition anchor.",
    )
    reachability: str | None = Field(
        None,
        description="Prose: carve-outs when it is NOT a live path — reachability + asset materiality, un-mitigated; 'not applicable if …'",
    )
    tags: list[str] | None = Field(None, description="Coarse labels, e.g. Vibe-Coding")


class ThreatCreate(ThreatBase):
    id: str = Field(..., description="Unique threat ID (e.g. T-INJECT)")


class ThreatUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    impact_class: ImpactClass | None = None
    vulnerability: list[str] | None = None
    reachability: str | None = None
    tags: list[str] | None = None


class Threat(BaseModel):
    """Threat in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    description: str | None = None
    impact_class: str | None = None
    vulnerability: list[str] | None = None
    reachability: str | None = None
    tags: list[str] | None = None
    mitigations: list[MitigationRef] = Field(default_factory=list)
