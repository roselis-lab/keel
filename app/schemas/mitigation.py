from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Honest enums pinned from the original library.
MitigationType = Literal["PREVENTIVE_HARD", "PREVENTIVE_SOFT", "DETECTIVE", "CORRECTIVE"]
RequirementLevel = Literal["MANDATORY", "RECOMMENDED"]


class MitigationBase(BaseModel):
    title: str | None = Field(None, description="Mitigation title")
    description: str | None = Field(None, description="What the mitigation is and how it reduces risk")
    type: MitigationType | None = Field(
        None,
        description="PREVENTIVE_HARD (blocks) | PREVENTIVE_SOFT (hinders) | DETECTIVE | CORRECTIVE",
    )
    requirement_level: RequirementLevel | None = Field(None, description="MANDATORY | RECOMMENDED")
    implementations: list[dict] | None = Field(None, description="Concrete ways to implement it")


class MitigationCreate(MitigationBase):
    id: str = Field(..., description="Unique mitigation ID (e.g. M-HITL)")
    type: MitigationType = Field(..., description="Required on create")


class MitigationUpdate(MitigationBase):
    pass


class Mitigation(BaseModel):
    """Mitigation in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    description: str | None = None
    type: str | None = None
    requirement_level: str | None = None
    implementations: list[dict] | None = None
