from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, JSON

from app.database import Base


class Mitigation(Base):
    """A mitigation card — a minimally sufficient, verifiable specification of a control.

    `mitigation_class` — gating_control | detector | process | evidential_mitigation | corrective.
    The class is a switch: it sets how `control_mechanism` and `failure_behavior` are read.
    `status` — draft | verified (draft until it passes acceptance).
    See the mitigation style guide for how each field is authored.
    """

    __tablename__ = "mitigations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mitigation_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    formal_implementation_risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    maintainer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locus: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    control_mechanism: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    telemetry: Mapped[str | None] = mapped_column(Text, nullable=True)
    anti_patterns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[list | None] = mapped_column(JSON, nullable=True)
    faq: Mapped[list | None] = mapped_column(JSON, nullable=True)
