from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, JSON, ForeignKey

from app.database import Base

if TYPE_CHECKING:
    from app.models.mitigation import Mitigation


class Threat(Base):
    """A GenAI/LLM threat pattern in the library.

    The catalog is impact-centric: each threat is an impact (what asset/damage).
    How it is exploitable and whether it is a live path are carried by two prose
    facets, mapping onto the assessment methodology's chain.

    `description` — what the threat is (impact narrative).
    `impact_class` — the asset/damage anchor. Strict, minimal, closed vocabulary
        (validated in the Pydantic schema, not the DB) — keeps the catalog from
        sliding back into cataloging causes.
    `vulnerability` — list of prose items: HOW the system is exploitable. Each item
        is one recognizable pattern weaving cause (injection/hallucination assumed),
        interaction point (where), and the predisposing weakness. System-agnostic;
        this is the sole recognition anchor, so each item must read as a pattern an
        assessor can spot on an unseen architecture. Enumerate every manifestation
        point (axis coverage); the assessor binds them into scenarios (skill step 7).
    `reachability` — prose: the carve-outs under which the pattern is NOT a live
        path even when it matches — pure reachability (the attacker cannot influence
        the input / surface not exposed) and asset materiality (nothing of value
        behind it). Judged on the UN-mitigated architecture; phrased "not applicable
        if …". No positive check (that is tautological given `vulnerability`).
    """

    __tablename__ = "threats"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vulnerability: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reachability: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    mitigation_links: Mapped[list["ThreatMitigation"]] = relationship(
        back_populates="threat",
        cascade="all, delete-orphan",
        order_by="ThreatMitigation.mitigation_id",
    )


class ThreatMitigation(Base):
    """Junction linking a threat to a mitigation, with rationale."""

    __tablename__ = "threat_mitigations"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)  # "{threat_id}::{mitigation_id}"
    threat_id: Mapped[str] = mapped_column(ForeignKey("threats.id", ondelete="CASCADE"))
    mitigation_id: Mapped[str] = mapped_column(ForeignKey("mitigations.id", ondelete="CASCADE"))
    rationale: Mapped[str] = mapped_column(Text)

    threat: Mapped["Threat"] = relationship(back_populates="mitigation_links")
    mitigation: Mapped["Mitigation"] = relationship()
