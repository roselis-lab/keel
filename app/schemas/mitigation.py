from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The class is a switch: it sets how control_mechanism and failure_behavior are read.
MitigationClass = Literal[
    "gating_control", "detector", "process", "evidential_mitigation", "corrective"
]
MitigationStatus = Literal["draft", "verified"]


class ValidationCheck(BaseModel):
    """One pass/fail acceptance criterion with its test scenario."""

    criterion: str
    test_scenario: str | None = None
    expected_result: str | None = None
    base: bool = True


class FaqItem(BaseModel):
    question: str
    answer: str


class MitigationBase(BaseModel):
    name: str | None = Field(None, description="Name of the mitigation")
    status: MitigationStatus | None = Field(None, description="draft | verified")
    mitigation_class: MitigationClass | None = Field(
        None, description="gating_control | detector | process | evidential_mitigation | corrective"
    )
    purpose: str | None = Field(None, description="1-3 sentences: which class of failure it prevents")
    formal_implementation_risk: str | None = Field(
        None, description="What a useless-but-mitigation-looking implementation looks like"
    )
    review: str | None = Field(None, description="Change-triggers + safety-net review cadence")
    maintainer: str | None = None
    owner: str | None = None
    locus: str | None = Field(None, description="product / infrastructure / split + rationale")
    scope: str | None = Field(None, description="Deterministic applicability rule + profiles + boundary")
    control_mechanism: str | None = Field(None, description="Read per mitigation_class")
    failure_behavior: str | None = Field(None, description="Read per mitigation_class")
    telemetry: str | None = None
    anti_patterns: list[str] | None = None
    validation: list[ValidationCheck] | None = None
    faq: list[FaqItem] | None = None


class MitigationCreate(MitigationBase):
    id: str = Field(..., description="Unique mitigation ID (e.g. CTRL-ACCESS-CONTROL)")
    name: str = Field(..., description="Name of the mitigation")
    mitigation_class: MitigationClass = Field(..., description="Required on create")


class MitigationUpdate(MitigationBase):
    pass


class Mitigation(BaseModel):
    """Mitigation card in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None = None
    status: str | None = None
    mitigation_class: str | None = None
    purpose: str | None = None
    formal_implementation_risk: str | None = None
    review: str | None = None
    maintainer: str | None = None
    owner: str | None = None
    locus: str | None = None
    scope: str | None = None
    control_mechanism: str | None = None
    failure_behavior: str | None = None
    telemetry: str | None = None
    anti_patterns: list[str] | None = None
    validation: list[dict] | None = None
    faq: list[dict] | None = None
