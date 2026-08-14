from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, JSON

from app.database import Base


class Mitigation(Base):
    """A mitigation (architectural control) that reduces one or more threats.

    `type` — PREVENTIVE_HARD | PREVENTIVE_SOFT | DETECTIVE | CORRECTIVE
             (hard = architecturally blocks; soft = hinders / lowers likelihood).
    `requirement_level` — MANDATORY | RECOMMENDED.
    Allowed values are enforced in the Pydantic schemas.
    """

    __tablename__ = "mitigations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    requirement_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    implementations: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
