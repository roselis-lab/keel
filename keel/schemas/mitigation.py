from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from keel.schemas.threat import EntityId

# The class is a switch: it sets how control_mechanism and failure_behavior are read.
MitigationClass = Literal[
    "gating_control", "detector", "process", "evidential_mitigation", "corrective"
]
ImplementationCoverage = Literal["shared", "local"]

# Which layer a control's mechanism naturally belongs to. An enum because "show me what
# could be built once for every product" is a real question a reader arrives with, and
# prose cannot answer it; a note because the answer is never obvious enough to stand alone.
Layer = Literal["product", "infrastructure", "split"]

# What happens when the control itself fails. Deliberately NOT constrained by
# mitigation_class: whether a blind detector is a shrug or a full stop is a property of
# the contour the control runs in, not of the control's kind.
FailureMode = Literal["fail_closed", "fail_open", "degraded"]


class Decision(BaseModel):
    """A closed answer with its reasoning.

    Two fields rather than two columns of prose: the value is what filters, groups and
    counts, and the note is what a value can never carry. Kept as one field so the schema
    can require the reasoning exactly where the value is recorded - a value written
    without it is the thing that turns a judgment into a label.
    """

    model_config = ConfigDict(extra="forbid")
    value: str
    note: str = Field(..., min_length=1, description="Why this value, in this control's terms")


class LocusDecision(Decision):
    value: Layer


class FailureDecision(Decision):
    value: FailureMode


class TelemetryEvent(BaseModel):
    """One logged event and what it has to carry to be worth logging."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="The event's name, as it is emitted")
    records: str = Field(..., description="What this event establishes, in one line")
    attributes: list[str] = Field(
        default_factory=list,
        description="Attributes without which the event proves nothing - attribution "
        "above all: who acted, on what, what was decided",
    )


class Telemetry(BaseModel):
    """The evidence a control leaves behind.

    Structured rather than prose because the events are the thing: they are counted,
    compared against what a system actually emits, and one day joined across controls
    into a single trace. None of that is possible against a paragraph.
    """

    model_config = ConfigDict(extra="forbid")
    events: list[TelemetryEvent] = Field(default_factory=list)
    evidence: str | None = Field(
        None,
        description="Where the record is held and for how long - a log the producing "
        "system can rewrite is not evidence",
    )


class ValidationCheck(BaseModel):
    """One pass/fail acceptance criterion with its test scenario."""

    criterion: str
    test_scenario: str | None = None
    expected_result: str | None = None
    base: bool = True


class FaqItem(BaseModel):
    question: str
    answer: str


class Implementation(BaseModel):
    """How an org realizes a control. Empty in the reference catalog; orgs fill it in."""

    model_config = ConfigDict(extra="forbid")
    title: str
    description: str
    reference: HttpUrl | None = None
    coverage: ImplementationCoverage = "local"
    covers: str | None = Field(
        None, description="Required when coverage='shared': the boundary this instance covers"
    )
    owner: str | None = Field(
        None, description="Accountable role for THIS deployed instance (RACI single-Accountable)"
    )

    @model_validator(mode="after")
    def _covers_required_when_shared(self) -> "Implementation":
        if self.coverage == "shared" and not (self.covers or "").strip():
            raise ValueError("covers is required when coverage is 'shared'")
        if self.coverage == "local" and self.covers:
            raise ValueError("covers only applies when coverage is 'shared'")
        return self


class MitigationBase(BaseModel):
    # `forbid`, like every other entity in the model. Without it a misspelled field was
    # silently dropped and the write still answered "changed", so the caller was told a
    # value had been saved that was never written anywhere.
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, description="Name of the mitigation")
    mitigation_class: MitigationClass | None = Field(
        None, description="gating_control | detector | process | evidential_mitigation | corrective"
    )
    purpose: str | None = Field(None, description="1-3 sentences: which class of failure it prevents")
    formal_implementation_risk: str | None = Field(
        None, description="What a useless-but-mitigation-looking implementation looks like"
    )
    review: str | None = Field(None, description="Change-triggers + safety-net review cadence")
    maintainer: str | None = None
    locus: LocusDecision | None = Field(
        None, description="Which layer this control's mechanism belongs to, and why")
    scope: str | None = Field(None, description="Deterministic applicability rule + profiles")
    out_of_scope: str | None = Field(
        None,
        description="What this control deliberately does not cover, and where that is "
        "handled instead. Its own field because a boundary written at the end of a long "
        "scope is the first thing dropped, and an absent field is visible",
    )
    control_mechanism: str | None = Field(None, description="Read per mitigation_class")
    failure_behavior: FailureDecision | None = Field(
        None, description="What happens when the control fails, and what makes it so")
    telemetry: Telemetry | None = None
    anti_patterns: list[str] | None = None
    validation: list[ValidationCheck] | None = None
    faq: list[FaqItem] | None = None
    positioning: str | None = Field(
        None,
        description="How this entry sits relative to the entries in the sources Keel "
        "tracks - only what the mapping itself does not already say. Where a source's "
        "entry is broader than this one, say what the rest of it is and where that "
        "lives. Never catalog state (which is computed) and never a to-do",
    )
    requires: list[str] = Field(
        default_factory=list,
        description="Mitigation ids this control presupposes. Use it only when this "
        "card's acceptance criteria cannot be checked without the other one being in "
        "place - not for controls that merely pair well",
    )
    implementations: list[Implementation] = Field(default_factory=list)


class MitigationCreate(MitigationBase):
    id: EntityId = Field(
        ...,
        description="Unique mitigation ID (e.g. CTRL-ACCESS-CONTROL). It is also the "
        "file name, so anything that could be read as a path is refused",
    )
    name: str = Field(..., description="Name of the mitigation")
    mitigation_class: MitigationClass = Field(..., description="Required on create")


class MitigationUpdate(MitigationBase):
    pass
