"""Report schema: a persisted assess-genai-with-library run.

Read-only from the app's side — a report is written once by the skill (via the Write
tool) and never edited through this schema; it exists here to parse and validate on
read. Enum fields reuse the catalog's own vocabularies (`Harm`, `Surface`, `Source`)
rather than defining parallel ones, so a report's risk signals line up with the model
they came from.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from keel.schemas.threat import Harm, Source, Surface

ExploitationComplexity = Literal["low", "medium", "high"]
Likelihood = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high", "critical"]
CoverageStatus = Literal["already_covered", "needs_implementation", "partial"]


class SourceInfo(BaseModel):
    """Who drives the threat, with the access and motive that make it realistic."""

    model_config = ConfigDict(extra="forbid")
    who: Source
    motive: str
    access: str


class RiskInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    likelihood: Likelihood
    severity: Severity
    reasoning: str


class Requirement(BaseModel):
    """One risk-reduction ask.

    Thin on purpose: a cataloged mitigation's `purpose`/`control_mechanism` already say
    what it does, and its threat-link `rationale` says why it fits — both one lookup away
    by `mitigation_id`. This records only the assessment-specific judgment (is it already
    covered in THIS deployment?) plus, for anything not yet in the catalog, the actual ask.
    """

    model_config = ConfigDict(extra="forbid")
    mitigation_id: str | None = None
    coverage_status: CoverageStatus
    coverage_note: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> "Requirement":
        if self.mitigation_id is None and not (self.description or "").strip():
            raise ValueError("description is required when mitigation_id is null")
        if self.mitigation_id is not None and self.description:
            raise ValueError(
                "description only applies when mitigation_id is null "
                "(a catalog card already names the control)"
            )
        needs_note = self.coverage_status in ("already_covered", "partial")
        if needs_note and not (self.coverage_note or "").strip():
            raise ValueError(
                "coverage_note is required when coverage_status is 'already_covered' or 'partial'"
            )
        if not needs_note and self.coverage_note:
            raise ValueError("coverage_note only applies to 'already_covered' or 'partial'")
        return self


class IgnoredMitigation(BaseModel):
    """A control linked to this threat in the catalog, but not applicable to this system."""

    model_config = ConfigDict(extra="forbid")
    mitigation_id: str
    reason: str


class Discarded(BaseModel):
    """A threat candidate ruled out during analysis.

    Deliberately NOT the full `Finding` chain — a discard is an id and why, nothing more.
    """

    model_config = ConfigDict(extra="forbid")
    id: str
    reason: str


class DialogueEntry(BaseModel):
    """One exchange with the specialist during the assessment, and what it changed.

    This is the reasoning that otherwise disappears into chat history: the question the
    agent asked, the answer or critique it got back, and how the analysis moved.
    """

    model_config = ConfigDict(extra="forbid")
    question: str
    answer: str
    impact: str


class Finding(BaseModel):
    """A threat that survived analysis, with its full chain."""

    model_config = ConfigDict(extra="forbid")
    id: str
    from_catalog: bool
    scenario: str
    source: SourceInfo
    asset: str
    attack_surface: Surface
    vulnerability: str
    exploitation_complexity: ExploitationComplexity
    harm: Harm
    risk: RiskInfo
    delta: str
    requirements: list[Requirement] = Field(default_factory=list)
    ignored_mitigations: list[IgnoredMitigation] = Field(default_factory=list)


class Report(BaseModel):
    """One assessment of one system on one date."""

    model_config = ConfigDict(extra="forbid")
    system_id: str
    system_name: str
    system_description: str = Field(
        ..., description="What the skill compares against when proposing a system match later"
    )
    date: str
    assessor: str = Field(..., description="From git config user.name/user.email at write time")
    delta_summary: str | None = Field(None, description="Re-assessments only: what changed and why")
    findings: list[Finding] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
    dialogue: list[DialogueEntry] = Field(default_factory=list)
