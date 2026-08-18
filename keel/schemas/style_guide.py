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


class StyleGuideEntity(BaseModel):
    entity_type: str
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
