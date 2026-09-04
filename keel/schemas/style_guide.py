from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StyleGuideFieldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    field_name: str
    purpose: str | None = None
    content_requirements: list[str] | None = None
    instructions: list[str] | None = None
    avoid: list[str] | None = None
    examples: list[str] | None = None
    subfields: dict[str, Any] | None = None
    allowed_values: dict[str, Any] | None = None
    is_orphan: bool = False
    updated_by: str | None = None


class StyleGuideEntityGuide(BaseModel):
    """The bar for the record as a whole, not for any one of its fields.

    Some rules are about whether a record should exist and where its edges are, and those
    have no field to live in. Parked in a field they are invisible to anyone reading a
    different one, and copied into several they go stale in all but the last. Same slot
    names as a field's bar, so there is nothing extra to learn and the same renderer and
    writer serve both.
    """

    model_config = ConfigDict(extra="forbid")
    purpose: str | None = Field(
        None, description="What one record of this entity is, in a sentence"
    )
    instructions: list[str] | None = Field(
        None,
        description="What to settle before writing any field: whether this is one record "
        "or part of one, and which decisions come first",
    )
    avoid: list[str] | None = Field(
        None, description="Failure modes of the record as a whole, named"
    )


class StyleGuideEntity(BaseModel):
    entity_type: str
    entity: StyleGuideEntityGuide | None = None
    fields: dict[str, StyleGuideFieldRead]


class StyleGuideFull(BaseModel):
    version: str = "1.0"
    entities: dict[str, StyleGuideEntity]


class FieldCoverage(BaseModel):
    field_name: str
    completeness: int = Field(ge=0, le=100)
    is_orphan: bool = False


class EntityCoverage(BaseModel):
    entity_type: str
    fields: list[FieldCoverage]
    overall: int = Field(ge=0, le=100)


class CoverageReport(BaseModel):
    entities: list[EntityCoverage]
    overall: int = Field(ge=0, le=100)
