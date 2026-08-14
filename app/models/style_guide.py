from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Integer, String, Text, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StyleGuideField(Base):
    """Authoring methodology for a single (entity_type, field_name) slot.

    Rows are auto-synced from the model columns of the tracked entities so new
    fields surface as coverage gaps. See services/style_guide_service.py.
    """

    __tablename__ = "style_guide_field"
    __table_args__ = (
        UniqueConstraint("entity_type", "field_name", name="uq_style_guide_field"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    field_name: Mapped[str] = mapped_column(String(100))

    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_requirements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    instructions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    avoid: Mapped[list | None] = mapped_column(JSON, nullable=True)
    examples: Mapped[list | None] = mapped_column(JSON, nullable=True)
    subfields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    allowed_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_orphan: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
