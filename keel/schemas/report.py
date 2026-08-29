"""Report schema: a persisted assess-genai-with-library run.

A report has two lives, and the `status` field is what keeps them apart. As a **draft**
it is unfinished work: the skill writes the first pass, then the specialist corrects it
in the UI — grades, wording, which requirements actually ship. Once **final** it is a
dated record of what was assessed on that day, and nothing rewrites it; correcting a
final report means opening a new dated draft beside it. Without that split, "the
assessment of 2026-08-26" degrades into "whatever someone last typed".

Enum fields reuse the catalog's own vocabularies (`Harm`, `Surface`, `Source`) rather
than defining parallel ones, so a report's risk signals line up with the model they
came from.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from keel.schemas.threat import Harm, Source, Surface

# Three levels, and the same three for every graded axis. An organisation's own risk
# policy is what turns a grade into an action, and policies are written against three
# bands; a fourth level ("critical") only ever meant "high, but really" and gave the
# assessor a choice with no consequence attached to it.
ExploitationComplexity = Literal["low", "medium", "high"]
Likelihood = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high"]
CoverageStatus = Literal["already_covered", "needs_implementation", "partial"]
ReportStatus = Literal["draft", "final"]


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
    included: bool | None = Field(
        None,
        description="Ships in the hand-off to the product team. None means 'not decided "
        "yet' and resolves to the obvious default: anything already covered is left out.",
    )

    @model_validator(mode="after")
    def _validate(self) -> "Requirement":
        # Resolve `included` on read so it is always a concrete boolean downstream, and
        # so the decision is recorded in the file the moment the report is saved. This
        # used to be a checkbox that existed only at copy time: it could not survive a
        # reload, which made it look like decoration rather than a judgment.
        if self.included is None:
            self.included = self.coverage_status != "already_covered"
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
    """One question the agent asked the specialist, and what the answer changed.

    This is the reasoning that otherwise disappears into chat history: the question, the
    answer it got back, and how the analysis moved because of it.
    """

    model_config = ConfigDict(extra="forbid")
    question: str
    answer: str
    impact: str


class RunMeta(BaseModel):
    """How this assessment ran — the record kept to improve the assessor, not the system.

    Everything here is about the process, which is why none of it reaches the hand-off:
    a product team has nowhere to put "the agent asked four questions". It exists because
    the only way to make the skill better is to see where it fell short, and the three
    things that show that are: what it thought to ask, what it FAILED to ask (so the
    specialist had to volunteer it), and where the specialist said it was wrong.

    `volunteered` is the sharpest of the three. A question the agent asked is a question
    the skill already knows to ask; a fact the specialist had to supply unprompted is a
    hole in the skill, named precisely.
    """

    model_config = ConfigDict(extra="forbid")
    started_at: str | None = Field(
        None, description="ISO timestamp when the skill began, so the run can be timed"
    )
    finished_at: str | None = Field(None, description="ISO timestamp when the report was written")
    questions: list[DialogueEntry] = Field(
        default_factory=list, description="What the agent asked, and what each answer changed"
    )
    volunteered: list[str] = Field(
        default_factory=list,
        description="Context the specialist gave that the agent never asked for — the skill's blind spots",
    )
    critique: list[str] = Field(
        default_factory=list,
        description="Where the specialist said the agent's reasoning was wrong, in their words",
    )


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
    status: ReportStatus = Field(
        "draft",
        description="draft = still being corrected in the UI; final = frozen dated record",
    )
    delta_summary: str | None = Field(None, description="Re-assessments only: what changed and why")
    findings: list[Finding] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
    # Named `meta`, not `_meta`: pydantic treats a leading underscore as a private
    # attribute and would not accept it as a field.
    meta: RunMeta = Field(
        default_factory=RunMeta, description="How the assessment ran — see RunMeta"
    )
